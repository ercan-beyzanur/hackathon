from sqlmodel import Session, select
from .models import Task
from .database import engine

def get_all_tasks():
    with Session(engine) as session:
        return session.exec(select(Task)).all()
    
def create_task(task: Task):
    with Session(engine) as session:
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    
def update_task_status_by_title(title: str, new_status: str):
    with Session(engine) as session:
        statement = select(Task).where(Task.title.contains(title))
        task = session.exec(statement).first()
        if task:
            task.status = new_status
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
        return None