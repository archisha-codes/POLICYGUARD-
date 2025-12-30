import boto3
import os
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def get_opensearch_client():
    # 1. Get Config from Environment Variables
    host = os.getenv("OPENSEARCH_HOST", "") 
    region = os.getenv("AWS_REGION", "ap-south-1")
    service = "aoss" # "aoss" for Serverless, "es" for Provisioned. 
    
    # 2. Setup AWS Authentication (SigV4)
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, service)

    # 3. Create the Client
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=20
    )
    
    return client