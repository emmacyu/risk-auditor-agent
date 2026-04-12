import asyncio
import os
import sys
from pathlib import Path
project_root = Path(os.path.abspath(__file__)).parent.parent
sys.path.append(str(project_root))

from app.services.vector_store import get_vector_store

async def test():
    vs = get_vector_store()
    retriever = vs.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke("what is Principle 3.6")
    print(f"Num docs found: {len(docs)}")
    for i, d in enumerate(docs):
        print(f"Doc {i}:\n{d.page_content[:200]}")

if __name__ == "__main__":
    asyncio.run(test())
