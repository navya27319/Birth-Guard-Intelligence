
"""
BirthGuard Intelligence — Flask Backend
Features: SQLite DB, JWT Auth, Rate Limiting, Input Validation, Logging
"""

import logging, os

from dotenv import load_dotenv

from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request, send_from_directory, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from database.mongo import mongo
from model import maternal_model

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('birthguard.log')]
)
logger = logging.getLogger(__name__)

# ── App Setup ─────────────────────────────────────────────────────────────────
load_dotenv()
app = Flask(__name__, static_folder='.')
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod'),
    JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-prod'),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=8),
   SQLALCHEMY_DATABASE_URI='sqlite:///birthguard.db',
SQLALCHEMY_TRACK_MODIFICATIONS=False,
)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo.init_app(app)
db = SQLAlchemy(app)

CORS(app, resources={r"/api/*": {"origins": "*"}})

jwt     = JWTManager(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200/day", "60/hour"])

# ── Models ────────────────────────────────────────────────────────────────────
class User(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), unique=True, nullable=False)
    password_hash= db.Column(db.String(256), nullable=False)
    role         = db.Column(db.String(20), default='worker')   # worker | doctor | admin
    phc          = db.Column(db.String(100), default='General')
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, pw):   self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class VitalRecord(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    patient_name     = db.Column(db.String(100), nullable=False)
    systolic         = db.Column(db.Integer, nullable=False)
    diastolic        = db.Column(db.Integer, nullable=False)
    spo2             = db.Column(db.Integer, nullable=False)
    fhr              = db.Column(db.Integer, nullable=False)
    age              = db.Column(db.Integer, default=28)
    gestational_week = db.Column(db.Integer, default=28)
    risk_level       = db.Column(db.String(10), nullable=False)
    confidence       = db.Column(db.Float, nullable=False)
    recommendations  = db.Column(db.Text, nullable=False)
    phc              = db.Column(db.String(100), default='Field Entry')
    recorded_by      = db.Column(db.String(80))
    created_at       = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id':               self.id,
            'patient_name':     self.patient_name,
            'systolic':         self.systolic,
            'diastolic':        self.diastolic,
            'spo2':             self.spo2,
            'fhr':              self.fhr,
            'risk_level':       self.risk_level,
            'confidence':       self.confidence,
            'recommendations':  self.recommendations.split('||'),
            'phc':              self.phc,
            'recorded_by':      self.recorded_by,
            'time':             self.created_at.strftime('%d %b %Y, %H:%M'),
            'explanation':      f"BP {self.systolic}/{self.diastolic}, SpO2 {self.spo2}%, FHR {self.fhr}"
        }

# ── Helpers ───────────────────────────────────────────────────────────────────
def validate_vitals(data):
    errors = []
    rules = {
        'systolic':  (60,  200, 'Systolic BP'),
        'diastolic': (40,  130, 'Diastolic BP'),
        'spo2':      (70,  100, 'SpO2'),
        'fhr':       (100, 200, 'Fetal Heart Rate'),
    }
    for field, (lo, hi, label) in rules.items():
        val = data.get(field)
        if val is None:
            errors.append(f'{label} is required')
        elif not (lo <= int(val) <= hi):
            errors.append(f'{label} must be between {lo}–{hi}')
    return errors

# ── Static Routes ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# ── Auth Routes ───────────────────────────────────────────────────────────────
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("10/hour")
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role     = data.get('role', 'worker')
    phc      = data.get('phc', 'General')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409

    user = User(username=username, role=role, phc=phc)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    logger.info(f"New user registered: {username} ({role})")
    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("20/hour")
def login():
    data = request.json or {}
    user = User.query.filter_by(username=data.get('username', '')).first()
    if not user or not user.check_password(data.get('password', '')):
        logger.warning(f"Failed login attempt for: {data.get('username')}")
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_access_token(identity=str(user.id), additional_claims={
        'username': user.username, 'role': user.role, 'phc': user.phc
    })
    logger.info(f"User logged in: {user.username}")
    return jsonify({'token': token, 'username': user.username, 'role': user.role, 'phc': user.phc})

