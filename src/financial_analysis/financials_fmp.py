from yahooquery import Ticker
import pandas as pd
import numpy as np
import numpy_financial as npf


def lbo_from_ticker_complete(ticker: str, purchase_price: float,
                             equity_ratio=0.3, debt_repayment_rate=0.2,
                             interest_rate=0.08, revenue_growth=0.05, years=5,
                             exit_multiples=[8, 9, 10]):
    """
    Orchestrateur complet LBO :
    - Récupère les financials pour un ticker
    - Calcule les marges et ratios
    - Projette le FCF opérationnel
    - Transforme en FCF actionnaire
    - Simule différents scénarios de LBO
    Retourne un dictionnaire avec :
        'fcf_operating': DataFrame du FCF opérationnel projeté
        'equity_fcf': DataFrame du FCF actionnaire avec dette et remboursements
        'scenarios': DataFrame des scénarios de sortie (MOIC, IRR, equity final)
    """
    # 1. Récupérer les états financiers
    df_financials = get_financials(ticker)

    # 2. Calculer les marges et ratios nécessaires
    df_financials = calculate_profitability_ratios(df_financials)

    # 3. Projeter le FCF opérationnel
    df_operating_fcf = project_operating_fcf(df_financials, years=years, revenue_growth=revenue_growth)

    # 4. Définir la structure du LBO
    lbo_structure = define_lbo_structure(purchase_price, equity_ratio)

    # 5. Calculer le FCF disponible pour les actionnaires
    df_equity_fcf = calculate_equity_fcf(df_operating_fcf, initial_debt=lbo_structure["debt"],
                                         interest_rate=interest_rate, repayment_rate=debt_repayment_rate)

    # 6. Simuler différents scénarios de sortie
    df_scenarios = lbo_scenario_analysis(df_equity_fcf, purchase_price, equity_contribution=equity_ratio,
                                         debt_repayment_rate=debt_repayment_rate, exit_multiples=exit_multiples)

    # 7. Retourner tous les DataFrames utiles
    return {
        "fcf_operating": df_operating_fcf,
        "equity_fcf": df_equity_fcf,
        "scenarios": df_scenarios
    }


def to_dataframe(data):
    """
    Convertit les données en DataFrame.
    """
    if isinstance(data, dict):
        key = list(data.keys())[0]
        return pd.DataFrame(data[key])
    return pd.DataFrame(data)

def get_financials(ticker: str) -> pd.DataFrame:
    """
    Récupère les états financiers annuels d'une entreprise via Yahooquery.
    Combine income statement et balance sheet.
    """
    t = Ticker(ticker)
    # Income statement
    income = t.income_statement(frequency='annual')
    balance = t.balance_sheet(frequency='annual')
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
    second_last_row = df.sort_values("date", ascending=False).iloc[1]
    projections = []
    revenue = last_row["totalrevenue"]
    ebitda_margin = last_row["ebitda_margin"]
    ebit_margin = last_row["ebit_margin"]
    revenue_prev = second_last_row["totalrevenue"]
    for i in range(1, years + 1):
        revenue = revenue * (1 + revenue_growth)
        ebitda = revenue * ebitda_margin
        ebit = revenue * ebit_margin
        if "capex" in df.columns:
            capex = df["capex"].iloc[0]  # utiliser historique réel si dispo
        else:
            capex = revenue * 0.05  # ESTIMATION
        tax_rate = 0.21  # 21% par défaut (ESTIMATION - USA)
        nopat = ebit * (1 - tax_rate)  # Net Operating Profit After Taxes
        # ESTIMATION : variation du BFR = 10% du changement de revenue
        working_capital_change = 0.1 * (revenue - revenue_prev)
        fcf = nopat - capex - working_capital_change
        projections.append({
            "year": pd.Timestamp(last_row["date"]).year + i,
            "revenue": revenue,
            "ebitda": ebitda,
            "ebit": ebit,
            "capex": capex,
            "fcf": fcf
        })
    return pd.DataFrame(projections)

def project_operating_fcf(df: pd.DataFrame, years: int = 5, revenue_growth: float = 0.05) -> pd.DataFrame:
    """
    Projette le FCF opérationnel pour les prochaines années.
    FCF opérationnel = NOPAT - CapEx - Variation du BFR
    """
    last_row = df.sort_values("date", ascending=False).iloc[0]
    second_last_row = df.sort_values("date", ascending=False).iloc[1]
    projections = []
    revenue = last_row["totalrevenue"]
    ebitda_margin = last_row["ebitda_margin"]
    ebit_margin = last_row["ebit_margin"]
    revenue_prev = second_last_row["totalrevenue"]
    for i in range(1, years + 1):
        revenue = revenue * (1 + revenue_growth)
        ebitda = revenue * ebitda_margin
        ebit = revenue * ebit_margin
        # --- CapEx ---
        capex = revenue * 0.05  # ESTIMATION si pas de données historiques
        # --- Impôts ---
        tax_rate = 0.21  # ESTIMATION USA
        nopat = ebit * (1 - tax_rate)
        # --- Variation BFR ---
        working_capital_change = 0.1 * (revenue - revenue_prev)  # ESTIMATION
        fcf_operating = nopat - capex - working_capital_change
        projections.append({
            "year": pd.Timestamp(last_row["date"]).year + i,
            "revenue": revenue,
            "ebitda": ebitda,
            "ebit": ebit,
            "capex": capex,
            "nopat": nopat,
            "working_capital_change": working_capital_change,
            "fcf_operating": fcf_operating
        })
        revenue_prev = revenue
    return pd.DataFrame(projections)

