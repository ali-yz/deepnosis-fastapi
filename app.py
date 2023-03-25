from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class InputData(BaseModel):
    age: int
    sex: int
    drug: str

@app.get("/ping")
def ping():
    return {"ping": "pong"}

@app.post("/predict")
def predict(data: InputData):
    # return the age * sex
    return {"prediction": data.age * data.sex}