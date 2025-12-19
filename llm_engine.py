
import os
import sys
# Try importing to catch if library is missing
try:
    from ctransformers import AutoModelForCausalLM
except ImportError:
    AutoModelForCausalLM = None

# --- CONFIGURATION ---
REPO_ID = "TheBloke/BioMistral-7B-GGUF"
MODEL_FILE = "biomistral-7b.Q4_K_M.gguf" 

class MedicalLLM:
    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.load_error = None

    def load_model(self):
        if self.is_loaded:
            return

        if AutoModelForCausalLM is None:
            self.load_error = "Library 'ctransformers' not installed."
            print(self.load_error)
            return

        print(f"Loading BioMistral (Hybrid Brain)...")
        print("NOTE: This downloads ~4GB data. Please wait if this is the first run...")
        
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                REPO_ID,
                model_file=MODEL_FILE,
                model_type="mistral",
                gpu_layers=0, # CPU Mode
                context_length=2048,
                threads=4     # Use 4 CPU cores
            )
            self.is_loaded = True
            self.load_error = None
            print("BioMistral Loaded Successfully.")
            
        except Exception as e:
            self.load_error = f"Failed to load model: {str(e)}"
            print(f"LLM CRITICAL ERROR: {self.load_error}")
            self.model = None

    def enhance_diagnosis(self, disease, description, user_symptoms):
        """
        Uses the LLM to generate a compassionate, detailed explanation.
        """
        # Attempt load if needed
        if not self.is_loaded:
            self.load_model()
            
        # Check if load failed
        if self.model is None:
            return f"Note: AI Explanation unavailable. ({self.load_error or 'Unknown Error'})"

        # The Prompt
        prompt = f"""<s>[INST] You are Swasthya Sahayak, a helpful medical assistant.
        
        Clinical Findings:
        - Patient Symptoms: {', '.join(user_symptoms)}
        - Diagnosis (High Confidence): {disease}
        - Clinical Validation: {description}
        
        Task:
        Explain this condition to the patient in simple, reassuring words. 
        Give 3 actionable home remedies. 
        Keep it brief (under 150 words). [/INST]"""
        
        try:
            # Generate
            # Stream=False ensures we get the full text
            response = self.model(prompt, max_new_tokens=256)
            return response
        except Exception as e:
            return f"Error during generation: {str(e)}"

# Singleton
hybrid_bot = MedicalLLM()
