"""
Vercel Serverless Function: List all sample properties
GET /api/properties
"""

from http.server import BaseHTTPRequestHandler
import json

SAMPLE_PROPERTIES = [
    {
        "id": 1,
        "title": "3 BHK Apartment in Downtown",
        "listed_price": 450000,
        "location": "New York, NY",
        "size_sqft": 1500,
        "amenities": ["Gym", "Swimming Pool", "Parking"],
        "image_url": "https://images.pexels.com/photos/106399/pexels-photo-106399.jpeg",
        "property_type": "Condo",
        "bedrooms": 3,
        "bathrooms": 2,
        "year_built": 1988,
        "has_pool": True,
        "has_garage": True,
        "school_rating": 8,
        "predicted_price": 681700.0
    },
    {
        "id": 2,
        "title": "2 BHK Condo with Sea View",
        "listed_price": 380000,
        "location": "Miami, FL",
        "size_sqft": 1200,
        "amenities": ["Beach Access", "Security", "Balcony"],
        "image_url": "https://images.pexels.com/photos/259588/pexels-photo-259588.jpeg",
        "property_type": "Condo",
        "bedrooms": 2,
        "bathrooms": 2,
        "year_built": 1995,
        "has_pool": False,
        "has_garage": False,
        "school_rating": 6,
        "predicted_price": 466500.0
    },
    {
        "id": 3,
        "title": "Luxury Villa with Private Garden",
        "listed_price": 850000,
        "location": "Los Angeles, CA",
        "size_sqft": 2800,
        "amenities": ["Private Garden", "Smart Home", "Garage"],
        "image_url": "https://images.pexels.com/photos/323780/pexels-photo-323780.jpeg",
        "property_type": "SFH",
        "bedrooms": 4,
        "bathrooms": 3,
        "year_built": 2005,
        "has_pool": False,
        "has_garage": True,
        "school_rating": 7,
        "predicted_price": 380100.0
    }
]


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(SAMPLE_PROPERTIES).encode())

