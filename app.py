from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator, Field
import sentry_sdk
from collections import defaultdict
import pickle
import json


sentry_sdk.init(
    dsn="https://52334479b581416f822df2c10d95f653@o4505065312485376.ingest.sentry.io/4505065314189312",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production,
    traces_sample_rate=1.0,
)

app = FastAPI(swagger_ui_parameters={"displayRequestDuration": True})
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


static_data = json.load(open("./app/static_data.json", "r"))
static_data_recommendation = json.load(open("./app/static_data_recommendation.json", "r"))

models = {'avastin': defaultdict(dict), 'revlimid': defaultdict(dict)}

for drug in models.keys():
    for symptom in static_data[f'{drug}_symptom'].keys():
        with open(f"./app/models/{drug}/over_{symptom.replace(' ', '_')}.model", "rb") as f:
            models[drug][symptom] = pickle.load(f)


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
    def validate_precondition(cls, v: list[str]):
        for item in v:
            if item not in static_data["precondition"]:
                raise ValueError("Invalid precondition name.")
        return v

    @validator('other_drug')
    def validate_other_drug(cls, v: list[str]):
        for item in v:
            if item not in static_data["other_drug"]:
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


class BannerData(BaseModel):
    average_patient_risk_all: float
    average_patient_risk_severe: float
    average_patient_risk_moderate: float
    population_risk_all: float
    population_risk_severe: float
    population_risk_moderate: float


class SymptomPredictionData(BaseModel):
    symptom_name: str = Field(..., description="Name of the drug")
    symptom_category: str = Field(..., description="Category of the symptom.")

    patient_risk: float = Field(..., description="Risk of the patient for the symptom")
    population_risk_rate: float = Field(..., description="Average risk of the population for the symptom")
    patient_risk_severity: str = Field(..., description="Severity of the patient risk. possible values: low, medium, high")
    population_risk_rate_x_three: float = Field(..., description="Risk rate of the population times 3")
    recommendation: str = Field(..., description="Recommendation for the patient")


class OutputData(BaseModel):
    symptom_data: list[SymptomPredictionData] = Field(..., description="Data for the symptoms that are for the main drug")
    banner_data: BannerData = Field(..., description="Data for the banner that is for the whole drug")


@app.get("/ping")
def ping():
    return {"ping": "pong"}


@app.post("/predict")
def predict(input_data: InputData) -> OutputData:
    # get the drug specific data
    drug_data = static_data[f"{input_data.main_drug.lower()}_average"]
    drug_specific_symptom = static_data[f"{input_data.main_drug.lower()}_symptom"].keys()

    # calculate the symptom data
    symptom_data = []
    severe_risks = []
    moderate_risks = []
    for symptom in drug_specific_symptom:
        symptom_category = static_data[f"{input_data.main_drug.lower()}_symptom"][symptom]['category']

        patient_model_data = []
        patient_model_data.append(input_data.age)
        patient_model_data.append(input_data.sex)
        for other_drug in static_data[f"{input_data.main_drug.lower()}_other_drug"]:
            if other_drug in input_data.other_drug:
                patient_model_data.append(1)
            else:
                patient_model_data.append(0)

        patient_risk = models[input_data.main_drug.lower()][symptom].predict_proba([patient_model_data])[0][0]

        if static_data[f"{input_data.main_drug.lower()}_symptom"][symptom]['severity'] == "Serious":
            severe_risks.append(patient_risk)
        elif static_data[f"{input_data.main_drug.lower()}_symptom"][symptom]['severity'] == "Moderate":
            moderate_risks.append(patient_risk)

        population_risk_rate = static_data[f"{input_data.main_drug.lower()}_symptom"][symptom]['rate']
        population_risk_rate_x_three = static_data[f"{input_data.main_drug.lower()}_symptom"][symptom]['three_x_rate']

        if patient_risk < population_risk_rate:
            patient_risk_severity = "low"
            recommendation_risk = "Low Risk"
        elif patient_risk < population_risk_rate_x_three:
            patient_risk_severity = "medium"
            recommendation_risk = "Medium Risk"
        else:
            patient_risk_severity = "high"
            recommendation_risk = "High Risk"

        symptom_risk_specific_recommendation = static_data_recommendation[input_data.main_drug.lower()][symptom][recommendation_risk]
        print("###", input_data.main_drug.lower(), "###", symptom, "###", recommendation_risk, "###")
        print(symptom_risk_specific_recommendation)
        print("///")

        symptom_data.append(SymptomPredictionData(
            symptom_name=symptom,
            symptom_category=symptom_category,
            patient_risk=patient_risk,
            population_risk_rate=population_risk_rate,
            patient_risk_severity=patient_risk_severity,
            population_risk_rate_x_three=population_risk_rate_x_three,
            recommendation=symptom_risk_specific_recommendation))

    # calculate the banner data
    all_risks = severe_risks + moderate_risks
    risk_all = sum(all_risks) / len(all_risks)
    risk_severe = sum(severe_risks) / len(severe_risks)
    risk_moderate = sum(moderate_risks) / len(moderate_risks)
    banner_data = BannerData(
        average_patient_risk_all=risk_all,
        average_patient_risk_severe=risk_severe,
        average_patient_risk_moderate=risk_moderate,
        population_risk_all=drug_data["all"],
        population_risk_severe=drug_data["severe"],
        population_risk_moderate=drug_data["moderate"])

    # return the output data
    output_data = OutputData(
        symptom_data=symptom_data,
        banner_data=banner_data)

    return output_data
