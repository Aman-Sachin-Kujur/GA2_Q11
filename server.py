from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict # NOTE: Imported ConfigDict
from typing import List, Optional
import pandas as pd
from pathlib import Path
import os

# --- Data Path Configuration ---
FILE_PATH = Path(os.path.dirname(__file__)) / "q-fastapi.csv" 

# --- Pydantic Models (The Final Fix) ---

class Student(BaseModel):
    # This config tells Pydantic to use the alias name for the output JSON key
    model_config = ConfigDict(populate_by_name=True, json_encoders={})
    
    studentId: int
    # Use Field(alias="class") for both validation/serialization
    # This ensures the internal Python name 'class_name' is mapped to external JSON 'class'
    class_name: str = Field(alias="class") 

# Define the Model for the required response structure
class StudentsResponse(BaseModel):
    students: List[Student]

# --- Data Loading ---
try:
    df = pd.read_csv(FILE_PATH, dtype={'studentId': int, 'class': str})
    
    # Rename the 'class' column to match the internal Pydantic field name
    df.rename(columns={'class': 'class_name'}, inplace=True)
    
    ALL_STUDENTS_DATA = df.to_dict('records')
except FileNotFoundError:
    ALL_STUDENTS_DATA = []
    print(f"Warning: CSV file not found at {FILE_PATH}")


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
@app.get("/api", response_model=StudentsResponse)
async def get_students_data(
    class_filter: Optional[List[str]] = Query(None, alias="class")
) -> StudentsResponse:
    
    if not ALL_STUDENTS_DATA:
        return StudentsResponse(students=[])

    students_list = ALL_STUDENTS_DATA

    if class_filter:
        filtered_data = [
            student for student in ALL_STUDENTS_DATA 
            if student['class_name'] in class_filter
        ]
        students_list = filtered_data

    # Map the dictionary list to Pydantic models for the response
    # The aliases (Field(alias="class")) will automatically be applied here
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