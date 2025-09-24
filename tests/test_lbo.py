import pandas as pd
from src.valuation.lbo import lbo_model,run_lbo_scenarios
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

def test_run_lbo_scenarios():
    """
    Test du générateur multi-scénarios LBO.
    Vérifie que la fonction retourne un DataFrame valide et que les résultats sont cohérents.
    """
    ticker  = "SW"
    # 1. Générer projection DCF simplifiée
    dcf_res = pipeline_value_report(
        ticker,
        years=5,
        revenue_growth=0.06,
        output_excel=None  # pas besoin d'export Excel
    )
    df_proj = dcf_res["df_proj"]  # récupère le DataFrame avec colonnes ['year', 'fcf']

    # 2. Valeur d'acquisition basée sur la somme des FCF projetés
    purchase_price = df_proj["fcf"].sum()

    # 3. Paramètres pour les scénarios
    equity_ratios = [0.3, 0.4]      # 30% et 40% d'equity
    interest_rates = [0.05, 0.06]   # 5% et 6% taux d'intérêt
    exit_multiples = [8.0, 10.0]    # multiples de sortie

    # 4. Appel de la fonction multi-scénarios
    df_results = run_lbo_scenarios(
        df_proj=df_proj,
        purchase_price=purchase_price,
        equity_ratios=equity_ratios,
        interest_rates=interest_rates,
        exit_ev_multiples=exit_multiples
    )

    # 5. Vérifications
    print(df_results)

    # Vérifie que le DataFrame n'est pas vide
    assert not df_results.empty, "Le DataFrame des résultats ne doit pas être vide"

    # Vérifie la présence des colonnes attendues
    expected_cols = [
        "Equity_Ratio", "Interest_Rate", "Exit_EV_Multiple",
        "Final_Equity", "MOIC", "IRR", "Final_Debt", "Exit_EV"
    ]
    for col in expected_cols:
        assert col in df_results.columns, f"La colonne {col} est manquante dans le résultat"

    # Vérifie que tous les scénarios ont bien été générés
    expected_rows = len(equity_ratios) * len(interest_rates) * len(exit_multiples)
    assert len(df_results) == expected_rows, (
        f"Le nombre de lignes attendues est {expected_rows}, "
        f"mais obtenu {len(df_results)}"
    )

    # Vérifie que les résultats financiers sont cohérents
    assert (df_results["Final_Equity"] > 0).all(), "Toutes les valeurs Final_Equity doivent être positives"
    assert (df_results["MOIC"] > 0).all(), "Toutes les valeurs MOIC doivent être positives"
    assert df_results["IRR"].notnull().all(), "Toutes les valeurs IRR doivent être calculées"
    df_results.to_excel(f"{ticker}_lbo_scenarios.xlsx", index=False)