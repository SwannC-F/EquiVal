from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

# Importer tes fonctions depuis ton projet
from src.data_ingestion.data_loader import get_stock_data, save_data
from src.data_preparation.data_cleaning import clean_stock_data, PROCESSED_DIR

def test_load_and_clean(ticker: str = "GOOGL"):
    """
    Charge les données via yfinance, les sauvegarde, les nettoie et affiche un graphique simple.
    Si ticker n'est pas fourni, demande à l'utilisateur.
    """
    if ticker is None:
        ticker = input("Entrez le symbole boursier à télécharger et nettoyer (ex: AAPL, MSFT) : ").upper().strip()

    # 1️⃣ Télécharger les données brutes
    df_raw = get_stock_data(ticker)
    filename = f"{ticker}_data.csv"
    save_data(df_raw, filename)

    # 2️⃣ Nettoyer les données
    clean_stock_data(filename)

    # 3️⃣ Vérifier rapidement avec un graphique
    processed_file = PROCESSED_DIR / filename
    df_processed = pd.read_csv(processed_file, index_col=0, parse_dates=True)

    # Graphique simple : prix de clôture
    df_processed['Close'].plot(title=f"Prix de clôture {ticker} - Cleaned Data")
    plt.xlabel("Date")
    plt.ylabel("Close Price")
    plt.show()


if __name__ == "__main__":
    test_load_and_clean()  # Si aucun ticker n'est fourni, demande à l'utilisateur
