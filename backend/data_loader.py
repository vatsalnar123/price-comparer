"""
Data loader that merges JSON property data and transforms it to the model schema.

Transformation logic:
- property_type: Inferred from title (Apartment/Condo/Studio/Penthouse → "Condo", Villa/House/Townhouse/Duplex → "SFH")
- lot_area: size_sqft (for SFH properties)
- building_area: size_sqft (for Condo properties)
- bedrooms: Direct from JSON
- bathrooms: Direct from JSON
- year_built: Generated based on property characteristics
- has_pool: Inferred from amenities ("Swimming Pool", "Pool", "Community Pool")
- has_garage: Inferred from amenities ("Garage", "Two-Car Garage", "Parking")
- school_rating: Generated based on location
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_json(filename: str) -> list[dict[str, Any]]:
    """Load a JSON file from the data directory."""
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _infer_property_type(title: str) -> str:
    """Infer property type from title. Returns 'SFH' or 'Condo'."""
    title_lower = title.lower()
    condo_keywords = ["apartment", "condo", "studio", "penthouse", "flat", "unit"]
    sfh_keywords = ["villa", "house", "townhouse", "duplex", "home", "cottage", "bungalow"]
    
    for keyword in condo_keywords:
        if keyword in title_lower:
            return "Condo"
    for keyword in sfh_keywords:
        if keyword in title_lower:
            return "SFH"
    
    # Default to Condo for ambiguous cases
    return "Condo"


def _infer_has_pool(amenities: list[str]) -> bool:
    """Check if property has a pool from amenities list."""
    pool_keywords = ["pool", "swimming"]
    for amenity in amenities:
        amenity_lower = amenity.lower()
        for keyword in pool_keywords:
            if keyword in amenity_lower:
                return True
    return False


def _infer_has_garage(amenities: list[str]) -> bool:
    """Check if property has a garage from amenities list."""
    garage_keywords = ["garage", "parking", "carport"]
    for amenity in amenities:
        amenity_lower = amenity.lower()
        for keyword in garage_keywords:
            if keyword in amenity_lower:
                return True
    return False


def _generate_year_built(prop_id: int, size_sqft: int, price: int) -> int:
    """Generate a plausible year_built based on property characteristics."""
    # Higher price and larger size suggest newer properties
    base_year = 1970
    
    # Price factor: higher price = newer
    if price > 1000000:
        base_year += 35
    elif price > 700000:
        base_year += 25
    elif price > 400000:
        base_year += 15
    
    # Size factor: modern homes tend to be larger
    if size_sqft > 2500:
        base_year += 10
    elif size_sqft > 1500:
        base_year += 5
    
    # Add some variance based on ID for diversity
    variance = (prop_id * 3) % 15
    
    year = base_year + variance
    return min(2024, max(1950, year))


def _generate_school_rating(location: str, prop_id: int) -> int:
    """Generate a school rating (1-10) based on location."""
    # Base ratings by city (simplified)
    city_ratings = {
        "new york": 8,
        "san francisco": 9,
        "boston": 9,
        "seattle": 8,
        "los angeles": 7,
        "chicago": 7,
        "miami": 6,
        "dallas": 7,
        "austin": 8,
    }
    
    location_lower = location.lower()
    base_rating = 6  # Default
    
    for city, rating in city_ratings.items():
        if city in location_lower:
            base_rating = rating
            break
    
    # Add small variance based on ID
    variance = (prop_id % 3) - 1  # -1, 0, or 1
    
    return min(10, max(1, base_rating + variance))


def load_all_properties() -> list[dict[str, Any]]:
    """
    Load and merge all property data from JSON files.
    Returns a list of properties with all fields needed for the frontend.
    """
    basic = _load_json("properties_basic.json")
    features = _load_json("properties_features.json")
    images = _load_json("properties_images.json")
    
    # Index by ID for easy lookup
    features_by_id = {f["id"]: f for f in features}
    images_by_id = {i["id"]: i for i in images}
    
    properties = []
    for prop in basic:
        prop_id = prop["id"]
        feat = features_by_id.get(prop_id, {})
        img = images_by_id.get(prop_id, {})
        
        title = prop.get("title", "")
        location = prop.get("location", "")
        price = prop.get("price", 0)
        size_sqft = feat.get("size_sqft", 1000)
        amenities = feat.get("amenities", [])
        
        property_type = _infer_property_type(title)
        
        merged = {
            # Original fields for display
            "id": prop_id,
            "title": title,
            "listed_price": price,
            "location": location,
            "size_sqft": size_sqft,
            "amenities": amenities,
            "image_url": img.get("image_url", ""),
            
            # Model schema fields
            "property_type": property_type,
            "lot_area": size_sqft if property_type == "SFH" else 0,
            "building_area": size_sqft if property_type == "Condo" else 0,
            "bedrooms": feat.get("bedrooms", 2),
            "bathrooms": feat.get("bathrooms", 1),
            "year_built": _generate_year_built(prop_id, size_sqft, price),
            "has_pool": _infer_has_pool(amenities),
            "has_garage": _infer_has_garage(amenities),
            "school_rating": _generate_school_rating(location, prop_id),
        }
        
        properties.append(merged)
    
    return properties


def get_property_by_id(prop_id: int) -> dict[str, Any] | None:
    """Get a single property by ID."""
    properties = load_all_properties()
    for prop in properties:
        if prop["id"] == prop_id:
            return prop
    return None


def get_model_input(prop: dict[str, Any]) -> dict[str, Any]:
    """
    Extract only the fields needed for the ML model from a property dict.
    """
    return {
        "property_type": prop["property_type"],
        "lot_area": prop["lot_area"],
        "building_area": prop["building_area"],
        "bedrooms": prop["bedrooms"],
        "bathrooms": prop["bathrooms"],
        "year_built": prop["year_built"],
        "has_pool": prop["has_pool"],
        "has_garage": prop["has_garage"],
        "school_rating": prop["school_rating"],
    }


def search_properties(query: str) -> list[dict[str, Any]]:
    """
    Search properties by title, location, or address.
    Returns matching properties.
    """
    properties = load_all_properties()
    query_lower = query.lower().strip()
    
    if not query_lower:
        return properties
    
    results = []
    for prop in properties:
        searchable = f"{prop['title']} {prop['location']}".lower()
        if query_lower in searchable:
            results.append(prop)
    
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Mock Data Generation from Address
# ─────────────────────────────────────────────────────────────────────────────

# Sample property images for mock data
MOCK_IMAGES = [
    "https://images.pexels.com/photos/106399/pexels-photo-106399.jpeg",
    "https://images.pexels.com/photos/259588/pexels-photo-259588.jpeg",
    "https://images.pexels.com/photos/323780/pexels-photo-323780.jpeg",
    "https://images.pexels.com/photos/271624/pexels-photo-271624.jpeg",
    "https://images.pexels.com/photos/534151/pexels-photo-534151.jpeg",
    "https://images.pexels.com/photos/1396122/pexels-photo-1396122.jpeg",
    "https://images.pexels.com/photos/1029599/pexels-photo-1029599.jpeg",
    "https://images.pexels.com/photos/2102587/pexels-photo-2102587.jpeg",
]

# City-based property characteristics for realistic mock data
CITY_DATA = {
    "new york": {"avg_price": 850000, "school": 8, "type": "Condo", "sqft_range": (800, 2000)},
    "manhattan": {"avg_price": 1200000, "school": 9, "type": "Condo", "sqft_range": (600, 1800)},
    "brooklyn": {"avg_price": 750000, "school": 7, "type": "Condo", "sqft_range": (900, 2200)},
    "los angeles": {"avg_price": 950000, "school": 7, "type": "SFH", "sqft_range": (1500, 3500)},
    "san francisco": {"avg_price": 1400000, "school": 9, "type": "Condo", "sqft_range": (800, 2000)},
    "miami": {"avg_price": 550000, "school": 6, "type": "Condo", "sqft_range": (1000, 2500)},
    "chicago": {"avg_price": 450000, "school": 7, "type": "Condo", "sqft_range": (1000, 2200)},
    "boston": {"avg_price": 750000, "school": 9, "type": "Condo", "sqft_range": (800, 1800)},
    "seattle": {"avg_price": 800000, "school": 8, "type": "SFH", "sqft_range": (1200, 2800)},
    "austin": {"avg_price": 550000, "school": 8, "type": "SFH", "sqft_range": (1500, 3000)},
    "dallas": {"avg_price": 450000, "school": 7, "type": "SFH", "sqft_range": (1800, 3500)},
    "denver": {"avg_price": 600000, "school": 8, "type": "SFH", "sqft_range": (1400, 2800)},
    "phoenix": {"avg_price": 450000, "school": 6, "type": "SFH", "sqft_range": (1600, 3200)},
    "atlanta": {"avg_price": 400000, "school": 7, "type": "SFH", "sqft_range": (1500, 3000)},
}

AMENITIES_POOL = [
    ["Gym", "Swimming Pool", "Parking", "Doorman"],
    ["Garden", "Garage", "Central AC", "Fireplace"],
    ["Rooftop Terrace", "Smart Home", "Security System"],
    ["Beach Access", "Balcony", "In-Unit Laundry"],
    ["Private Dock", "BBQ Area", "Pet Friendly"],
    ["Home Office", "Solar Panels", "EV Charging"],
    ["Community Pool", "Tennis Court", "Clubhouse"],
    ["Park View", "Concierge", "Fitness Center"],
]


def _hash_address(address: str) -> int:
    """Generate a deterministic hash from an address for consistent mock data."""
    return sum(ord(c) * (i + 1) for i, c in enumerate(address.lower()))


def _extract_city_from_address(address: str) -> str | None:
    """Try to extract a known city from the address."""
    address_lower = address.lower()
    for city in CITY_DATA.keys():
        if city in address_lower:
            return city
    return None


def generate_mock_property(address: str) -> dict[str, Any]:
    """
    Generate realistic mock property data based on an address.
    
    Uses deterministic hashing so the same address always returns the same data.
    """
    if not address or not address.strip():
        raise ValueError("Address cannot be empty")
    
    address = address.strip()
    addr_hash = _hash_address(address)
    
    # Try to find a known city in the address
    city = _extract_city_from_address(address)
    
    if city:
        city_info = CITY_DATA[city]
        base_price = city_info["avg_price"]
        school_rating = city_info["school"]
        property_type = city_info["type"]
        sqft_min, sqft_max = city_info["sqft_range"]
    else:
        # Default values for unknown locations
        base_price = 500000
        school_rating = 7
        property_type = "SFH" if addr_hash % 2 == 0 else "Condo"
        sqft_min, sqft_max = 1000, 2500
    
    # Generate property features deterministically from address hash
    size_sqft = sqft_min + (addr_hash % (sqft_max - sqft_min))
    bedrooms = 1 + (addr_hash % 5)  # 1-5 bedrooms
    bathrooms = 1 + (addr_hash % 4)  # 1-4 bathrooms
    
    # Year built: newer in expensive areas
    year_base = 1960 + (addr_hash % 60)  # 1960-2020
    year_built = min(2024, year_base)
    
    # Price variation based on size and hash
    price_multiplier = 0.8 + (addr_hash % 40) / 100  # 0.8 to 1.2
    listed_price = int(base_price * price_multiplier * (size_sqft / 1500))
    
    # Select amenities
    amenity_set_1 = AMENITIES_POOL[addr_hash % len(AMENITIES_POOL)]
    amenity_set_2 = AMENITIES_POOL[(addr_hash + 3) % len(AMENITIES_POOL)]
    amenities = list(set(amenity_set_1[:2] + amenity_set_2[:2]))
    
    # Determine pool and garage from amenities
    has_pool = any("pool" in a.lower() for a in amenities)
    has_garage = any("garage" in a.lower() or "parking" in a.lower() for a in amenities)
    
    # School rating variation
    school_rating = max(1, min(10, school_rating + (addr_hash % 3) - 1))
    
    # Select image
    image_url = MOCK_IMAGES[addr_hash % len(MOCK_IMAGES)]
    
    # Generate a title based on property type
    if property_type == "Condo":
        titles = [
            f"{bedrooms} BR Condo",
            f"Modern {bedrooms} Bedroom Apartment",
            f"Luxury {bedrooms}BR Unit",
            f"Stylish {bedrooms} Bed Condo",
        ]
    else:
        titles = [
            f"{bedrooms} BR Single Family Home",
            f"Beautiful {bedrooms} Bedroom House",
            f"Spacious {bedrooms}BR Home",
            f"Charming {bedrooms} Bed House",
        ]
    title = titles[addr_hash % len(titles)]
    
    # Extract location for display (or use the full address)
    location = address.split(",")[-2:] if "," in address else [address]
    location = ", ".join(part.strip() for part in location)
    
    return {
        "id": addr_hash % 100000,  # Pseudo-unique ID from address
        "address": address,
        "title": title,
        "listed_price": listed_price,
        "location": location,
        "size_sqft": size_sqft,
        "amenities": amenities,
        "image_url": image_url,
        "property_type": property_type,
        "lot_area": size_sqft if property_type == "SFH" else 0,
        "building_area": size_sqft if property_type == "Condo" else 0,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "year_built": year_built,
        "has_pool": has_pool,
        "has_garage": has_garage,
        "school_rating": school_rating,
    }

