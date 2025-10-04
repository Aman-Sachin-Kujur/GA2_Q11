from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from pathlib import Path

# --- Data Path Configuration ---
FILE_PATH = Path("q-fastapi.csv")

# --- Pydantic Models ---
class Student(BaseModel):
    studentId: int
    class_name: str = Field(..., alias="class")  # Internal name is class_name, JSON uses "class"

    # Ensure alias is used on export
    model_config = {"populate_by_name": True}  # Allows using class_name in constructor

class StudentsResponse(BaseModel):
    students: List[Student]

# --- Data Loading ---
try:
    df = pd.read_csv(FILE_PATH, dtype={'studentId': int, 'class': str})
    ALL_STUDENTS_DATA = df.to_dict('records')
    print(f"INFO: Successfully loaded {len(ALL_STUDENTS_DATA)} student records.")
except FileNotFoundError:
    ALL_STUDENTS_DATA = []
    print(f"CRITICAL: CSV file not found at {FILE_PATH}. Returning empty data.")

# --- Application Setup and CORS ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# --- REST API Endpoint ---
@app.get("/api")
async def get_students_data(
    class_filter: Optional[List[str]] = Query(None, alias="class")
):
    if not ALL_STUDENTS_DATA:
        return {"students": []}

    filtered_data = ALL_STUDENTS_DATA
    if class_filter:
        filtered_data = [s for s in ALL_STUDENTS_DATA if s['class'] in class_filter]

    # Return as list of dicts with correct key "class"
    return {"students": filtered_data}
