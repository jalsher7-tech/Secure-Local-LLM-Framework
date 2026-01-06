from engine_loader import setup_ai_engine
import os
import sys

# --- THIS WAS MISSING OR MOVED ---
# This variable must be defined at the TOP level so the class can see it.
IS_GPU_MODE = setup_ai_engine()
# ---------------------------------

try:
    from ctransformers import AutoModelForCausalLM
except ImportError as e:
    print(f"CRITICAL ENGINE FAILURE: {e}")
    # Fallback import
    from ctransformers import AutoModelForCausalLM

from config_manager import get_custom_model_path, clear_custom_model, get_template_settings, get_model_params

class AIManager:
    def __init__(self, default_model_path):
        self.default_path = default_model_path
        self.current_model_path = default_model_path
        self.is_custom_model = False
        
        # Now the class can see the global variable defined at line 7
        self.is_gpu_mode = IS_GPU_MODE 
        
        # Load Params from Config
        self.params = get_model_params()
        print(f"Engine Params: {self.params}")
        print(f"Acceleration Mode: {'GPU (CUDA)' if self.is_gpu_mode else 'CPU'}")

        custom_path = get_custom_model_path()
        
        # 1. Try to load Custom Model (Pro Mode)
        if custom_path and os.path.exists(custom_path):
            print(f"Attempting to load custom model: {custom_path}")
            try:
                # --- GPU LAYER LOGIC ---
                if self.is_gpu_mode:
                    # Use user setting, or default to 0
                    gpu_layers = self.params.get('gpu_layers', 0)
                else:
                    gpu_layers = 0
                
                self.llm = AutoModelForCausalLM.from_pretrained(
                    custom_path, 
                    model_type="llama", 
                    context_length=self.params['context_length'],
                    gpu_layers=gpu_layers 
                )
                self.current_model_path = custom_path
                self.is_custom_model = True
                print(f"Custom model loaded! (GPU Layers: {gpu_layers})")
            except Exception as e:
                print(f"CRITICAL: Custom model failed. {e}")
                clear_custom_model()
                self.load_default_model()
        else:
            self.load_default_model()

    def load_default_model(self):
        # 2. Load Default Model (Safe Mode)
        print("Loading default TinyLlama model...")
        
        # --- SAFE MODE CLAMPING ---
        raw_ctx = self.params.get('context_length', 2048)
        safe_ctx = max(512, min(raw_ctx, 2048))
        self.params['context_length'] = safe_ctx

        raw_max = self.params.get('max_new_tokens', 1024)
        self.params['max_new_tokens'] = max(128, min(raw_max, 1024))

        raw_temp = self.params.get('temperature', 0.3)
        self.params['temperature'] = max(0.1, min(raw_temp, 0.5))

        # --- NEW CLAMPING FOR HIDDEN KNOBS (Safe Mode) ---
        raw_rep = self.params.get('repetition_penalty', 1.15)
        self.params['repetition_penalty'] = max(1.0, min(raw_rep, 1.2))

        raw_top_k = self.params.get('top_k', 40)
        self.params['top_k'] = max(10, min(raw_top_k, 100))

        raw_top_p = self.params.get('top_p', 0.95)
        self.params['top_p'] = max(0.1, min(raw_top_p, 0.95))

        raw_last_n = self.params.get('last_n_tokens', 64)
        self.params['last_n_tokens'] = max(0, min(raw_last_n, 256))
        # -------------------------------------------------

        # Respect user settings for layers
        if self.is_gpu_mode:
            gpu_layers = self.params.get('gpu_layers', 0)
        else:
            gpu_layers = 0

        self.llm = AutoModelForCausalLM.from_pretrained(
            self.default_path, 
            model_type="llama", 
            context_length=safe_ctx,
            gpu_layers=gpu_layers 
        )
        self.is_custom_model = False
        print("Default model loaded.")

    def get_response(self, chat_history):
        full_prompt = ""
        use_template, template_str = get_template_settings()
        
        # --- PROMPT BUILDING ---
        if use_template and template_str:
            system_content = ""
            user_content = ""
            for message in chat_history:
                if message["role"] == "system": system_content = message["content"]
                elif message["role"] == "user": user_content = message["content"]
            full_prompt = template_str.replace("{system}", system_content).replace("{user}", user_content)

        elif not self.is_custom_model:
            for message in chat_history:
                role = message["role"]
                content = message["content"]
                if role == "system": full_prompt += f"<|system|>\n{content}</s>\n"
                elif role == "user": full_prompt += f"<|user|>\n{content}</s>\n"
                elif role == "assistant": full_prompt += f"<|assistant|>\n{content}</s>\n"
            full_prompt += "<|assistant|>\n"
            
        else:
            for message in chat_history:
                role = message["role"]
                content = message["content"]
                if role == "system": full_prompt += f"System: {content}\n"
                elif role == "user": full_prompt += f"User: {content}\n"
                elif role == "assistant": full_prompt += f"Assistant: {content}\n"
            full_prompt += "Assistant: "

        print("Sending prompt...")
        stops = ['</s>', '<|user|>', '<|system|>'] if not self.is_custom_model and not use_template else []
        
        response = self.llm(
            full_prompt, 
            stop=stops,
            max_new_tokens=self.params['max_new_tokens'],
            temperature=self.params['temperature'],
            repetition_penalty=self.params['repetition_penalty'],
            top_k=self.params['top_k'],
            top_p=self.params['top_p'],
            last_n_tokens=self.params['last_n_tokens']
        )
        return response.strip()
