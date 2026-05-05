# BirthGuard Intelligence

AI-powered maternal health monitoring system for reducing pregnancy complications through real-time risk assessment.

## Features

- Real-time CTG waveform visualization
- Live alerts dashboard with risk stratification
- Mobile-optimized field data entry
- Geographic risk heatmap
- **ML-powered risk assessment** using Random Forest Classifier
- Clinical recommendations based on vitals
- Confidence scores and probability distributions

## Tech Stack

- **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript
- **Backend**: Python Flask
- **Fonts**: Google Fonts (Inter), Font Awesome 6.0
- **APIs**: RESTful endpoints for alerts and vitals

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask server:
```bash
python app.py
```

3. Open browser to `http://localhost:5000`

## API Endpoints

- `GET /api/alerts` - Fetch current alerts
- `POST /api/save_vitals` - Submit patient vitals and get ML prediction
  - Body: `{systolic, diastolic, spo2, fhr, age?, gestational_week?}`
  - Returns: Risk level, confidence, probabilities, recommendations
- `POST /api/predict` - Get ML prediction without saving
  - Body: Same as save_vitals
  - Returns: ML analysis results

## ML Model

The system uses a Random Forest Classifier trained on maternal health indicators:

- **Input Features**: Systolic BP, Diastolic BP, SpO2, Fetal Heart Rate, Age, Gestational Week
- **Output**: Risk Level (Low/Medium/High) with confidence scores
- **Clinical Recommendations**: Automated based on vitals and risk level
- **Model File**: `maternal_health_model.pkl` (auto-generated on first run)

### Testing the Model

```bash
python test_model.py
```

## Project Structure

```
├── index.html              # Main landing page
├── landing.css             # Styles and design system
├── landing.js.download     # Frontend interactivity
├── app.py                  # Flask backend
├── all.min.css            # Font Awesome icons
├── css2                    # Google Fonts
└── requirements.txt        # Python dependencies
```

## Risk Assessment Logic

- **High Risk**: BP >140/90, SpO2 <95%, FHR >160 or <120
- **Medium Risk**: BP >130/85, SpO2 <97%
- **Low Risk**: All vitals within normal range

## Future Enhancements

- ML model integration for predictive analytics
- PostgreSQL database for persistent storage
- User authentication and role-based access
- SMS/WhatsApp alert notifications
- Offline-first PWA capabilities
