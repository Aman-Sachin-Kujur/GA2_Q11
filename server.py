from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
# Pydantic V2 required for configuration
from pydantic import BaseModel, Field, ConfigDict 
from typing import List, Optional
import pandas as pd
from pathlib import Path
import os

# --- Data Path Configuration (FIXED for Codespaces) ---
# Look for the file in the current working directory (project root), 
# which is the most reliable way in Codespaces.
FILE_PATH = Path("q-fastapi.csv") 

# --- Pydantic Models (Fixes "Property Name Mismatch") ---

class Student(BaseModel):
    # CRITICAL FIX: Ensures Pydantic uses the alias ("class") for output JSON keys
    model_config = ConfigDict(populate_by_name=True)
    
    studentId: int
    # Alias ensures Python's internal 'class_name' maps to JSON's required 'class'
    class_name: str = Field(alias="class") 

# Required response structure: {"students": [...]}
class StudentsResponse(BaseModel):
    students: List[Student]

# --- Data Loading ---
try:
    # Read the CSV
    df = pd.read_csv(FILE_PATH, dtype={'studentId': int, 'class': str})
    
    # Rename the CSV column to match the internal Pydantic field name
    df.rename(columns={'class': 'class_name'}, inplace=True)
    
    # Convert to a list of dictionaries (maintains CSV order)
    ALL_STUDENTS_DATA = df.to_dict('records')
    print(f"INFO: Successfully loaded {len(ALL_STUDENTS_DATA)} student records.")
    
except FileNotFoundError:
    ALL_STUDENTS_DATA = []
    print(f"CRITICAL: CSV file not found at {FILE_PATH}. Returning empty data.")


# --- Application Setup and CORS ---
app = FastAPI()

# Enable CORS for GET requests from any origin (as required)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["GET"],  
    allow_headers=["*"],
)

# --- REST API Endpoint ---
@app.get("/api", response_model=StudentsResponse)
async def get_students_data(
    # Handles multiple ?class= parameters (e.g., ?class=1A&class=1B)
    class_filter: Optional[List[str]] = Query(None, alias="class")
) -> StudentsResponse:
    
    # If data loading failed, return an empty list
    if not ALL_STUDENTS_DATA:
        return StudentsResponse(students=[])

    students_list = ALL_STUDENTS_DATA

    if class_filter:
        # Filter the list by class_name, preserving the original CSV order
        filtered_data = [
            student for student in ALL_STUDENTS_DATA 
            if student['class_name'] in class_filter
        ]
        students_list = filtered_data

    # Convert the filtered list of dicts into the Pydantic Student models
    students = [
        Student(studentId=s['studentId'], class_name=s['class_name']) 
        for s in students_list
    ]

    return StudentsResponse(students=students)


# --- Running the Server ---
if __name__ == "__main__":
    import uvicorn
    # Use python -m uvicorn instead of uv run if uv is not in PATH
    uvicorn.run(app, host="0.0.0.0", port=8000)