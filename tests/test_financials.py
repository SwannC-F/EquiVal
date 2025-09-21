from src.financial_analysis.financials_fmp import (
    get_financials,
    calculate_lbo_ready_fcf,
    project_financials,
    calculate_leverage_ratios,
    calculate_profitability_ratios,
    define_lbo_structure,
    simulate_lbo_cashflows,
    calculate_lbo_return,
    lbo_from_ticker_complete,
lbo_to_excel
)


def test_get_financials_and_lbo():
    ticker = "GOOGL"

    # Étape 1 : Récupération des données financières brutes
    df_fin = get_financials(ticker)
    assert not df_fin.empty, "Le DataFrame brut des données financières est vide"

    # Étape 2 : Calcul des ratios
    df_ratios = calculate_profitability_ratios(df_fin)
    df_leverage_ratios = calculate_leverage_ratios(df_fin)

    print("\n--- Ratios de Profitabilité ---")
    print(df_ratios[["date", "totalrevenue", "ebitda_margin", "ebit_margin", "net_income_margin"]].head())

    # Étape 3 : Projection à 5 ans
    df_proj = project_financials(df_ratios, years=5, revenue_growth=0.06)
    print("\n--- Projection Financière ---")
    print(df_proj.head())

    # Étape 4 : Calcul du FCF pour LBO
    df_lbo_ready = calculate_lbo_ready_fcf(df_proj, df_leverage_ratios)
    print("\n--- FCF LBO-ready ---")
    print(df_lbo_ready.head())

    # Étape 5 : Structure du LBO
    purchase_price = 500_000_000_000  # 500B$
    structure = define_lbo_structure(purchase_price, equity_ratio=0.3)
    print("\n--- Structure LBO ---")
    print(structure)

    # Étape 6 : Simulation LBO
    df_simulation = simulate_lbo_cashflows(
        df_lbo_ready,
        initial_debt=structure["debt"],
        interest_rate=0.08,
        repayment_rate=0.2
    )
    print("\n--- Simulation LBO ---")
    print(df_simulation.head())

    # Étape 7 : Calcul final avec multiple EV/EBITDA
    lbo_results = calculate_lbo_return(df_simulation, structure["equity"], exit_multiple=10.0)
    print("\n--- Résultats LBO avec multiple ---")
    print(lbo_results)

    # Vérifications
    assert lbo_results["final_equity"] > 0, "L'équity final doit être positif"
    assert lbo_results["multiple"] > 1, "Le multiple doit être > 1"
    assert 0 < lbo_results["irr"] < 2, "L'IRR doit être raisonnable"

def test_calculate_lbo_return(ticker="GOOGL" , pp =200000000):
    df = lbo_from_ticker_complete(ticker, 200000000)
    print(df)
    lbo_to_excel(ticker,pp)
    return df