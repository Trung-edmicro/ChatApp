from dotenv import load_dotenv, set_key

# Load biến môi trường từ file .env
load_dotenv()

def set_api_keys(gemini_key, gpt_key):
    env_file = ".env"

    if not gemini_key.strip() and not gpt_key.strip():
        return
    
    if gemini_key.strip():
        set_key(env_file, "GEMINI_API_KEY", gemini_key)
        return "success"

    if gpt_key.strip():
        set_key(env_file, "OPENAI_API_KEY", gpt_key)
        return "success"