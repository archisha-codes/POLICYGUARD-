import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print("🚀 Starting PolicyGuard Integration Test...")

    # Step 1: Login (Get Token)
    print("\n1. Authenticating as Compliance Officer...")
    try:
        auth_response = requests.post(f"{BASE_URL}/api/auth/login?role=compliance_officer")
        if auth_response.status_code != 200:
            print(f"❌ Login Failed: {auth_response.text}")
            return
        
        token = auth_response.json()["access_token"]
        print(f"✅ Authenticated! Token: {token[:20]}...")
    except Exception as e:
        print(f"❌ Connection Failed. Is the server running? ({e})")
        return

    # Step 2: Prepare Transaction
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "transaction_id": "TXN_998877",
        "customer_id": "CUST_555",
        "amount": 150000.00,
        "currency": "INR",
        "transaction_type": "transfer",
        "description": "Large transfer to overseas unknown account",
        "source_account": "123456789012",
        "destination_account": "987654321098",
        "metadata": {"location": "Mumbai"}
    }

    # Step 3: Send to API
    print("\n2. Sending Transaction for Analysis...")
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/analyze",
        headers=headers,
        json=payload
    )
    duration = time.time() - start_time

    # Step 4: Show Results
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Analysis Complete ({duration:.2f}s)!")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Analysis Failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    run_test()