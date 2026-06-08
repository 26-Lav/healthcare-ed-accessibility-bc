import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from io import StringIO

load_dotenv()

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Healthcare ED Accessibility BC",
    page_icon="🏥",
    layout="wide"
)

# ── Load data from Azure ─────────────────────────────────────────
@st.cache_data
def load_from_azure(filename):
    conn_str  = os.getenv('AZURE_CONNECTION_STRING')
    container = os.getenv('AZURE_CONTAINER_NAME')
    client    = BlobServiceClient.from_connection_string(conn_str)
    blob      = client.get_blob_client(container=container,
                                       blob=f'processed/{filename}')
    content   = blob.download_blob().readall().decode('utf-8')
    return pd.read_csv(StringIO(content))

# ── Header ───────────────────────────────────────────────────────
st.title("🏥 Healthcare ED Accessibility BC")
st.markdown("**VanML 2025 Hackathon** — Predicting wait times and finding underserved communities")

st.markdown("---")

# ── Tabs ─────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊 Q1 — Wait Time Predictions",
    "📍 Q2ex — Location Recommendations",
    "ℹ️ About"
])

# ── TAB 1: WAIT TIMES ────────────────────────────────────────────
with tab1:
    st.header("ED/UPCC Wait Time Predictions")
    st.markdown("Our XGBoost model predicts wait times with **MAE = 26 minutes** and **R² = 0.949**")

    try:
        df = load_from_azure('wait_times_features.csv')
        df['time'] = pd.to_datetime(df['time'])

        # Facility selector
        facilities = sorted(df['name'].unique())
        selected = st.multiselect(
            "Select facilities to compare:",
            facilities,
            default=facilities[:3]
        )

        if selected:
            fig = go.Figure()

            for fac in selected:
                fac_df = df[df['name'] == fac].sort_values('time').tail(200)

                fig.add_trace(go.Scatter(
                    x=fac_df['time'],
                    y=fac_df['waitTimeMinutes'],
                    name=f'{fac[:25]}',
                    mode='lines'
                ))

            fig.update_layout(
                title='Wait Time Trends by Facility',
                xaxis_title='Date',
                yaxis_title='Wait Time (minutes)',
                hovermode='x unified',
                template='plotly_white',
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)

        # Key stats
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mean Wait Time",  f"{df['waitTimeMinutes'].mean():.0f} min")
        col2.metric("Best Model",      "XGBoost")
        col3.metric("MAE",             "26.0 min")
        col4.metric("R²",              "0.949")

        # Hour heatmap
        st.subheader("When is it busiest?")
        pivot = df.groupby(['day_of_week', 'hour'])['waitTimeMinutes'].mean().unstack()
        pivot.index = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

        import plotly.express as px
        fig2 = px.imshow(
            pivot,
            color_continuous_scale='RdYlGn_r',
            title='Average wait time by hour and day',
            labels=dict(x='Hour of day', y='Day of week', color='Wait (min)'),
            aspect='auto'
        )
        st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"Could not load data from Azure: {e}")
        st.info("Make sure your .env file has the correct Azure credentials.")

# ── TAB 2: LOCATION ──────────────────────────────────────────────
with tab2:
    st.header("Where Should the Next ED Open?")
    st.markdown("Composite underserved score across **191 BC FSAs** — distance, population, poverty, seniors, physician gap")

    try:
        loc = load_from_azure('q3_location_scores.csv')

        # Top 10 bar chart
        top10 = loc.nlargest(10, 'underserved_score').sort_values('underserved_score')

        fig3 = go.Figure(go.Bar(
            x=top10['underserved_score'],
            y=top10['CFSAUID'] + ' — ' + top10['CSDNAME'].str[:20],
            orientation='h',
            marker_color='crimson'
        ))
        fig3.update_layout(
            title='Top 10 Most Underserved FSAs',
            xaxis_title='Underserved Score',
            template='plotly_white',
            height=400
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Score weight slider
        st.subheader("Adjust the weights — does the recommendation change?")
        col1, col2, col3 = st.columns(3)
        w_dist = col1.slider("Distance weight",  0.0, 1.0, 0.35, 0.05)
        w_pop  = col2.slider("Population weight", 0.0, 1.0, 0.25, 0.05)
        w_poor = col3.slider("Poverty weight",    0.0, 1.0, 0.20, 0.05)

        def norm(s):
            return (s - s.min()) / (s.max() - s.min() + 1e-9)

        loc_s = loc.copy()
        loc_s['custom_score'] = (
            w_dist * loc_s['s_dist'] +
            w_pop  * loc_s['s_pop']  +
            w_poor * loc_s['s_poor']
        )

        st.markdown("**Top 5 with your weights:**")
        top5 = loc_s.nlargest(5, 'custom_score')[
            ['CFSAUID', 'CSDNAME', 'min_distance_km', 'population', 'custom_score']
        ].round(3)
        st.dataframe(top5, use_container_width=True)

    except Exception as e:
        st.error(f"Could not load data from Azure: {e}")

# ── TAB 3: ABOUT ─────────────────────────────────────────────────
with tab3:
    st.header("About This Project")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### The Problem
        - ED patients leaving without care increased **85%** from 2018–2024
        - **6.5 million** Canadians have no regular care provider
        - No new ED has opened in Vancouver since 2010

        ### Research Questions
        - **Q1:** How well can we predict ED wait times?
        - **Q3:** Where should the next ED open?
        """)

    with col2:
        st.markdown("""
        ### Tech Stack
        - **Python 3.11** — pandas, scikit-learn, XGBoost
        - **Microsoft Azure** — Blob Storage, Azure Functions
        - **Streamlit** — interactive web app
        - **Plotly** — interactive charts

        ### Key Results
        - XGBoost MAE = **26.0 minutes**, R² = **0.949**
        - Prince George (V2L): **76,000 people**, **392km** from nearest ED
        - Three-tier recommendation framework
        """)

    st.markdown("---")
    st.markdown("Built by **Lavi Singh** — SFU Computing Science | VanML 2025 Hackathon")