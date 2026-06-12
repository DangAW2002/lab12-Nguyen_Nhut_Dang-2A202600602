"""
❌ BASIC — Agent "Kiểu Localhost" (Anti-patterns)

Đây là cách KHÔNG NÊN làm. Dùng để so sánh với advanced/.
Hãy đếm bao nhiêu vấn đề bạn tìm được trong file này.
"""
import os

from fastapi import FastAPI
import uvicorn
from utils.mock_llm import ask

app = FastAPI(title="My Agent")

# ❌ Vấn đề 1: API key hardcode trong code
# Nếu push lên GitHub → key bị lộ ngay lập tức
OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"
DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"

# ❌ Vấn đề 2: Không có config management
DEBUG = True
MAX_TOKENS = 500


@app.get("/")
def home():
    return {"message": "Hello! Agent is running on my machine :)"}


@app.post("/ask")
def ask_agent(question: str):
    # ❌ Vấn đề 3: Print thay vì proper logging
    print(f"[DEBUG] Got question: {question}")
    print(f"[DEBUG] Using key: {OPENAI_API_KEY}")  # ❌ log ra secret!

    response = ask(question)

    print(f"[DEBUG] Response: {response}")
    return {"answer": response}


# ❌ Vấn đề 4: Không có health check endpoint
# Nếu agent crash, platform không biết để restart

# ❌ Vấn đề 5: Port cố định — không đọc từ environment
# Trên Railway/Render, PORT được inject qua env var
if __name__ == "__main__":
    print("Starting agent on localhost:8081...")
    uvicorn.run(
        "app:app",
        host="localhost",   # ❌ chỉ chạy được trên local
        port=8081,          # ❌ cứng port
        reload=True         # ❌ debug reload trong production
    )