def calculate_equity_fcf(df_operating_fcf, initial_debt, interest_rate=0.08, repayment_rate=0.2):
    """
    Transforme le FCF opérationnel en FCF actionnaire.
    """
    df = df_operating_fcf.copy()
    debt = initial_debt
    equity_cashflows = []
    debt_balances = []
    for i, row in df.iterrows():
        interest = debt * interest_rate
        fcf_after_interest = row["fcf_operating"] - interest
        repayment = min(debt, fcf_after_interest * repayment_rate)
        debt -= repayment
        equity_cf = max(fcf_after_interest - repayment, 0)
        debt_balances.append(debt)
        equity_cashflows.append(equity_cf)
    df["debt_balance"] = debt_balances
    df["fcf_equity"] = equity_cashflows
    return df

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

def define_lbo_structure(purchase_price, equity_ratio=0.3):
    """
    Détermine la structure initiale du financement du LBO.
    """
    equity = purchase_price * equity_ratio
    debt = purchase_price - equity
    return {
        "purchase_price": purchase_price,
        "equity": equity,
        "debt": debt
    }

def simulate_lbo_cashflows(df_lbo_ready, initial_debt, interest_rate=0.08, repayment_rate=0.2):
    """
    Simule l'évolution de la dette et du FCF disponible pour les actionnaires.
    """
    df = df_lbo_ready.copy()
    debt = initial_debt
    debt_balances = []
    equity_cashflows = []
    for i, row in df.iterrows():
        interest = debt * interest_rate
        fcf_after_interest = row["fcf"] - interest
        repayment = min(debt, fcf_after_interest * repayment_rate)
        debt -= repayment
        equity_cashflow = max(fcf_after_interest - repayment, 0)
        debt_balances.append(debt)
        equity_cashflows.append(equity_cashflow)
    df["debt_balance"] = debt_balances
    df["equity_cashflow"] = equity_cashflows
    return df

def calculate_lbo_return(df_simulation, initial_equity, exit_multiple=10.0):
    """
    Calcule le multiple et l'IRR du LBO en incluant la valeur de sortie basée sur un multiple d'EBITDA.
    Args:
        df_simulation (pd.DataFrame): DataFrame contenant la simulation LBO avec au minimum
                                      'year', 'ebitda', et 'debt_balance'.
        initial_equity (float): Montant de l'équity initial investi.
        exit_multiple (float): Multiple EV/EBITDA à la sortie (par défaut 10x).
    Returns:
        dict: Contient le 'multiple' et l''irr'.
    """
    # 1. EBITDA final
    final_ebitda = df_simulation["ebitda"].iloc[-1]
    # 2. Valeur de sortie de l'entreprise
    exit_value = final_ebitda * exit_multiple
    # 3. Dette finale
    final_debt = df_simulation["debt_balance"].iloc[-1]
    # 4. Equity final à la sortie
    final_equity = exit_value - final_debt
    # 5. Flux de trésorerie pour l'IRR
    cashflows = [-initial_equity] + [0] * (len(df_simulation) - 1) + [final_equity]
    # 6. Calcul de l'IRR et du Multiple
    irr = npf.irr(cashflows)
    multiple = final_equity / initial_equity
    return {
        "multiple": multiple,
        "irr": irr,
        "exit_value": exit_value,
        "final_equity": final_equity,
        "final_debt": final_debt
    }

