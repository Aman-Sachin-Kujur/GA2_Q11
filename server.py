from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd
from pathlib import Path
import os

# --- Data Path Configuration ---
# Use the actual file name provided in your environment
FILE_PATH = Path(os.path.dirname(__file__)) / "q-fastapi.csv" 

# --- Pydantic Models (Fixes Property Mismatch Error) ---

# The Student model uses Field(alias="class") to solve the "Property name mismatch"
# It uses 'class_name' internally (to avoid Python keyword conflict) but exports 'class' externally.
class Student(BaseModel):
    studentId: int
    class_name: str = Field(alias="class") 

# Define the Model for the required response structure
class StudentsResponse(BaseModel):
    students: List[Student]

# --- Data Loading ---
try:
    # Read the CSV
    df = pd.read_csv(FILE_PATH, dtype={'studentId': int, 'class': str})
    
    # Rename the 'class' column to match the internal Pydantic field name
    df.rename(columns={'class': 'class_name'}, inplace=True)
    
    # Convert to a list of dicts for easy filtering (maintains CSV order)
    ALL_STUDENTS_DATA = df.to_dict('records')
except FileNotFoundError:
    ALL_STUDENTS_DATA = []
    print(f"Warning: CSV file not found at {FILE_PATH}")


# --- Application Setup and CORS ---
app = FastAPI()

# Enable CORS for all origins and GET method (as required)
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
    # Use Query(..., alias="class") to handle repeated query parameters (e.g., ?class=1A&class=1B)
    class_filter: Optional[List[str]] = Query(None, alias="class")
) -> StudentsResponse:
    
    if not ALL_STUDENTS_DATA:
        return StudentsResponse(students=[])

    students_list = ALL_STUDENTS_DATA

    if class_filter:
        # Filter the list based on the requested classes
        # Uses 'class_name' (the renamed column) for filtering
        filtered_data = [
            student for student in ALL_STUDENTS_DATA 
            if student['class_name'] in class_filter
        ]
        students_list = filtered_data

    # Map the dictionary list to Pydantic models for the response
    students = [
        Student(studentId=s['studentId'], class_name=s['class_name']) 
        for s in students_list
    ]

    return StudentsResponse(students=students)


# --- Running the Server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)