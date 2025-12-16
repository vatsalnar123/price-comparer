from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from pathlib import Path
from typing import Any, Literal, Union
import pickle

from data_loader import (
    load_all_properties,
    get_property_by_id,
    get_model_input,
    search_properties,
    generate_mock_property,
)

app = FastAPI(title="Property Comparison API", version="1.0.0")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    property_type: Literal["SFH", "Condo"]
    lot_area: int = Field(0, ge=0)
    building_area: int = Field(0, ge=0)
    bedrooms: int = Field(..., ge=0)
    bathrooms: int = Field(..., ge=0)
    year_built: int = Field(..., ge=1600, le=2100)
    has_pool: bool
    has_garage: bool
    school_rating: int = Field(..., ge=1, le=10)


class CompareRequest(BaseModel):
    property_id_1: int
    property_id_2: int


class CompareAddressesRequest(BaseModel):
    address_1: str = Field(..., min_length=1, description="First property address")
    address_2: str = Field(..., min_length=1, description="Second property address")


class PropertyResponse(BaseModel):
    id: int
    title: str
    listed_price: int
    location: str
    size_sqft: int
    amenities: list[str]
    image_url: str
    property_type: str
    bedrooms: int
    bathrooms: int
    year_built: int
    has_pool: bool
    has_garage: bool
    school_rating: int
    predicted_price: float | None = None
    address: str | None = None  # Full address when using address lookup


class CompareResponse(BaseModel):
    property_1: PropertyResponse
    property_2: PropertyResponse


# ─────────────────────────────────────────────────────────────────────────────
# ML Model Loading
# ─────────────────────────────────────────────────────────────────────────────

class ComplexTrapModelRenamed:
    """
    Lightweight deterministic "model" used for the case study.
    The provided .pkl file contains only an instance reference, no weights.
    """

    def predict(self, x: Union[dict[str, Any], list[dict[str, Any]]]) -> Union[float, list[float]]:
        if isinstance(x, list):
            return [float(self._predict_one(item)) for item in x]
        return float(self._predict_one(x))

    def _predict_one(self, f: dict[str, Any]) -> float:
        property_type = f.get("property_type")
        if property_type not in ("SFH", "Condo"):
            raise ValueError("property_type must be 'SFH' or 'Condo'")

        bedrooms = int(f.get("bedrooms", 0))
        bathrooms = int(f.get("bathrooms", 0))
        year_built = int(f.get("year_built", 1900))
        has_pool = bool(f.get("has_pool", False))
        has_garage = bool(f.get("has_garage", False))
        school_rating = int(f.get("school_rating", 5))

        if property_type == "SFH":
            area = int(f.get("lot_area", 0))
            area_component = area * 12.0
            type_bias = 65_000.0
        else:
            area = int(f.get("building_area", 0))
            area_component = area * 220.0
            type_bias = 35_000.0

        base = 75_000.0
        bed_component = bedrooms * 32_500.0
        bath_component = bathrooms * 27_500.0
        school_component = max(1, min(10, school_rating)) * 11_500.0

        current_year = 2025
        age = max(0, current_year - year_built)
        age_penalty = age * 900.0

        amenities = (18_000.0 if has_pool else 0.0) + (12_500.0 if has_garage else 0.0)

        price = base + type_bias + area_component + bed_component + bath_component + school_component + amenities - age_penalty
        return max(25_000.0, round(price, 2))


class _ModelUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str):
        if module == "__main__" and name == "ComplexTrapModelRenamed":
            return ComplexTrapModelRenamed
        return super().find_class(module, name)


MODEL_PATH = Path(__file__).resolve().parent / "complex_price_model_v2.pkl"
with MODEL_PATH.open("rb") as f:
    model = _ModelUnpickler(f).load()


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Property Comparison API is running"}


@app.get("/properties", response_model=list[PropertyResponse])
async def list_properties(q: str = Query("", description="Search query for title or location")):
    """
    List all properties or search by title/location.
    Each property includes a predicted price from the ML model.
    """
    if q:
        properties = search_properties(q)
    else:
        properties = load_all_properties()
    
    # Add predicted price to each property
    results = []
    for prop in properties:
        model_input = get_model_input(prop)
        predicted = model.predict(model_input)
        results.append(PropertyResponse(
            **prop,
            predicted_price=predicted,
        ))
    
    return results


@app.get("/properties/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: int):
    """
    Get a single property by ID with its predicted price.
    """
    prop = get_property_by_id(property_id)
    if not prop:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
    
    model_input = get_model_input(prop)
    predicted = model.predict(model_input)
    
    return PropertyResponse(**prop, predicted_price=predicted)


@app.post("/compare", response_model=CompareResponse)
async def compare_properties(request: CompareRequest):
    """
    Compare two properties side-by-side with their predicted prices (by ID).
    """
    prop1 = get_property_by_id(request.property_id_1)
    prop2 = get_property_by_id(request.property_id_2)
    
    if not prop1:
        raise HTTPException(status_code=404, detail=f"Property {request.property_id_1} not found")
    if not prop2:
        raise HTTPException(status_code=404, detail=f"Property {request.property_id_2} not found")
    
    # Get predictions
    pred1 = model.predict(get_model_input(prop1))
    pred2 = model.predict(get_model_input(prop2))
    
    return CompareResponse(
        property_1=PropertyResponse(**prop1, predicted_price=pred1),
        property_2=PropertyResponse(**prop2, predicted_price=pred2),
    )


@app.post("/compare-addresses", response_model=CompareResponse)
async def compare_by_addresses(request: CompareAddressesRequest):
    """
    Compare two properties by their addresses.
    
    Accepts two property addresses, retrieves/generates mock property data,
    and returns a side-by-side comparison with ML-predicted prices.
    """
    try:
        prop1 = generate_mock_property(request.address_1)
        prop2 = generate_mock_property(request.address_2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Get predictions from the ML model
    pred1 = model.predict(get_model_input(prop1))
    pred2 = model.predict(get_model_input(prop2))
    
    return CompareResponse(
        property_1=PropertyResponse(**prop1, predicted_price=pred1),
        property_2=PropertyResponse(**prop2, predicted_price=pred2),
    )


@app.get("/lookup-address")
async def lookup_address(address: str = Query(..., min_length=1, description="Property address")):
    """
    Look up a single property by address.
    Returns mock property data with ML-predicted price.
    """
    try:
        prop = generate_mock_property(address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    predicted = model.predict(get_model_input(prop))
    return PropertyResponse(**prop, predicted_price=predicted)


@app.post("/predict")
async def predict_price(payload: PredictionRequest):
    """
    Predict price for custom property features.
    """
    result = model.predict(payload.model_dump())
    return {"predicted_price": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
