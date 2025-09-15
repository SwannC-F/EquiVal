# Import et nettoyage des données
import pandas as pd
def load_csv(file_path: str) -> pd.DataFrame:
    """Charge un fichier CSV et retourne un DataFrame pandas."""

def fetch_yfinance_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Télécharge des données financières via yfinance pour une entreprise donnée."""

def clean_financial_data(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie les données : suppression valeurs nulles, formatage dates, conversion devises."""
