# Interface Streamlit
import streamlit as st

st.title("EquiVal - Plateforme d'évaluation d'entreprises")
st.write("Bienvenue dans EquiVal")

ticker = st.text_input("Entrez le ticker (ex: AAPL, MSFT, TSLA)")
if ticker:
    st.write(f"Vous avez entré : {ticker}")