# ── Vitals Routes ─────────────────────────────────────────────────────────────
@app.route('/api/save_vitals', methods=['POST'])
@limiter.limit("100/hour")
def save_vitals():
    data   = request.json or {}
    errors = validate_vitals(data)
    if errors:
        return jsonify({'error': errors[0]}), 400

    systolic         = int(data['systolic'])
    diastolic        = int(data['diastolic'])
    spo2             = int(data['spo2'])
    fhr              = int(data['fhr'])
    age              = int(data.get('age', 28))
    gestational_week = int(data.get('gestational_week', 28))
    patient_name     = data.get('patient_name', f'Patient-{datetime.now().strftime("%H%M%S")}')
    phc              = data.get('phc', 'Field Entry')

    prediction = maternal_model.predict_risk(systolic, diastolic, spo2, fhr, age, gestational_week)
    mongo.db.vitals.insert_one({
    "patient_name": patient_name,
    "systolic": systolic,
    "diastolic": diastolic,
    "spo2": spo2,
    "fhr": fhr,
    "risk_level": prediction['risk_level'],
    "confidence": prediction['confidence']
})
    return jsonify(prediction)

    record = VitalRecord(
        patient_name     = patient_name,
        systolic         = systolic,
        diastolic        = diastolic,
        spo2             = spo2,
        fhr              = fhr,
        age              = age,
        gestational_week = gestational_week,
        risk_level       = prediction['risk_level'],
        confidence       = prediction['confidence'],
        recommendations  = '||'.join(prediction['recommendations']),
        phc              = phc,
        recorded_by      = data.get('recorded_by', 'anonymous')
    )
    db.session.add(record)
    db.session.commit()
    logger.info(f"Vitals saved: {patient_name} | Risk: {prediction['risk_level']} | PHC: {phc}")

    return jsonify({
        'status':          'success',
        'patient':         patient_name,
        'risk_level':      prediction['risk_level'],
        'confidence':      prediction['confidence'],
        'risk_score':      prediction['risk_score'],
        'probabilities':   prediction['probabilities'],
        'recommendations': prediction['recommendations'],
        'message':         'Vitals analyzed by ML model'
    })

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    records = VitalRecord.query.filter(
        VitalRecord.risk_level.in_(['High', 'Medium'])
    ).order_by(VitalRecord.created_at.desc()).limit(20).all()
    return jsonify([r.to_dict() for r in records])

@app.route('/api/history', methods=['GET'])
def get_history():
    records = VitalRecord.query.order_by(VitalRecord.created_at.desc()).limit(50).all()
    return jsonify([r.to_dict() for r in records])

@app.route('/api/predict', methods=['POST'])
@limiter.limit("200/hour")
def predict():
    data   = request.json or {}
    errors = validate_vitals(data)
    if errors:
        return jsonify({'error': errors[0]}), 400
    return jsonify(maternal_model.predict_risk(
        int(data['systolic']), int(data['diastolic']),
        int(data['spo2']),     int(data['fhr']),
        int(data.get('age', 28)), int(data.get('gestational_week', 28))
    ))

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total  = VitalRecord.query.count()
    high   = VitalRecord.query.filter_by(risk_level='High').count()
    medium = VitalRecord.query.filter_by(risk_level='Medium').count()
    low    = VitalRecord.query.filter_by(risk_level='Low').count()
    return jsonify({'total': total, 'high': high, 'medium': medium, 'low': low})

# ── Init DB ───────────────────────────────────────────────────────────────────
def seed_demo_data():
    """Seed some demo alerts so the dashboard isn't empty on first run"""
    if VitalRecord.query.count() > 0:
        return
    demos = [
        ('Priya S.',  160, 110, 92, 175, 38, 35, 'Dharavi PHC'),
        ('Meena R.',  138, 90,  95, 162, 36, 30, 'Kurla PHC'),
        ('Sunita K.', 118, 78,  98, 142, 27, 24, 'Andheri PHC'),
    ]
    for name, sys, dia, spo2, fhr, age, week, phc in demos:
        pred = maternal_model.predict_risk(sys, dia, spo2, fhr, age, week)
        db.session.add(VitalRecord(
            patient_name=name, systolic=sys, diastolic=dia,
            spo2=spo2, fhr=fhr, age=age, gestational_week=week,
            risk_level=pred['risk_level'], confidence=pred['confidence'],
            recommendations='||'.join(pred['recommendations']),
            phc=phc, recorded_by='system'
        ))
    db.session.commit()
    logger.info("Demo data seeded.")

