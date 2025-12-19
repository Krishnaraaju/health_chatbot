
import pandas as pd
import numpy as np
import random
import os

# Common diseases to add (we will target ~100 total)
NEW_DISEASES = {
    "Influenza": ["fever", "chills", "muscle_aches", "cough", "congestion", "runny_nose", "headache", "fatigue"],
    "COVID-19": ["fever", "cough", "tiredness", "loss_of_taste", "loss_of_smell", "sore_throat"],
    "Anemia": ["fatigue", "weakness", "pale_skin", "irregular_heartbeat", "shortness_of_breath", "dizziness"],
    "Food Poisoning": ["nausea", "vomiting", "watery_diarrhea", "abdominal_pain", "fever"],
    "Bronchitis": ["cough", "production_of_mucus", "fatigue", "shortness_of_breath", "slight_fever_and_chills", "chest_discomfort"],
    "Depression": ["hopelessness", "loss_of_interest", "fatigue", "anxiety", "changes_in_appetite", "uncontrollable_emotions"],
    "Insomnia": ["difficulty_falling_asleep", "waking_up_during_night", "waking_up_too_early", "daytime_tiredness"],
    "Anxiety Disorder": ["feeling_nervous", "feeling_restless", "panic", "rapid_breathing", "sweating", "trembling"],
    "Hypertension (High BP)": ["severe_headache", "nosebleed", "fatigue", "vision_problems", "chest_pain", "difficulty_breathing"],
    "Stroke": ["sudden_numbness", "confusion", "trouble_speaking", "trouble_seeing", "trouble_walking", "severe_headache"],
    "Kidney Stones": ["severe_pain_in_side_and_back", "pain_on_urination", "pink_red_or_brown_urine", "cloudy_urine", "fever"],
    "Urinary Tract Infection (UTI)": ["strong_urge_to_urinate", "burning_sensation", "cloudy_urine", "strong_smelling_urine", "pelvic_pain"],
    "Conjunctivitis (Pink Eye)": ["redness_in_one_or_both_eyes", "itchiness_in_one_or_both_eyes", "tearing", "discharge_from_eye"],
    "Tonsillitis": ["red_swollen_tonsils", "white_or_yellow_coating_on_tonsils", "sore_throat", "difficult_or_painful_swallowing", "fever"],
    "Measles": ["fever", "dry_cough", "runny_nose", "sore_throat", "inflamed_eyes", "tiny_white_spots_inside_mouth", "skin_rash"],
    "Cholera": ["diarrhea", "nausea", "vomiting", "dehydration"],
    "Tetanus": ["jaw_cramping", "muscle_spasms", "painful_muscle_stiffness", "trouble_swallowing", "seizures", "headache", "fever"],
    "Rabies": ["fever", "headache", "nausea", "vomiting", "agitation", "anxiety", "confusion", "hyperactivity", "difficulty_swallowing"],
    "Ebola": ["fever", "severe_headache", "joint_and_muscle_aches", "weakness", "fatigue", "diarrhea", "vomiting", "stomach_pain"],
    "Zika Virus": ["mild_fever", "rash", "joint_pain", "conjunctivitis", "muscle_pain", "headache"],
    "Mumps": ["swollen_salivary_glands", "pain_on_chewing", "fever", "headache", "muscle_aches", "weakness", "fatigue", "loss_of_appetite"],
    "Rubella": ["mild_fever", "headache", "stuffy_or_runny_nose", "inflamed_red_eyes", "enlarged_lymph_nodes", "pink_rash"],
    "Whooping Cough": ["runny_nose", "nasal_congestion", "red_watery_eyes", "fever", "cough"],
    "Diphtheria": ["thick_gray_membrane_covering_throat", "sore_throat", "swollen_glands", "difficulty_breathing", "nasal_discharge", "fever"],
    "Scabies": ["itching", "thin_irregular_burrow_tracks", "blisters"],
    "Ringworm": ["scaly_ring_shaped_area", "itchiness", "red_scaly_cracked_skin", "hair_loss"],
    "Lyme Disease": ["rash", "fever", "chills", "fatigue", "body_aches", "headache", "stiff_neck", "swollen_lymph_nodes"],
    "Gout": ["intense_joint_pain", "lingering_discomfort", "inflammation_and_redness", "limited_range_of_motion"],
    "Fibromyalgia": ["widespread_pain", "fatigue", "cognitive_difficulties"],
    "Osteoporosis": ["back_pain", "loss_of_height", "stooped_posture", "bone_fracture"],
    "Appendicitis": ["sudden_pain_on_right_side", "pain_worsens_if_cough", "nausea", "vomiting", "loss_of_appetite", "fever"],
    "Hernia": ["bulge_or_lump", "pain_or_discomfort", "weakness_or_pressure", "heavy_feeling"],
    "Gallstones": ["sudden_pain_in_upper_right_abdomen", "sudden_pain_in_center_abdomen", "back_pain", "pain_in_right_shoulder", "nausea"],
    "Pancreatitis": ["upper_abdominal_pain", "abdominal_pain_radiates_to_back", "abdominal_pain_worsens_after_eating", "fever", "rapid_pulse"],
    "Liver Cirrhosis": ["fatigue", "easily_bleeding_or_bruising", "loss_of_appetite", "nausea", "swelling_in_legs", "weight_loss", "itchy_skin", "jaundice"],
    "Eczema": ["dry_skin", "itching", "red_to_brownish_gray_patches", "small_raised_bumps", "thickened_cracked_scaly_skin", "raw_sensitive_skin"],
    "Rosacea": ["facial_redness", "swollen_red_bumps", "eye_problems", "enlarged_nose"],
    "Melanoma": ["unusual_moles", "change_in_existing_mole", "dark_lesions"],
    "Glaucoma": ["patchy_blind_spots", "tunnel_vision", "severe_headache", "eye_pain", "nausea", "vomiting", "blurred_vision", "halos_around_lights"],
    "Cataracts": ["clouded_delayed_or_dim_vision", "increasing_difficulty_with_vision_at_night", "sensitivity_to_light", "need_for_brighter_light"],
    "Otitis Media (Ear Infection)": ["ear_pain", "trouble_sleeping", "trouble_hearing", "loss_of_balance", "fever", "drainage_of_fluid_from_ear"],
    "Sinusitis": ["thick_yellow_or_green_discharge", "nasal_blockage", "pain_tenderness_swelling_around_eyes_cheeks", "reduced_sense_of_smell_and_taste"]
}

