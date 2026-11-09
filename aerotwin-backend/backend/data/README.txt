This folder holds LOCALLY GENERATED, DERIVED files only.

It does NOT (and should NOT) contain the raw NGAFID dataset
(flight_header.csv, flight_data.pkl, stats.csv) - that stays wherever
you set NGAFID_DATA_PATH in your .env file, outside this repo.

Everything under this data/ folder is created automatically by the
ml/ scripts and is safe to delete at any time to reset your local
setup (you'll just need to re-run the relevant script(s)):

  data/config/sensor_mapping.json
      Written by ml/verify_sensor_mapping.py. The verified pkl-column
      <-> sensor-name mapping. This is the one file in here you should
      open and hand-check before trusting it (see the script's docstring).

  data/processed/flights/<flight_id>.npy
      Written by ml/preprocess_dataset.py. A fast per-flight cache
      extracted from the big flight_data.pkl, so the API and later
      scripts don't need to reload the whole ~2.7GB pickle every time.
      Optional but strongly recommended.

  data/processed/flight_manifest.csv
      Written by ml/preprocess_dataset.py. One row per flight: id,
      timesteps, columns, dtype. Handy quick reference.

  data/features/flight_features.csv
      Written by ml/create_features.py. The full engineered feature
      table used to train the models.

  data/aerotwin.db
      SQLite database used only to store simulated missions created via
      POST /api/missions/simulate. Safe to delete to reset mission history.

None of these files are committed/shipped in the project ZIP - this
folder starts empty (aside from this README) and fills up as you run
the setup steps in SETUP_GUIDE.md.
