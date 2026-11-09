# SETUP_GUIDE.md

Exact, copy-pasteable steps to get the AeroTwin AI backend running on
Windows, from zero. Every command below is meant to be run in
**PowerShell**, from inside the `backend\` folder unless stated otherwise.

If you hit an error, check **Section 12: Troubleshooting** near the bottom
before anything else - most first-time issues are covered there.

---

## 0. Before you start

You should have:
- Python 3.10, 3.11, or 3.12 installed (`python --version` to check)
- The NGAFID dataset somewhere on your laptop, in ONE folder containing
  exactly: `flight_header.csv`, `flight_data.pkl`, `stats.csv`
- This `backend\` folder unzipped somewhere convenient, e.g. `C:\Projects\aerotwin\backend`

---

## 1. Install Python dependencies

Open PowerShell, `cd` into the `backend` folder, then:

```powershell
cd C:\Projects\aerotwin\backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

> If `venv\Scripts\Activate.ps1` fails with a "running scripts is disabled"
> error, see Troubleshooting item 12.1 below.

You'll know it worked if your prompt now starts with `(venv)`.

---

## 2. Configure NGAFID_DATA_PATH

```powershell
copy .env.example .env
notepad .env
```

In Notepad, set:

```
NGAFID_DATA_PATH=C:/Users/YOUR_NAME/Datasets/ngafid
```

Use **forward slashes** (`/`), even on Windows - it avoids backslash
escape-character headaches and Python accepts it fine. This must be the
folder that directly contains `flight_header.csv`, `flight_data.pkl`, and
`stats.csv`. Save and close Notepad.

---

## 3. Inspect the dataset

This just reads and prints info about your files - nothing is written or
trained yet. Confirms your `.env` path is correct and shows you exactly
what's in the files.

```powershell
python ml\inspect_dataset.py
```

For a deeper look that also opens `flight_data.pkl` (slower, ~2.7GB, can
take a couple of minutes and a good chunk of RAM):

```powershell
python ml\inspect_dataset.py --full-scan
```

---

## 4. (Recommended) Build the fast per-flight cache

`flight_data.pkl` is one big file; loading all of it every time is slow.
This one-time step splits it into small per-flight files so everything
after this is much faster (including the live API later):

```powershell
python ml\preprocess_dataset.py
```

This can take a few minutes the first time. Safe to re-run any time
(add `--force` to overwrite existing cached files).

---

## 5. Verify the sensor mapping

**This is the most important step - read the printed output carefully.**

```powershell
python ml\verify_sensor_mapping.py
```

This prints a suggested table like:

```
pkl col suggested parameter confidence  typical range (for your reference only)
0       volt1                0.91        ~12-30 V
1       volt2                0.88        ~12-30 V
...
9       E1 RPM               0.94        ~500-2700 RPM
...
```

It also writes `data\config\sensor_mapping.json`. Open it:

```powershell
notepad data\config\sensor_mapping.json
```

Compare the suggested mapping against the printed table (and any real
documentation you have for the data logger, if available). Fix anything
that looks wrong by editing the `"parameter"` value for that column index.
When you're satisfied, change:

```json
"verified": false
```

to:

```json
"verified": true
```

Save the file. **Nothing else in the project will trust this mapping
until you do this.**

---

## 6. Preprocess the data / build features

Feature engineering reads every flight, cleans it, and computes the
mean/std/min/max/median/range/slope/rolling-std/rate-of-change features
per sensor channel:

```powershell
python ml\create_features.py
```

This writes `data\features\flight_features.csv`. For a quick test on a
small subset first (recommended before committing to a full run on all
~11,446 flights):

```powershell
python ml\create_features.py --limit 500
```

If that looks right, re-run it without `--limit` for the full dataset.

---

## 7. Train the anomaly model

```powershell
python ml\train_anomaly_model.py
```

Saves `models\anomaly_model.pkl`, `models\scaler.pkl`, and
`models\feature_columns.json`.

---

## 8. Train the fault classifier

```powershell
python ml\train_fault_model.py
```

Saves `models\fault_model.pkl` and `models\label_encoder.pkl`, and prints
a test-set accuracy/F1/classification report. This will also overwrite
`scaler.pkl` / `feature_columns.json` with an equivalent version (same
feature set, same data) - that's expected, see the note the script prints.

Optional: try XGBoost instead of Random Forest (only if you `pip install
xgboost` first):

```powershell
python ml\train_fault_model.py --model xgboost
```

---

## 9. Evaluate the models

```powershell
python ml\evaluate_models.py
```

Prints the fault classifier's held-out test metrics, plus a diagnostic
cross-check of how well the (unsupervised) anomaly model's flags line up
with real fault labels.

Then, right before your demo, run the final readiness checklist:

```powershell
python ml\save_models.py
```

---

## 10. Start the FastAPI backend

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

or just double-click **`run_backend.bat`** (it activates the venv and
starts the server for you).

You should see log lines ending with something like:
```
AeroTwin AI Backend ready. Visit http://localhost:8000/docs to explore the API.
```

Open **http://localhost:8000/docs** in your browser - this is an
interactive page where you can call every endpoint directly, no frontend
needed, to confirm everything works.

---

## 11. Connect the React frontend

1. Make sure the backend is running (step 10) on `http://localhost:8000`.
2. In the frontend project root, create a `.env` file:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api
   ```
   (Vite reads `.env` automatically - restart `npm run dev` after creating/editing it.)
3. CORS is already enabled for `localhost:3000`, `localhost:5173`, and
   `localhost:4173` (see `CORS_ORIGINS` in `.env` if your frontend runs on
   a different port - add it there, comma-separated).
4. For the WebSocket telemetry stream, connect to:
   `ws://localhost:8000/ws/telemetry/{flight_id}`
