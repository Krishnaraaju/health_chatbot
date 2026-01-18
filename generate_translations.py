import os
import pandas as pd
from deep_translator import GoogleTranslator
import time

# CONFIG
LANGUAGES = {
    "Tamil": "ta",
    "Hindi": "hi",
    "Odia": "or"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(BASE_DIR, "MasterData")
TARGET_DIR = os.path.join(BASE_DIR, "static", "data")

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

def translate_text(text, target_lang_code):
    if not text or pd.isna(text): return ""
    try:
        # Retry logic
        for attempt in range(3):
            try:
                translator = GoogleTranslator(source='auto', target=target_lang_code)
                res = translator.translate(str(text))
                return res
            except Exception as e:
                time.sleep(1)
                if attempt == 2: print(f"Failed to translate '{text[:20]}...': {e}")
        return text
    except Exception as e:
        return text

def process_file(filename, cols_to_translate):
    src_path = os.path.join(SOURCE_DIR, filename)
    if not os.path.exists(src_path):
        print(f"Skipping {filename} (Not found)")
        return

    print(f"Processing {filename}...")
    df = pd.read_csv(src_path)

    for lang_name, lang_code in LANGUAGES.items():
        output_filename = filename.replace(".csv", f"_{lang_name}.csv")
        save_path = os.path.join(TARGET_DIR, output_filename)
        
        # RESUME LOGIC: Load existing if matches source length, else start fresh/copy
        target_df = df.copy() # Start with fresh copy
        
        # Check if we already have a partial file? 
        # For simplicity in this script: We will load the EXISTING file if it exists, 
        # and only translate rows that are still English (or identical to source).
        # But determining "still English" is tricky. Use a simple checkpoint file or just check equality.
        
        if os.path.exists(save_path):
            print(f"  > Resuming {lang_name}...")
            existing_df = pd.read_csv(save_path)
            if len(existing_df) == len(df):
                target_df = existing_df
            else:
                print("    (Length mismatch, starting over)")

        print(f"  > Translating to {lang_name} ({lang_code})...")
        
        # Counters
        translated_count = 0
        skipped_count = 0
        
        for index, row in target_df.iterrows():
            row_changed = False
            for col_idx in cols_to_translate:
                if col_idx < len(row):
                    original_en = str(df.iat[index, col_idx]) # Source Truth
                    current_val = str(target_df.iat[index, col_idx])
                    
                    # If current value is same as English source (and source isn't empty), it needs translation
                    # (Unless the word is actually same in both langs, but we assume it needs translation)
                    if current_val == original_en and len(original_en) > 1 and not current_val.isdigit():
                        translated = translate_text(original_en, lang_code)
                        if translated != current_val:
                            target_df.iat[index, col_idx] = translated
                            row_changed = True
                    else:
                        pass # Already translated or empty

            if row_changed:
                translated_count += 1
                # Save every 5 rows to prevent data loss
                if translated_count % 5 == 0:
                    target_df.to_csv(save_path, index=False)
                    print(f"    Translated {index}/{len(df)} rows... (Saved)", end='\r')
            else:
                skipped_count += 1
                if index % 50 == 0:
                     print(f"    Skipping {index}/{len(df)} (Already done)...", end='\r')

        target_df.to_csv(save_path, index=False)
        print(f"\n    Finished {output_filename}. (Translated: {translated_count}, Skipped: {skipped_count})")

if __name__ == "__main__":
    # Symptom Description: Col 0 = Disease, Col 1 = Description
    # We only translate Description (Col 1) usually, but for offline lookup we might want Disease name too?
    # Actually, for lookup, we still search by English name usually (or we need a map).
    # Let's translate Description (1)
    process_file("symptom_Description.csv", [1])

    # Symptom Precaution: Col 0 = Disease, Col 1..4 = Precautions
    process_file("symptom_precaution.csv", [1, 2, 3, 4])
    
    print("All translations completed.")
