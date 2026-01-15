"""AWS Kinesis Consumer for PolicyGuard transaction processing.

This module consumes transaction messages from Kinesis stream and processes them
through the compliance analysis pipeline (RAG bridge, rule engine, compliance agent).
Results are persisted to Aurora RDS with audit trail.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class TransactionConsumer:
    """Consumes and processes transactions from AWS Kinesis stream."""
    
    def __init__(
        self,
        stream_name: str = "policyguard-transaction-stream",
        region_name: str = "ap-south-1",
        initial_position: str = "LATEST"
    ):
        """
        Initialize Kinesis consumer.
        
        Args:
            stream_name: Name of Kinesis stream
            region_name: AWS region (default: ap-south-1)
            initial_position: Position to start reading (LATEST, TRIM_HORIZON, AT_TIMESTAMP)
        """
        self.stream_name = stream_name
        self.region_name = region_name
        self.initial_position = initial_position
        self.processed_records = 0
        self.failed_records = 0
        
        try:
            self.kinesis_client = boto3.client(
                'kinesis',
                region_name=region_name
            )
            logger.info(f"Kinesis consumer initialized for stream: {stream_name}")
        except ClientError as e:
            logger.error(f"Failed to initialize Kinesis client: {e}")
            raise
    
    def get_shard_iterator(self, shard_id: str) -> str:
        """
        Get shard iterator for reading records.
        
        Args:
            shard_id: Kinesis shard ID
        
        Returns:
            Shard iterator string
        """
        try:
            response = self.kinesis_client.get_shard_iterator(
                StreamName=self.stream_name,
                ShardId=shard_id,
                ShardIteratorType=self.initial_position
            )
            return response['ShardIterator']
        except ClientError as e:
            logger.error(f"Failed to get shard iterator: {e}")
            return None
    
    def get_shards(self) -> List[str]:
        """
        Get list of shards from stream.
        
        Returns:
            List of shard IDs
        """
        try:
            response = self.kinesis_client.describe_stream(
                StreamName=self.stream_name
            )
            shards = [shard['ShardId'] for shard in response['StreamDescription']['Shards']]
            logger.info(f"Found {len(shards)} shards: {shards}")
            return shards
        except ClientError as e:
            logger.error(f"Failed to get shards: {e}")
            return []
    
    def process_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single Kinesis record through compliance pipeline.
        
        This is where the transaction gets analyzed:
        1. Deserialize transaction data
        2. Validate schema
        3. Retrieve relevant policies from OpenSearch (RAG bridge)
        4. Run rule engine checks
        5. Call compliance agent (Amazon Nova analysis)
        6. Aggregate results
        7. Store in Aurora RDS
        
        Args:
            record: Kinesis record with Data and SequenceNumber
        
        Returns:
            Processing result dictionary
        """
        try:
            # Deserialize Kinesis data
            transaction_data = json.loads(record['Data'].decode('utf-8'))
            transaction_id = transaction_data.get('transaction_id')
            
            logger.info(f"Processing transaction: {transaction_id}")
            
            # TODO: Implement schema validation
            # TODO: Call RAG bridge to retrieve relevant policies
            # TODO: Call rule engine for deterministic checks
            # TODO: Call compliance agent for LLM analysis
            # TODO: Aggregate results from all agents
            # TODO: Store in Aurora RDS
            
            result = {
                'transaction_id': transaction_id,
                'status': 'processed',
                'timestamp': datetime.utcnow().isoformat(),
                'sequence_number': record['SequenceNumber']
            }
            
            self.processed_records += 1
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize record: {e}")
            self.failed_records += 1
            return None
        except Exception as e:
            logger.error(f"Error processing record: {e}")
            self.failed_records += 1
            return None
    
    def consume_from_shard(
        self,
        shard_id: str,
        max_records: int = 100,
        process_callback=None
    ) -> Dict[str, Any]:
        """
        Consume records from a specific shard.
        
        Args:
            shard_id: Shard ID to consume from
            max_records: Maximum records to fetch per iteration
            process_callback: Optional async callback to process records
        
        Returns:
            Statistics dict with record counts
        """
        shard_iterator = self.get_shard_iterator(shard_id)
        if not shard_iterator:
            return {'error': 'Could not get shard iterator'}
        
        stats = {'records': 0, 'processed': 0, 'failed': 0}
        
        while shard_iterator:
            try:
                response = self.kinesis_client.get_records(
                    ShardIterator=shard_iterator,
                    Limit=max_records
                )
                
                records = response.get('Records', [])
                stats['records'] += len(records)
                
                # Process each record
                for record in records:
                    result = self.process_record(record)
                    if result:
                        stats['processed'] += 1
                        if process_callback:
                            # Allow async processing if callback provided
                            try:
                                if asyncio.iscoroutine(process_callback(result)):
                                    asyncio.run(process_callback(result))
                                else:
                                    process_callback(result)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                    else:
                        stats['failed'] += 1
                
                # Continue with next iterator
                shard_iterator = response.get('NextShardIterator')
                
                # Avoid rapid polling
                if shard_iterator:
                    import time
                    time.sleep(0.5)
            
            except ClientError as e:
                logger.error(f"Error getting records from shard {shard_id}: {e}")
                break
        
        logger.info(
            f"Shard {shard_id} consumption complete: "
            f"{stats['processed']} processed, {stats['failed']} failed"
        )
        return stats
    
    def start_consuming(
        self,
        process_callback=None,
        poll_interval: int = 5
    ):
        """
        Start continuous consumption from all shards.
        
        Args:
            process_callback: Async callback for processing results
            poll_interval: Seconds between polling attempts
        """
        logger.info(f"Starting continuous consumption from {self.stream_name}")
        
        shards = self.get_shards()
        if not shards:
            logger.error("No shards found in stream")
            return
        
        try:
            while True:
                for shard_id in shards:
                    self.consume_from_shard(
                        shard_id,
                        process_callback=process_callback
                    )
                
                logger.info(
                    f"Poll cycle complete. "
                    f"Total: {self.processed_records} processed, "
                    f"{self.failed_records} failed"
                )
                asyncio.run(asyncio.sleep(poll_interval))
        
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}")


def get_consumer(
    stream_name: str = "policyguard-transaction-stream",
    region_name: str = "ap-south-1"
) -> TransactionConsumer:
    """Factory function to get a TransactionConsumer instance."""
    return TransactionConsumer(stream_name, region_name)
