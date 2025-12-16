"""
Vercel Serverless Function: Compare two properties by address
POST /api/compare-addresses
"""

from http.server import BaseHTTPRequestHandler
import json
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Mock Data Generation
# ─────────────────────────────────────────────────────────────────────────────

MOCK_IMAGES = [
    "https://images.pexels.com/photos/106399/pexels-photo-106399.jpeg",
    "https://images.pexels.com/photos/259588/pexels-photo-259588.jpeg",
    "https://images.pexels.com/photos/323780/pexels-photo-323780.jpeg",
    "https://images.pexels.com/photos/271624/pexels-photo-271624.jpeg",
    "https://images.pexels.com/photos/534151/pexels-photo-534151.jpeg",
]

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
]


def _hash_address(address: str) -> int:
    return sum(ord(c) * (i + 1) for i, c in enumerate(address.lower()))


def _extract_city(address: str) -> str | None:
    address_lower = address.lower()
    for city in CITY_DATA.keys():
        if city in address_lower:
            return city
    return None


def generate_mock_property(address: str) -> dict[str, Any]:
    address = address.strip()
    addr_hash = _hash_address(address)
    city = _extract_city(address)
    
    if city:
        city_info = CITY_DATA[city]
        base_price = city_info["avg_price"]
        school_rating = city_info["school"]
        property_type = city_info["type"]
        sqft_min, sqft_max = city_info["sqft_range"]
    else:
        base_price = 500000
        school_rating = 7
        property_type = "SFH" if addr_hash % 2 == 0 else "Condo"
        sqft_min, sqft_max = 1000, 2500
    
    size_sqft = sqft_min + (addr_hash % (sqft_max - sqft_min))
    bedrooms = 1 + (addr_hash % 5)
    bathrooms = 1 + (addr_hash % 4)
    year_built = min(2024, 1960 + (addr_hash % 60))
    
    price_multiplier = 0.8 + (addr_hash % 40) / 100
    listed_price = int(base_price * price_multiplier * (size_sqft / 1500))
    
    amenity_set_1 = AMENITIES_POOL[addr_hash % len(AMENITIES_POOL)]
    amenity_set_2 = AMENITIES_POOL[(addr_hash + 3) % len(AMENITIES_POOL)]
    amenities = list(set(amenity_set_1[:2] + amenity_set_2[:2]))
    
    has_pool = any("pool" in a.lower() for a in amenities)
    has_garage = any("garage" in a.lower() or "parking" in a.lower() for a in amenities)
    school_rating = max(1, min(10, school_rating + (addr_hash % 3) - 1))
    image_url = MOCK_IMAGES[addr_hash % len(MOCK_IMAGES)]
    
    if property_type == "Condo":
        titles = [f"{bedrooms} BR Condo", f"Modern {bedrooms} Bedroom Apartment"]
    else:
        titles = [f"{bedrooms} BR Single Family Home", f"Beautiful {bedrooms} Bedroom House"]
    title = titles[addr_hash % len(titles)]
    
    location = ", ".join(part.strip() for part in address.split(",")[-2:]) if "," in address else address
    
    return {
        "id": addr_hash % 100000,
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


# ─────────────────────────────────────────────────────────────────────────────
# ML Model (Deterministic Price Prediction)
# ─────────────────────────────────────────────────────────────────────────────

def predict_price(f: dict[str, Any]) -> float:
    property_type = f.get("property_type")
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

    age = max(0, 2025 - year_built)
    age_penalty = age * 900.0

    amenities = (18_000.0 if has_pool else 0.0) + (12_500.0 if has_garage else 0.0)

    price = base + type_bias + area_component + bed_component + bath_component + school_component + amenities - age_penalty
    return max(25_000.0, round(price, 2))


# ─────────────────────────────────────────────────────────────────────────────
# Vercel Handler
# ─────────────────────────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            address_1 = data.get('address_1', '').strip()
            address_2 = data.get('address_2', '').strip()
            
            if not address_1 or not address_2:
                self.send_error_response(400, "Both addresses are required")
                return
            
            prop1 = generate_mock_property(address_1)
            prop2 = generate_mock_property(address_2)
            
            prop1['predicted_price'] = predict_price(prop1)
            prop2['predicted_price'] = predict_price(prop2)
            
            response = {
                "property_1": prop1,
                "property_2": prop2
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON")
        except Exception as e:
            self.send_error_response(500, str(e))

    def send_error_response(self, code: int, message: str):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())

