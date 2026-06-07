# Cloud Architecture — Healthcare ED Accessibility BC

## Overview

This project uses a cloud-native data pipeline built on **Microsoft Azure**
to process, validate, store, and serve healthcare data for ML modelling.

## Pipeline Architecture
Raw CSVs (local)
│
▼
┌─────────────────────┐
│   validate.py       │  ← 15 data quality checks
│   Data Validation   │    Stops pipeline if data is bad
└─────────────────────┘
│ passes
▼
┌─────────────────────┐
│     etl.py          │  ← Extract, Transform, Load
│   ETL Pipeline      │    Cleans data, engineers features
│                     │    Builds 3 processed datasets
└─────────────────────┘
│
▼
┌─────────────────────┐
│   upload_data.py    │  ← Pushes processed CSVs to cloud
│   Azure Blob Upload │
└─────────────────────┘
│
▼
┌──────────────────────────────┐
│   Azure Blob Storage         │
│   Account: healthcaredatabc  │
│   Container: healthcare-ed-data
│   Region: West US 2          │
│                              │
│   processed/                 │
│   ├── wait_times_features.csv   (15.2 MB)
│   ├── master_fsa_sociodem.csv   (0.03 MB)
│   └── q3_location_scores.csv   (0.03 MB)
└──────────────────────────────┘
│
▼
┌─────────────────────┐
│  azure_function.py  │  ← Event-driven trigger
│  Azure Function     │    Fires automatically when
│  (BlobTrigger)      │    new raw data is uploaded
└─────────────────────┘
│
▼
┌─────────────────────┐
│  download_data.py   │  ← Pulls processed data
│  Azure Blob         │    back to local machine
│  Download           │    or to any other system
└─────────────────────┘
│
▼
┌─────────────────────┐
│  ML Model           │  ← Notebooks read from
│  notebooks/         │    processed data
│  modeling/          │
└─────────────────────┘

## Azure Services Used

| Service | Purpose | Resource name |
|---|---|---|
| Azure Blob Storage | Stores all processed CSV files | healthcaredatabc |
| Azure Functions | Event-driven ETL trigger | BlobTrigger on new uploads |
| Resource Group | Organises all Azure resources | healthcare-ed-bc-rg |

## Files

| File | Purpose |
|---|---|
| `src/pipelines/validate.py` | Runs 15 data quality checks before ETL |
| `src/pipelines/etl.py` | Full ETL pipeline — extract, transform, load |
| `cloud/config.py` | Centralised Azure configuration |
| `cloud/upload_data.py` | Uploads processed files to Azure Blob Storage |
| `cloud/download_data.py` | Downloads processed files from Azure |
| `cloud/azure_function.py` | Azure Function triggered on new file upload |
| `cloud/architecture.md` | This document |

## How to Run

**Full pipeline (validate → ETL → upload):**
```bash
python src/pipelines/validate.py   # check data quality first
python src/pipelines/etl.py        # run ETL pipeline
python cloud/upload_data.py        # upload to Azure
```

**Download processed data from Azure:**
```bash
python cloud/download_data.py
```

**Simulate the full automated Azure Function:**
```bash
python cloud/azure_function.py
```

## Production Architecture

In a production environment this pipeline would be orchestrated using
**Azure Data Factory** — Microsoft's cloud ETL and pipeline service.
Data Factory would schedule daily pipeline runs, monitor for failures,
send alerts, and provide a visual dashboard of pipeline health.

The BlobTrigger Azure Function would be deployed to Azure Functions
so the pipeline runs automatically whenever new ED wait time data
is dropped into the raw/ folder — no manual steps required.

## Security

- Azure connection string stored in `.env` file (excluded from GitHub)
- `.env` listed in `.gitignore` — credentials never committed to version control
- Blob Storage container set to Private — no public access
- All data transfer encrypted via HTTPS (TLS 1.2)