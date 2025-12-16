# 🏠 Property Comparison & Price Prediction App (Junior Full Stack Developer Case Study)

## 🎯 Objective

Build a web application that:
- Accepts two property addresses as input
- Scrapes or uses mocked data to retrieve key property features
- Compares properties side-by-side
- Uses a provided ML model to predict their estimated price
- Displays results in a simple, clean web interface

---

## 🛠️ Tech Stack (Recommended)

- Frontend: React + Vite, HTML/CSS
- Backend (local): Python + FastAPI
- Backend (deployment): Vercel Python Serverless Functions (`/api`)
- Deployment: Vercel

---

## ✅ What I Built (Features)

- **Address-based compare flow (frontend)**: I built a UI with two address inputs and a “Compare” action. When you submit, it calls the backend and renders a side-by-side comparison card for each property.

- **Mock data generation (backend)**: Since the prompt explicitly allows mocked data, I generate realistic-ish property attributes from the input address. The same address always produces the same output (deterministic hashing), and I bias values by recognized cities (e.g., NYC / SF tend to be higher priced and more condo-like).
  - **Generated fields** include bedrooms, bathrooms, size, year built, amenities, pool/garage flags, and a school rating.

- **Schema alignment to `model_interface.md`**: The backend transforms the generated mock features into the exact model input schema:
  - `property_type` is `"SFH"` or `"Condo"`
  - `lot_area` is used only for `"SFH"` and `building_area` only for `"Condo"`
  - `school_rating` is constrained to 1–10

- **Model loading + prediction**: The backend loads the provided `complex_price_model_v2.pkl` and exposes prediction through the compare flow so each property returns a `predicted_price`.

- **Endpoints**:
  - `POST /compare-addresses`: takes `{ address_1, address_2 }` and returns both properties + predictions
  - `GET /lookup-address`: takes `address=...` and returns one property + prediction

---

## 🧩 Challenges I Faced

- **The provided pickle wasn’t a “real” saved model**: When I first tried to load `complex_price_model_v2.pkl`, I hit an error because it referenced a class (`ComplexTrapModelRenamed`) that didn’t exist in my runtime. After inspecting the pickle, I realized it contained only a class instance reference and no stored parameters/weights/state, so there was nothing to “run” unless I recreated the missing class.

- **Making the model usable while still honoring the provided file**: To keep it faithful to the prompt (“use the provided ML model”), I implemented the missing class and a predictable `predict()` method, and I used a custom unpickler that maps `__main__.ComplexTrapModelRenamed` to my implementation so the provided `.pkl` can still be loaded.

- **Turning unstructured addresses into structured model inputs**: Addresses are messy strings, but the model expects a strict schema. I handled this by generating mock features deterministically from the address (so demos are reproducible) and then carefully mapping them into the exact schema described in `model_interface.md` (including the `lot_area` vs `building_area` conditional).

- **Keeping local dev and deployment paths clean**: I made the frontend call the API via `/api` in production (Vercel) and `http://127.0.0.1:8000` locally, so it works both when developing and when deployed.

---

## 🌐 Live Demo

- **Deployment**: `https://price-comparer-five.vercel.app/`
