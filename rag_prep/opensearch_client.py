from opensearchpy import OpenSearch

def get_opensearch_client():
    return OpenSearch(
        hosts=[{"host": "localhost", "port": 9200}],
        http_auth=("admin", "admin"),  # change in prod
        use_ssl=False,
        verify_certs=False
    )
