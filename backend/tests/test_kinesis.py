"""Comprehensive unit tests for Kinesis integration.

Tests cover producer, consumer, and schema validation modules.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal

from services.kinesis_producer import TransactionProducer, DecimalEncoder
from services.kinesis_consumer import TransactionConsumer
from services.transaction_schema import (
    TransactionRequest,
    ComplianceVerdict,
    validate_transaction,
    validate_multiple_transactions,
    TransactionType,
    TransactionStatus
)


class TestDecimalEncoder:
    """Test JSON Decimal encoding."""
    
    def test_decimal_encoding(self):
        """Test that Decimal values are converted to float."""
        encoder = DecimalEncoder()
        result = encoder.default(Decimal('100.50'))
        assert result == 100.5
        assert isinstance(result, float)
    
    def test_non_decimal_raises_error(self):
        """Test that non-Decimal values raise TypeError."""
        encoder = DecimalEncoder()
        with pytest.raises(TypeError):
            encoder.default(object())


class TestTransactionProducer:
    """Test TransactionProducer functionality."""
    
    @patch('services.kinesis_producer.boto3.client')
    def test_producer_initialization(self, mock_client):
        """Test producer initializes with correct parameters."""
        mock_kinesis = MagicMock()
        mock_client.return_value = mock_kinesis
        
        producer = TransactionProducer(
            stream_name="test-stream",
            region_name="ap-south-1"
        )
        
        assert producer.stream_name == "test-stream"
        assert producer.region_name == "ap-south-1"
        mock_client.assert_called_once_with('kinesis', region_name='ap-south-1')
    
    @patch('services.kinesis_producer.boto3.client')
    def test_send_transaction_success(self, mock_client):
        """Test successful transaction send."""
        mock_kinesis = MagicMock()
        mock_client.return_value = mock_kinesis
        mock_kinesis.put_record.return_value = {
            'ShardId': 'shardId-000000000000',
            'SequenceNumber': '49590338271490256608559692538361571095921575989136588898'
        }
        
        producer = TransactionProducer()
        transaction = {
            'transaction_id': 'TXN001',
            'customer_id': 'CUST001',
            'amount': 10000.00,
            'currency': 'INR',
            'transaction_type': 'transfer',
            'description': 'Test transfer',
            'source_account': 'ACC001',
            'destination_account': 'ACC002'
        }
        
        result = producer.send_transaction(transaction)
        
        assert result == 'shardId-000000000000'
        assert mock_kinesis.put_record.called
    
    @patch('services.kinesis_producer.boto3.client')
    def test_send_transaction_missing_customer_id(self, mock_client):
        """Test transaction send fails without customer_id."""
        mock_kinesis = MagicMock()
        mock_client.return_value = mock_kinesis
        
        producer = TransactionProducer()
        transaction = {
            'transaction_id': 'TXN001',
            'amount': 10000.00
        }
        
        result = producer.send_transaction(transaction)
        
        assert result is None
        assert not mock_kinesis.put_record.called
    
    @patch('services.kinesis_producer.boto3.client')
    def test_batch_transactions(self, mock_client):
        """Test batch transaction sending."""
        mock_kinesis = MagicMock()
        mock_client.return_value = mock_kinesis
        mock_kinesis.put_record.return_value = {'ShardId': 'shard-1'}
        
        producer = TransactionProducer()
        transactions = [
            {
                'transaction_id': f'TXN{i:03d}',
                'customer_id': f'CUST{i:03d}',
                'amount': 5000.00 * i,
                'currency': 'INR',
                'transaction_type': 'transfer',
                'description': f'Batch transfer {i}',
                'source_account': 'ACC001',
                'destination_account': 'ACC002'
            }
            for i in range(1, 6)
        ]
        
        result = producer.send_batch_transactions(transactions)
        
        assert result['success_count'] == 5
        assert result['failed_count'] == 0
        assert len(result['failed_transaction_ids']) == 0


class TestTransactionConsumer:
    """Test TransactionConsumer functionality."""
    
    @patch('services.kinesis_consumer.boto3.client')
    def test_consumer_initialization(self, mock_client):
        """Test consumer initializes correctly."""
        mock_kinesis = MagicMock()
        mock_client.return_value = mock_kinesis
        
        consumer = TransactionConsumer(
            stream_name="test-stream",
            region_name="ap-south-1"
        )
        
        assert consumer.stream_name == "test-stream"
        assert consumer.region_name == "ap-south-1"
        assert consumer.processed_records == 0
        assert consumer.failed_records == 0
    
    @patch('services.kinesis_consumer.boto3.client')
    def test_get_shard_iterator(self, mock_client):
        """Test shard iterator retrieval."""
        mock_kinesis = MagicMock()
        mock_client.return_value = mock_kinesis
        mock_kinesis.get_shard_iterator.return_value = {
            'ShardIterator': 'test-iterator-123'
        }
        
        consumer = TransactionConsumer()
        iterator = consumer.get_shard_iterator('shardId-000000000000')
        
        assert iterator == 'test-iterator-123'
        assert mock_kinesis.get_shard_iterator.called
    
    @patch('services.kinesis_consumer.boto3.client')
    def test_get_shards(self, mock_client):
        """Test shard discovery."""
        mock_kinesis = MagicMock()
        mock_client.return_value = mock_kinesis
        mock_kinesis.describe_stream.return_value = {
            'StreamDescription': {
                'Shards': [
                    {'ShardId': 'shardId-000000000000'},
                    {'ShardId': 'shardId-000000000001'}
                ]
            }
        }
        
        consumer = TransactionConsumer()
        shards = consumer.get_shards()
        
        assert len(shards) == 2
        assert 'shardId-000000000000' in shards


class TestTransactionSchema:
    """Test transaction schema validation."""
    
    def test_valid_transaction(self):
        """Test validation of valid transaction."""
        valid_data = {
            'transaction_id': 'TXN001',
            'customer_id': 'CUST001',
            'amount': 10000.00,
            'currency': 'INR',
            'transaction_type': 'transfer',
            'description': 'Test transfer',
            'source_account': 'ACC001',
            'destination_account': 'ACC002'
        }
        
        is_valid, validated, error = validate_transaction(valid_data)
        
        assert is_valid is True
        assert validated is not None
        assert error is None
        assert validated.transaction_id == 'TXN001'
    
    def test_invalid_transaction_missing_field(self):
        """Test validation fails with missing required field."""
        invalid_data = {
            'transaction_id': 'TXN001',
            'amount': 10000.00
        }
        
        is_valid, validated, error = validate_transaction(invalid_data)
        
        assert is_valid is False
        assert validated is None
        assert error is not None
    
    def test_invalid_amount(self):
        """Test validation fails with invalid amount."""
        invalid_data = {
            'transaction_id': 'TXN001',
            'customer_id': 'CUST001',
            'amount': -1000.00,  # Negative amount
            'currency': 'INR',
            'transaction_type': 'transfer',
            'description': 'Test',
            'source_account': 'ACC001',
            'destination_account': 'ACC002'
        }
        
        is_valid, _, _ = validate_transaction(invalid_data)
        assert is_valid is False
    
    def test_invalid_currency_code(self):
        """Test validation fails with invalid currency code."""
        invalid_data = {
            'transaction_id': 'TXN001',
            'customer_id': 'CUST001',
            'amount': 10000.00,
            'currency': 'INVALID',  # Not ISO 4217 code
            'transaction_type': 'transfer',
            'description': 'Test',
            'source_account': 'ACC001',
            'destination_account': 'ACC002'
        }
        
        is_valid, _, _ = validate_transaction(invalid_data)
        assert is_valid is False
    
    def test_transaction_type_enum(self):
        """Test transaction type enumeration."""
        assert TransactionType.DEPOSIT == 'deposit'
        assert TransactionType.WITHDRAWAL == 'withdrawal'
        assert TransactionType.TRANSFER == 'transfer'
        assert TransactionType.PAYMENT == 'payment'
        assert TransactionType.REFUND == 'refund'
    
    def test_multiple_transactions_validation(self):
        """Test validation of multiple transactions."""
        valid_transactions = [
            {
                'transaction_id': f'TXN{i:03d}',
                'customer_id': f'CUST{i:03d}',
                'amount': 5000.00,
                'currency': 'INR',
                'transaction_type': 'transfer',
                'description': f'Test {i}',
                'source_account': 'ACC001',
                'destination_account': 'ACC002'
            }
            for i in range(1, 4)
        ]
        
        valid, invalid = validate_multiple_transactions(valid_transactions)
        
        assert len(valid) == 3
        assert len(invalid) == 0
    
    def test_compliance_verdict_model(self):
        """Test compliance verdict model."""
        verdict = ComplianceVerdict(
            transaction_id='TXN001',
            verdict='Compliant',
            confidence=0.95,
            risk_score=0.05,
            applicable_policies=['KYC-001', 'AML-001'],
            reasoning='Transaction passes all compliance checks',
            required_actions=[]
        )
        
        assert verdict.transaction_id == 'TXN001'
        assert verdict.verdict == 'Compliant'
        assert verdict.confidence == 0.95


class TestIntegration:
    """Integration tests for Kinesis pipeline."""
    
    @patch('services.kinesis_producer.boto3.client')
    @patch('services.kinesis_consumer.boto3.client')
    def test_producer_consumer_integration(self, mock_consumer_client, mock_producer_client):
        """Test producer and consumer work together."""
        mock_producer_kinesis = MagicMock()
        mock_consumer_kinesis = MagicMock()
        mock_producer_client.return_value = mock_producer_kinesis
        mock_consumer_client.return_value = mock_consumer_kinesis
        
        # Setup mocks
        mock_producer_kinesis.put_record.return_value = {'ShardId': 'shard-1'}
        mock_consumer_kinesis.describe_stream.return_value = {
            'StreamDescription': {
                'Shards': [{'ShardId': 'shardId-000000000000'}]
            }
        }
        
        # Test producer
        producer = TransactionProducer()
        transaction = {
            'transaction_id': 'TXN001',
            'customer_id': 'CUST001',
            'amount': 10000.00,
            'currency': 'INR',
            'transaction_type': 'transfer',
            'description': 'Integration test',
            'source_account': 'ACC001',
            'destination_account': 'ACC002'
        }
        result = producer.send_transaction(transaction)
        assert result == 'shard-1'
        
        # Test consumer
        consumer = TransactionConsumer()
        shards = consumer.get_shards()
        assert len(shards) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
