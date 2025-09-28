import streamlit as st
import pandas as pd
import plotly.express as px

import sys
import os

# Chemin racine du projet = dossier parent de "src"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.valuation.dcf_and_reporting import pipeline_value_report

st.set_page_config(page_title="Equity Valuation App", layout="wide")

st.title("📊 Equity Valuation Tool")

# --- Inputs utilisateur ---
ticker = st.text_input("Ticker (ex: AAPL, MSFT, TSLA)", "AAPL")
years = st.slider("Projection horizon (years)", 3, 10, 5)
revenue_growth = st.slider("Revenue growth (%)", 0.0, 0.20, 0.05, step=0.01)

if st.button("Run Valuation"):
    res = pipeline_value_report(ticker, years=years, revenue_growth=revenue_growth)

    # Résumé
    dcf = res["dcf_res"]
    st.subheader("Valuation Summary")
    st.metric("Enterprise Value", f"${dcf['enterprise_value']:,.0f}")
    st.metric("Equity Value", f"${dcf['equity_value']:,.0f}")
    if dcf["per_share"]:
        st.metric("Value per Share", f"${dcf['per_share']:.2f}")

    # Projections chart
    df_proj = res["df_proj"]
    fig = px.line(df_proj, x="year", y="fcf", title="Projected Free Cash Flows")
    st.plotly_chart(fig, use_container_width=True)

    # Sensibilité
    st.subheader("Sensitivity (WACC vs g)")
    sensi = res["sensitivity"]
    st.dataframe(sensi)

    fig_sensi = px.imshow(
        sensi.values,
        x=sensi.columns,
        y=sensi.index,
        color_continuous_scale="RdBu",
        labels=dict(x="Terminal growth", y="WACC", color="EV"),
        title="Sensitivity Heatmap"
    )
    st.plotly_chart(fig_sensi, use_container_width=True)

    # Comparables
    st.subheader("Multiples comparables")
    comps = res["comparables"]
    if not comps.empty:
        st.dataframe(comps)
    else:
        st.info("Pas de comparables disponibles pour ce ticker.")