5. The Dashboard, Diagnostics, Simulation, and Mission Replay pages use the
   REST adapters in `src/services/api.js`; the Dashboard also streams selected
   historical telemetry over `ws://localhost:8000/ws/telemetry/{flight_id}`.
6. The frontend's Manual Check page calls `POST /api/manual/evaluate` and the
   Dashboard's manual override remains a local what-if overlay. Restart Vite
   after changing `VITE_API_BASE_URL` or `VITE_WS_BASE_URL`.

---

## 12. Test every API endpoint

The easiest way is `http://localhost:8000/docs` (Swagger UI) - click any
endpoint, "Try it out", fill in a `flight_id`, and execute.

From PowerShell, using `curl` (works in PowerShell 5.1+ / Windows 10+):

```powershell
curl http://localhost:8000/api/health
curl http://localhost:8000/api/sensors/available
curl http://localhost:8000/api/flights
curl "http://localhost:8000/api/flights?page=1&page_size=10"
curl http://localhost:8000/api/flights/1
curl http://localhost:8000/api/flights/1/telemetry
curl http://localhost:8000/api/flights/1/health
curl http://localhost:8000/api/flights/1/faults
curl http://localhost:8000/api/engine/status
curl http://localhost:8000/api/dashboard/summary
curl http://localhost:8000/api/replay/1
curl http://localhost:8000/api/missions

curl -X POST http://localhost:8000/api/predict -H "Content-Type: application/json" -d '{\"flight_id\": 1}'
curl -X POST http://localhost:8000/api/anomaly -H "Content-Type: application/json" -d '{\"flight_id\": 1}'
curl -X POST http://localhost:8000/api/missions/simulate -H "Content-Type: application/json" -d '{\"base_flight_id\": 1}'
curl -X POST http://localhost:8000/api/manual/evaluate -H "Content-Type: application/json" -d '{\"rpm\": 2300, \"oil_pressure\": 20}'
```

`POST /api/manual/evaluate` is the endpoint behind the frontend's **Manual Check** page - type in
current engine readings by hand (no flight_id needed) and get a real AI comparison against the
trained models. It expects values in NGAFID-native units (RPM, °F, psi, gal/hr, volts); the
frontend converts from its own display units (°C, bar, L/h) automatically - see
`src/utils/unitConversions.js` and `src/services/api.js` in the frontend project.

(Replace `1` with a real `flight_id` from your dataset - see the output of
`GET /api/flights` for valid IDs.)

For the WebSocket endpoint, the simplest test is from your browser's
DevTools console while `http://localhost:8000/docs` (or any page) is open:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/telemetry/1");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## 13. Troubleshooting

**12.1 - `venv\Scripts\Activate.ps1 cannot be loaded because running
scripts is disabled on this system`**
PowerShell's execution policy is blocking it. Run PowerShell **as
Administrator** once and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try activating the venv again in a normal PowerShell window.

**12.2 - `pip install` fails on a package**
Make sure the venv is activated (prompt starts with `(venv)`), then:
```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**12.3 - `/api/health` shows `dataset_configured: false`**
`.env` either doesn't exist or `NGAFID_DATA_PATH` is wrong/misspelled.
Re-check step 2. Remember to **restart** `uvicorn` after editing `.env`
(env vars are only read at startup).

**12.4 - `/api/flights/.../telemetry` (or similar) returns HTTP 503 "mapping
not verified"**
You haven't run `ml\verify_sensor_mapping.py` yet, or you ran it but never
changed `"verified": false` to `"verified": true` in
`data\config\sensor_mapping.json`. See step 5.

**12.5 - Everything returns `model_status: "NOT_TRAINED"`**
You haven't trained the models yet, or `models\*.pkl` got deleted. Re-run
steps 7-8, then `python ml\save_models.py` to confirm.

**12.6 - `MemoryError` / the computer grinds to a halt loading flight_data.pkl**
This file is ~2.7GB and loading it fully needs a few GB of free RAM. Close
other heavy programs, or run step 4 (`ml\preprocess_dataset.py`) once on a
machine/at a time when you have enough RAM free - after that, the API and
scripts use the small per-flight cache instead and won't need to reload
the full pickle again.

**12.7 - `ModuleNotFoundError: No module named 'app'` when running an
`ml\*.py` script**
Make sure you're running it as `python ml\script_name.py` from inside the
`backend\` folder (not from inside `ml\`). Every script also adds the
`backend\` folder to `sys.path` automatically at the top, so this should
only happen if the file was moved out of `ml\`.

**12.8 - React frontend gets a CORS error in the browser console**
Add your frontend's exact origin (protocol + host + port) to
`CORS_ORIGINS` in `.env`, comma-separated, then restart `uvicorn`. E.g.:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:1234
```

**12.9 - Port 8000 already in use**
Either stop whatever else is using it, or run on a different port:
```powershell
uvicorn app.main:app --reload --port 8001
```
(update the frontend's API URL and `CORS_ORIGINS` accordingly)

**12.10 - Training feels slow / you just want to demo the pipeline quickly**
Use `--limit` on `ml\create_features.py` (e.g. `--limit 500`) to build a
smaller feature table fast, then train on that subset. Swap to the full
dataset once you have time before the final demo.
