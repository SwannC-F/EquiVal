import pandas as pd
from src.valuation.lbo import lbo_model
from src.valuation.dcf_and_reporting import pipeline_value_report

def test_lbo_with_dcf():
    """
    Test simplifié du LBO model en utilisant la projection FCF issue du pipeline DCF.
    Vérifie que l'appel à lbo_model fonctionne et renvoie des valeurs plausibles.
    """
    # Générer projection DCF simplifiée
    dcf_res = pipeline_value_report(
        "GNRC",
        years=5,
        revenue_growth=0.06,
        output_excel=None  # pas besoin d'export Excel ici
    )
    df_proj = dcf_res["df_proj"]  # récupère le DataFrame avec 'year' et 'fcf'

    # Paramètres LBO simples
    purchase_price = df_proj["fcf"].sum()
    equity_contrib = purchase_price * 0.3
    debt_contrib = purchase_price * 0.7
    interest_rate = 0.06
    exit_year = df_proj["year"].iloc[-1]
    exit_ev_multiple = 10.0

    # Appel LBO
    lbo_res = lbo_model(
        df_proj=df_proj,
        purchase_price=purchase_price,
        equity_contrib=equity_contrib,
        debt_contrib=debt_contrib,
        interest_rate=interest_rate,
        exit_year=exit_year,
        exit_ev_multiple=exit_ev_multiple
    )

    # Vérifications simples
    final_equity = lbo_res["final_equity"]
    moic = lbo_res["MOIC"]
    irr = lbo_res["IRR"]

    print("Final Equity:", final_equity)
    print("MOIC:", moic)
    print("IRR:", irr)

    assert final_equity > 0, "Equity finale doit être positive"
    assert moic > 0, "MOIC doit être positif"
    assert irr is not None, "IRR doit être calculable"
