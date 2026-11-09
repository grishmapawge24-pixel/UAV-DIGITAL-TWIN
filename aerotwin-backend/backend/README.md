# AeroTwin AI - Backend

Backend for **AeroTwin AI**: an AI-enabled real-time digital twin system for
health monitoring, fault prediction, and mission reliability enhancement of
aero piston engines used in MALE UAVs. Built for Smart India Hackathon 2026,
Problem Statement 26054.

This backend serves real NGAFID (National General Aviation Flight
Information Database) historical flight data through a FastAPI REST +
WebSocket API, with two trained scikit-learn models (anomaly detection,
fault classification) behind it. **No sensor data is fabricated anywhere**
- parameters the dataset doesn't provide (vibration, injection timing) are
explicitly marked unavailable, never invented.

For the full step-by-step setup, see **SETUP_GUIDE.md**.

---

## 1. Architecture

```
backend/
├── app/                      # the FastAPI application
│   ├── main.py                 # app entrypoint, CORS, routers, startup checks
│   ├── config.py                # all paths & settings, read from .env
│   │
│   ├── api/                    # one file per group of endpoints (thin - no business logic)
│   │   ├── routes_health.py       # /api/health, /api/engine/status, /api/dashboard/summary, /api/sensors/available
│   │   ├── routes_flights.py      # /api/flights, /api/flights/{id}, /telemetry, /health
│   │   ├── routes_faults.py       # /api/flights/{id}/faults, /api/faults/labels
│   │   ├── routes_predictions.py  # POST /api/predict, POST /api/anomaly
│   │   ├── routes_missions.py     # /api/missions, POST /api/missions/simulate
│   │   └── routes_replay.py       # GET /api/replay/{id}, WS /ws/telemetry/{id}
│   │
│   ├── services/                # all business logic lives here
│   │   ├── data_service.py         # ONLY module that touches the raw NGAFID files
│   │   ├── preprocessing.py         # raw array -> named, cleaned DataFrame
│   │   ├── feature_engineering.py   # DataFrame -> flat feature vector (used online AND offline)
│   │   ├── inference_utils.py       # feature dict -> ordered model input vector
│   │   ├── anomaly_service.py       # Isolation Forest wrapper
│   │   ├── fault_prediction_service.py  # Random Forest wrapper + severity/action/component heuristics
│   │   ├── health_index_service.py  # 0-100 prototype health score
│   │   ├── rul_service.py           # prototype Remaining-Useful-Life heuristic
│   │   ├── replay_service.py        # historical telemetry playback (REST + streaming)
│   │   └── mission_service.py       # what-if mission simulation
│   │
│   ├── models/
│   │   ├── schemas.py              # every request/response Pydantic model
│   │   └── model_loader.py          # lazy-loads the trained .pkl artifacts
│   │
│   └── utils/
│       ├── sensor_mapping.py        # loads/validates the verified column mapping - single source of truth
│       ├── db.py                     # tiny SQLite helper (stores simulated missions only)
│       ├── errors.py                 # maps internal exceptions -> HTTP responses
│       └── logging_config.py
│
├── ml/                        # standalone scripts - the training pipeline (run from the command line)
│   ├── inspect_dataset.py         # STEP 1: look at the raw files, no assumptions
│   ├── verify_sensor_mapping.py    # STEP 2: suggest + let you verify the column<->sensor mapping
│   ├── preprocess_dataset.py       # performance helper: pkl -> fast per-flight cache
│   ├── create_features.py          # STEP 3: build the training feature table
│   ├── train_anomaly_model.py       # STEP 4: Isolation Forest
│   ├── train_fault_model.py         # STEP 5: Random Forest (or XGBoost) classifier
│   ├── evaluate_models.py           # STEP 6: print/inspect evaluation metrics
│   └── save_models.py                # STEP 7: final "ready to demo?" checklist
│
├── models/                    # trained artifacts land here (empty until you train)
├── data/                      # locally generated derived files only (empty until you run ml/ scripts)
├── requirements.txt
├── .env.example
├── run_backend.bat
├── SETUP_GUIDE.md
└── README.md                  # this file
```

A few deliberate additions beyond a minimal "one file per box" layout
(`inference_utils.py`, `db.py`, `errors.py`, `mission_service.py`): small,
focused modules that keep the route files thin and avoid duplicating logic
between the anomaly and fault services. Nothing in the required structure
was removed - the whole thing still maps directly onto the API/ML/models
layout requested in the brief.

---

## 2. Why the sensor mapping is a separate, manual-verification step

`flight_data.pkl` gives each flight as a `(timesteps, 23)` NumPy array with
**no column names**. `stats.csv` gives named parameters. Nothing in the raw
files says which pkl column is which parameter. Guessing wrong here would
silently corrupt every downstream feature, model, and API response - so
this project treats it as a hard gate:

1. `ml/verify_sensor_mapping.py` statistically SUGGESTS a mapping (Hungarian
   algorithm matching column statistics to stats.csv's parameter
   statistics) and writes it to `data/config/sensor_mapping.json` with
   `"verified": false`.
