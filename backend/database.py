from sqlmodel import create_engine, SQLModel
import os


sqlite_file_name = "kobi_asistan.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    from .models import Task
    SQLModel.metadata.create_all(engine)