def lbo_scenario_analysis(df_fcf, purchase_price, equity_contribution=0.30, debt_repayment_rate=0.20,
                          exit_multiples=[8, 9, 10]):
    """
    Simule plusieurs scénarios de LBO avec différents multiples de sortie.
    """
    results = []
    # Calcul des montants de départ
    equity_initial = purchase_price * equity_contribution
    debt_initial = purchase_price - equity_initial
    # On simule une fois la structure de remboursement de la dette
    df_sim = df_fcf.copy()
    debt_balance = debt_initial
    debt_balances = []
    for _, row in df_sim.iterrows():
        repayment = debt_balance * debt_repayment_rate
        debt_balance = max(debt_balance - repayment, 0)
        debt_balances.append(debt_balance)
    df_sim["debt_balance"] = debt_balances
    # Pour chaque multiple de sortie, on calcule la valeur finale
    for multiple_exit in exit_multiples:
        ebitda_final = df_sim["ebitda"].iloc[-1]
        exit_value = ebitda_final * multiple_exit
        final_debt = df_sim["debt_balance"].iloc[-1]
        # Calcul de l'Equity final
        equity_final = exit_value - final_debt
        # MOIC (Multiple On Invested Capital)
        moic = equity_final / equity_initial
        # IRR
        cashflows = [-equity_initial] + [0] * (len(df_sim) - 1) + [equity_final]
        irr = npf.irr(cashflows)
        results.append({
            "Exit Multiple": multiple_exit,
            "Equity Final (B$)": round(equity_final, 2),
            "MOIC": round(moic, 2),
            "IRR": round(irr * 100, 2)
        })
    return pd.DataFrame(results)


def lbo_simulation_scenarios(df_operating_fcf, purchase_price, equity_ratio=0.3,
                             debt_repayment_rate=0.2, interest_rate=0.08, exit_multiples=[8, 9, 10]):
    """
    Simule plusieurs scénarios de LBO et retourne un DataFrame prêt pour export.

    Args:
        df_operating_fcf: DataFrame avec au moins 'year' et 'fcf_operating'.
        purchase_price: Prix d'achat de l'entreprise.
        equity_ratio: Pourcentage d'equity initial (le reste = dette).
        debt_repayment_rate: Pourcentage du FCF utilisé pour rembourser la dette chaque année.
        interest_rate: Taux d'intérêt sur la dette.
        exit_multiples: Liste de multiples EV/EBITDA pour la sortie.

    Returns:
        pd.DataFrame: Scénarios avec FCF actionnaire, MOIC et IRR.
    """
    # 1. Définir structure LBO
    equity_initial = purchase_price * equity_ratio
    debt_initial = purchase_price - equity_initial

    # 2. Préparer DataFrame
    df = df_operating_fcf.copy()
    df["debt_balance"] = debt_initial
    df["fcf_equity"] = 0.0

    debt = debt_initial
    # 3. Calculer FCF actionnaire année par année
    for i, row in df.iterrows():
        interest = debt * interest_rate
        fcf_after_interest = row["fcf_operating"] - interest
        repayment = min(debt, fcf_after_interest * debt_repayment_rate)
        debt -= repayment
        equity_cf = max(fcf_after_interest - repayment, 0)
        df.at[i, "debt_balance"] = debt
        df.at[i, "fcf_equity"] = equity_cf

    # 4. Scénarios selon multiples de sortie
    results = []
    final_ebitda = df["ebitda"].iloc[-1] if "ebitda" in df.columns else df["fcf_operating"].iloc[-1]

    for multiple in exit_multiples:
        exit_value = final_ebitda * multiple
        final_debt = df["debt_balance"].iloc[-1]
        final_equity = exit_value - final_debt
        cashflows = [-equity_initial] + [0] * (len(df) - 1) + [final_equity]
        irr = npf.irr(cashflows)
        moic = final_equity / equity_initial
        results.append({
            "Exit Multiple": multiple,
            "Equity Final": round(final_equity, 2),
            "MOIC": round(moic, 2),
            "IRR (%)": round(irr * 100, 2)
        })

    df_results = pd.DataFrame(results)
    return df, df_results


def lbo_to_excel(ticker: str, purchase_price: float,
                 equity_ratio=0.3, debt_repayment_rate=0.2, interest_rate=0.08,
                 revenue_growth=0.05, years=5, exit_multiples=[8, 9, 10]):
    """
    Génère les projections LBO pour un ticker et exporte les résultats dans un Excel.

    Onglets Excel :
      - 'FCF_Operating' : Free Cash Flow opérationnel projeté
      - 'Equity_FCF'     : FCF actionnaire avec dette et remboursements
      - 'Scenarios'      : Scénarios de sortie LBO (MOIC, IRR, equity final)
    """
    # Générer tous les DataFrames via la fonction orchestratrice
    result = lbo_from_ticker_complete(
        ticker, purchase_price,
        equity_ratio=equity_ratio,
        debt_repayment_rate=debt_repayment_rate,
        interest_rate=interest_rate,
        revenue_growth=revenue_growth,
        years=years,
        exit_multiples=exit_multiples
    )
    filename = f"lbo_analysis_{ticker}.xlsx"

    # Exporter en Excel avec plusieurs onglets
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        result["fcf_operating"].to_excel(writer, sheet_name="FCF_Operating", index=False)
        result["equity_fcf"].to_excel(writer, sheet_name="Equity_FCF", index=False)
        result["scenarios"].to_excel(writer, sheet_name="Scenarios", index=False)

    print(f"Analyse LBO exportée avec succès dans : {filename}")
    return filename