def generate_expanded_dataset(base_path, output_path):
    print("Loading existing data...")
    try:
        df = pd.read_csv(base_path)
    except:
        print("Base file not found. Creating new.")
        df = pd.DataFrame()

    all_features = set(df.columns.tolist()) if not df.empty else set()
    if 'prognosis' in all_features: all_features.remove('prognosis')

    # Collect new symptoms from NEW_DISEASES
    for d, symptoms in NEW_DISEASES.items():
        for s in symptoms:
            all_features.add(s)

    all_features_list = sorted(list(all_features))
    
    # 1. Convert existing DF to new schema
    print("Normalizing existing data...")
    new_rows = []
    
    if not df.empty:
        for idx, row in df.iterrows():
            new_row = {k: 0 for k in all_features_list}
            new_row['prognosis'] = row['prognosis']
            # Find active symptoms
            for col in df.columns:
                if col != 'prognosis' and row[col] == 1:
                    new_row[col] = 1
            new_rows.append(new_row)

    # 2. Add New Diseases (Generate ~50 samples each to match Training.csv density)
    print("Generating synthetic data for new diseases...")
    for disease, symptoms in NEW_DISEASES.items():
        base_symptoms = symptoms
        
        # Generate 50 variants
        for _ in range(50):
            row_data = {k: 0 for k in all_features_list}
            row_data['prognosis'] = disease
            
            # Logic: Select 70-100% of the defining symptoms
            # + small random noise (1 random other symptom)
            
            k = max(2, int(len(base_symptoms) * random.uniform(0.7, 1.0)))
            active_symptoms = random.sample(base_symptoms, min(k, len(base_symptoms)))
            
            for s in active_symptoms:
                if s in all_features_list:
                    row_data[s] = 1
                    
            new_rows.append(row_data)

    # Create Final DataFrame
    final_df = pd.DataFrame(new_rows)
    # Ensure prognosis is last
    cols = [c for c in final_df.columns if c != 'prognosis'] + ['prognosis']
    final_df = final_df[cols]
    
    print(f"Final Dataset Size: {len(final_df)} rows")
    print(f"Total Features: {len(cols)-1}")
    print(f"Total Diseases: {len(final_df['prognosis'].unique())}")
    
    final_df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")

    # Generate Descriptions/Precautions for new diseases (Placeholder)
    # In a real scenario, we'd need a dictionary for these too.
    # We will append generic placeholders to MasterData so the App doesn't crash on lookup.
    
    update_metadata(list(NEW_DISEASES.keys()))

def update_metadata(new_disease_names):
    desc_path = os.path.join(os.path.dirname(os.path.abspath(base_path)), "..", "MasterData", "symptom_Description.csv")
    prec_path = os.path.join(os.path.dirname(os.path.abspath(base_path)), "..", "MasterData", "symptom_precaution.csv")
    
    # Read existing to check duplicates
    try:
        current_desc = pd.read_csv(desc_path, header=None)
        existing_diseases = set(current_desc.iloc[:,0].tolist())
    except:
        existing_diseases = set()

    with open(desc_path, 'a') as f:
        for d in new_disease_names:
            if d not in existing_diseases:
                f.write(f"\n{d},A medical condition characterized by {', '.join(NEW_DISEASES[d][:3])}.")
    
    with open(prec_path, 'a') as f:
        for d in new_disease_names:
            if d not in existing_diseases:
                f.write(f"\n{d},consult doctor,rest,drink plenty of fluids,monitor symptoms")

if __name__ == "__main__":
    base_path = "d:/health chatbot/Data/Training.csv"
    output_path = "d:/health chatbot/Data/Training_Expanded.csv"
    generate_expanded_dataset(base_path, output_path)
