import pandas as pd
import random
import os

REMEDIES = {
    'Belladonna': {
        'symptoms': ['throbbing headache', 'high fever', 'red face', 'sore throat', 'earache'],
        'worse': ['light', 'noise', 'jarring', 'touch'],
        'better': ['semi-erect', 'warm room'],
        'mental': ['Delirious', 'Anxious/Fearful', 'Irritable/Angry'],
        'temp_range': (100.5, 104.5),
        'pulse_range': (95, 130),
        'bp_sys_range': (120, 150),
        'miasm': 'Psoric (Acute)',
        'keynotes': 'Sudden violent onset. High fever. Throbbing pain. Flushed red face.'
    },
    'Aconite': {
        'symptoms': ['sudden fever', 'panic attack', 'dry cough', 'restlessness', 'fear of death'],
        'worse': ['cold dry wind', 'night', 'fright'],
        'better': ['open air'],
        'mental': ['Anxious/Fearful', 'Restless'],
        'temp_range': (100.0, 103.5),
        'pulse_range': (100, 140),
        'bp_sys_range': (120, 140),
        'miasm': 'Psoric (Acute)',
        'keynotes': 'Sudden fright or shock. High fever sudden onset. Fear of death.'
    },
    'Arsenicum Album': {
        'symptoms': ['food poisoning', 'asthma', 'burning pain', 'exhaustion', 'watery diarrhea'],
        'worse': ['midnight', 'cold drinks', 'cold air'],
        'better': ['heat', 'warm drinks'],
        'mental': ['Anxious/Fearful', 'Restless', 'Fastidious'],
        'temp_range': (98.0, 101.5),
        'pulse_range': (80, 110),
        'bp_sys_range': (100, 130),
        'miasm': 'Psoric/Syphilitic',
        'keynotes': 'Restlessness with exhaustion. Fear of death. Burning pains. Midnight aggravation.'
    },
    'Rhus Toxicodendron': {
        'symptoms': ['joint pain', 'stiffness', 'back pain', 'red rash', 'sprain'],
        'worse': ['first motion', 'cold damp weather', 'rest'],
        'better': ['continued motion', 'warm applications'],
        'mental': ['Restless', 'Sad/Depressed'],
        'temp_range': (98.0, 100.0),
        'pulse_range': (70, 90),
        'bp_sys_range': (110, 130),
        'miasm': 'Sycotic',
        'keynotes': 'Worse on first motion, better continued motion. Restlessness.'
    },
    'Bryonia Alba': {
        'symptoms': ['dry cough', 'joint pain', 'splitting headache', 'constipation'],
        'worse': ['any motion', 'warmth', 'morning'],
        'better': ['absolute rest', 'pressure', 'cold things'],
        'mental': ['Irritable/Angry', 'Wants to be alone'],
        'temp_range': (98.5, 101.0),
        'pulse_range': (75, 95),
        'bp_sys_range': (110, 140),
        'miasm': 'Psoric',
        'keynotes': 'Worse any motion. Wants absolute rest. Dryness. Irritable.'
    },
    'Natrum Muriaticum': {
        'symptoms': ['migraine', 'depression', 'cold sores', 'watery eyes', 'grief'],
        'worse': ['sun', 'consolation', '10 AM'],
        'better': ['open air', 'fasting', 'resting'],
        'mental': ['Sad/Depressed', 'Reserved'],
        'temp_range': (97.5, 99.0),
        'pulse_range': (65, 85),
        'bp_sys_range': (100, 125),
        'miasm': 'Sycotic',
        'keynotes': 'Reserved, dwells on grief. Headache above eyes. Craves salt.'
    },
    'Ignatia Amara': {
        'symptoms': ['grief', 'insomnia', 'lump in throat', 'sighing', 'spasms'],
        'worse': ['coffee', 'tobacco', 'emotions'],
        'better': ['eating', 'change of position'],
        'mental': ['Sad/Depressed', 'Changeable'],
        'temp_range': (98.0, 99.0),
        'pulse_range': (70, 100),
        'bp_sys_range': (110, 130),
        'miasm': 'Psoric',
        'keynotes': 'Grief, disappointment. Contradictory symptoms. Sighing.'
    },
    'Pulsatilla': {
        'symptoms': ['yellow nasal discharge', 'earache', 'indigestion', 'wandering pain'],
        'worse': ['heat', 'rich food', 'stuffy room'],
        'better': ['open air', 'consolation', 'cold applications'],
        'mental': ['Weeping', 'Yielding', 'Mild'],
        'temp_range': (98.0, 100.5),
        'pulse_range': (70, 90),
        'bp_sys_range': (105, 125),
        'miasm': 'Sycotic',
        'keynotes': 'Mild, gentle, yielding. Changeable symptoms. Worse heat, better open air.'
    },
    'Sulphur': {
        'symptoms': ['itchy skin rash', 'acidity', 'morning diarrhea', 'burning soles'],
        'worse': ['warm bed', 'bathing', '11 AM'],
        'better': ['dry warm weather', 'lying on right side'],
        'mental': ['Philosophical', 'Irritable/Angry', 'Lazy'],
        'temp_range': (98.0, 99.5),
        'pulse_range': (75, 95),
        'bp_sys_range': (120, 150),
        'miasm': 'Psoric',
        'keynotes': 'Burning pains. Skin eruptions. Heat. Morning diarrhea.'
    },
    'Lycopodium': {
        'symptoms': ['bloating', 'gas', 'right sided pain', 'kidney stones', 'hair loss'],
        'worse': ['4-8 PM', 'cold food', 'right side'],
        'better': ['warm drinks', 'motion', 'passing gas'],
        'mental': ['Anxious/Fearful', 'Dictatorial', 'Lack of confidence'],
        'temp_range': (98.0, 99.0),
        'pulse_range': (70, 85),
        'bp_sys_range': (115, 140),
        'miasm': 'Sycotic/Syphilitic',
        'keynotes': '4-8 PM aggravation. Right-sided. Gastric complaints.'
    },
    'Nux Vomica': {
        'symptoms': ['indigestion', 'constipation', 'headache', 'insomnia', 'hangover'],
        'worse': ['morning', 'cold', 'spices', 'alcohol'],
        'better': ['rest', 'warm drinks', 'evening'],
        'mental': ['Irritable/Angry', 'Impatient', 'Driven'],
        'temp_range': (98.0, 99.5),
        'pulse_range': (75, 95),
        'bp_sys_range': (120, 150),
        'miasm': 'Sycotic',
        'keynotes': 'Over-indulgence. Irritable. Constipation. Hypersensitivity.'
    },
    'Gelsemium': {
        'symptoms': ['flu', 'fatigue', 'heavy eyelids', 'anticipatory anxiety', 'trembling'],
        'worse': ['damp weather', 'bad news', '10 AM'],
        'better': ['profuse urination', 'sweating', 'bending forward'],
        'mental': ['Anxious/Fearful', 'Dull/Apathetic'],
        'temp_range': (99.0, 102.0),
        'pulse_range': (65, 85),
        'bp_sys_range': (100, 120),
        'miasm': 'Psoric',
        'keynotes': 'Slowness, dullness, weakness. Anticipatory anxiety. Flu.'
    },
    'Drosera': {
        'symptoms': ['barking cough', 'whooping cough', 'hoarseness', 'choking'],
        'worse': ['after midnight', 'lying down', 'warmth'],
        'better': ['sitting up', 'open air'],
        'mental': ['Restless', 'Anxious/Fearful'],
        'temp_range': (98.0, 100.0),
        'pulse_range': (75, 95),
        'bp_sys_range': (110, 130),
        'miasm': 'Tubercular',
        'keynotes': 'Spasmodic barking cough. Worse after midnight.'
    },
    'Calcarea Carbonica': {
        'symptoms': ['fatigue', 'weakness', 'joint pain', 'acid reflux', 'sweaty head'],
        'worse': ['cold', 'exertion', 'dampness'],
        'better': ['dry weather', 'lying on painful side'],
        'mental': ['Anxious/Fearful', 'Obstinate', 'Overworked'],
        'temp_range': (97.0, 98.6),
        'pulse_range': (60, 80),
        'bp_sys_range': (110, 135),
        'miasm': 'Psoric/Sycotic',
        'keynotes': 'Chilly, obese, sweaty head at night. Slow metabolism.'
    },
    'Phosphorus': {
        'symptoms': ['bleeding', 'burning pain', 'respiratory issues', 'hoarseness', 'gastritis'],
        'worse': ['twilight', 'left side', 'cold'],
        'better': ['eating', 'sleep', 'cold water'],
        'mental': ['Anxious/Fearful', 'Sympathetic', 'Excitable'],
        'temp_range': (98.0, 101.0),
        'pulse_range': (80, 100),
        'bp_sys_range': (105, 125),
        'miasm': 'Tubercular',
        'keynotes': 'Burning everywhere. Craves cold drinks. Fears thunderstorms. Sympathetic.'
    },
    'Lachesis': {
        'symptoms': ['hot flushes', 'palpitations', 'sore throat left side', 'asthma'],
        'worse': ['sleep (wakes worse)', 'heat', 'tight clothing'],
        'better': ['discharges', 'cold drinks', 'open air'],
        'mental': ['Suspicious', 'Talkative', 'Jealous'],
        'temp_range': (98.5, 100.5),
        'pulse_range': (85, 110),
        'bp_sys_range': (130, 160),
        'miasm': 'Syphilitic',
        'keynotes': 'Left-sided. Worse after sleep. Intolerant of tight clothing. Loquacious.'
    },
    'Sepia': {
        'symptoms': ['hormonal imbalance', 'fatigue', 'prolapse sensation', 'hair loss', 'hot flushes'],
        'worse': ['cold air', 'before menses', 'pregnancy'],
        'better': ['vigorous exercise', 'warmth', 'dancing'],
        'mental': ['Indifferent', 'Irritable/Angry', 'Sad/Depressed'],
        'temp_range': (97.5, 98.8),
        'pulse_range': (65, 80),
        'bp_sys_range': (100, 120),
        'miasm': 'Sycotic/Syphilitic',
        'keynotes': 'Indifference to loved ones. Bearing down sensation. Chilly. Better vigorous exercise.'
    },
    'Silicea': {
        'symptoms': ['frequent infections', 'weak nails', 'constipation', 'headache', 'acne'],
        'worse': ['cold', 'drafts', 'vaccination'],
        'better': ['warmth', 'wrapping up head', 'summer'],
        'mental': ['Yielding', 'Lacks confidence', 'Obstinate'],
        'temp_range': (97.0, 98.5),
        'pulse_range': (60, 75),
        'bp_sys_range': (105, 125),
        'miasm': 'Syphilitic/Psoric',
        'keynotes': 'Chilly, lacks vital heat. Weakness. Suppurative conditions. Better warmth.'
    },
    'Apis Mellifica': {
        'symptoms': ['edema', 'stinging pain', 'hives', 'urinary retention', 'joint swelling'],
        'worse': ['heat', 'touch', 'pressure', 'late afternoon'],
        'better': ['cold applications', 'open air'],
        'mental': ['Irritable/Angry', 'Restless', 'Jealous'],
        'temp_range': (99.0, 102.5),
        'pulse_range': (90, 120),
        'bp_sys_range': (120, 140),
        'miasm': 'Psoric',
        'keynotes': 'Stinging, burning pains. Edema. Thirstless. Worse heat, better cold.'
    },
    'Arnica Montana': {
        'symptoms': ['bruising', 'trauma', 'muscle soreness', 'shock', 'sprains'],
        'worse': ['touch', 'jarring', 'damp cold'],
        'better': ['lying down', 'head low'],
        'mental': ['Says they are fine', 'Irritable/Angry', 'Fear of being touched'],
        'temp_range': (98.0, 99.5),
        'pulse_range': (75, 95),
        'bp_sys_range': (110, 130),
        'miasm': 'Psoric',
        'keynotes': 'Trauma, bruising, soreness. Says "I am okay" when very sick. Fears touch.'
    }
}

