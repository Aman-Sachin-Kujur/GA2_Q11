from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from pathlib import Path

# --- Data Path Configuration ---
FILE_PATH = Path("q-fastapi.csv") 

# --- Pydantic Models (Simplest structure to avoid conflict) ---
class Student(BaseModel):
    studentId: int
    # We will not use this model for output serialization; we use it only for validation.
    # We use a neutral name here to avoid Python keyword conflict.
    class_safe: str 

class StudentsResponse(BaseModel):
    students: List[Student]

# --- Data Loading ---
try:
    df = pd.read_csv(FILE_PATH, dtype={'studentId': int, 'class': str})
    
    # CRITICAL: Rename 'class' to a safe internal name 'class_safe' for Python use
    df.rename(columns={'class': 'class_safe'}, inplace=True)
    
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

# --- REST API Endpoint (Manual Dict Construction) ---
@app.get("/api") 
async def get_students_data(
    # Use 'class' as the alias to extract the query parameter
    class_filter: Optional[List[str]] = Query(None, alias="class")
):
    
    if not ALL_STUDENTS_DATA:
        return {"students": []}

    students_list = ALL_STUDENTS_DATA

    if class_filter:
        # Filter using the internal column name 'class_safe'
        filtered_data = [
            student for student in ALL_STUDENTS_DATA 
            if student['class_safe'] in class_filter
        ]
        students_list = filtered_data

    # --- FINAL CRITICAL STEP: Manual Dictionary Construction ---
    final_output = []
    for student_dict in students_list:
        
        # This dictionary construction guarantees the exact key names and the required order.
        output_record = {
            # Use the data directly from the dictionary (original key is safe)
            "studentId": student_dict['studentId'],
            
            # CRUCIAL: Manually use the required output key "class" 
            "class": student_dict['class_safe'] 
        }
        final_output.append(output_record)

    # Return the final dictionary structure
    return {"students": final_output}


# --- Running the Server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)