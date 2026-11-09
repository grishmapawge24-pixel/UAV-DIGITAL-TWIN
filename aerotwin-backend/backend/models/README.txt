This folder is EMPTY until you train the models (see SETUP_GUIDE.md,
steps 7-8). It will then contain:

  anomaly_model.pkl      - trained sklearn IsolationForest    (ml/train_anomaly_model.py)
  fault_model.pkl         - trained sklearn RandomForestClassifier (or XGBoost) (ml/train_fault_model.py)
  scaler.pkl               - sklearn StandardScaler fit on the training features (both scripts)
  label_encoder.pkl        - sklearn LabelEncoder for fault label strings <-> ints (ml/train_fault_model.py)
  feature_columns.json     - ordered list of feature names the models expect
  metrics.json              - evaluation metrics from both training scripts

None of these are shipped in the project ZIP (they're generated locally
from YOUR copy of the NGAFID dataset) and are safe to delete any time to
force retraining.

Run `python ml\save_models.py` any time to check which of these files
exist and get a PASS/FAIL "ready to demo" summary.
