import boto3
import os
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def get_opensearch_client():
    """
    Creates and returns an OpenSearch client with AWS SigV4 authentication.
    Handles both environment variables and default configuration.
    """
    # 1. Get Config from Environment Variables
    host = os.getenv("OPENSEARCH_HOST", "yeexgrjjc1uaaa0l1g43.ap-south-1.aoss.amazonaws.com")
    region = os.getenv("AWS_REGION", "ap-south-1")
    service = "aoss"  # "aoss" for Serverless, "es" for Provisioned
    
    # 2. Setup AWS Authentication (SigV4)
    try:
        # Try to get credentials from boto3 session
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            raise ValueError(
                "AWS credentials not found. Please configure credentials using:\n"
                "  1. aws configure\n"
                "  2. Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables\n"
                "  3. Or use IAM role if running on EC2/Lambda"
            )
        
        auth = AWSV4SignerAuth(credentials, region, service)
        
    except Exception as e:
        raise RuntimeError(f"Failed to setup AWS authentication: {str(e)}")
    
    # 3. Create the Client
    try:
        client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_maxsize=20,
            timeout=30
        )
        
        # Test the connection
        info = client.info()
        print(f"Successfully connected to OpenSearch at {host}")
        print(f"   OpenSearch Version: {info['version']['number']}")
        
        return client
        
    except Exception as e:
        raise RuntimeError(
            f"Failed to create OpenSearch client or connect to {host}: {str(e)}\n"
            f"Make sure:\n"
            f"  1. The OpenSearch domain is accessible at {host}\n"
            f"  2. Your IAM user/role has permissions for the 'policyguardvectorsearch' index\n"
            f"  3. The data access policy includes your IAM principal"
        )
