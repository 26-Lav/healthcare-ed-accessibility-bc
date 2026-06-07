"""
validate.py
Data validation checks before the ETL pipeline runs.
Catches bad data early so nothing broken gets uploaded to Azure.
"""

import pandas as pd
import os
import sys

# Paths
RAW = "data/raw/"

def check(condition, message):
    """Print pass or fail for each check."""
    if condition:
        print(f"  ✓ {message}")
        return True
    else:
        print(f"  ✗ FAILED: {message}")
        return False


def validate_wait_times():
    print("\n--- Validating EDWaitTimes ---")
    passed = []

    df = pd.read_csv(RAW + "EDWaitTimes.csv-train-fixed.csv")
    df['time'] = pd.to_datetime(df['time'])

    passed.append(check(len(df) >= 70000,
        f"Row count OK — got {len(df):,} rows (expected at least 70,000)"))

    passed.append(check(df['waitTimeMinutes'].isnull().sum() == 0,
        "No missing wait times"))

    passed.append(check((df['waitTimeMinutes'] >= 0).all(),
        "All wait times are positive numbers"))

    passed.append(check(df['name'].nunique() >= 20,
        f"Facility count OK — got {df['name'].nunique()} facilities"))

    passed.append(check(df['time'].min().year == 2025,
        f"Date range starts in 2025 — got {df['time'].min().date()}"))

    passed.append(check(df['time'].max().month >= 7,
        f"Data goes to at least July 2025 — got {df['time'].max().date()}"))

    return all(passed)


def validate_census():
    print("\n--- Validating Census Data ---")
    passed = []

    df = pd.read_csv(RAW + "census_filtered.csv")

    passed.append(check(len(df) > 1000,
        f"Row count OK — got {len(df):,} rows"))

    passed.append(check('GEO_NAME' in df.columns,
        "GEO_NAME column present"))

    passed.append(check('C1_COUNT_TOTAL' in df.columns,
        "C1_COUNT_TOTAL column present"))

    passed.append(check(df['C1_COUNT_TOTAL'].isnull().sum() / len(df) < 0.5,
        "Less than 50% missing values in count column"))

    return all(passed)


def validate_physicians():
    print("\n--- Validating Physicians Data ---")
    passed = []

    df = pd.read_csv(RAW + "CPSBC Family Physicians.csv")

    passed.append(check(len(df) > 100,
        f"Row count OK — got {len(df):,} rows"))

    passed.append(check('FSA' in df.columns,
        "FSA column present"))

    passed.append(check('Practitioners' in df.columns,
        "Practitioners column present"))

    passed.append(check(df['Practitioners'].sum() > 5000,
        f"Total practitioners OK — got {df['Practitioners'].sum():,}"))

    return all(passed)


def validate_distances():
    print("\n--- Validating Distance Data ---")
    passed = []

    df = pd.read_csv(RAW + "fsa_nearest_ed.csv")

    passed.append(check(len(df) >= 150,
        f"FSA count OK — got {len(df)} FSAs"))

    passed.append(check('min_distance_km' in df.columns,
        "min_distance_km column present"))

    passed.append(check((df['min_distance_km'] >= 0).all(),
        "All distances are positive"))

    return all(passed)


def run_all_checks():
    print("=" * 50)
    print("RUNNING DATA VALIDATION CHECKS")
    print("=" * 50)

    results = [
        validate_wait_times(),
        validate_census(),
        validate_physicians(),
        validate_distances()
    ]

    print("\n" + "=" * 50)
    if all(results):
        print("ALL CHECKS PASSED — safe to run ETL pipeline")
        return True
    else:
        print("SOME CHECKS FAILED — fix data before proceeding")
        return False


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)