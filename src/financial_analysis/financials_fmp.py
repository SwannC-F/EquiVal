from yahooquery import Ticker
import pandas as pd
import numpy as np


def debug_yahooquery_structure(ticker: str):
    t = Ticker(ticker)
    income = t.income_statement(frequency='annual')
    print("=== Structure income_statement ===")
    print(income)
    return income
def clean_column_names(df):
    """
    Nettoie les noms de colonnes :
    - minuscules
    - remplace les espaces par des underscores
    - supprime les caractères spéciaux
    """
    df.columns = (
        df.columns.str.strip()            # Supprimer espaces début/fin
                  .str.lower()            # Mettre en minuscules
                  .str.replace(' ', '_')  # Espaces -> underscores
                  .str.replace('[^a-z0-9_]', '', regex=True)  # Supprimer caractères spéciaux
    )
    return df


def get_financials(ticker: str) -> pd.DataFrame:
    """
    Récupère les états financiers annuels d'une entreprise via Yahooquery.
    Combine income statement et balance sheet.
    """

    t = Ticker(ticker)

    # Income statement
    income = t.income_statement(frequency='annual')
    balance = t.balance_sheet(frequency='annual')

    def to_dataframe(data):
        if isinstance(data, dict):
            key = list(data.keys())[0]
            return pd.DataFrame(data[key])
        return pd.DataFrame(data)

    df_income = to_dataframe(income)
    df_balance = to_dataframe(balance)

    # Merge sur la date
    df = pd.merge(df_income, df_balance, on="asOfDate", how="outer", suffixes=('', '_balance'))
    # Supprime lignes entièrement vides
    df = df.dropna(how='all')



    # Trier par date décroissante
    df.sort_values('asOfDate', ascending=False, inplace=True)

    # Supprimer les lignes entièrement vides
    df.dropna(how="all", inplace=True)

    # Mettre toutes les colonnes en minuscules pour éviter les erreurs de noms
    df.columns = [col.lower() for col in df.columns]

    rename_map = {
        'asofdate': 'date'}
    df.rename(columns=rename_map, inplace=True)
    #print("Colonnes disponibles :", df.columns.tolist())

    return df


def calculate_profitability_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les ratios de profitabilité à partir du DataFrame financier.

    Ratios calculés :
      - EBITDA Margin
      - EBIT Margin
      - Net Income Margin
      - ROE (Return on Equity)
      - ROA (Return on Assets)
      - ROIC (Return on Invested Capital)
    """
    # Supprimer les lignes entièrement vides
    df.dropna(how="all", inplace=True)

    # Colonnes minimales pour les marges
    required_cols = ["totalrevenue", "ebitda", "ebit", "netincome"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes pour les ratios de base : {missing_cols}")

    # Marges
    df["ebitda_margin"] = df["ebitda"] / df["totalrevenue"]
    df["ebit_margin"] = df["ebit"] / df["totalrevenue"]
    df["net_income_margin"] = df["netincome"] / df["totalrevenue"]

    # ROE
    if "stockholdersequity" in df.columns:
        df["roe"] = df["netincome"] / df["stockholdersequity"]

    # ROA
    if "totalassets" in df.columns:
        df["roa"] = df["netincome"] / df["totalassets"]

    # ROIC
    if "operatingincome" in df.columns and "taxrateforcalcs" in df.columns and "investedcapital" in df.columns:
        df["nopat"] = df["operatingincome"] * (1 - df["taxrateforcalcs"])
        df["roic"] = df["nopat"] / df["investedcapital"]

    return df


def calculate_leverage_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les principaux ratios de structure financière.
    Ratios calculés :
      - Debt to Equity
      - Debt to EBITDA
      - Interest Coverage
      - Current Ratio
      - Quick Ratio
    """
    required_cols = [
        "totaldebt", "stockholdersequity", "ebitda", "ebit",
        "interestexpense", "currentassets", "inventory", "currentliabilities"
    ]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"La colonne {col} est manquante pour calculer les ratios de levier.")

    df["debt_to_equity"] = df["totaldebt"] / df["stockholdersequity"]
    df["debt_to_ebitda"] = df["totaldebt"] / df["ebitda"]

    # Interest Coverage
    df["interest_coverage_ratio"] = df.apply(
        lambda row: row["ebit"] / abs(row["interestexpense"]) if row["interestexpense"] != 0 else pd.NA,
        axis=1
    )

    # Ratios de liquidité
    df["current_ratio"] = df["currentassets"] / df["currentliabilities"]
    df["quick_ratio"] = (df["currentassets"] - df["inventory"]) / df["currentliabilities"]

    # Nettoyer infinis ou NaN
    df.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
    df.dropna(how="all", inplace=True)

    return df

def project_financials(df: pd.DataFrame, years: int = 5, revenue_growth: float = 0.05) -> pd.DataFrame:
    """
    Projette les principales lignes financières pour les prochaines années.

    Args:
        df: DataFrame historique avec au moins 'date', 'totalrevenue', 'ebitda_margin', 'ebit_margin'.
        years: nombre d'années de projection.
        revenue_growth: taux de croissance annuel moyen du chiffre d'affaires.

    Returns:
        DataFrame avec les projections.
    """



    # On prend la dernière année connue
    last_row = df.sort_values("date", ascending=False).iloc[0]

    projections = []
    revenue = last_row["totalrevenue"]
    ebitda_margin = last_row["ebitda_margin"]
    ebit_margin = last_row["ebit_margin"]

    for i in range(1, years + 1):
        revenue = revenue * (1 + revenue_growth)
        ebitda = revenue * ebitda_margin
        ebit = revenue * ebit_margin

        # CapEx = 5% du revenue par défaut
        capex = revenue * 0.05

        # Free Cash Flow simplifié = EBITDA - CapEx (ignorer impôts et BFR pour l'instant)
        fcf = ebitda - capex

        projections.append({
            "year": pd.Timestamp(last_row["date"]).year + i,
            "revenue": revenue,
            "ebitda": ebitda,
            "ebit": ebit,
            "capex": capex,
            "fcf": fcf
        })

    return pd.DataFrame(projections)

def calculate_lbo_ready_fcf(df_proj, df_leverage):
    """
    Prépare un DataFrame de Free Cash Flow simplifié pour être utilisé dans un LBO.
    """
    df = df_proj.copy()

    # Vérifier ou créer la colonne working_capital_change
    if "change_in_wc" in df.columns:
        df.rename(columns={"change_in_wc": "working_capital_change"}, inplace=True)
    else:
        # Si elle n'existe pas, on crée une colonne avec 0
        df["working_capital_change"] = 0.0

    # Placeholder pour les taxes (actuellement 0%, à ajuster plus tard)
    df["taxes"] = df["ebitda"] * 0.0

    # Renommer le FCF final si nécessaire
    if "fcf_leveraged" in df.columns:
        df.rename(columns={"fcf_leveraged": "fcf"}, inplace=True)

    # --- FIX pour la clé de merge ---
    if "date" in df_leverage.columns:
        # Crée une colonne 'year' à partir de la date
        df_leverage["year"] = df_leverage["date"].dt.year

        # Merge en utilisant la colonne 'year' des deux DataFrames
        df = df.merge(
            df_leverage[["year", "debt_to_ebitda", "interest_coverage_ratio"]],
            on="year",
            how="left"
        )

    # Sélectionner uniquement les colonnes nécessaires pour le test
    return df[["year", "ebitda", "capex", "taxes", "working_capital_change", "fcf"]]
