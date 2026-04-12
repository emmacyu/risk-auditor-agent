import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os
from pathlib import Path

# 将项目根目录以及 backend 加入环境变量，方便导包
project_root = Path(os.path.abspath(__file__)).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "backend"))

from backend.app.main import app

from fastapi.testclient import TestClient

def test_chat_endpoint():
    print("\n🌐 开始启动虚拟浏览器 HTTP 测试...")
    # 使用 TestClient 并用 with 上下文，它会强制唤醒 FastAPI 的 lifespan
    with TestClient(app) as client:
        payload = {
            "message": "你好啊，智能风控引擎！",
            "user_id": "fastapi_api_tester_02"
        }
        
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
        
        print("\n✅ API 返回状态码：200 OK")
        print(f"🤖 API 解析返回的大模型文本: \n{data['answer']}\n")
