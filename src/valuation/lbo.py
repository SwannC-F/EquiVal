import pandas as pd
import numpy_financial as npf
from typing import Optional, Dict, Any,List
import itertools
import numpy as np


def lbo_model(df_proj: pd.DataFrame,
              purchase_price: float,
              equity_contrib: float,
              debt_contrib: float,
              interest_rate: float = 0.06,
              exit_year: Optional[int] = None,
              exit_ev_multiple: float = 10.0,
              multiple_on: str = "fcf") -> Dict[str, Any]:

    if "fcf" not in df_proj.columns:
        raise ValueError("Le DataFrame doit contenir 'fcf'")
    if multiple_on not in ["fcf", "ebitda"]:
        raise ValueError("multiple_on doit être 'fcf' ou 'ebitda'")

    df = df_proj.copy().sort_values("year").reset_index(drop=True)
    n_years = len(df)
    if exit_year is None:
        exit_year = df["year"].iloc[-1]

    df["debt_begin"] = 0.0
    df["interest"] = 0.0
    df["debt_repayment"] = 0.0
    df["debt_end"] = 0.0
    df["equity_begin"] = 0.0
    df["equity_end"] = 0.0
    df["cash"] = 0.0

    df.at[0, "debt_begin"] = debt_contrib
    df.at[0, "equity_begin"] = equity_contrib

    for i in range(n_years):
        debt_start = df.at[i, "debt_begin"]
        df.at[i, "interest"] = debt_start * interest_rate
        fcf = df.at[i, "fcf"]

        repayment = max(fcf - df.at[i, "interest"], 0.0)
        df.at[i, "debt_repayment"] = min(repayment, debt_start)
        df.at[i, "debt_end"] = debt_start - df.at[i, "debt_repayment"]

        net_to_equity = max(fcf - df.at[i, "interest"] - df.at[i, "debt_repayment"], 0.0)
        df.at[i, "cash"] = net_to_equity
        df.at[i, "equity_end"] = df.at[i, "equity_begin"] + net_to_equity

        if i + 1 < n_years:
            df.at[i+1, "debt_begin"] = df.at[i, "debt_end"]
            df.at[i+1, "equity_begin"] = df.at[i, "equity_end"]

    # Sortie
    idx = df.index[df["year"] == exit_year].tolist()[0]
    exit_value_base = df.at[idx, multiple_on]
    exit_ev = exit_value_base * exit_ev_multiple
    final_debt = df.at[idx, "debt_end"]
    final_equity = exit_ev - final_debt
    df.at[idx, "equity_end"] += final_equity

    cashflows = [-equity_contrib] + df["cash"].tolist()
    cashflows[-1] += final_equity

    moic = final_equity / equity_contrib if equity_contrib else None
    irr = npf.irr(cashflows)

    return {
        "df_lbo": df,
        "exit_ev": exit_ev,
        "final_debt": final_debt,
        "final_equity": final_equity,
        "final_cash": df.at[idx, "cash"],
        "MOIC": moic,
        "IRR": irr
    }


import pandas as pd
import itertools

def run_lbo_scenarios(df_proj, purchase_price, exit_ev_multiples, equity_ratios, interest_rates):
    """
    Génère plusieurs scénarios LBO et ajoute des métriques financières clés :
    - MOIC
    - IRR
    - Debt/EBITDA initial et final
    - Cash final
    """

    scenarios = []

    # EBITDA de la première et de la dernière année pour ratios
    ebitda_initial = df_proj["ebitda"].iloc[0]
    ebitda_final = df_proj["ebitda"].iloc[-1]

    for eq_ratio, rate, exit_ev_multiple in itertools.product(equity_ratios, interest_rates, exit_ev_multiples):

        # Détermination des montants equity et dette
        equity_contrib = purchase_price * eq_ratio
        debt_contrib = purchase_price * (1 - eq_ratio)

        # Appel du modèle LBO (à définir ailleurs dans ton code)
        lbo_res = lbo_model(
            df_proj=df_proj,
            purchase_price=purchase_price,
            equity_contrib=equity_contrib,
            debt_contrib=debt_contrib,
            interest_rate=rate,
            exit_year=df_proj["year"].iloc[-1],
            exit_ev_multiple=exit_ev_multiple
        )

        # Calcul des ratios Debt/EBITDA
        debt_to_ebitda_initial = debt_contrib / ebitda_initial if ebitda_initial > 0 else None
        debt_to_ebitda_final = lbo_res["final_debt"] / ebitda_final if ebitda_final > 0 else None

        # Valeur d’entreprise en sortie
        exit_ebitda = df_proj['ebitda'].iloc[-1]
        exit_ev = exit_ebitda * exit_ev_multiple

        # Ajout d'un scénario enrichi
        scenarios.append({
            "Equity_Ratio": eq_ratio,
            "Interest_Rate": rate,
            "Exit_EV_Multiple": exit_ev_multiple,
            "Exit_EV": exit_ev,
            "Final_Equity": lbo_res["final_equity"],
            "MOIC": lbo_res["MOIC"],
            "IRR": lbo_res["IRR"],
            "Initial_Debt/EBITDA": debt_to_ebitda_initial,
            "Final_Debt/EBITDA": debt_to_ebitda_final,
            "Final_Debt": lbo_res["final_debt"],
            "Final_Cash": lbo_res["final_cash"]  # Ajout du cash final
        })

    return pd.DataFrame(scenarios)