with app.app_context():
    db.create_all()
    seed_demo_data()

@app.route('/mongo-test')
def mongo_test():
    mongo.db.test.insert_one({
        "name": "Navya"
    })

    return "MongoDB Working"
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

"""
BirthGuard Intelligence — Flask Backend
Features: SQLite DB, JWT Auth, Rate Limiting, Input Validation, Logging
"""

import logging, os
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request, send_from_directory, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from model import maternal_model

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('birthguard.log')]
)
logger = logging.getLogger(__name__)

# ── App Setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='.')
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod'),
    JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-prod'),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=8),
    SQLALCHEMY_DATABASE_URI='sqlite:///birthguard.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

CORS(app, resources={r"/api/*": {"origins": "*"}})
db      = SQLAlchemy(app)
jwt     = JWTManager(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200/day", "60/hour"])

# ── Models ────────────────────────────────────────────────────────────────────
class User(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), unique=True, nullable=False)
    password_hash= db.Column(db.String(256), nullable=False)
    role         = db.Column(db.String(20), default='worker')   # worker | doctor | admin
    phc          = db.Column(db.String(100), default='General')
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, pw):   self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class VitalRecord(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    patient_name     = db.Column(db.String(100), nullable=False)
    systolic         = db.Column(db.Integer, nullable=False)
    diastolic        = db.Column(db.Integer, nullable=False)
    spo2             = db.Column(db.Integer, nullable=False)
    fhr              = db.Column(db.Integer, nullable=False)
    age              = db.Column(db.Integer, default=28)
    gestational_week = db.Column(db.Integer, default=28)
    risk_level       = db.Column(db.String(10), nullable=False)
    confidence       = db.Column(db.Float, nullable=False)
    recommendations  = db.Column(db.Text, nullable=False)
    phc              = db.Column(db.String(100), default='Field Entry')
    recorded_by      = db.Column(db.String(80))
    created_at       = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id':               self.id,
            'patient_name':     self.patient_name,
            'systolic':         self.systolic,
            'diastolic':        self.diastolic,
            'spo2':             self.spo2,
            'fhr':              self.fhr,
            'risk_level':       self.risk_level,
            'confidence':       self.confidence,
            'recommendations':  self.recommendations.split('||'),
            'phc':              self.phc,
            'recorded_by':      self.recorded_by,
            'time':             self.created_at.strftime('%d %b %Y, %H:%M'),
            'explanation':      f"BP {self.systolic}/{self.diastolic}, SpO2 {self.spo2}%, FHR {self.fhr}"
        }

# ── Helpers ───────────────────────────────────────────────────────────────────
def validate_vitals(data):
    errors = []
    rules = {
        'systolic':  (60,  200, 'Systolic BP'),
        'diastolic': (40,  130, 'Diastolic BP'),
        'spo2':      (70,  100, 'SpO2'),
        'fhr':       (100, 200, 'Fetal Heart Rate'),
    }
    for field, (lo, hi, label) in rules.items():
        val = data.get(field)
        if val is None:
            errors.append(f'{label} is required')
        elif not (lo <= int(val) <= hi):
            errors.append(f'{label} must be between {lo}–{hi}')
    return errors

# ── Static Routes ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# ── Auth Routes ───────────────────────────────────────────────────────────────
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("10/hour")
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role     = data.get('role', 'worker')
    phc      = data.get('phc', 'General')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409

    user = User(username=username, role=role, phc=phc)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    logger.info(f"New user registered: {username} ({role})")
    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("20/hour")
def login():
    data = request.json or {}
    user = User.query.filter_by(username=data.get('username', '')).first()
    if not user or not user.check_password(data.get('password', '')):
        logger.warning(f"Failed login attempt for: {data.get('username')}")
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_access_token(identity=str(user.id), additional_claims={
        'username': user.username, 'role': user.role, 'phc': user.phc
    })
    logger.info(f"User logged in: {user.username}")
    return jsonify({'token': token, 'username': user.username, 'role': user.role, 'phc': user.phc})

