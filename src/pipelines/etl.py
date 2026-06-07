"""
etl.py
ETL Pipeline — Extract, Transform, Load.
Reads raw CSVs, cleans and transforms them,
writes processed files ready for ML modelling.

Run: python src/pipelines/etl.py
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime

# Set up logging so we can see what the pipeline is doing
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# Paths
RAW       = "data/raw/"
PROCESSED = "data/processed/"
os.makedirs(PROCESSED, exist_ok=True)


# ── EXTRACT ───────────────────────────────────────────────────────

def extract():
    """Load all raw datasets."""
    log.info("EXTRACT — loading raw data files")

    data = {}

    data['wait_times'] = pd.read_csv(RAW + "EDWaitTimes.csv-train-fixed.csv")
    log.info(f"  Loaded wait times: {data['wait_times'].shape}")

    data['census'] = pd.read_csv(RAW + "census_filtered.csv")
    log.info(f"  Loaded census: {data['census'].shape}")

    data['physicians'] = pd.read_csv(RAW + "CPSBC Family Physicians.csv")
    log.info(f"  Loaded physicians: {data['physicians'].shape}")

    data['fsa_csd'] = pd.read_csv(RAW + "fsa_csd_keys.csv")
    log.info(f"  Loaded FSA-CSD keys: {data['fsa_csd'].shape}")

    data['fsa_nearest'] = pd.read_csv(RAW + "fsa_nearest_ed.csv")
    log.info(f"  Loaded nearest ED: {data['fsa_nearest'].shape}")

    data['fsa_gps'] = pd.read_csv(RAW + "Gps_and_nearest_ed_by_FSA.csv")
    log.info(f"  Loaded GPs by FSA: {data['fsa_gps'].shape}")

    return data


# ── TRANSFORM ────────────────────────────────────────────────────

def transform_wait_times(df):
    """Clean and feature-engineer the wait times dataset."""
    log.info("TRANSFORM — processing wait times")

    df = df.copy()
    df['time'] = pd.to_datetime(df['time'])

    # Time features
    df['hour']        = df['time'].dt.hour
    df['day_of_week'] = df['time'].dt.dayofweek
    df['month']       = df['time'].dt.month
    df['is_weekend']  = df['day_of_week'].isin([5, 6]).astype(int)
    df['is_night']    = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
    df['open247_int'] = df['open247'].astype(int)
    df['facility_code'] = df['name'].astype('category').cat.codes

    # Lag features — sort by facility and time first
    df = df.sort_values(['name', 'time']).reset_index(drop=True)
    g = df.groupby('name')['waitTimeMinutes']

    df['lag_1h']   = g.shift(1)
    df['lag_2h']   = g.shift(2)
    df['lag_3h']   = g.shift(3)
    df['lag_24h']  = g.shift(24)
    df['roll_3h']  = g.transform(lambda x: x.shift(1).rolling(3,  min_periods=1).mean())
    df['roll_6h']  = g.transform(lambda x: x.shift(1).rolling(6,  min_periods=1).mean())
    df['roll_24h'] = g.transform(lambda x: x.shift(1).rolling(24, min_periods=1).mean())

    log.info(f"  Wait times transformed: {df.shape}")
    return df


def transform_master_fsa(data):
    """Build the master FSA-level sociodemographic dataset."""
    log.info("TRANSFORM — building master FSA dataset")

    # Census column names
    LOW_INC = 'Prevalence of low income based on the Low-income measure, after tax (LIM-AT) (%)'
    POP     = 'Population, 2021'
    SENIORS = '  65 years and over'
    MED_INC = '  Median total income of household in 2020 ($)'
    DENSITY = 'Population density per square kilometre'

    # Pivot census from long to wide
    census_wide = data['census'].pivot_table(
        index=['GEO_NAME', 'ALT_GEO_CODE'],
        columns='CHARACTERISTIC_NAME',
        values='C1_COUNT_TOTAL',
        aggfunc='first'
    ).reset_index()

    # Physicians per FSA
    phys_fsa = (data['physicians']
                .groupby('FSA')['Practitioners']
                .sum()
                .reset_index())
    phys_fsa.columns = ['FSA', 'total_physicians']

    # Fix join keys
    fsa_csd = data['fsa_csd'][['CFSAUID', 'CSDUID', 'CSDNAME']].copy()
    fsa_csd['CSDUID']           = fsa_csd['CSDUID'].astype(str)
    census_wide['ALT_GEO_CODE'] = census_wide['ALT_GEO_CODE'].astype(str)

    # Join all datasets
    master = (fsa_csd
        .merge(census_wide,    left_on='CSDUID',  right_on='ALT_GEO_CODE', how='left')
        .merge(data['fsa_nearest'], left_on='CFSAUID', right_on='FSA', how='left')
        .merge(phys_fsa,       left_on='CFSAUID', right_on='FSA',          how='left')
        .merge(data['fsa_gps'][['FSA', 'GPs in the FSA (Not hospital)']],
                               left_on='CFSAUID', right_on='FSA',          how='left')
    )

    # Clean column names
    master['population']     = master[POP]
    master['low_income_pct'] = master[LOW_INC]
    master['seniors_count']  = master[SENIORS]
    master['median_income']  = master[MED_INC]
    master['pop_density']    = master[DENSITY]

    # Derived columns
    master['seniors_pct']   = master['seniors_count'] / master['population'].replace(0, np.nan) * 100
    master['phys_per_1000'] = master['total_physicians'] / master['population'].replace(0, np.nan) * 1000
    master['pop_per_phys']  = master['population'] / (master['total_physicians'].fillna(0) + 0.1)
    master['is_rural']      = (master['pop_density'] < 400).map({True: 'Rural', False: 'Urban'})

    log.info(f"  Master FSA dataset built: {master.shape}")
    return master


def transform_location_scores(master):
    """Calculate underserved score for Q3 location analysis."""
    log.info("TRANSFORM — calculating location scores")

    def norm(col):
        return (col - col.min()) / (col.max() - col.min() + 1e-9)

    loc = master.dropna(subset=['min_distance_km', 'population']).copy()
    loc = loc[loc['population'] > 0]

    loc['s_dist']  = norm(loc['min_distance_km'])
    loc['s_pop']   = norm(loc['population'])
    loc['s_poor']  = norm(loc['low_income_pct'].fillna(loc['low_income_pct'].median()))
    loc['s_old']   = norm(loc['seniors_pct'].fillna(0))
    loc['s_phys']  = norm(loc['pop_per_phys'].clip(upper=loc['pop_per_phys'].quantile(0.95)))

    loc['underserved_score'] = (
        0.35 * loc['s_dist']  +
        0.25 * loc['s_pop']   +
        0.20 * loc['s_poor']  +
        0.10 * loc['s_old']   +
        0.10 * loc['s_phys']
    )

    save_cols = ['CFSAUID', 'CSDNAME', 'min_distance_km', 'population',
                 'low_income_pct', 'phys_per_1000', 's_dist', 's_pop',
                 's_poor', 's_old', 's_phys', 'underserved_score']

    result = loc[[c for c in save_cols if c in loc.columns]].sort_values(
        'underserved_score', ascending=False
    )

    log.info(f"  Location scores calculated: {result.shape}")
    return result


# ── LOAD ─────────────────────────────────────────────────────────

def load(wait_times, master, location_scores):
    """Save all processed datasets to data/processed/."""
    log.info("LOAD — saving processed files")

    wait_times.to_csv(PROCESSED + "wait_times_features.csv", index=False)
    log.info(f"  Saved wait_times_features.csv — {wait_times.shape}")

    master_cols = ['CFSAUID', 'CSDNAME', 'population', 'pop_density', 'is_rural',
                   'min_distance_km', 'nearest_ed', 'total_physicians',
                   'phys_per_1000', 'pop_per_phys', 'low_income_pct',
                   'seniors_pct', 'median_income']
    master[[c for c in master_cols if c in master.columns]].to_csv(
        PROCESSED + "master_fsa_sociodem.csv", index=False)
    log.info(f"  Saved master_fsa_sociodem.csv")

    location_scores.to_csv(PROCESSED + "q3_location_scores.csv", index=False)
    log.info(f"  Saved q3_location_scores.csv — {location_scores.shape}")


# ── RUN PIPELINE ─────────────────────────────────────────────────

def run():
    start = datetime.now()
    log.info("=" * 50)
    log.info("STARTING ETL PIPELINE")
    log.info("=" * 50)

    # Extract
    data = extract()

    # Transform
    wait_times      = transform_wait_times(data['wait_times'])
    master          = transform_master_fsa(data)
    location_scores = transform_location_scores(master)

    # Load
    load(wait_times, master, location_scores)

    elapsed = (datetime.now() - start).seconds
    log.info("=" * 50)
    log.info(f"ETL PIPELINE COMPLETE — {elapsed}s")
    log.info("=" * 50)


if __name__ == "__main__":
    run()