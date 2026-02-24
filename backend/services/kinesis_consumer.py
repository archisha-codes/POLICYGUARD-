import json
import logging
import time
import os
import boto3
from botocore.exceptions import ClientError

# Re-use core agents
from agents.pii_masking_agent import PIIMaskingAgent
from agents.rule_engine import DeterministicRuleEngine
from agents.rag_bridge import retrieve_relevant_rules
from agents.compliance_agent import analyze_transaction # Changed from analyze_with_nova
from services.audit_logger import TamperProofAuditLogger

logger = logging.getLogger("PolicyGuard-Stream")
logging.basicConfig(level=logging.INFO)

class PolicyStreamProcessor:
    def __init__(self, stream_name):
        self.stream_name = stream_name
        # Updated region to use AWS_REGION
        self.kinesis = boto3.client('kinesis', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
        
        # Initialize Agents
        self.pii_masker = PIIMaskingAgent()
        self.rule_engine = DeterministicRuleEngine()
        self.audit_logger = TamperProofAuditLogger()

    def process_record(self, record_data):
        try:
            txn = json.loads(record_data)
            logger.info(f"Processing Streamed Txn: {txn.get('transaction_id')}")
            
            # 1. Mask
            masked_txn = self.pii_masker.mask_transaction(txn)
            
            # 2. Rule Check
            rule_decision = self.rule_engine.evaluate(masked_txn)
            
            final_verdict = {}
            if rule_decision.requires_llm:
                # 3. AI Analysis (Now using Gemini)
                query = f"{masked_txn.get('description')} {masked_txn.get('amount')}"
                policy_text, _ = retrieve_relevant_rules(query)
                
                # Update variable mapping for Gemini schema
                llm_response = analyze_transaction(masked_txn, policy_text)
                if llm_response.get("status") == "success":
                    analysis = llm_response.get("analysis", {})
                    final_verdict = {
                        "verdict": analysis.get("verdict", "Manual Review").title(),
                        "explanation": analysis.get("explanation", "AI analysis complete."),
                        "risk_score": analysis.get("risk_score", 50)
                    }
                else:
                    final_verdict = {
                        "verdict": "Manual Review",
                        "explanation": "Gemini LLM Analysis Failed",
                        "risk_score": 100
                    }
            else:
                final_verdict = {
                    "verdict": "Compliant" if getattr(rule_decision, "is_compliant", True) else "Non-Compliant",
                    "explanation": getattr(rule_decision, "reason", "Rule Engine decision"),
                    "risk_score": 10 if getattr(rule_decision, "is_compliant", True) else 85
                }
            
            # 4. Log
            self.audit_logger.log_compliance_decision(
                transaction_id=txn.get("transaction_id"),
                verdict=final_verdict.get("verdict"),
                risk_score=final_verdict.get("risk_score", 0),
                explanation=final_verdict.get("explanation"),
                user_id="STREAM_PROCESSOR"
            )
            
        except Exception as e:
            logger.error(f"Error processing record: {e}")

    def run(self):
        logger.info(f"Listening to stream: {self.stream_name}")
        # Simplified polling loop for demo
        # In production, use KCL (Kinesis Client Library)
        shard_iterator = self.get_shard_iterator()
        
        while True:
            try:
                response = self.kinesis.get_records(
                    ShardIterator=shard_iterator,
                    Limit=10
                )
                
                for record in response['Records']:
                    self.process_record(record['Data'])
                    
                shard_iterator = response['NextShardIterator']
                time.sleep(1)
            except Exception as e:
                logger.error(f"Stream Error: {e}")
                time.sleep(5)

    def get_shard_iterator(self):
        # Helper to get iterator for the first shard
        response = self.kinesis.describe_stream(StreamName=self.stream_name)
        shard_id = response['StreamDescription']['Shards'][0]['ShardId']
        iter_response = self.kinesis.get_shard_iterator(
            StreamName=self.stream_name,
            ShardId=shard_id,
            ShardIteratorType='LATEST'
        )
        return iter_response['ShardIterator']

if __name__ == "__main__":
    processor = PolicyStreamProcessor(stream_name=os.getenv("KINESIS_STREAM_NAME", "pawan-stream"))
    processor.run()