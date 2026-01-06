import json
import os

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config_value(key, value):
    config = load_config()
    config[key] = value
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_config_value(key, default):
    config = load_config()
    return config.get(key, default)

# --- HELPER FUNCTIONS ---

def save_model_path(path):
    return save_config_value("custom_model_path", path)

def get_custom_model_path():
    return get_config_value("custom_model_path", None)

def clear_custom_model():
    """
    Performs a Factory Reset on the configuration.
    Removes Custom Model, GPU settings, Prompt Templates, and Policies.
    """
    config = load_config()
    
    # List of ALL keys to wipe to return to a "Fresh Install" state
    keys_to_remove = [
        "custom_model_path", 
        "use_custom_template", 
        "prompt_template", 
        "model_params",
        "use_gpu",           # <-- Now resets GPU to CPU
        "session_timeout",   # <-- Now resets Policy to 60s
        "history_limit"      # <-- Now resets History to 1
    ]
    
    changed = False
    for k in keys_to_remove:
        if k in config:
            del config[k]
            changed = True
            
    if changed:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

# --- TEMPLATE SETTINGS ---
def save_template_settings(enabled, template_str):
    config = load_config()
    config["use_custom_template"] = enabled
    config["prompt_template"] = template_str
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def get_template_settings():
    config = load_config()
    return config.get("use_custom_template", False), config.get("prompt_template", "")

# --- NEW: MODEL PARAMETERS ---
def save_model_params(ctx, max_tokens, temp, rep_pen, top_k, top_p, last_n):
    params = {
        "context_length": ctx, 
        "max_new_tokens": max_tokens, 
        "temperature": temp,
        "repetition_penalty": rep_pen,
        "top_k": top_k,
        "top_p": top_p,
        "last_n_tokens": last_n
    }
    return save_config_value("model_params", params)

def get_model_params():
    config = load_config()
    # Expanded Defaults for TinyLlama
    defaults = {
        "context_length": 2048, 
        "max_new_tokens": 512, 
        "temperature": 0.1,
        "repetition_penalty": 1.15,
        "top_k": 20,
        "top_p": 0.95,
        "last_n_tokens": 64
    }
    # Merges saved config with defaults (handles old config files safely)
    saved = config.get("model_params", {})
    return {**defaults, **saved}
