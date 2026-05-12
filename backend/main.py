from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from .models import Task
from .database import create_db_and_tables
from . import crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    print("Veritabanı tabloları oluşturuldu ve uygulama hazır!")
    
    yield

    print("Uygulama kapanıyor...")

app = FastAPI(title="ProKOBİ Backend API", lifespan=lifespan)

@app.get("/tasks")
def read_tasks():
    return crud.get_all_tasks()

@app.post("/tasks")
def add_task(task: Task):
    return crud.create_task(task)

@app.patch("/tasks/update")
def update_task(title: str, new_status: str):
    updated_task = crud.update_task_status_by_title(title, new_status)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    return update_task