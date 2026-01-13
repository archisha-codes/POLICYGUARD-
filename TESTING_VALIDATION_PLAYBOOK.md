# TESTING & VALIDATION PLAYBOOK - Phase 1 Complete

## For All Team Members: Validation & Testing Checklist

Now that the Amazon Nova (Bedrock) migration code is committed, this playbook guides you through validation, testing, and production readiness checks.

**Target Audience**: Pawan (Infrastructure), Himansh (QA/Testing), Archisha (Lead)
**Status**: Phase 1 Code Commit Complete ✅
**Current Date**: January 13, 2026

---

## 📋 Master Checklist

### Infrastructure (Pawan)
- [ ] **Step 1**: Enable Nova models in AWS Bedrock console (Model Access)
- [ ] **Step 2**: Create IAM policy `PolicyGuard-Bedrock-Nova-Access`
- [ ] **Step 3**: Attach policy to compute role (EC2/Lambda/ECS)
- [ ] **Step 4**: Set environment variables (BEDROCK_REGION, NOVA_MODEL_ID)
- [ ] **Step 5**: Run health check - verify Bedrock connectivity
- [ ] **Step 6**: Document setup in team wiki

### Testing (Himansh / QA Team)
- [ ] **Test 1**: Unit test compliance agent directly
- [ ] **Test 2**: API endpoint test with sample transactions
- [ ] **Test 3**: Performance baseline (latency, throughput)
- [ ] **Test 4**: Error handling test (simulate failures)
- [ ] **Test 5**: Cost calculation test
- [ ] **Test 6**: Comparison vs IBM Granite (historical data)

### Production Readiness (Archisha)
- [ ] Code review of all changes
- [ ] Security audit (no hardcoded keys, IAM-only)
- [ ] Performance sign-off
- [ ] Documentation complete
- [ ] Team trained

---

## ✅ Step-by-Step Testing Guide

### Phase 1: Unit Tests (Local/Dev)

#### 1.1 Health Check

```bash
# In Python REPL or test script
from services.bedrock_client import health_check
import json

print("Testing Bedrock health...")
result = health_check()
print(json.dumps(result, indent=2))

# Expected: {"status": "success", "text": "..."}
assert result["status"] == "success", "Health check failed"
print("✅ Health check PASSED")
```

**Expected Output**:
```json
{
  "status": "success",
  "text": "{\"status\": \"ok\", \"model\": \"nova\"}",
  "tokens_used": "45",
  "timestamp": "2026-01-13T..."
}
```

#### 1.2 Direct Compliance Agent Test

```python
from backend.agents.compliance_agent import call_nova_for_compliance
import json

# Test 1: Compliant transaction
print("\nTest 1: Compliant Transaction")
transaction_1 = """
Sender: ABC Corp, Amount: $5,000, Destination: Bank of America
Customer Status: Verified, Risk Level: Low
"""

policies_1 = """
AML Rule 1: Flag transactions >$10,000 to high-risk countries
AML Rule 2: Require verification for new entities
PMLA Rule 1: Monitor politically exposed persons
"""

result_1 = call_nova_for_compliance(transaction_1, policies_1)
print(json.dumps(result_1, indent=2))

assert "verdict" in result_1, "Missing 'verdict' in response"
assert "risk_score" in result_1, "Missing 'risk_score' in response"
assert result_1["verdict"] in ["Compliant", "Non-Compliant", "Manual Review"], "Invalid verdict"
print("✅ Test 1 PASSED")

# Test 2: Non-compliant transaction
print("\nTest 2: Non-Compliant Transaction")
transaction_2 = """
Sender: Unknown Corp, Amount: $50,000, Destination: Syria
Customer Status: Not Verified, Multiple transactions in 1 hour
"""

result_2 = call_nova_for_compliance(transaction_2, policies_1)
print(json.dumps(result_2, indent=2))

if result_2["verdict"] == "Non-Compliant":
    print("✅ Test 2 PASSED - Correctly identified non-compliant transaction")
else:
    print(f"⚠️ Test 2 ATTENTION - Got verdict: {result_2['verdict']} (may be correct depending on model)")

# Test 3: JSON Parsing
print("\nTest 3: Response Format Validation")
assert isinstance(result_1, dict), "Response should be dict"
assert isinstance(result_1["risk_score"], (int, float)), "Risk score should be numeric"
assert 0 <= result_1["risk_score"] <= 100, "Risk score should be 0-100"
print("✅ Test 3 PASSED - Response format valid")
```

**Expected Results**:
- ✅ Health check returns success
- ✅ Compliance agent processes transactions
- ✅ Response is valid JSON with required fields
- ✅ Risk scores are 0-100
- ✅ Verdicts are one of: Compliant, Non-Compliant, Manual Review

---

### Phase 2: API Integration Tests

#### 2.1 FastAPI Endpoint Test

```bash
# Start FastAPI server (if not running)
cd backend
uvicorn main:app --reload --port 8000 &

# Test 1: Health endpoint
curl -X GET http://localhost:8000/bedrock-health

# Expected: {"status": "success", ...}

# Test 2: Compliance classification
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Transaction from ABC Corp, $5,000 to Bank of America"
  }'

# Expected:
# {"compliant": "Compliant", "risk_score": 15, "reasoning": "...", "citations": [...]}
```

#### 2.2 Load Test (Throughput)

```bash
# Install ab (Apache Bench) if not installed
# apt-get install apache2-utils  # Ubuntu/Debian
# brew install httpd              # macOS

# Run 100 requests with 10 concurrent
ab -n 100 -c 10 http://localhost:8000/bedrock-health

# Expected:
# - Requests per second: > 50 (for Nova Micro)
# - Response time: 200-500ms average
# - Failed requests: 0
```

