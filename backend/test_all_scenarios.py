import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_scenarios():
    print("=== Testing PolicyGuard End-to-End Compliance Scenarios ===")
    
    # 1. Login
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "officer@bank.com", "role": "compliance_officer"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Scenario A: Low risk compliant transaction
    print("\nTest A: Low-risk transaction (INR 2,500, KYC verified)")
    tx_a = {
        "transaction_id": "TXN_LOW_001",
        "customer_id": "CUST_GOOD",
        "amount": 2500.0,
        "currency": "INR",
        "transaction_type": "retail",
        "description": "Grocery shopping payment",
        "source_account": "ACC_111",
        "destination_account": "ACC_222",
        "kyc_verified": True
    }
    res_a = requests.post(f"{BASE_URL}/api/analyze", headers=headers, json=tx_a)
    print(f"Status Code: {res_a.status_code}")
    print(f"Verdict: {res_a.json().get('status')}, Risk Score: {res_a.json().get('risk_score')}")
    print(f"Explanation: {res_a.json().get('ai_explanation')}")

    # Scenario B: Structuring / Smurfing pattern
    print("\nTest B: Structuring transaction (INR 9,800 wire transfer)")
    tx_b = {
        "transaction_id": "TXN_STRUCT_001",
        "customer_id": "CUST_SUSP",
        "amount": 9800.0,
        "currency": "INR",
        "transaction_type": "wire_transfer",
        "description": "Structuring wire transfer under limit",
        "source_account": "ACC_333",
        "destination_account": "ACC_444"
    }
    res_b = requests.post(f"{BASE_URL}/api/analyze", headers=headers, json=tx_b)
    print(f"Verdict: {res_b.json().get('status')}, Risk Score: {res_b.json().get('risk_score')}")
    print(f"Explanation: {res_b.json().get('ai_explanation')}")

    # Scenario C: RAG Knowledge Base Query
    print("\nTest C: RAG Knowledge Base Query ('What are the KYC identity verification rules?')")
    res_c = requests.post(f"{BASE_URL}/api/rag/query", headers=headers, json={"query": "What are the KYC identity verification rules?"})
    print(f"Citations Found: {len(res_c.json().get('citations', []))}")
    if res_c.json().get('citations'):
        print(f"Top Citation: {res_c.json()['citations'][0].get('citation')}")

    # Scenario D: Audit Trail Integrity
    print("\nTest D: Cryptographic Audit Trail Retrieval")
    res_d = requests.get(f"{BASE_URL}/api/audit-logs", headers=headers)
    print(f"Total Audit Trail Entries: {len(res_d.json())}")
    if res_d.json():
        print(f"Latest Audit Event: {res_d.json()[0]}")

if __name__ == "__main__":
    test_scenarios()
