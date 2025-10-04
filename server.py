from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from pathlib import Path
import os

# --- 1. Data Loading and Pydantic Model ---
# Define the Pydantic Model for a single student record
class Student(BaseModel):
    studentId: int
    class_name: str # Renamed to class_name to avoid Python 'class' keyword conflict

# Define the Model for the response structure
class StudentsResponse(BaseModel):
    students: List[Student]

# Load data globally once (adjust path if needed)
FILE_PATH = Path(os.path.dirname(__file__)) / "q-fastapi.csv"
try:
    # Read the CSV, using pandas for simple loading
    df = pd.read_csv(FILE_PATH, dtype={'studentId': int, 'class': str})
    # Rename the 'class' column to 'class_name' to match the Pydantic model
    df.rename(columns={'class': 'class_name'}, inplace=True)
    # Convert DataFrame to a list of dicts for easy filtering
    ALL_STUDENTS_DATA = df.to_dict('records')
except FileNotFoundError:
    ALL_STUDENTS_DATA = []
    print(f"Warning: CSV file not found at {FILE_PATH}")


# --- 2. Application Setup and CORS ---
app = FastAPI()

# Configure CORS to allow GET requests from ANY origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET"],  # Only need GET for this public API
    allow_headers=["*"],
)

# --- 3. REST API Endpoint ---
@app.get("/api", response_model=StudentsResponse)
async def get_students_data(
    # Use Query with 'List' to handle repeated parameters (e.g., ?class=1A&class=1B)
    class_filter: Optional[List[str]] = Query(None, alias="class")
) -> StudentsResponse:
    """
    Returns all students or filters students by class name(s).
    """
    if not ALL_STUDENTS_DATA:
        # Return an empty list if data loading failed
        return StudentsResponse(students=[])

    if not class_filter:
        # If no filter is provided, return all students in CSV order
        students_list = ALL_STUDENTS_DATA
    else:
        # Filter the list, maintaining the original order
        # We use 'class_name' from the renamed column
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


# --- 4. Running the Server ---
if __name__ == "__main__":
    import uvicorn
    # The API URL endpoint will be http://127.0.0.1:8000/api
    uvicorn.run(app, host="0.0.0.0", port=8000)