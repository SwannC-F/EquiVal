from src.financial_analysis.financials_fmp import get_financials,calculate_lbo_ready_fcf,project_financials,calculate_leverage_ratios, calculate_profitability_ratios,debug_yahooquery_structure

##ticker = "AAPL"
##df_fin = get_financials(ticker)
##df_ratios = calculate_ratios(df_fin)

# Affiche les 5 derniers résultats
##print(df_ratios[["date", "revenue", "ebitda", "operatingIncome", "netIncome", "EBITDA Margin", "EBIT Margin", "Net Income Margin"]].head())
#*



def test_get_financials():
        ticker = "GOOGL"
        df_fin = get_financials(ticker)

        # Calcul des ratios
        df_ratios = calculate_profitability_ratios(df_fin)
        df_leverage_ratios = calculate_leverage_ratios(df_fin)

        # Affichage des premiers résultats
        print(df_ratios[["date", "totalrevenue", "ebitda_margin", "ebit_margin", "net_income_margin"]].head())
        print(df_leverage_ratios[["date", "debt_to_equity", "debt_to_ebitda", "interest_coverage_ratio",
                                  "current_ratio", "quick_ratio"]].head())

        # Vérifier que les DataFrames ne sont pas vides
        assert not df_ratios.empty, "Le DataFrame des ratios de profitabilité est vide"
        assert not df_leverage_ratios.empty, "Le DataFrame des ratios de levier est vide"

        # Test de projection à 5 ans
        df_proj = project_financials(df_ratios, years=5, revenue_growth=0.06)
        print(df_proj.head())
        required_proj_cols = ["year", "revenue", "ebitda", "ebit", "capex", "fcf"]
        assert all(col in df_proj.columns for col in required_proj_cols), \
            f"Colonnes manquantes dans le DataFrame de projection : {required_proj_cols}"

        # Test du calcul du FCF pour LBO
        df_lbo_ready = calculate_lbo_ready_fcf(df_proj,df_leverage_ratios)
        print(df_lbo_ready.head())

        required_lbo_cols = ["year", "ebitda", "capex", "taxes", "working_capital_change", "fcf"]
        assert all(col in df_lbo_ready.columns for col in required_lbo_cols), \
            f"Colonnes manquantes dans le FCF LBO-ready : {required_lbo_cols}"

        assert df_lbo_ready["fcf"].iloc[-1] > 0, "Le dernier FCF doit être positif"

