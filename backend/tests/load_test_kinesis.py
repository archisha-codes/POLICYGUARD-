"""Load testing for Kinesis producer with Locust.

Tests transaction throughput and latency under various load conditions.
Run with: locust -f load_test_kinesis.py --host=http://localhost:8000
"""

import os
import json
import time
import random
from datetime import datetime
from locust import HttpUser, task, between, events
from services.kinesis_producer import TransactionProducer


class KinesisLoadTest:
    """Standalone load test for Kinesis producer."""
    
    def __init__(self, num_users=10, duration=60, stream_name="policyguard-transaction-stream"):
        self.num_users = num_users
        self.duration = duration
        self.stream_name = stream_name
        self.producer = TransactionProducer(stream_name=stream_name)
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'total_latency': 0,
            'latencies': []
        }
    
    def generate_transaction(self, txn_id: int):
        """Generate a random transaction for testing."""
        customer_ids = [f'CUST{i:06d}' for i in range(1000)]
        account_ids = [f'ACC{i:05d}' for i in range(500)]
        transaction_types = ['deposit', 'withdrawal', 'transfer', 'payment', 'refund']
        
        return {
            'transaction_id': f'TXN{txn_id:010d}',
            'customer_id': random.choice(customer_ids),
            'amount': round(random.uniform(100.0, 100000.0), 2),
            'currency': 'INR',
            'transaction_type': random.choice(transaction_types),
            'description': f'Load test transaction {txn_id}',
            'source_account': random.choice(account_ids),
            'destination_account': random.choice(account_ids),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def run(self):
        """Execute load test."""
        print(f"\n" + "="*60)
        print(f"Kinesis Producer Load Test")
        print(f"Duration: {self.duration}s | Users: {self.num_users}")
        print(f"Stream: {self.stream_name}")
        print(f"="*60)
        
        start_time = time.time()
        txn_counter = 0
        
        while time.time() - start_time < self.duration:
            for user_id in range(self.num_users):
                txn_data = self.generate_transaction(txn_counter)
                txn_counter += 1
                
                # Measure send latency
                send_start = time.time()
                result = self.producer.send_transaction(txn_data)
                send_latency = (time.time() - send_start) * 1000  # Convert to ms
                
                if result:
                    self.stats['total_sent'] += 1
                    self.stats['latencies'].append(send_latency)
                    self.stats['total_latency'] += send_latency
                else:
                    self.stats['total_failed'] += 1
        
        # Print results
        self.print_results()
    
    def print_results(self):
        """Print load test results."""
        print(f"\n" + "="*60)
        print(f"Load Test Results")
        print(f"="*60)
        
        total = self.stats['total_sent'] + self.stats['total_failed']
        success_rate = (self.stats['total_sent'] / total * 100) if total > 0 else 0
        
        print(f"Total Transactions: {total}")
        print(f"Successful: {self.stats['total_sent']}")
        print(f"Failed: {self.stats['total_failed']}")
        print(f"Success Rate: {success_rate:.2f}%")
        
        if self.stats['latencies']:
            latencies = sorted(self.stats['latencies'])
            print(f"\nLatency Metrics (ms):")
            print(f"  Min: {min(latencies):.2f}")
            print(f"  Max: {max(latencies):.2f}")
            print(f"  Avg: {sum(latencies)/len(latencies):.2f}")
            print(f"  P50: {latencies[int(len(latencies)*0.5)]:.2f}")
            print(f"  P95: {latencies[int(len(latencies)*0.95)]:.2f}")
            print(f"  P99: {latencies[int(len(latencies)*0.99)]:.2f}")
        
        throughput = self.stats['total_sent'] / self.duration if self.duration > 0 else 0
        print(f"\nThroughput: {throughput:.2f} txn/sec")
        print(f"="*60 + "\n")


class KinesisLoadUser(HttpUser):
    """Locust user for HTTP-based load testing."""
    
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Initialize user."""
        self.producer = TransactionProducer()
        self.txn_counter = 0
    
    @task(1)
    def send_transaction(self):
        """Send a transaction to Kinesis."""
        transaction = {
            'transaction_id': f'LOAD-{time.time()}-{self.txn_counter}',
            'customer_id': f'CUST{random.randint(1, 10000):06d}',
            'amount': round(random.uniform(100.0, 100000.0), 2),
            'currency': 'INR',
            'transaction_type': random.choice(['deposit', 'withdrawal', 'transfer', 'payment']),
            'description': 'Load test transaction',
            'source_account': f'ACC{random.randint(1, 500):05d}',
            'destination_account': f'ACC{random.randint(1, 500):05d}'
        }
        
        try:
            start_time = time.time()
            result = self.producer.send_transaction(transaction)
            latency = time.time() - start_time
            
            if result:
                self.environment.events.request.fire(
                    request_type='kinesis',
                    name='put_record',
                    response_time=latency * 1000,
                    response_length=0,
                    response=None,
                    context={},
                    exception=None
                )
                self.txn_counter += 1
        except Exception as e:
            self.environment.events.request.fire(
                request_type='kinesis',
                name='put_record',
                response_time=0,
                response_length=0,
                response=None,
                context={},
                exception=e
            )


if __name__ == '__main__':
    import sys
    
    # Check if running as standalone or with Locust
    if 'locust' in sys.argv[0]:
        # Locust will handle the HttpUser
        pass
    else:
        # Standalone load test
        duration = int(os.getenv('LOAD_TEST_DURATION', '60'))
        num_users = int(os.getenv('LOAD_TEST_USERS', '10'))
        stream = os.getenv('KINESIS_STREAM_NAME', 'policyguard-transaction-stream')
        
        test = KinesisLoadTest(num_users=num_users, duration=duration, stream_name=stream)
        test.run()


# Standalone execution:
# python load_test_kinesis.py
#
# With custom parameters:
# LOAD_TEST_DURATION=120 LOAD_TEST_USERS=20 python load_test_kinesis.py
#
# With Locust (HTTP API):
# locust -f load_test_kinesis.py --host=http://localhost:8000 -u 50 -r 10 -t 5m
