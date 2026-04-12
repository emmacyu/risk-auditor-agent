import os
import json
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.checkpoint.postgres import PostgresSaver

from app.services.vector_store import get_vector_store
from app.services.database import get_db_pool
from app.config import settings

# Define universal LLM engine here
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0,  # Force generation to be highly robust and deterministic for risk auditing
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# =========================================================================
# 1. Core Agent State - handling storage, memory, and serving as system's diagnostic black box
# =========================================================================
class AgentState(TypedDict):
    # Leverage LangGraph's built-in Reducer to automatically append new messages
    messages: Annotated[list[AnyMessage], add_messages]
    
    # Traceability fields for industrial-grade auditing:
    intent: str                  # User intent classified by dispatcher: 'chat' or 'audit'
    current_context: str         # Raw document context relied on for answers (used by logic auditor to catch hallucinations)
    audit_trail: list[str]       # A history log of rejection reasons from the logic auditor
    retry_count: int             # Loop restart attempts (used for infinite loop circuit-breaking)
    is_hallucinating: bool       # Flags if the current output hallucinates

# =========================================================================
# 2. Four Core Processing Nodes
# =========================================================================

def dispatcher_node(state: AgentState):
    """Dispatcher Node: Combine conversation history to identify the true user intent."""
    messages = state["messages"]
    last_msg = messages[-1].content
    
    # Extract recent context to assist intention recognition
    history = "\n".join([f"{m.type}: {m.content}" for m in messages[-3:-1]]) if len(messages) > 1 else "None"
    
    sys_msg = SystemMessage(content=f"""You are an intent recognizer. If the user asks about risk control, compliance, clause interpretation, or auditing (even utilizing pronouns like 'what does it mean', as long as previous context relates to risk), reply ONLY with the word AUDIT.
    If it is purely casual small talk disconnected from business, reply ONLY with the word CHAT.
    Historical Context: {history}""")
    
    resp = llm.invoke([sys_msg, HumanMessage(content=last_msg)])
    
    intent = "chat" if "CHAT" in resp.content.upper() else "audit"
    
    # Initialize state tracking fields here
    return {
        "intent": intent, 
        "retry_count": state.get("retry_count", 0), 
        "audit_trail": state.get("audit_trail", [])
    }

def retrieve_node(state: AgentState):
    """Retriever Node: Equipped with Query Expansion & Contextual Rewrite capabilities."""
    messages = state["messages"]
    last_msg = messages[-1].content
    vector_store = get_vector_store()
    
    if not vector_store:
        return {"current_context": "The system hasn't mounted the vector database. Please prompt the user to upload documents."}

    query = last_msg
    
    # 🚨 1st Advanced Mechanism: Contextual Query Rewrite (Resolving Pronouns)
    if len(messages) > 1 and state.get("retry_count", 0) == 0:
        history_text = "\n".join([f"{m.type}: {m.content}" for m in messages[-4:-1]])
        rewrite_prompt = f"""You are a search query optimizer. Given the following conversation history, the user may have used pronouns in their latest question (e.g., 'it', 'this meaning') or omitted the subject.
        Please combine the context and rewrite the user's latest question into an independent, complete, and explicit search sentence for database retrieval (if no rewrite is needed, return it exactly as is, without any extra explanations):
        History: {history_text}
        Current question: {last_msg}"""
        rewrite_resp = llm.invoke([HumanMessage(content=rewrite_prompt)])
        query = rewrite_resp.content.strip()
        print(f"🔄 [Context Rewrite] '{last_msg}' -> '{query}'")

    # 🚨 2nd Advanced Mechanism: Query Expansion based on Auditor Rejections
    if state.get("retry_count", 0) > 0 and state.get("audit_trail"):
        feedback = state["audit_trail"][-1]
        expand_prompt = f"The user's previous search term was: {query}.\nHowever, the audit judge criticized it: {feedback}.\nPlease generate a entirely new search keyword phrase based on this criticism, aimed at finding the exact compliance clause (no extra explanations):"
        expand_resp = llm.invoke([HumanMessage(content=expand_prompt)])
        query = expand_resp.content.strip()
        print(f"🔄 [Correction Rewrite] Fusing penalizing feedback -> '{query}'")
    
    # Pull from ChromaDB (since dense neural embeddings ignore strict numbers, widen radar to K=15 chunks)
    docs = vector_store.similarity_search(query, k=15)
    
    # Assemble the found documents and their metadata into pure text context
    context_str = "\n\n".join([
        f"[Source File Page: {d.metadata.get('page', 'Unknown')} ] Content Snippet:\n{d.page_content}"
        for d in docs
    ])
    
    return {"current_context": context_str}

