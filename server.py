from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
# Pydantic V2 required imports (best to keep these for future compatibility)
from pydantic import BaseModel, Field, ConfigDict 
from typing import List, Optional
import pandas as pd
from pathlib import Path
import os
import json # Ensure json is imported for serialization fix below

# --- Data Path Configuration ---
FILE_PATH = Path("q-fastapi.csv") 

# --- Pydantic Models ---
class Student(BaseModel):
    # CRITICAL V2/V1 FIX: Pydantic configuration class
    # The 'model_config' or nested 'Config' class helps control serialization
    model_config = ConfigDict(populate_by_name=True)
    
    studentId: int
    # Alias ensures Python's internal 'class_name' maps to JSON's required 'class'
    class_name: str = Field(alias="class") 

# Required response structure
class StudentsResponse(BaseModel):
    students: List[Student]

# --- Data Loading ---
try:
    df = pd.read_csv(FILE_PATH, dtype={'studentId': int, 'class': str})
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
@app.get("/api") # Removed response_model=StudentsResponse for custom serialization control
async def get_students_data(
    class_filter: Optional[List[str]] = Query(None, alias="class")
): # Removed type hint for return until serialization is fixed
    
    if not ALL_STUDENTS_DATA:
        # Return a standard JSON response when no data is loaded
        return {"students": []}

    students_list = ALL_STUDENTS_DATA

    if class_filter:
        filtered_data = [
            student for student in ALL_STUDENTS_DATA 
            if student['class_name'] in class_filter
        ]
        students_list = filtered_data

    # --- CRITICAL SERIALIZATION FIX ---
    # 1. Convert the list of dicts to Pydantic models.
    # 2. Convert the Pydantic models to a dict, explicitly demanding the use of aliases (by_alias=True).
    students = [
        Student(studentId=s['studentId'], class_name=s['class_name']) 
        for s in students_list
    ]
    
    # Manually dump the list, forcing the alias to be used in the output keys
    serialized_students = [s.model_dump(by_alias=True) for s in students] 
    
    # Return the dictionary that matches the exact structure required by the assignment
    return {"students": serialized_students}


# --- Running the Server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)