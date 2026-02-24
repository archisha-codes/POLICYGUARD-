"""AWS Kinesis Producer for PolicyGuard transaction streaming.

This module handles sending transaction data to AWS Kinesis stream.
Transactions are serialized as JSON and sent with customer_id as partition key
for efficient stream processing and load distribution.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types (from Aurora RDS queries)."""
    
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


class TransactionProducer:
    """Produces transactions to AWS Kinesis stream."""
    
    def __init__(
        self,
        stream_name: str = None,
        region_name: str = None
    ):
        """Initialize Kinesis producer."""
        self.stream_name = stream_name or os.getenv("KINESIS_STREAM_NAME", "pawan-stream")
        self.region_name = region_name or os.getenv("AWS_REGION", "ap-south-1")
        
        try:
            self.kinesis_client = boto3.client(
                'kinesis',
                region_name=self.region_name
            )
            logger.info(f"Kinesis producer initialized for stream: {self.stream_name}")
        except ClientError as e:
            logger.error(f"Failed to initialize Kinesis client: {e}")
            raise
    
    def send_transaction(
        self,
        transaction: Dict[str, Any]
    ) -> Optional[str]:
        """
        Send transaction to Kinesis stream.
        
        Args:
            transaction: Transaction data dictionary containing:
                - transaction_id: Unique transaction ID
                - customer_id: Customer identifier (used as partition key)
                - amount: Transaction amount
                - currency: Currency code
                - transaction_type: Type of transaction
                - description: Transaction description
                - timestamp: Transaction timestamp
                - source_account: Source account
                - destination_account: Destination account
        
        Returns:
            Shard ID of the record if successful, None otherwise
        """
        try:
            # Validate required fields
            if not transaction.get('customer_id'):
                logger.error("Missing customer_id in transaction")
                return None
            
            # Add timestamp if not present
            if 'timestamp' not in transaction:
                transaction['timestamp'] = datetime.utcnow().isoformat()
            
            # Serialize transaction data
            transaction_json = json.dumps(
                transaction,
                cls=DecimalEncoder,
                default=str
            ).encode('utf-8')
            
            # Use customer_id as partition key for consistent routing
            partition_key = str(transaction['customer_id'])
            
            # Send to Kinesis
            response = self.kinesis_client.put_record(
                StreamName=self.stream_name,
                Data=transaction_json,
                PartitionKey=partition_key
            )
            
            shard_id = response.get('ShardId')
            sequence_number = response.get('SequenceNumber')
            
            logger.info(
                f"Transaction {transaction.get('transaction_id')} sent to "
                f"Kinesis - Shard: {shard_id}, Sequence: {sequence_number}"
            )
            
            return shard_id
        
        except ClientError as e:
            logger.error(
                f"Failed to send transaction {transaction.get('transaction_id')}: {e}"
            )
            return None
    
    def send_batch_transactions(
        self,
        transactions: list
    ) -> Dict[str, Any]:
        """
        Send multiple transactions to Kinesis stream.
        
        Args:
            transactions: List of transaction dictionaries
        
        Returns:
            Dictionary with success count and failed transaction IDs
        """
        success_count = 0
        failed_transactions = []
        
        for transaction in transactions:
            result = self.send_transaction(transaction)
            if result:
                success_count += 1
            else:
                failed_transactions.append(transaction.get('transaction_id'))
        
        logger.info(
            f"Batch send completed: {success_count} successful, "
            f"{len(failed_transactions)} failed"
        )
        
        return {
            'success_count': success_count,
            'failed_count': len(failed_transactions),
            'failed_transaction_ids': failed_transactions
        }


def get_producer(
    stream_name: str = None,
    region_name: str = None
) -> TransactionProducer:
    """Factory function to get a TransactionProducer instance."""
    return TransactionProducer(stream_name, region_name)
