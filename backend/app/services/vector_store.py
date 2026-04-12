import os
import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

# Using local HuggingFace embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store_instance = None

def get_chroma_client():
    # Retrieve Chroma configuration from environment with fallbacks for local execution
    chroma_host = os.environ.get("CHROMA_HOST", "localhost")
    chroma_port = int(os.environ.get("CHROMA_PORT", "8001"))
    # Connect directly to the isolated Docker microservice via HTTP
    return chromadb.HttpClient(host=chroma_host, port=chroma_port)

def process_pdf(file_path: str):
    global vector_store_instance
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, 
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )
    splits = text_splitter.split_documents(docs)
    
    # Send the chunked documents into the standalone server via HttpClient
    client = get_chroma_client()
    vector_store_instance = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings,
        client=client,
        collection_name="risk_auditor_docs"
    )
    return vector_store_instance

def get_vector_store():
    global vector_store_instance
    if vector_store_instance is None:
        try:
            client = get_chroma_client()
            db = Chroma(client=client, collection_name="risk_auditor_docs", embedding_function=embeddings)
            
            # Use HTTP Client to fetch remote collection data to verify if it's empty
            collection = client.get_or_create_collection("risk_auditor_docs")
            count = collection.count()
            if count > 0:
                vector_store_instance = db
                print(f"📦 [Microservice Log]: Successfully bridged to the standalone Chroma container via HTTP, mounting {count} memory chunks!")
            else:
                vector_store_instance = None
        except Exception as e:
            # Fail silently here, meaning the service contains no data or is offline
            vector_store_instance = None
                
    return vector_store_instance
