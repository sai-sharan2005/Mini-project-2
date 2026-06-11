from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import spacy
from pymongo import MongoClient
import datetime
import re
import pandas as pd
import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

app = Flask(__name__)
CORS(app)

# 1. Database Setup
try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    db = client['mvsr_hospital']
    patients_collection = db['patients']
    prescriptions_collection = db['prescriptions']
    mongodb_active = True
except Exception:
    mongodb_active = False
    patients_collection = None
    prescriptions_collection = None

# 2. NLP Setup (spaCy)
try:
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        import os
        os.system("python -m spacy download en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    spacy_active = True
except Exception:
    nlp = None
    spacy_active = False

# 3. ML Model Setup
ml_model_active = False
ml_pipeline = None
label_encoder = None
remedy_metadata = {}

def train_model():
    global ml_model_active, ml_pipeline, label_encoder, remedy_metadata
    try:
        if not os.path.exists('homeopathy_dataset.csv'):
            print("Dataset not found. ML Model disabled.")
            return

        print("Training ML Model on homeopathy_dataset.csv...")
        df = pd.read_csv('homeopathy_dataset.csv')
        
        # Build metadata dictionary
        for _, row in df.iterrows():
            rem = row['prescribed_remedy']
            if rem not in remedy_metadata:
                remedy_metadata[rem] = {
                    'miasm': row['miasm'],
                    'keynotes': row['keynotes'],
                    'potency': row['potency']
                }

        # Feature Engineering
        df['combined_text'] = df['complaints'].fillna('') + ' ' + \
                              df['modalities_worse'].fillna('') + ' ' + \
                              df['modalities_better'].fillna('') + ' ' + \
                              df['mental_state'].fillna('')

        # Fill missing numerics with medians
        df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce').fillna(df['temperature'].median() if not df['temperature'].empty else 98.6)
        df['pulse'] = pd.to_numeric(df['pulse'], errors='coerce').fillna(df['pulse'].median() if not df['pulse'].empty else 75)
        df['bp_systolic'] = pd.to_numeric(df['bp_systolic'], errors='coerce').fillna(df['bp_systolic'].median() if not df['bp_systolic'].empty else 120)
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(df['weight'].median() if not df['weight'].empty else 70)

        X = df[['combined_text', 'temperature', 'pulse', 'bp_systolic', 'weight']]
        y = df['prescribed_remedy']

        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)

        preprocessor = ColumnTransformer(
            transformers=[
                ('text', TfidfVectorizer(max_features=500), 'combined_text'),
                ('num', 'passthrough', ['temperature', 'pulse', 'bp_systolic', 'weight'])
            ]
        )

        ml_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42))
        ])

        ml_pipeline.fit(X, y_encoded)
        ml_model_active = True
        print(f"ML Model trained successfully! Categories: {len(label_encoder.classes_)}")
    except Exception as e:
        print(f"Error training ML model: {e}")
        ml_model_active = False

# Train on startup
train_model()

SYMPTOM_LIST = [
  'Headache','Fever','Fatigue','Nausea','Joint Pain','Cough','Cold','Anxiety',
  'Insomnia','Back Pain','Skin Rash','Digestive Issues','Throat Pain','Weakness',
  'Migraine','Acidity','Asthma','Allergy','Depression','Hair Loss'
]

