from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic.fields import validator


app = FastAPI()

class InputData(BaseModel):
    age: int
    sex: int
    drug: str

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