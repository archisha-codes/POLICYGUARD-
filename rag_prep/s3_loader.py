import boto3
import os

LOCAL_DATA_DIR = "../data/s3"


def download_pdfs_from_s3(bucket_name, prefix=""):
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

    session = boto3.Session(profile_name="default")
    s3 = session.client("s3")

    response = s3.list_objects_v2(
        Bucket=bucket_name,
        Prefix=prefix
    )

    if "Contents" not in response:
        print("⚠️ No PDFs found in S3 bucket")
        return

    for obj in response["Contents"]:
        key = obj["Key"]

        if not key.lower().endswith(".pdf"):
            continue

        local_path = os.path.join(
            LOCAL_DATA_DIR,
            os.path.basename(key)
        )

        print(f"⬇️ Downloading {key} → {local_path}")
        s3.download_file(bucket_name, key, local_path)

    print("✅ S3 PDF download completed")