# 4. Routes
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Prakriti Hospital Digital Care Python Backend API"
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "success": True,
        "services": {
            "spacy": spacy_active,
            "xgboost": ml_model_active,
            "mongodb": mongodb_active
        }
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json or {}
    text = data.get('text', '')
    vitals = data.get('vitals', {})
    lower = text.lower()
    
    # Extract entities using spaCy
    entities = []
    if nlp and spacy_active:
        doc = nlp(text)
        entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
        
    detected_symptoms = [s for s in SYMPTOM_LIST if s.lower() in lower]
    
    # Meta features for frontend compatibility
    modalities_worse = []
    modalities_better = []
    worse_matches = re.findall(r'worse[^,\.;]*', text, re.IGNORECASE)
    better_matches = re.findall(r'better[^,\.;]*', text, re.IGNORECASE)
    for m in worse_matches:
        modalities_worse.append(re.sub(r'worse\s*', '', m, flags=re.IGNORECASE).strip())
    for m in better_matches:
        modalities_better.append(re.sub(r'better\s*', '', m, flags=re.IGNORECASE).strip())
        
    thermal = 'cold' if ('cold' in lower or 'chilly' in lower) else ('heat' if ('heat' in lower or 'hot' in lower) else 'normal')
    mental_state = vitals.get('mental', 'Calm/Content')
    duration = vitals.get('duration', 'Acute onset')
    
    remedies = []
    feature_vector = [0.0] * 20

    if ml_model_active and ml_pipeline and label_encoder:
        # Prepare input for ML pipeline
        combined_text = f"{text} {vitals.get('modalities', '')} {mental_state}"
        
        # Parse BP
        bp_str = str(vitals.get('bp', '120/80'))
        sys_bp = 120
        if '/' in bp_str:
            try:
                sys_bp = float(bp_str.split('/')[0])
            except: pass
            
        temp = float(vitals.get('temp', 98.6)) if vitals.get('temp') else 98.6
        pulse = float(vitals.get('pulse', 75)) if vitals.get('pulse') else 75
        weight = float(vitals.get('weight', 70)) if vitals.get('weight') else 70

        input_df = pd.DataFrame([{
            'combined_text': combined_text,
            'temperature': temp,
            'pulse': pulse,
            'bp_systolic': sys_bp,
            'weight': weight
        }])

        # Predict probabilities
        probas = ml_pipeline.predict_proba(input_df)[0]
        
        # Get top 5 indices
        top_indices = np.argsort(probas)[::-1][:5]
        
        for idx in top_indices:
            prob = probas[idx]
            if prob > 0.01: # only include if > 1% confidence
                remedy_name = label_encoder.inverse_transform([idx])[0]
                meta = remedy_metadata.get(remedy_name, {})
                remedies.append({
                    "name": remedy_name,
                    "potency": meta.get('potency', '30C'),
                    "confidence": min(round(prob * 100), 99),
                    "keynotes": meta.get('keynotes', 'Predicted by ML based on symptoms and vitals.'),
                    "matched_symptoms": detected_symptoms,
                    "matched_modalities": modalities_worse[:1],
                    "constitution": "Determined by ML",
                    "miasm": meta.get('miasm', 'Unknown')
                })
    else:
        # Fallback if ML is disabled
        remedies.append({
            "name": "Sulphur",
            "potency": "30C",
            "confidence": 72,
            "keynotes": "Constitutional remedy; skin, heat, burning. (ML FALLBACK)",
            "matched_symptoms": ["General"],
            "matched_modalities": [],
            "constitution": "Sulphur Type",
            "miasm": "Psoric"
        })

    # Frontend requires 'miasm' and 'constitution' inside 'analysis'
    top_miasm = remedies[0]['miasm'] if remedies else 'Psoric'
        
    return jsonify({
        "success": True,
        "nlp": {
            "spacy_used": spacy_active,
            "detected_symptoms": detected_symptoms,
            "modalities_worse": modalities_worse,
            "modalities_better": modalities_better,
            "thermal": thermal,
            "mental_state": mental_state,
            "duration": duration
        },
        "ml": {
            "xgboost_used": ml_model_active,
            "feature_vector": feature_vector
        },
        "analysis": {
            "miasm": top_miasm,
            "constitution": "ML Predicted"
        },
        "remedies": remedies
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    # Legacy fallback endpoint
    return jsonify({
        "entities": [],
        "recommendations": [{"name": "Sulphur 30C", "miasm": "Mixed", "conf": 70}],
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/predict_stock', methods=['POST'])
def predict_stock():
    data = request.json or {}
    inventory = data.get('inventory', [])
    
    predictions = []
    for item in inventory:
        stock = item.get('stock', 0)
        name = item.get('name', '')
        
        # ML Heuristic: Polychrests are used more frequently.
        base_usage_rate = 1.0
        if any(x in name for x in ['Belladonna', 'Aconite', 'Arsenicum', 'Rhus Tox']):
            base_usage_rate = 2.8
        elif any(x in name for x in ['Sulphur', 'Calcarea', 'Lycopodium']):
            base_usage_rate = 1.8
            
        # Add slight statistical noise
        import random
        daily_usage = base_usage_rate * (1 + random.uniform(-0.15, 0.15))
        
        days_left = int(stock / daily_usage) if daily_usage > 0 and stock > 0 else 0
        if stock == 0:
            days_left = 0
            
        predictions.append({
            "name": name,
            "days_left": days_left,
            "urgent": days_left <= 5
        })
        
    return jsonify({"success": True, "predictions": predictions})

@app.route('/api/save_patient', methods=['POST'])
def save_patient():
    if not mongodb_active or not patients_collection:
        return jsonify({"status": "error", "message": "Database disconnected"}), 500
    patient_data = request.json
    patient_data['created_at'] = datetime.datetime.now()
    result = patients_collection.insert_one(patient_data)
    return jsonify({"status": "success", "id": str(result.inserted_id)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
