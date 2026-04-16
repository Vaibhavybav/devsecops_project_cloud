from __future__ import annotations

from io import StringIO

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from feature_engineering import add_inference_features, apply_decision_engine
from model import ModelArtifactError, load_model_artifacts, predict_with_artifacts


app = FastAPI(title="Green FinOps API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_request_csv(upload: UploadFile) -> pd.DataFrame:
    if not upload.filename or not upload.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    try:
        payload = upload.file.read().decode("utf-8")
        frame = pd.read_csv(StringIO(payload))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {exc}") from exc

    frame.columns = frame.columns.str.strip().str.lower()
    required_columns = {"vcpu_usage", "ram_usage"}
    missing_columns = sorted(required_columns - set(frame.columns))
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing_columns)}",
        )

    try:
        frame["vcpu_usage"] = pd.to_numeric(frame["vcpu_usage"], errors="raise")
        frame["ram_usage"] = pd.to_numeric(frame["ram_usage"], errors="raise")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"vcpu_usage and ram_usage must be numeric: {exc}",
        ) from exc

    prepared = frame.copy()
    if "server_id" not in prepared.columns:
        prepared["server_id"] = [f"vm-{index + 1}" for index in range(len(prepared))]

    return prepared[["server_id", "vcpu_usage", "ram_usage"]].copy()


def _add_estimated_savings(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    enriched["estimated_savings"] = 0.0
    move_mask = enriched["final_action"].str.startswith("Move from ", na=False)
    enriched.loc[move_mask, "estimated_savings"] = enriched.loc[move_mask, "cost"] * 0.3
    return enriched


@app.post("/predict")
async def predict(file: UploadFile = File(...)) -> list[dict[str, float | int | str]]:
    request_frame = _load_request_csv(file)

    try:
        model, scaler = load_model_artifacts("model.pkl", "scaler.pkl")
    except ModelArtifactError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    featured = add_inference_features(request_frame)
    scored = predict_with_artifacts(featured, model=model, scaler=scaler)
    decided = apply_decision_engine(scored)
    response_frame = _add_estimated_savings(decided)

    output_columns = [
        "server_id",
        "vcpu_usage",
        "ram_usage",
        "region",
        "target_region",
        "cost",
        "carbon_intensity",
        "carbon_saving",
        "ml_anomaly",
        "vm_status",
        "final_action",
        "estimated_savings",
        "reason",
    ]
    return response_frame[output_columns].to_dict(orient="records")
