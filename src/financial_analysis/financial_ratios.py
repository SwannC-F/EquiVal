import pandas as pd


def calculate_ebitda(df: pd.DataFrame) -> pd.Series:
    """
    Calcule l'EBITDA à partir du DataFrame.
    Hypothèse : df doit contenir les colonnes 'Revenue', 'Operating Expenses', 'Depreciation', 'Amortization'.
    """
    if not all(col in df.columns for col in ['Revenue', 'Operating Expenses', 'Depreciation', 'Amortization']):
        raise ValueError("Les colonnes nécessaires pour calculer l'EBITDA sont manquantes.")

    ebitda = df['Revenue'] - df['Operating Expenses'] + df['Depreciation'] + df['Amortization']
    return ebitda


def calculate_ebit(df: pd.DataFrame) -> pd.Series:
    """
    Calcule l'EBIT à partir du DataFrame.
    Hypothèse : df doit contenir 'Revenue', 'Operating Expenses', 'Depreciation', 'Amortization'.
    """
    if not all(col in df.columns for col in ['Revenue', 'Operating Expenses']):
        raise ValueError("Les colonnes nécessaires pour calculer l'EBIT sont manquantes.")

    ebit = df['Revenue'] - df['Operating Expenses']
    return ebit


def calculate_net_income_margin(df: pd.DataFrame) -> pd.Series:
    """
    Calcule le Net Income Margin = Net Income / Revenue
    Hypothèse : df doit contenir 'Net Income' et 'Revenue'.
    """
    if not all(col in df.columns for col in ['Net Income', 'Revenue']):
        raise ValueError("Les colonnes nécessaires pour calculer le Net Income Margin sont manquantes.")

    net_income_margin = df['Net Income'] / df['Revenue']
    return net_income_margin