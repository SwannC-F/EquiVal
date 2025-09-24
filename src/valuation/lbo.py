import pandas as pd
import numpy_financial as npf
from typing import Optional, Dict, Any

def lbo_model(
    df_proj: pd.DataFrame,
    purchase_price: float,
    equity_contrib: float,
    debt_contrib: float,
    interest_rate: float = 0.06,
    exit_year: Optional[int] = None,
    exit_ev_multiple: float = 10.0,
    multiple_on: str = "fcf"  # "fcf" ou "ebitda"
) -> Dict[str, Any]:
    """
    Modèle simplifié de LBO.

    df_proj doit contenir au moins 'year' et 'fcf' (ou 'ebitda' si multiple_on='ebitda').

    Parameters
    ----------
    purchase_price : float
        Enterprise Value à l'acquisition.
    equity_contrib : float
        Montant de l'equity injecté.
    debt_contrib : float
        Montant de la dette levée.
    interest_rate : float
        Taux d'intérêt annuel sur la dette.
    exit_year : int, optional
        Année de sortie (si None -> dernière année de df_proj).
    exit_ev_multiple : float
        Multiple sur EBITDA ou FCF pour sortie.
    multiple_on : str
        "fcf" ou "ebitda" pour le calcul de la valeur de sortie.

    Returns
    -------
    dict
        Dictionnaire contenant le DataFrame LBO, final equity, MOIC, IRR, etc.
    """

    # Vérifications
    if "fcf" not in df_proj.columns:
        raise ValueError("Le DataFrame doit contenir la colonne 'fcf'")
    if multiple_on not in ["fcf", "ebitda"]:
        raise ValueError("multiple_on doit être 'fcf' ou 'ebitda'")

    df = df_proj.copy().sort_values("year").reset_index(drop=True)
    n_years = len(df)

    if exit_year is None:
        exit_year = df["year"].iloc[-1]

    # Colonnes de suivi
    df["debt_begin"] = 0.0
    df["interest"] = 0.0
    df["debt_repayment"] = 0.0
    df["debt_end"] = 0.0
    df["equity_begin"] = 0.0
    df["equity_end"] = 0.0

    # Année 0 : acquisition
    df.at[0, "debt_begin"] = debt_contrib
    df.at[0, "equity_begin"] = equity_contrib

    # Simulation flux annuels
    for i in range(n_years):
        debt_start = df.at[i, "debt_begin"]
        df.at[i, "interest"] = debt_start * interest_rate
        fcf = df.at[i, "fcf"]

        # Flux disponible pour rembourser la dette
        repayment = max(fcf - df.at[i, "interest"], 0.0)
        df.at[i, "debt_repayment"] = min(repayment, debt_start)
        df.at[i, "debt_end"] = debt_start - df.at[i, "debt_repayment"]

        # Equity begin/end
        net_to_equity = max(fcf - df.at[i, "interest"] - df.at[i, "debt_repayment"], 0.0)
        df.at[i, "equity_end"] = df.at[i, "equity_begin"] + net_to_equity
        if i + 1 < n_years:
            df.at[i + 1, "debt_begin"] = df.at[i, "debt_end"]
            df.at[i + 1, "equity_begin"] = df.at[i, "equity_end"]

    # Sortie
    exit_idx = df.index[df["year"] == exit_year].tolist()
    idx = exit_idx[0] if exit_idx else n_years - 1
    exit_value_base = df.at[idx, multiple_on]
    exit_ev = exit_value_base * exit_ev_multiple
    final_debt = df.at[idx, "debt_end"]
    final_equity = exit_ev - final_debt
    df.at[idx, "equity_end"] += final_equity

    # Calcul cashflows pour IRR
    cashflows = [-equity_contrib]
    for i in range(n_years):
        net_to_equity = max(df.at[i, "fcf"] - df.at[i, "interest"] - df.at[i, "debt_repayment"], 0.0)
        cashflows.append(net_to_equity)
    cashflows[-1] += final_equity  # ajoute la sortie finale

    # MOIC & IRR
    moic = final_equity / equity_contrib if equity_contrib else None
    try:
        irr = npf.irr(cashflows)
    except:
        irr = None

    return {
        "df_lbo": df,
        "exit_ev": exit_ev,
        "final_debt": final_debt,
        "final_equity": final_equity,
        "MOIC": moic,
        "IRR": irr
    }
