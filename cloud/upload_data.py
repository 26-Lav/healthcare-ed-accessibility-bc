"""
upload_data.py
Uploads processed CSV files to Azure Blob Storage.
Run after etl.py has generated the processed files.

Run: python cloud/upload_data.py
"""

import os
import sys
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME    = os.getenv("AZURE_CONTAINER_NAME")
PROCESSED_PATH    = "data/processed/"

# Files to upload
FILES = [
    "wait_times_features.csv",
    "master_fsa_sociodem.csv",
    "q3_location_scores.csv"
]


def upload_files():
    print("=" * 50)
    print("UPLOADING FILES TO AZURE BLOB STORAGE")
    print(f"Container: {CONTAINER_NAME}")
    print("=" * 50)

    # Connect to Azure
    client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container = client.get_container_client(CONTAINER_NAME)

    uploaded = 0
    failed   = 0

    for filename in FILES:
        local_path = PROCESSED_PATH + filename
        blob_path  = "processed/" + filename

        if not os.path.exists(local_path):
            print(f"  ✗ SKIP — {filename} not found locally (run etl.py first)")
            failed += 1
            continue

        try:
            # Get file size for display
            size_mb = os.path.getsize(local_path) / (1024 * 1024)

            print(f"  Uploading {filename} ({size_mb:.2f} MB)...", end=" ")

            with open(local_path, "rb") as f:
                container.upload_blob(
                    name=blob_path,
                    data=f,
                    overwrite=True  # overwrite if file already exists
                )

            print("✓ done")
            uploaded += 1

        except Exception as e:
            print(f"✗ failed — {e}")
            failed += 1

    print()
    print("=" * 50)
    print(f"UPLOAD COMPLETE — {uploaded} uploaded, {failed} failed")
    print(f"Files are now in Azure: {CONTAINER_NAME}/processed/")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = upload_files()
    sys.exit(0 if success else 1)