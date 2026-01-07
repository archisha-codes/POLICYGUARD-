# test_ibm.py
from dotenv import load_dotenv
from ibm_watsonx_ai.foundation_models import ModelInference


# Get creds from .env (Make sure these are set!)
api_key = "kSTCg7uk4kb7qM-OtpQBaI1vHGzLMBzHQxwer6BFPTQG"
project_id = "633eed58-706c-487e-94c8-382b368feae3" 

print(f"Testing connection to Project: {project_id}...")

try:
    model = ModelInference(
        model_id="ibm/granite-13b-instruct-v2",
        credentials={
            "apikey": api_key,
            "url": "https://jp-tok.ml.cloud.ibm.com"
        },
        project_id=project_id
    )
    
    # Try a simple "Hello"
    result = model.generate_text("Say 'System Operational' if you can hear me.")
    print(f"\n✅ SUCCESS! Granite replied: {result}")

except Exception as e:
    print(f"\n❌ FAILED. Error: {e}")