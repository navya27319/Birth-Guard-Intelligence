<<<<<<< HEAD
"""
ML Model for Maternal Health Risk Assessment
Random Forest Classifier with expanded synthetic training data
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle, os, logging

logger = logging.getLogger(__name__)

class MaternalHealthModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = 'maternal_health_model.pkl'
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            self.train_model()

    def _generate_samples(self, n, systolic_range, diastolic_range, spo2_range,
                           fhr_range, age_range, week_range):
        rng = np.random.default_rng(42)
        return np.column_stack([
            rng.integers(*systolic_range,  size=n),
            rng.integers(*diastolic_range, size=n),
            rng.integers(*spo2_range,      size=n),
            rng.integers(*fhr_range,       size=n),
            rng.integers(*age_range,       size=n),
            rng.integers(*week_range,      size=n),
        ])

    def train_model(self):
        logger.info("Training maternal health risk model...")

        low    = self._generate_samples(200, (90,130),  (60,85),  (97,100), (120,155), (18,35), (12,40))
        medium = self._generate_samples(200, (130,145), (85,95),  (94,97),  (155,165), (35,42), (28,38))
        high   = self._generate_samples(200, (145,185), (95,120), (85,94),  (165,190), (40,50), (32,42))

        X = np.vstack([low, medium, high])
        y = np.array([0]*200 + [1]*200 + [2]*200)

        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        self.model = RandomForestClassifier(
            n_estimators=200, max_depth=12,
            min_samples_split=5, random_state=42, n_jobs=-1
        )
        self.model.fit(X_scaled, y)
        self.save_model()
        logger.info("Model trained and saved.")

    def save_model(self):
        with open(self.model_path, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)

    def load_model(self):
        with open(self.model_path, 'rb') as f:
            data = pickle.load(f)
        self.model  = data['model']
        self.scaler = data['scaler']
        logger.info("Model loaded.")

    def predict_risk(self, systolic, diastolic, spo2, fhr, age=28, gestational_week=28):
        features = np.array([[systolic, diastolic, spo2, fhr, age, gestational_week]])
        features_scaled = self.scaler.transform(features)

        pred   = self.model.predict(features_scaled)[0]
        probs  = self.model.predict_proba(features_scaled)[0]
        labels = ['Low', 'Medium', 'High']

        return {
            'risk_level':    labels[pred],
            'risk_score':    float(probs[pred]),
            'confidence':    float(max(probs)),
            'probabilities': {'low': float(probs[0]), 'medium': float(probs[1]), 'high': float(probs[2])},
            'recommendations': self._recommendations(systolic, diastolic, spo2, fhr, labels[pred])
        }

    def _recommendations(self, sys, dia, spo2, fhr, risk):
        recs = []
        if sys > 140 or dia > 90:
            recs += ["⚠️ Hypertension — monitor BP every 4 hrs", "Screen for pre-eclampsia"]
        elif sys > 130 or dia > 85:
            recs.append("Elevated BP — recheck in 30 mins")

        if spo2 < 95:
            recs += ["🫁 Low SpO2 — administer supplemental O₂", "Assess for respiratory distress"]
        elif spo2 < 97:
            recs.append("Monitor SpO2 closely")

        if fhr > 160:
            recs.append("💓 Fetal tachycardia — check for maternal fever/infection")
        elif fhr < 120:
            recs.append("💓 Fetal bradycardia — immediate obstetric consult")
        elif fhr > 150 or fhr < 130:
            recs.append("Monitor fetal heart rate continuously")

        if risk == 'High':
            recs += ["🚨 URGENT: Transfer to tertiary care", "Notify on-call obstetrician immediately"]
        elif risk == 'Medium':
            recs += ["Schedule follow-up within 24 hrs", "Educate patient on warning signs"]
        else:
            recs.append("✅ Continue routine antenatal care")

        return recs or ["All vitals within normal range"]

maternal_model = MaternalHealthModel()
=======
"""
ML Model for Maternal Health Risk Assessment
Random Forest Classifier with expanded synthetic training data
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle, os, logging

