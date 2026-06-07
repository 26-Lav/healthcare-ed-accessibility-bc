"""
azure_function.py

Azure Function — Event-driven ETL trigger.
This function automatically runs the ETL pipeline
when a new CSV file is uploaded to Azure Blob Storage.

In production this would be deployed to Azure Functions.
Trigger type: BlobTrigger
Trigger path: healthcare-ed-data/raw/{filename}
"""

import logging
import os
import sys

# Azure Functions SDK
import azure.functions as func

# Import our ETL pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.pipelines.validate import run_all_checks
from src.pipelines.etl import run as run_etl
from cloud.upload_data import upload_files


# ── FUNCTION APP ──────────────────────────────────────────────────

app = func.FunctionApp()


@app.blob_trigger(
    arg_name="blob",
    path="healthcare-ed-data/raw/{filename}",
    connection="AZURE_CONNECTION_STRING"
)
def etl_trigger(blob: func.InputStream):
    """
    Triggered automatically when a new file lands in
    the raw/ folder of our Azure Blob Storage container.

    Flow:
    1. Log the incoming file details
    2. Run data validation checks
    3. If validation passes, run the ETL pipeline
    4. Upload processed files back to Azure
    5. Log success or failure
    """

    logging.info("=" * 50)
    logging.info("AZURE FUNCTION TRIGGERED")
    logging.info(f"  New file detected: {blob.name}")
    logging.info(f"  File size: {blob.length} bytes")
    logging.info("=" * 50)

    # Step 1 — Validate the incoming data
    logging.info("Step 1: Running data validation...")
    validation_passed = run_all_checks()

    if not validation_passed:
        logging.error("Validation failed — ETL pipeline aborted.")
        logging.error("Fix the data issues and re-upload the file.")
        return

    logging.info("Validation passed.")

    # Step 2 — Run the ETL pipeline
    logging.info("Step 2: Running ETL pipeline...")
    try:
        run_etl()
        logging.info("ETL pipeline completed successfully.")
    except Exception as e:
        logging.error(f"ETL pipeline failed: {e}")
        return

    # Step 3 — Upload processed files to Azure
    logging.info("Step 3: Uploading processed files to Azure...")
    try:
        upload_files()
        logging.info("Upload completed successfully.")
    except Exception as e:
        logging.error(f"Upload failed: {e}")
        return

    logging.info("=" * 50)
    logging.info("PIPELINE COMPLETE — all steps successful")
    logging.info("=" * 50)


# ── LOCAL TEST ────────────────────────────────────────────────────

def simulate_trigger():
    """
    Simulates what the Azure Function would do when triggered.
    Run this locally to test the full pipeline end to end.

    Run: python cloud/azure_function.py
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(message)s",
        datefmt="%H:%M:%S"
    )

    logging.info("SIMULATING AZURE FUNCTION TRIGGER")
    logging.info("(In production this fires automatically on new file upload)")
    logging.info("")

    # Step 1 — Validate
    logging.info("Step 1: Running data validation...")
    validation_passed = run_all_checks()
    if not validation_passed:
        logging.error("Validation failed — stopping.")
        return

    # Step 2 — ETL
    logging.info("Step 2: Running ETL pipeline...")
    run_etl()

    # Step 3 — Upload
    logging.info("Step 3: Uploading to Azure...")
    upload_files()

    logging.info("SIMULATION COMPLETE — full pipeline ran successfully")


if __name__ == "__main__":
    simulate_trigger()