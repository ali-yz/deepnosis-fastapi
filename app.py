from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator, Field

app = FastAPI()

class InputData(BaseModel):
    age: int = Field(..., gt=0, lt=150, description="Age of the patient")
    sex: int = Field(..., ge=0, le=1, description="Sex of the patient, 0 for male, 1 for female")
    drug: str = Field(..., description="Name of the drug prescribed")

    @validator('drug')
    def validate_drug_name(cls, v):
        if v not in ["Drug_A", "Drug_B", "Drug_C"]:
            raise ValueError("Invalid drug name")
        return v

@app.get("/ping")
def ping():
    return {"ping": "pong"}

@app.post("/predict")
def predict(data: InputData):
    # return the age * sex
    return {"prediction": data.age * data.sex}