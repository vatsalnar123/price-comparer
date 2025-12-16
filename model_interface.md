# 🧠 Model Input Schema - complex_price_model_v2.pkl

Expected dictionary format:

{
  "property_type": "SFH" or "Condo",
  "lot_area": int,               # Used only if property_type == "SFH"
  "building_area": int,          # Used only if property_type == "Condo"
  "bedrooms": int,
  "bathrooms": int,
  "year_built": int,
  "has_pool": bool,
  "has_garage": bool,
  "school_rating": int           # Scale of 1 to 10
}
