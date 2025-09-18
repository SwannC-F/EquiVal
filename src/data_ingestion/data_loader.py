# Script principal pour importer et préparer les données
import pandas as pd
import yfinance as yf
from pathlib import Path

# Dossier data
DATA_DIR = Path(__file__).resolve().parents[2] / "data/raw"

def load_csv(file_path: str) -> pd.DataFrame:
    """Charge un fichier CSV et retourne un DataFrame pandas."""

def fetch_yfinance_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Télécharge des données financières via yfinance pour une entreprise donnée."""

def clean_financial_data(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie les données : suppression valeurs nulles, formatage dates, conversion devises."""


def get_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Récupère les données historiques d'une action via Yahoo Finance.

    :param ticker: Symbole boursier (ex: 'AAPL', 'MSFT')
    :param period: Période d'historique (ex: '1y', '6mo')
    :return: DataFrame avec les données financières
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)

    # Vérification basique
    if df.empty:
        raise ValueError(f"Aucune donnée trouvée pour {ticker}")

    return df


def save_data(df: pd.DataFrame, filename: str) -> None:
    """
    Sauvegarde les données dans le dossier /data en CSV.

    :param df: DataFrame à sauvegarder
    :param filename: Nom du fichier CSV
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_DIR / filename
    df.reset_index().to_csv(filepath, index=False)
    print(f"Données sauvegardées dans {filepath}")
    print(df.shape)

def get_financial_report(ticker: str, report_type: str = "annual") -> dict:
    """
    Récupère les états financiers via yfinance pour une entreprise donnée.

    :param ticker: Symbole boursier (ex: 'GOOGL')
    :param report_type: 'annual' ou 'quarterly'
    :return: dictionnaire avec 'income', 'balance', 'cashflow'
    """
    stock = yf.Ticker(ticker)

    if report_type == "annual":
        income = stock.financials
        balance = stock.balance_sheet
        cashflow = stock.cashflow
    elif report_type == "quarterly":
        income = stock.quarterly_financials
        balance = stock.quarterly_balance_sheet
        cashflow = stock.quarterly_cashflow
    else:
        raise ValueError("report_type doit être 'annual' ou 'quarterly'")

    return {"income": income, "balance": balance, "cashflow": cashflow}

if __name__ == "__main__":
    # Demande à l'utilisateur quel ticker récupérer
    ticker = input("Entrez le symbole boursier à télécharger (ex: AAPL, MSFT, GOOGL) : ").upper().strip()

    # Télécharge et sauvegarde les données
    data = get_stock_data(ticker)

    # Affiche les 5 premières lignes
    print(data.head())

    save_data(data, f"{ticker}_data.csv")
