from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict 
from typing import List, Optional
import pandas as pd
from pathlib import Path

# --- Data Path Configuration (FIXED for Codespaces) ---
FILE_PATH = Path("q-fastapi.csv") 

# --- Pydantic Models ---
class Student(BaseModel):
    # CRITICAL: We keep the model clean but explicitly configure it.
    model_config = ConfigDict(populate_by_name=True)
    
    studentId: int
    # This alias ensures the data can be created internally with 'class_name' 
    # and has the name 'class' available for output.
    class_name: str = Field(alias="class") 

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

# --- REST API Endpoint (The Final Fix) ---
# NOTE: response_model is REMOVED to allow manual serialization control
@app.get("/api") 
async def get_students_data(
    class_filter: Optional[List[str]] = Query(None, alias="class")
):
    
    if not ALL_STUDENTS_DATA:
        return {"students": []}

    students_list = ALL_STUDENTS_DATA

    if class_filter:
        filtered_data = [
            student for student in ALL_STUDENTS_DATA 
            if student['class_name'] in class_filter
        ]
        students_list = filtered_data

    # 1. Convert the list of dicts to Pydantic models.
    students_models = [
        Student(studentId=s['studentId'], class_name=s['class_name']) 
        for s in students_list
    ]
    
    # 2. CRITICAL FIX: Manually convert the models to dictionaries,
    # FORCING the use of the external alias name ("class").
    # This bypasses FastAPI's conflicting serialization logic.
    serialized_students = [s.model_dump(by_alias=True) for s in students_models]
    
    # Return the dictionary that matches the exact JSON structure required by the assignment
    return {"students": serialized_students}


# --- Running the Server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)