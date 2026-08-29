import time
from fastapi import FastAPI, Request
from pydantic import BaseModel
from agent import get_region_summary, answer_question

app = FastAPI(title="InsightEngine: Enterprise AI Data Agent API")

class Question(BaseModel):
    question: str

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response

@app.get("/")
def home():
    return {
        "message": "InsightEngine: Enterprise AI Data Agent Running"
    }

@app.get("/summary")
def summary():
    return {
        "result": get_region_summary()
    }

@app.post("/ask")
def ask(question: Question):
    return answer_question(question.question)
