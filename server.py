from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from pathlib import Path

# --- Data Path Configuration (Fixed) ---
FILE_PATH = Path("q-fastapi.csv") 

# --- Pydantic Models (Simplified) ---
# Use the internal name that matches the renamed DataFrame column
class Student(BaseModel):
    studentId: int
    class_val: str 

class StudentsResponse(BaseModel):
    students: List[Student]

# --- Data Loading ---
try:
    df = pd.read_csv(FILE_PATH, dtype={'studentId': int, 'class': str})
    
    # CRITICAL: Rename 'class' to a safe internal name 'class_val'
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

# --- REST API Endpoint (Final Fix: Manual Dict Construction) ---
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

    # --- FINAL CRITICAL STEP: Construct the JSON output manually ---
    final_output = []
    for student_dict in students_list:
        # Create a new dictionary, enforcing the exact key names and the required order.
        # Python dicts are ordered starting from Python 3.7+
        output_record = {
            "studentId": student_dict['studentId'],
            "class": student_dict['class_val'] # Manually use the required key "class"
        }
        final_output.append(output_record)

    # Return the final dictionary structure
    return {"students": final_output}


# --- Running the Server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)