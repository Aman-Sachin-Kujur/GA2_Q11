from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
# Keep V2 imports as they often include V1 compatibility features
from pydantic import BaseModel, Field 
from typing import List, Optional
import pandas as pd
from pathlib import Path

# --- Data Path Configuration (FIXED for Codespaces) ---
FILE_PATH = Path("q-fastapi.csv") 

# --- Pydantic Models (The Final Compatibility Fix) ---
class Student(BaseModel):
    # CRITICAL V1/V2 FIX: Nested Config class for serialization settings
    # This configuration tells Pydantic to use the alias ("class") for output JSON keys
    class Config:
        # Pydantic V1/V2 setting to use the alias name for serialization
        allow_population_by_field_name = True
    
    studentId: int
    
    # Use Field(alias="class") for input mapping, 
    # and rely on Config to force alias use in output.
    class_name: str = Field(alias="class") 

# Required response structure
class StudentsResponse(BaseModel):
    students: List[Student]

# --- Data Loading ---
try:
    df = pd.read_csv(FILE_PATH, dtype={'studentId': int, 'class': str})
    
    # Rename the CSV column to match the internal Python field name
    df.rename(columns={'class': 'class_name'}, inplace=True)
    
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
@app.get("/api", response_model=StudentsResponse) # Reinstated response_model for strict validation
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

    # Map the dictionary list to Pydantic models
    students = [
        Student(studentId=s['studentId'], class_name=s['class_name']) 
        for s in students_list
    ]
    
    # Returning the model list directly now forces FastAPI to apply the alias from the Config/Field
    return StudentsResponse(students=students)


# --- Running the Server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)