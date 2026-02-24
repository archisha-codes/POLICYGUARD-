# Load Testing Configuration & Performance Baselines
**Completed:** January 15, 2026 | **Status:** Ready for Execution

---

## 🔧 Test Environment Setup

### Prerequisites
```bash
pip install locust==2.17.0  # Load testing framework
pip install pytest-benchmark  # Benchmarking
```

### Services to Start
```bash
# 1. PostgreSQL (RDS)
docker run -d -e POSTGRES_PASSWORD=testpass -p 5432:5432 postgres:15

# 2. OpenSearch
docker run -d -p 9200:9200 opensearchproject/opensearch:2.11.0

# 3. FastAPI Backend
cd backend
python -m uvicorn app:app --port 8000
```

---

## 📊 Load Testing Scenarios

### Scenario 1: Low Load (Baseline)
**Concurrent Users:** 50
**Duration:** 3 minutes
**Ramp-up:** 10 seconds

**Expected Metrics:**
- Response Time (p50): <100ms
- Response Time (p95): <500ms
- Error Rate: <0.1%
- Throughput: 500-1000 tx/sec

**Command:**
```bash
locust -f load_test_kinesis.py --users 50 --spawn-rate 5 -t 180s
```

### Scenario 2: Medium Load (Demo Ready)
**Concurrent Users:** 100
**Duration:** 5 minutes
**Ramp-up:** 20 seconds

**Expected Metrics:**
- Response Time (p50): <150ms
- Response Time (p95): <800ms
- Error Rate: <0.5%
- Throughput: 1000-2000 tx/sec

**Command:**
```bash
locust -f load_test_kinesis.py --users 100 --spawn-rate 5 -t 300s
```

### Scenario 3: High Load (Stress Test)
**Concurrent Users:** 200
**Duration:** 5 minutes
**Ramp-up:** 30 seconds

**Expected Metrics:**
- Response Time (p50): <300ms
- Response Time (p95): <1500ms
- Error Rate: <2%
- Throughput: 1500-3000 tx/sec
- No system crashes

**Command:**
```bash
locust -f load_test_kinesis.py --users 200 --spawn-rate 5 -t 300s
```

---

## 📈 Performance Baselines (Expected Results)

### Rule Engine Performance
| Load Level | Avg Latency | p95 | Throughput | Notes |
|-----------|------------|-----|-----------|-------|
| 50 users | 45ms | 120ms | 750 tx/s | Excellent - Low risk path |
| 100 users | 75ms | 200ms | 1500 tx/s | Good - Mix of rules/LLM |
| 200 users | 150ms | 400ms | 2500 tx/s | Acceptable - Under load |

### Database Connection Pool
| Load Level | Active Connections | Connection Waits | Pool Efficiency |
|-----------|-------------------|-----------------|----------------|
| 50 users | 8-12 | 0% | 100% |
| 100 users | 15-18 | <1% | 99% |
| 200 users | 20-25 | <5% | 95% |

---

## 🔍 Monitoring During Tests

### Key Metrics to Watch
1. **CPU Usage:** Should stay <80%
2. **Memory Usage:** Should stay <85%
3. **Database Connections:** Should not exceed 30
4. **Error Rate:** Should stay <2%
5. **Response Times:** p95 should stay <1.5s

### Commands to Monitor
```bash
# Monitor Docker container
docker stats policyguard-backend

# Monitor PostgreSQL connections
psql -h localhost -U postgres -d policyguard -c "SELECT count(*) FROM pg_stat_activity;"

# Monitor OpenSearch health
curl http://localhost:9200/_cluster/health?pretty
```

---

## ✅ Success Criteria

### Minimum Requirements
- [ ] **No crashes** during 100-user load test
- [ ] **<0.5% error rate** at 100 users
- [ ] **p95 latency <1s** at 100 users
- [ ] **Database connections** stable (no leaks)
- [ ] **Rule engine** avg <100ms latency

### Ideal Requirements
- [ ] Handle **200 concurrent users** without degradation
- [ ] **<0.1% error rate** at all load levels
- [ ] **p95 latency <500ms** even at 200 users
- [ ] Auto-approved transactions (<10ms latency)
- [ ] LLM queries responsive (<5s total)

---

## 📋 Results Template

After running tests, fill this in:

```
Test Run Date: _______________
Tester: _______________

### 50-User Test
Average Latency: _____ ms
p95 Latency: _____ ms
Throughput: _____ tx/sec
Error Rate: _____ %
Status: [ ] PASS [ ] FAIL

### 100-User Test
Average Latency: _____ ms
p95 Latency: _____ ms
Throughput: _____ tx/sec
Error Rate: _____ %
Status: [ ] PASS [ ] FAIL

### 200-User Test
Average Latency: _____ ms
p95 Latency: _____ ms
Throughput: _____ tx/sec
Error Rate: _____ %
Status: [ ] PASS [ ] FAIL

### Overall Result
[ ] Demo Ready
[ ] Needs Optimization
[ ] Fails Baseline
```

---

## 🚀 Running the Complete Test Suite

```bash
#!/bin/bash
# Run all 3 load tests in sequence

echo "Starting Low Load Test..."
locust -f load_test_kinesis.py --users 50 --spawn-rate 5 -t 180s
sleep 60

echo "Starting Medium Load Test..."
locust -f load_test_kinesis.py --users 100 --spawn-rate 5 -t 300s
sleep 60

echo "Starting High Load Test..."
locust -f load_test_kinesis.py --users 200 --spawn-rate 5 -t 300s

echo "All tests complete!"
```

---

## 📝 Troubleshooting

If you see high error rates:
1. **Check database connections:** `SELECT count(*) FROM pg_stat_activity;`
2. **Check OpenSearch:** `curl http://localhost:9200/`
3. **Check application logs:** `docker logs <container_id>`
4. **Reduce concurrent users** and try again
5. **Check system resources:** `top` or `docker stats`
