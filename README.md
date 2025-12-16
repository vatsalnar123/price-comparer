# 🏠 Property Comparison & Price Prediction App (Junior Full Stack Developer Case Study)

Welcome! This is a case study for evaluating junior full stack developer candidates at Agent Mira.

## 🎯 Objective

Build a web application that:
- Accepts two property addresses as input
- Scrapes or uses mocked data to retrieve key property features
- Compares properties side-by-side
- Uses a provided ML model to predict their estimated price
- Displays results in a simple, clean web interface

---

## 🧠 What You’ll Learn and Show Us

- Frontend development using modern JS frameworks
- Backend API design in Python (Flask/FastAPI)
- Data processing and handling unstructured inputs
- Integrating a real model object for prediction
- Thinking through edge cases and business logic

---

## 🛠️ Tech Stack (Recommended)

- Frontend: React, HTML/CSS, Tailwind
- Backend: Python (FastAPI or Flask)
- Tools: Docker (optional), GitHub Copilot, Cursor, Postman

---

## 🔗 Files Provided

- `complex_price_model_v2.pkl`: Serialized model file
- `model_interface.md`: Description of model input schema
- `backend/main.py`: Starter backend script (optional use)
- `README.md`: This file

---

## 🚀 Task Details

1. Build a frontend with two input fields for property addresses.
2. On clicking "Compare", send the addresses to the backend.
3. Backend should:
   - Scrape or simulate property data
   - Prepare data using the correct schema
   - Load and invoke the provided ML model
4. Return estimated price and features for each property.
5. Show the results side-by-side in the frontend.

---

## 📥 Model Integration Guide

Import and use like this:
```python
import pickle

with open('complex_price_model_v2.pkl', 'rb') as f:
    model = pickle.load(f)

prediction = model.predict({
    "property_type": "SFH",
    "lot_area": 5000,
    "building_area": 0,
    "bedrooms": 3,
    "bathrooms": 2,
    "year_built": 2015,
    "has_pool": True,
    "has_garage": False,
    "school_rating": 9
})
```

---

## ✅ Evaluation Criteria

- Clear UI and working compare flow
- Correct use of the model and data structure
- Thoughtfulness in debugging and schema alignment
- Bonus: Hosting instructions, GitHub repo, styling polish

---

Good luck! And have fun.
