import joblib
import sys

rf = joblib.load('app/models/crop_recommendation_model.pkl')
le = joblib.load('app/models/crop_label_encoder.pkl')

n, p, k, t, h, ph, r = map(float, sys.argv[1:])
features = [[n, p, k, t, h, ph, r]]
probs = rf.predict_proba(features)[0]

results = {le.inverse_transform([i])[0]: prob for i, prob in enumerate(probs) if prob > 0}
for k, v in sorted(results.items(), key=lambda x: x[1], reverse=True):
    print(f"{k}: {v:.2f}")

