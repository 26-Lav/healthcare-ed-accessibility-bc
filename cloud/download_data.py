"""
download_data.py
Downloads processed CSV files from Azure Blob Storage
back to your local machine.

Run: python cloud/download_data.py
"""

import os
import sys
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME    = os.getenv("AZURE_CONTAINER_NAME")
DOWNLOAD_PATH     = "data/processed/"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Files to download
FILES = [
    "processed/wait_times_features.csv",
    "processed/master_fsa_sociodem.csv",
    "processed/q3_location_scores.csv"
]


def download_files():
    print("=" * 50)
    print("DOWNLOADING FILES FROM AZURE BLOB STORAGE")
    print(f"Container: {CONTAINER_NAME}")
    print("=" * 50)

    client    = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container = client.get_container_client(CONTAINER_NAME)

    downloaded = 0
    failed     = 0

    for blob_path in FILES:
        filename   = blob_path.split("/")[-1]
        local_path = DOWNLOAD_PATH + filename

        try:
            print(f"  Downloading {filename}...", end=" ")

            blob_client = container.get_blob_client(blob_path)
            with open(local_path, "wb") as f:
                data = blob_client.download_blob()
                f.write(data.readall())

            size_mb = os.path.getsize(local_path) / (1024 * 1024)
            print(f"✓ done ({size_mb:.2f} MB)")
            downloaded += 1

        except Exception as e:
            print(f"✗ failed — {e}")
            failed += 1

    print()
    print("=" * 50)
    print(f"DOWNLOAD COMPLETE — {downloaded} downloaded, {failed} failed")
    print(f"Files saved to: {DOWNLOAD_PATH}")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = download_files()
    sys.exit(0 if success else 1)