DURATIONS = ['Acute onset', '1 day', '2-3 days', '1 week', '2 weeks', '1 month', '3 months', '6 months', 'Years']
POTENCIES = ['30C', '200C', '1M']

def generate_row():
    remedy_name = random.choice(list(REMEDIES.keys()))
    r = REMEDIES[remedy_name]
    
    # 1-3 symptoms
    num_sym = random.randint(1, min(3, len(r['symptoms'])))
    syms = random.sample(r['symptoms'], num_sym)
    
    # 1-2 modalities
    worse = random.choice(r['worse']) if r['worse'] else ''
    better = random.choice(r['better']) if r['better'] else ''
    
    mental = random.choice(r['mental']) if r['mental'] else 'Calm/Content'
    
    # Generate vitals with some noise
    temp = round(random.uniform(r['temp_range'][0], r['temp_range'][1]), 1)
    pulse = random.randint(r['pulse_range'][0], r['pulse_range'][1])
    sys_bp = random.randint(r['bp_sys_range'][0], r['bp_sys_range'][1])
    dia_bp = int(sys_bp * random.uniform(0.6, 0.75))
    bp = f"{sys_bp}/{dia_bp}"
    weight = random.randint(45, 95)
    
    duration = random.choice(DURATIONS)
    potency = random.choice(POTENCIES)
    
    return {
        'complaints': ", ".join(syms),
        'modalities_worse': worse,
        'modalities_better': better,
        'mental_state': mental,
        'duration': duration,
        'bp': bp,
        'bp_systolic': sys_bp,
        'bp_diastolic': dia_bp,
        'temperature': temp,
        'pulse': pulse,
        'weight': weight,
        'prescribed_remedy': remedy_name,
        'potency': potency,
        'miasm': r['miasm'],
        'keynotes': r['keynotes']
    }

if __name__ == '__main__':
    rows = []
    for _ in range(1500):
        rows.append(generate_row())
        
    df = pd.DataFrame(rows)
    df.to_csv('homeopathy_dataset.csv', index=False)
    print("Generated homeopathy_dataset.csv with 1500 rows.")