# ── Vitals Routes ─────────────────────────────────────────────────────────────
@app.route('/api/save_vitals', methods=['POST'])
@limiter.limit("100/hour")
def save_vitals():
    data   = request.json or {}
    errors = validate_vitals(data)
    if errors:
        return jsonify({'error': errors[0]}), 400

    systolic         = int(data['systolic'])
    diastolic        = int(data['diastolic'])
    spo2             = int(data['spo2'])
    fhr              = int(data['fhr'])
    age              = int(data.get('age', 28))
    gestational_week = int(data.get('gestational_week', 28))
    patient_name     = data.get('patient_name', f'Patient-{datetime.now().strftime("%H%M%S")}')
    phc              = data.get('phc', 'Field Entry')

    prediction = maternal_model.predict_risk(systolic, diastolic, spo2, fhr, age, gestational_week)

    record = VitalRecord(
        patient_name     = patient_name,
        systolic         = systolic,
        diastolic        = diastolic,
        spo2             = spo2,
        fhr              = fhr,
        age              = age,
        gestational_week = gestational_week,
        risk_level       = prediction['risk_level'],
        confidence       = prediction['confidence'],
        recommendations  = '||'.join(prediction['recommendations']),
        phc              = phc,
        recorded_by      = data.get('recorded_by', 'anonymous')
    )
    db.session.add(record)
    db.session.commit()
    logger.info(f"Vitals saved: {patient_name} | Risk: {prediction['risk_level']} | PHC: {phc}")

    return jsonify({
        'status':          'success',
        'patient':         patient_name,
        'risk_level':      prediction['risk_level'],
        'confidence':      prediction['confidence'],
        'risk_score':      prediction['risk_score'],
        'probabilities':   prediction['probabilities'],
        'recommendations': prediction['recommendations'],
        'message':         'Vitals analyzed by ML model'
    })

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    records = VitalRecord.query.filter(
        VitalRecord.risk_level.in_(['High', 'Medium'])
    ).order_by(VitalRecord.created_at.desc()).limit(20).all()
    return jsonify([r.to_dict() for r in records])

@app.route('/api/history', methods=['GET'])
def get_history():
    records = VitalRecord.query.order_by(VitalRecord.created_at.desc()).limit(50).all()
    return jsonify([r.to_dict() for r in records])

@app.route('/api/predict', methods=['POST'])
@limiter.limit("200/hour")
def predict():
    data   = request.json or {}
    errors = validate_vitals(data)
    if errors:
        return jsonify({'error': errors[0]}), 400
    return jsonify(maternal_model.predict_risk(
        int(data['systolic']), int(data['diastolic']),
        int(data['spo2']),     int(data['fhr']),
        int(data.get('age', 28)), int(data.get('gestational_week', 28))
    ))

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total  = VitalRecord.query.count()
    high   = VitalRecord.query.filter_by(risk_level='High').count()
    medium = VitalRecord.query.filter_by(risk_level='Medium').count()
    low    = VitalRecord.query.filter_by(risk_level='Low').count()
    return jsonify({'total': total, 'high': high, 'medium': medium, 'low': low})

# ── Init DB ───────────────────────────────────────────────────────────────────
def seed_demo_data():
    """Seed some demo alerts so the dashboard isn't empty on first run"""
    if VitalRecord.query.count() > 0:
        return
    demos = [
        ('Priya S.',  160, 110, 92, 175, 38, 35, 'Dharavi PHC'),
        ('Meena R.',  138, 90,  95, 162, 36, 30, 'Kurla PHC'),
        ('Sunita K.', 118, 78,  98, 142, 27, 24, 'Andheri PHC'),
    ]
    for name, sys, dia, spo2, fhr, age, week, phc in demos:
        pred = maternal_model.predict_risk(sys, dia, spo2, fhr, age, week)
        db.session.add(VitalRecord(
            patient_name=name, systolic=sys, diastolic=dia,
            spo2=spo2, fhr=fhr, age=age, gestational_week=week,
            risk_level=pred['risk_level'], confidence=pred['confidence'],
            recommendations='||'.join(pred['recommendations']),
            phc=phc, recorded_by='system'
        ))
    db.session.commit()
    logger.info("Demo data seeded.")

with app.app_context():
    db.create_all()
    seed_demo_data()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)