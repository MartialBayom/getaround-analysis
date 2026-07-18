"""
Getaround Pricing API
======================
Sert le pipeline entraîné (préprocesseur + modèle) sauvegardé dans
notebooks/02_ml_pricing.ipynb -> model.pkl

Endpoints :
- GET  /            -> healthcheck simple
- POST /predict     -> prédiction du prix journalier
- GET  /docs        -> documentation interactive (générée automatiquement par FastAPI)
"""

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Union

# Ordre EXACT des colonnes attendu par le pipeline (cf. notebook, cellule "Format d'entrée pour l'API")
FEATURE_ORDER = [
    "mileage", "engine_power",                                   # NUM_FEATURES
    "model_key", "fuel", "paint_color", "car_type",               # CAT_FEATURES
    "private_parking_available", "has_gps", "has_air_conditioning",
    "automatic_car", "has_getaround_connect", "has_speed_regulator",
    "winter_tires",                                               # BOOL_FEATURES
]

app = FastAPI(
    title="Getaround Pricing API",
    description=(
        "API de prédiction du prix de location journalier optimal pour un véhicule "
        "Getaround, à partir de ses caractéristiques (kilométrage, puissance, "
        "équipements...). Modèle entraîné sur get_around_pricing_project.csv."
    ),
    version="1.0.0",
)

# Chargé une seule fois au démarrage du conteneur
model = joblib.load("model.pkl")


class PredictionInput(BaseModel):
    input: List[List[Union[float, int, str, bool]]]

    class Config:
        json_schema_extra = {
            "example": {
                "input": [
                    [50000, 120, "Renault", "diesel", "black", "sedan",
                     True, True, True, False, True, False, False]
                ]
            }
        }


@app.get("/")
def read_root():
    return {
        "message": "Getaround Pricing API — see /docs for usage",
        "predict_endpoint": "/predict",
    }


@app.post("/predict")
def predict(payload: PredictionInput):
    df = pd.DataFrame(payload.input, columns=FEATURE_ORDER)

    # Les colonnes booléennes doivent être castées en int, comme à l'entraînement
    bool_cols = [
        "private_parking_available", "has_gps", "has_air_conditioning",
        "automatic_car", "has_getaround_connect", "has_speed_regulator",
        "winter_tires",
    ]
    df[bool_cols] = df[bool_cols].astype(int)

    preds = model.predict(df)
    return {"prediction": preds.round(0).astype(int).tolist()}
