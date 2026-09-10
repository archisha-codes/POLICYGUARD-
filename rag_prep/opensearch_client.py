import os
from opensearchpy import OpenSearch

def _to_bool(v: str | None, default: bool) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")

def get_opensearch_client() -> OpenSearch:
    url = os.getenv("OPENSEARCH_URL")
    user = os.getenv("OPENSEARCH_USERNAME")
    pwd = os.getenv("OPENSEARCH_PASSWORD")
    print (url, user, pwd)

    if not url:
        raise RuntimeError("OPENSEARCH_URL environment variable is missing")

    return OpenSearch(
        hosts=[url],
        http_auth=(user, pwd) if (user and pwd) else None,
        use_ssl=_to_bool(os.getenv("OPENSEARCH_USE_SSL"), True),
        verify_certs=_to_bool(os.getenv("OPENSEARCH_VERIFY_CERTS"), False),
        ssl_show_warn=False,
        timeout=60,
        max_retries=3,
        retry_on_timeout=True,
    )

get_opensearch_client()