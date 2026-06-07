"""
config.py
Central configuration for the Azure cloud pipeline.
Loads credentials from .env file — never hardcoded.
"""

import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Azure settings
CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME    = os.getenv("AZURE_CONTAINER_NAME")
STORAGE_ACCOUNT   = os.getenv("AZURE_STORAGE_ACCOUNT")

# Local folder paths
RAW_DATA_PATH       = "data/raw/"
PROCESSED_DATA_PATH = "data/processed/"
RESULTS_PATH        = "results/"

# Files we expect the ETL to produce
PROCESSED_FILES = [
    "wait_times_features.csv",
    "master_fsa_sociodem.csv",
    "q3_location_scores.csv"
]

# Quick check — confirm credentials loaded correctly
if __name__ == "__main__":
    if CONNECTION_STRING:
        print("✓ Azure connection string loaded")
    else:
        print("✗ Azure connection string missing — check your .env file")

    print(f"✓ Container: {CONTAINER_NAME}")
    print(f"✓ Storage account: {STORAGE_ACCOUNT}")