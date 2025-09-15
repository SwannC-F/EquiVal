import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

def clean_stock_data(filename: str):
    filepath = RAW_DIR / filename
    df = pd.read_csv(filepath)

    # Vérifier les colonnes
    print(f"Colonnes présentes : {df.columns.tolist()}")

    # Si la colonne 'Date' n'existe pas, on prend l'index
    if 'Date' not in df.columns:
        df.reset_index(inplace=True)

    # Transformer la colonne Date en datetime
    df['Date'] = pd.to_datetime(df['Date'], utc=True)
    df = df.set_index('Date')

    # Supprimer les lignes avec des valeurs nulles
    df = df.dropna()

    # Sauvegarde en processed
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / filename
    df.to_csv(output_path)
    print(f"Données propres sauvegardées dans {output_path}")


if __name__ == "__main__":
    # Demander à l'utilisateur quel fichier nettoyer
    filename = input("Entrez le nom du fichier à nettoyer (ex: AAPL_data.csv) : ").strip()

    # Nettoyer les données
    clean_stock_data(filename)