2. **You look at it** - the script also prints a human-readable table with
   typical general-aviation value ranges next to each suggestion, so you can
   sanity-check ("column 9 -> E1 RPM, confidence 0.94, typical range
   500-2700 RPM" - does that look right?).
3. Only after you edit the file to `"verified": true` will
   `app/utils/sensor_mapping.py` let any other code (features, training,
   the live API) use it. Until then, telemetry/health/fault endpoints
   return HTTP 503 with a clear message instead of silently mismapped data.

## 3. What's genuinely data-driven vs. what's a documented heuristic

| Component | Basis |
|---|---|
| Sensor telemetry (`/telemetry`, `/replay`) | Real NGAFID data, mapped via the verified column mapping. |
| Fault labels (`fault_type`) | Only real label strings seen in `flight_header.csv` during training. Never invented. |
| Fault classifier confidence | Real `predict_proba` output of a trained RandomForestClassifier. |
| Anomaly score | Real `decision_function` output of a trained IsolationForest. |
| `severity`, `uav_component`, `recommended_action` | **Rule-based keyword heuristics**, not learned from data - see `fault_prediction_service.py`. Needed to make the demo/3D-UAV integration useful; documented as such. |
| `health_score` / `health_status` | **Hand-weighted heuristic** combining the anomaly score, fault confidence/severity, deviation-from-training-baseline, and within-flight trend. No ground-truth health label exists in NGAFID to train against - see `health_index_service.py`. |
| `estimated_remaining_flights` (RUL) | **Illustrative heuristic** combining the health score with a real, data-derived statistic (average `number_flights_before` for flights sharing the predicted label). Not a trained regression - NGAFID lacks true run-to-failure labels. See `rul_service.py` for exactly what a production RUL model would need. |
| Mission simulation | Uses a **real** flight as a template with simple multiplicative perturbation, not a physics engine. See `mission_service.py`. |

## 4. Parameters NOT available in NGAFID

The SIH problem statement asks for vibration and injection-timing
monitoring. NGAFID does not log either. `GET /api/sensors/available`
reports these explicitly under `unavailable_sensors` - the backend never
fabricates values for them, in the API or anywhere else.

## 5. Frontend integration note

This backend was built against the actual React (Vite) frontend project -
not just the spec in the brief. A few things were deliberately aligned to
the real frontend code rather than the brief's example JSON:

- `severity` values are `'warning' | 'major' | 'critical'` and
  `uav_component` ids are `'engine' | 'fuelSystem' | 'coolingSystem' |
  'lubricationSystem' | 'electricalSystem' | 'battery' | 'propeller' |
  'sensors' | 'avionics'` - copied directly from the frontend's
  `src/utils/status.js` and `src/data/uavProfiles.js`, so API responses
  render with the frontend's existing badge/status-dot CSS and 3D
  component-highlight logic with no translation layer needed.
- The frontend displays temperatures in °C, oil pressure in bar, and fuel
  flow in L/h, while NGAFID's native units are °F/psi/gal-hr. The **Manual
  Check** feature (see below) converts between them client-side - the
  backend always speaks NGAFID-native units, consistent with every other
  endpoint (telemetry/replay were never unit-converted either).

## 6. Manual Parameter Check (`POST /api/manual/evaluate`)

Lets a person type in current engine readings by hand - no flight_id, no
time series - and get a real AI comparison back: health score, fault
likelihood, and a per-parameter deviation-from-baseline breakdown. Powers
the frontend's new **Manual Check** page.

Since the anomaly/fault models were trained on whole-flight AGGREGATE
features (mean/std/slope/etc. over hundreds of timesteps), a single manual
reading can't supply variability or trend information. Rather than
zero-fill the missing pieces (which would look like an impossible,
flat-lined flight), `manual_input_service.py` starts every feature at the
trained StandardScaler's baseline mean - "assume an otherwise completely
average flight" - and overlays only the parameter(s) the user actually
typed in. This was empirically necessary: an early version that zero-filled
unknown features caused the fault classifier to barely react even to
extreme values. The per-parameter z-score comparison (direct, not routed
through the classifier) turned out to be the most reliable signal for a
single-moment reading, so the overall health score is anchored on that,
with the ML models contributing a secondary, score-reducing vote when they
do fire. See the module docstring for the full reasoning.

## 7. Replay-window analysis and reliability

`GET /api/analyze/{flight_id}?end_index=500&window=120` computes the exact
same engineered features used in training over a trailing window from the
real NGAFID flight. It returns the anomaly-model result, learned-baseline
parameter deviations, transparent engineering advisories, health index, and
`Mission Reliability Index`. The latter is explicitly an index—not a
probability of mission success—and changes with health, anomaly/fault output,
and available sensor samples.

`GET /api/reliability/{flight_id}` returns the reliability subset, while
`GET /api/model/status` exposes saved evaluation data. The React replay calls
the analysis endpoint periodically as it receives historical WebSocket
points; dashboard sensor values are never sent back as manually altered model
input.

The current saved fault classifier has held-out macro-F1 below the 0.50
prototype deployment gate. Its top class is therefore returned only as a
`candidate_fault_type` with `LIMITED_VALIDATION`; it does not raise a fault
alert. Retrain with a defensible normal class, better label linkage, and
time/flight-aware validation before enabling fault alerts.

## 8. Useful commands

```powershell
# backend (run from backend/)
pip install -r requirements.txt
python ml/inspect_dataset.py
python ml/verify_sensor_mapping.py
python ml/preprocess_dataset.py
python ml/create_features.py
python ml/train_anomaly_model.py
python ml/train_fault_model.py
python ml/evaluate_models.py
uvicorn app.main:app --reload --port 8000

# frontend (run from uav-digital-twin/)
npm install
npm run dev
```

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/flights?page=1'&'page_size=5
Invoke-RestMethod http://127.0.0.1:8000/api/analyze/1?end_index=500'&'window=120
Invoke-RestMethod http://127.0.0.1:8000/api/model/status
```
