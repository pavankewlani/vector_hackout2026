# VECTOR

Renewable Energy Intelligence Platform for off-grid communities.

VECTOR connects weather signals, renewable availability, demand, and battery reserve into an explainable dispatch recommendation. This repository contains a functional hackathon MVP with a React operations dashboard and Django REST API.

## Architecture

- `frontend/`: Vite + React dashboard, Lucide icons, responsive CSS, API integration.
- `backend/`: Django service with PostgreSQL/SQLite configuration, JWT authentication, role-scoped APIs, weather storage, forecasting services, model evaluation, and optimizer endpoints.
- `backend/optimizer/engine.py`: modular rule-based dispatch engine. Solar and wind are prioritized, battery is protected by a configurable reserve, and diesel covers the reliability gap.
- Demo data is clearly labeled in the UI and lives in the dashboard service for a zero-setup demo.

## Run locally

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal. The dashboard reads from `http://127.0.0.1:8000` by default.

### Backend

```powershell
py -m pip install -r requirements.txt
py backend\manage.py migrate
py backend\manage.py runserver
```

Django uses SQLite by default for local development. Production PostgreSQL can be configured with `DATABASE_URL` or `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`.

Install the complete backend dependencies, including XGBoost and TensorFlow, before training models:

```powershell
py -m pip install -r requirements.txt
py backend\manage.py migrate
py backend\manage.py seed_demo
```

The seeded accounts are `admin@vector.local` and `operator@vector.local`, both using `VectorDemo!2026`. The operator is restricted to Rampur by backend permissions. Demo accounts and seeded energy values are simulated and must not be treated as live telemetry.

## API

- `GET /api/dashboard/`: network KPIs, community demo data, weather signal, and model summary.
- `POST /api/auth/login/`, `POST /api/auth/refresh/`, `GET /api/auth/me/`: JWT authentication.
- `GET /api/communities/`: communities visible to the authenticated role.
- `GET /api/weather/<community_id>/forecast/`: cached or Open-Meteo forecast.
- `GET /api/weather/<community_id>/history/`: stored or ingested historical weather.
- `GET /api/models/<community_id>/`: stored model metrics and selected models.
- `POST /api/models/<community_id>/train/`: chronological XGBoost/LSTM training and evaluation.
- `GET /api/alerts/`, `POST /api/alerts/<alert_id>/read/`: role-scoped alerts.
- `POST /api/optimizer/run/`: dispatch calculation. Send `demand`, `solar_available`, `wind_available`, `battery_percent`; optional `battery_minimum` and `diesel_price` are supported.

Example:

```json
{
  "demand": 100,
  "solar_available": 60,
  "wind_available": 25,
  "battery_percent": 72
}
```

## Forecasting and model selection

Historical weather is fetched from Open-Meteo and stored with a unique `(community, timestamp)` constraint. XGBoost uses chronological feature engineering and validation; LSTM uses 24-hour sequences and normalized values. Metrics are calculated from validation predictions, persisted in `ForecastModel`, and selected by lowest MAE with RMSE as the tie-breaker. Training is explicit and is never performed during dashboard requests.

## Environment

Copy `.env.example` to `.env` and set secrets before deployment. `OPEN_METEO_BASE_URL`, `CORS_ALLOWED_ORIGINS`, JWT lifetimes, and database settings are supported. PostgreSQL is the production target; SQLite remains a local fallback.

## Product extension points

The data models cover `Community`, `EnergyReading`, and `OptimizationResult`. Weather ingestion, Open-Meteo caching, JWT authentication, model training/evaluation, scheduled jobs, reports, and PostgreSQL deployment should be added as the next production slices. The optimizer contract is deliberately isolated so linear programming or a model-predictive controller can replace the first-pass engine without changing the dashboard.

## Demo scenario

Rampur is selected by default: 100 kW demand, 60 kW solar, 25 kW wind, and 72% battery state. Use **Run optimizer** to calculate the mix and show cost/CO2 from the returned dispatch. Selecting other communities changes the operating context and alert status.