logger = logging.getLogger(__name__)

class MaternalHealthModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = 'maternal_health_model.pkl'
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            self.train_model()

    def _generate_samples(self, n, systolic_range, diastolic_range, spo2_range,
                           fhr_range, age_range, week_range):
        rng = np.random.default_rng(42)
        return np.column_stack([
            rng.integers(*systolic_range,  size=n),
            rng.integers(*diastolic_range, size=n),
            rng.integers(*spo2_range,      size=n),
            rng.integers(*fhr_range,       size=n),
            rng.integers(*age_range,       size=n),
            rng.integers(*week_range,      size=n),
        ])

    def train_model(self):
        logger.info("Training maternal health risk model...")

        low    = self._generate_samples(200, (90,130),  (60,85),  (97,100), (120,155), (18,35), (12,40))
        medium = self._generate_samples(200, (130,145), (85,95),  (94,97),  (155,165), (35,42), (28,38))
        high   = self._generate_samples(200, (145,185), (95,120), (85,94),  (165,190), (40,50), (32,42))

        X = np.vstack([low, medium, high])
        y = np.array([0]*200 + [1]*200 + [2]*200)

        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        self.model = RandomForestClassifier(
            n_estimators=200, max_depth=12,
            min_samples_split=5, random_state=42, n_jobs=-1
        )
        self.model.fit(X_scaled, y)
        self.save_model()
        logger.info("Model trained and saved.")

    def save_model(self):
        with open(self.model_path, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)

    def load_model(self):
        with open(self.model_path, 'rb') as f:
            data = pickle.load(f)
        self.model  = data['model']
        self.scaler = data['scaler']
        logger.info("Model loaded.")

    def predict_risk(self, systolic, diastolic, spo2, fhr, age=28, gestational_week=28):
        features = np.array([[systolic, diastolic, spo2, fhr, age, gestational_week]])
        features_scaled = self.scaler.transform(features)

        pred   = self.model.predict(features_scaled)[0]
        probs  = self.model.predict_proba(features_scaled)[0]
        labels = ['Low', 'Medium', 'High']

        return {
            'risk_level':    labels[pred],
            'risk_score':    float(probs[pred]),
            'confidence':    float(max(probs)),
            'probabilities': {'low': float(probs[0]), 'medium': float(probs[1]), 'high': float(probs[2])},
            'recommendations': self._recommendations(systolic, diastolic, spo2, fhr, labels[pred])
        }

    def _recommendations(self, sys, dia, spo2, fhr, risk):
        recs = []
        if sys > 140 or dia > 90:
            recs += ["⚠️ Hypertension — monitor BP every 4 hrs", "Screen for pre-eclampsia"]
        elif sys > 130 or dia > 85:
            recs.append("Elevated BP — recheck in 30 mins")

        if spo2 < 95:
            recs += ["🫁 Low SpO2 — administer supplemental O₂", "Assess for respiratory distress"]
        elif spo2 < 97:
            recs.append("Monitor SpO2 closely")

        if fhr > 160:
            recs.append("💓 Fetal tachycardia — check for maternal fever/infection")
        elif fhr < 120:
            recs.append("💓 Fetal bradycardia — immediate obstetric consult")
        elif fhr > 150 or fhr < 130:
            recs.append("Monitor fetal heart rate continuously")

        if risk == 'High':
            recs += ["🚨 URGENT: Transfer to tertiary care", "Notify on-call obstetrician immediately"]
        elif risk == 'Medium':
            recs += ["Schedule follow-up within 24 hrs", "Educate patient on warning signs"]
        else:
            recs.append("✅ Continue routine antenatal care")

        return recs or ["All vitals within normal range"]

maternal_model = MaternalHealthModel()
>>>>>>> 9bb3e26e38b4e8a35de943457524a5215c876960
