from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    task_time: Optional[str] = Field(default=None)
    status: str = Field(default="To Do")
    created_at: datetime = Field(default_factory=datetime.now)