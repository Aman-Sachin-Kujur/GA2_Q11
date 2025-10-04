from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from pathlib import Path

# --- Data Path Configuration (FIXED for Codespaces) ---
FILE_PATH = Path("q-fastapi.csv") 

# --- Pydantic Models (Simplest form matching the output JSON) ---
class Student(BaseModel):
    # CRITICAL: We use the exact key name 'class' despite Python's keyword warnings 
    # and rely on it to be correctly serialized in the final output.
    # This bypasses all alias/serialization conflict issues.
    studentId: int
    class_val: str # Internal name must be different from 'class' keyword if Python version is older
    
    # We will manually map the key in the final return

class StudentsResponse(BaseModel):
    students: List[Student]

# --- Data Loading ---
try:
    df = pd.read_csv(FILE_PATH, dtype={'studentId': int, 'class': str})
    
    # CRITICAL FIX: Rename the CSV column to a safe internal name
    df.rename(columns={'class': 'class_val'}, inplace=True)
    
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

    students_list = ALL_STUDENTS_DATA

    if class_filter:
        filtered_data = [
            student for student in ALL_STUDENTS_DATA 
            if student['class_val'] in class_filter
        ]
        students_list = filtered_data

    # Map the list of dicts to Pydantic Student models
    students_models = [
        Student(studentId=s['studentId'], class_val=s['class_val']) 
        for s in students_list
    ]
    
    final_output = []
    for s_model in students_models:
        # Convert model to dict
        data_dict = s_model.model_dump()
        
        # FINAL CRITICAL STEP: Manually pop the internal key and write the required external key.
        data_dict['class'] = data_dict.pop('class_val') 
        final_output.append(data_dict)

    # Return the dictionary that matches the exact JSON structure required by the assignment
    return {"students": final_output}


# --- Running the Server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)