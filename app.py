from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator, Field
import json

app = FastAPI()
static_data = json.load(open("./app/static_data.json", "r"))


class InputData(BaseModel):
    age: int = Field(..., gt=0, lt=150, description="Age of the patient")
    sex: int = Field(..., ge=0, le=1, description="Sex of the patient, 0 for male, 1 for female")
    height: float = Field(..., gt=0, description="Height of the patient in cm")
    weight: float = Field(..., gt=0, description="Weight of the patient in kg")
    smoking: int = Field(..., ge=0, le=1, description="Smoking status of the patient, 0 for non-smoker (i.e. Never), 1 for smoker (i.e. Yes - More than a pack in a week, Yes - Less than a pack in a week, Quit)")
    precondition: list[str] = Field(..., description="Precondition of the patient")
    main_drug: str = Field(..., description="Name of the main drug prescribed e.g. Revlimid or Avastin")
    other_drug: list[str] = Field(..., description="Name of the other drug/drugs prescribed")

    @validator('main_drug')
    def validate_drug_name(cls, v):
        if v not in static_data["main_drug"]:
            raise ValueError("Invalid main drug name.")
        return v

    @validator('precondition')
    def validate_precondition(cls, v):
        if v not in static_data["precondition"]:
            raise ValueError("Invalid precondition name.")
        return v

    @validator('other_drug')
    def validate_other_drug(cls, v):
        if v not in static_data["other_drug"]:
            raise ValueError("Invalid other drug name.")
        return v

    class Config:
        schema_extra = {
            "example": {
                "age": 50,
                "sex": 0,
                "height": 180,
                "weight": 80,
                "smoking": 0,
                "precondition": ["Obesity"],
                "main_drug": "Avastin",
                "other_drug": ["ALLOPURINOL", "ACETAMINOPHEN"]
            }
        }


@app.get("/ping")
def ping():
    return {"ping": "pong"}

@app.post("/predict")
def predict(data: InputData):
    # return the age * sex
    return {"prediction": data.age * data.sex}