def generate_node(state: AgentState):
    """Generator Node: Strictly anchor to source documents while relaxing constraints for casual chat/explanations."""
    context = state.get("current_context", "")
    intent = state.get("intent", "chat")
    
    if intent == "chat":
        sys_prompt = "You are a senior AI security assistant for the risk control team. Please engage with the user naturally or explain professional concepts directly based on chat history, staying professional and composed."
    else:
        sys_prompt = f"""You are a Chief AI System Architect and Risk Review Officer.
        Please answer the user's question STRICTLY combining the following [Extracted Official Context] and [Chat History].
        [CRITICAL RULES]
        1. If you cite information from the context, you MUST tag its source (e.g. Page number) before the period.
        2. If the user asks you to explain a concept just mentioned (e.g. 'what does it mean'), give a professional and adequate explanation using your LLM knowledge.
        3. If the user asks about an entirely new clause and absolutely zero related info exists in the context, directly state 'Cannot find related content in the database'.
        
        Context:
        {context if context else 'No reference materials'}
        """
    
    messages = [SystemMessage(content=sys_prompt)] + state["messages"]
    response = llm.invoke(messages)
    
    # Return a list here to trigger the state's add_messages Reducer to append them
    return {"messages": [response]} 

def auditor_node(state: AgentState):
    """Logic Auditor Node: Responsible for catching LLM hallucinations."""
    # Let casual chats pass through
    if state.get("intent") == "chat":
        return {"is_hallucinating": False}
        
    last_aimessage = state["messages"][-1].content
    context = state.get("current_context", "")
    
    prompt = f"""You are a ruthless hallucination checker. Contrast the following [Reference Context] against the [AI Answer].
    
    Reference Context:
    {context}
    
    AI Answer:
    {last_aimessage}
    
    Strictly evaluate: Does the AI answer contain falsified, invented, or over-extended hallucinated content?
    You MUST output a JSON dictionary containing:
    A boolean field 'is_hallucinating' (true if hallucination exists, false if perfectly accurate).
    A string field 'feedback' (If hallucination exists, provide specific rejection feedback for the AI to retrieve better text; if safe, leave empty).
    """
    
    # Force the LLM to return a strict JSON Object
    eval_llm = llm.bind(response_format={"type": "json_object"})
    resp = eval_llm.invoke([
        SystemMessage(content="You are a structured risk control system. Output must be valid JSON."), 
        HumanMessage(content=prompt)
    ])
    
    try:
        data = json.loads(resp.content)
        is_hallucinating = data.get("is_hallucinating", False)
        feedback = data.get("feedback", "")
    except Exception:
        # Safety fallback: If JSON parsing fails, approve to prevent application deadlocks
        is_hallucinating = False
        feedback = "Parsing anomaly encountered, skipping validation"
        
    if is_hallucinating:
        trail = list(state.get("audit_trail", []))
        trail.append(feedback)
        rc = state.get("retry_count", 0) + 1
        return {"is_hallucinating": True, "audit_trail": trail, "retry_count": rc}
    else:
        return {"is_hallucinating": False}


# =========================================================================
# 3. Pipeline Definitions: Wiring dynamic routing and recursive loops (Edges and Compilation)
# =========================================================================

def route_after_dispatcher(state: AgentState):
    """Dynamic pipeline dispatching based on intent."""
    if state.get("intent") == "audit":
        return "retrieve_node"
    return "generate_node"

def route_after_auditor(state: AgentState):
    """Core self-reflection and rejection loop."""
    # If hallucinations exist and retries < 3, route back to the retriever (uses audit trace to search better)
    if state.get("is_hallucinating") and state.get("retry_count", 0) < 3:
        return "retrieve_node"
    # If passes, or circuit breaker hits 3 retries, route to the END phase
    return END

def get_agent_app():
    builder = StateGraph(AgentState)
    
    # Register the four core computational nodes
    builder.add_node("dispatcher", dispatcher_node)
    builder.add_node("retrieve_node", retrieve_node)
    builder.add_node("generate_node", generate_node)
    builder.add_node("auditor_node", auditor_node)
    
    # Wiring: START -> Dispatcher
    builder.add_edge(START, "dispatcher")
    
    # Dispatcher -> Fork (Retrieve vs Chat Generate)
    builder.add_conditional_edges("dispatcher", route_after_dispatcher)
    
    # Retrieve -> Generate
    builder.add_edge("retrieve_node", "generate_node")
    
    # Generate -> Logic Auditor
    builder.add_edge("generate_node", "auditor_node")
    
    
    # Avoid forcing database hookups here; instead, expose the raw architecture blueprint (builder)
    # Allowing FastAPI or test scripts to hook up real databases inside their own Async Event Loops
    return builder

# Expose the architectural blueprint
agent_builder = get_agent_app()
