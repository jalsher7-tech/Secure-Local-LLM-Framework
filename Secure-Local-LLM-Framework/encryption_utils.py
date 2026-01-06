import os
import json
import base64      
import keyring 
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"
SERVICE_ID = "OpsGuard_App"
USER_ID = "Local_User_Key"

def load_key():
    # 1. Try to get key from System Vault (Secure)
    stored_key = keyring.get_password(SERVICE_ID, USER_ID)

    if stored_key:
        # Found in vault! Decode from text back to bytes
        return base64.b64decode(stored_key)
    
    # 2. If not in vault, check if we have an old insecure file (Migration Logic)
    elif os.path.exists(KEY_FILE):
        print("SECURITY UPGRADE: Migrating key to System Vault...")
        with open(KEY_FILE, "rb") as f:
            old_key_bytes = f.read()
            
        # Save to Vault
        key_str = base64.b64encode(old_key_bytes).decode('utf-8')
        keyring.set_password(SERVICE_ID, USER_ID, key_str)
        
        # DELETE the insecure file
        try:
            os.remove(KEY_FILE)
            print("SUCCESS: Insecure 'secret.key' file deleted.")
        except Exception as e:
            print(f"WARNING: Could not delete old key file: {e}")
            
        return old_key_bytes

    # 3. If neither exists, generate a brand new one directly in Vault
    else:
        print("SECURITY: Generating new secure key in System Vault...")
        new_key = Fernet.generate_key()
        
        # Save to Vault
        key_str = base64.b64encode(new_key).decode('utf-8')
        keyring.set_password(SERVICE_ID, USER_ID, key_str)
        
        return new_key

def encrypt_data(data_dict):
    """
    Takes a Dictionary, converts to JSON string, then bytes, then encrypts.
    """
    key = load_key()
    f = Fernet(key)
    
    # Use json.dumps instead of str()
    json_str = json.dumps(data_dict)
    
    encrypted_data = f.encrypt(json_str.encode())
    return encrypted_data

def decrypt_data(encrypted_data):
    """
    Takes encrypted bytes, decrypts them, returns a Dictionary.
    """
    key = load_key()
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data)
    
    # Use json.loads instead of eval() (Security Fix)
    return json.loads(decrypted_data.decode())