---

### Phase 3: Comparison Tests (Nova vs Granite)

#### 3.1 Compliance Accuracy

```python
# Compare outputs on same test cases
test_cases = [
    {
        "name": "High-value compliant",
        "transaction": "ABC Corp, $50,000, verified customer",
        "expected_verdict": "Compliant",
    },
    {
        "name": "High-risk jurisdiction",
        "transaction": "Unknown entity, $100,000, Syria",
        "expected_verdict": "Non-Compliant",
    },
    # ... more test cases
]

passed = 0
failed = 0

for test in test_cases:
    result = call_nova_for_compliance(test["transaction"], "Standard AML/PMLA policies")
    verdict = result["verdict"]
    
    if verdict == test["expected_verdict"]:
        print(f"✅ {test['name']}: {verdict}")
        passed += 1
    else:
        print(f"❌ {test['name']}: Expected {test['expected_verdict']}, got {verdict}")
        failed += 1

print(f"\nResults: {passed} passed, {failed} failed")
accuracy = (passed / (passed + failed)) * 100
print(f"Accuracy: {accuracy:.1f}%")

# Target: >= 95% accuracy compared to Granite baseline
assert accuracy >= 90, f"Accuracy {accuracy}% below threshold"
print("✅ Accuracy test PASSED")
```

#### 3.2 Latency Benchmark

```python
import time
import statistics

latencies = []

for i in range(50):
    start = time.time()
    result = call_nova_for_compliance("Test transaction", "Test policy")
    elapsed = time.time() - start
    latencies.append(elapsed)

print(f"Average latency: {statistics.mean(latencies):.2f}s")
print(f"Median latency: {statistics.median(latencies):.2f}s")
print(f"P95 latency: {statistics.quantiles(latencies, n=20)[18]:.2f}s")
print(f"P99 latency: {statistics.quantiles(latencies, n=100)[98]:.2f}s")

# Target: < 1 second average for Nova Micro
assert statistics.mean(latencies) < 1.0, "Latency exceeds threshold"
print("✅ Latency test PASSED")
```

---

### Phase 4: Error Handling Tests

```python
# Test 1: Missing environment variables
import os
original_region = os.environ.get("BEDROCK_REGION")
try:
    del os.environ["BEDROCK_REGION"]
    # Should fall back to default
    from services.bedrock_client import get_bedrock_client
    client = get_bedrock_client()
    assert client.region_name == "us-east-1", "Default region not applied"
    print("✅ Env var fallback test PASSED")
finally:
    if original_region:
        os.environ["BEDROCK_REGION"] = original_region

# Test 2: Invalid model response
from services.bedrock_client import BedrockNovaClient
client = BedrockNovaClient()

# Simulate bad JSON from model
response_text = "This is not JSON"
parsed = client.parse_json_response(response_text)
assert "status" in parsed, "Should have fallback status"
assert parsed["status"] == "parse_error", "Should indicate parse error"
print("✅ Invalid JSON handling test PASSED")

# Test 3: Network failure handling
try:
    # Simulate no internet (manual test)
    result = client.invoke("Test prompt")
    if result["status"] == "error":
        print("✅ Network failure handling test PASSED")
except Exception as e:
    print(f"⚠️ Network test - caught exception: {e}")
```

---

## 📊 Metrics to Track

### Performance Metrics
- **Latency**: P50, P95, P99 response times
- **Throughput**: Requests/second, transactions/minute
- **Error Rate**: Failed invocations %
- **Token Usage**: Input/output tokens per request

### Business Metrics
- **Accuracy**: % of verdicts matching baseline
- **Cost**: $ per transaction (compare to Granite)
- **Coverage**: % of transactions classified vs manual review
- **False Positive Rate**: Non-compliant flagged but actually safe

### Operational Metrics
- **Availability**: % uptime of Bedrock service
- **IAM Errors**: Permission denials (should be 0 after setup)
- **Model Errors**: Invalid model IDs, region errors

---

## 🚨 Rollback Plan

If Nova performs worse than Granite:

1. **Immediate**: Revert `backend/agents/compliance_agent.py` to use `analyze_with_granite()` fallback
2. **Short-term**: Investigate cause (accuracy, latency, cost)
3. **Mid-term**: Tune Nova parameters (temperature, max_tokens)
4. **Long-term**: Consider hybrid approach (Micro for simple, Pro for complex)

---

## ✅ Sign-Off Checklist

Before moving to production:

- [ ] All unit tests passing
- [ ] API endpoint tests successful
- [ ] Performance meets SLA (latency < 1s, accuracy > 95%)
- [ ] Error handling verified
- [ ] Cost within budget ($300-400/month estimated)
- [ ] Security audit passed (no secrets, IAM-only)
- [ ] Documentation updated
- [ ] Team trained
- [ ] Monitoring alerts configured

---

## 📞 Contact & Escalation

| Issue | Owner | Contact |
|-------|-------|----------|
| Infrastructure setup | Pawan | pawan@policyguard.dev |
| Testing failures | Himansh | himansh@policyguard.dev |
| Production issues | Archisha | archisha@policyguard.dev |
| AWS Bedrock support | AWS | https://console.aws.amazon.com/support |

---

**Status**: Phase 1 Code Complete ✅
**Next Phase**: Infrastructure Setup (Pawan) → Testing (Himansh) → Production (Archisha)
**Deadline**: Mid-January 2026
