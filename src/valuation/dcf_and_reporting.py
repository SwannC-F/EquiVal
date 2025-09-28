from typing import Optional, Tuple, Dict, Any
from yahooquery import Ticker
import pandas as pd
import numpy as np
import numpy_financial as npf
from pathlib import Path

# exporter Excel
def _ensure_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------
# 1) WACC / Cost of Equity
# ---------------------------
def compute_wacc(
    ticker: str,
    equity_value: Optional[float] = None,
    debt_value: Optional[float] = None,
    tax_rate: Optional[float] = None,
    risk_free_rate: Optional[float] = None,
    market_premium: Optional[float] = None,
    beta_override: Optional[float] = None,
    interest_expense: Optional[float] = None,
    target_debt_ratio: Optional[float] = None  # si on veut réendetter le bêta
) -> Dict[str, float]:
    """
    Calcule le WACC avec récupération possible du beta via YahooQuery.
    Gère les hypothèses par défaut et indique ce qui est estimé.
    Retourne un dict avec composantes + assumptions.
    """

    # === Hypothèses par défaut centralisées ===
    assumptions = {}
    if risk_free_rate is None:
        risk_free_rate = 0.035
        assumptions["risk_free_rate"] = "estimé"
    if market_premium is None:
        market_premium = 0.06
        assumptions["market_premium"] = "estimé"
    if tax_rate is None:
        tax_rate = 0.21
        assumptions["tax_rate"] = "estimé"

    # === Beta ===
    beta = None
    try:
        t = Ticker(ticker)
        ks = t.key_stats
        if isinstance(ks, dict):
            k = list(ks.keys())[0]
            beta = ks[k].get("beta")
        elif isinstance(ks, pd.DataFrame) and "beta" in ks.columns:
            beta = ks["beta"].iloc[0]
    except Exception:
        beta = None

    if beta_override is not None:
        beta = beta_override
        assumptions["beta"] = "override"
    if beta is None:
        beta = 1.0
        assumptions["beta"] = "estimé"

    # === Cost of equity (CAPM) ===
    cost_of_equity = risk_free_rate + beta * market_premium

    # === Cost of debt ===
    if interest_expense is not None and debt_value and debt_value > 0:
        cost_of_debt = interest_expense / debt_value
        assumptions["cost_of_debt"] = "calculé sur intérêts/dette"
    else:
        cost_of_debt = 0.05
        assumptions["cost_of_debt"] = "estimé"

    # === Structure du capital ===
    if equity_value is None and debt_value is None:
        equity_weight, debt_weight = 0.4, 0.6
        assumptions["capital_structure"] = "estimée (40/60)"
    else:
        equity_value = 1.0 if equity_value is None else equity_value
        debt_value = 0.0 if debt_value is None else debt_value
        total = max(equity_value + debt_value, 1e-9)
        equity_weight = equity_value / total
        debt_weight = debt_value / total

    if equity_weight < 0 or debt_weight < 0:
        warnings.warn("⚠️ Poids négatif dans la structure du capital, vérifie tes inputs.")

    # === WACC final ===
    wacc = cost_of_equity * equity_weight + cost_of_debt * (1 - tax_rate) * debt_weight

    return {
        "beta": beta,
        "risk_free_rate": risk_free_rate,
        "market_premium": market_premium,
        "cost_of_equity": cost_of_equity,
        "cost_of_debt": cost_of_debt,
        "tax_rate": tax_rate,
        "equity_weight": equity_weight,
        "debt_weight": debt_weight,
        "wacc": wacc,
        "assumptions": assumptions
    }

# ---------------------------
# 2) DCF valuation
# ---------------------------
def dcf_valuation(df_proj: pd.DataFrame,
                  wacc: float,
                  terminal_method: str = "gordon",
                  terminal_growth: float = 0.02,
                  exit_multiple: float = 10.0,
                  last_reported_net_debt: float = 0.0,
                  shares_outstanding: Optional[float] = None) -> Dict[str, Any]:
    """
    df_proj must contain columns: 'year', 'fcf' (free cash flow to firm)
    terminal_method: "gordon" or "exit_multiple"
    Returns dictionary with PV of cashflows, TV, enterprise value, equity value, per share.
    """
    df = df_proj.copy().sort_values("year")
    years = df["year"].tolist()
    fcfs = df["fcf"].values.astype(float)

    # Actualisation année par année (discount factors)
    discounted = []
    for i, f in enumerate(fcfs, start=1):
        dfactor = (1 + wacc) ** i
        discounted.append(f / dfactor)
    pv_cashflows = float(np.nansum(discounted))

    # Terminal value
    final_fcf = float(fcfs[-1])
    if terminal_method == "gordon":
        tv = final_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
    else:  # exit multiple
        # on utilise EBITDA si présent, sinon on approx avec FCF->EBITDA ratio (ESTIMATION)
        if "ebitda" in df.columns:
            final_ebitda = float(df["ebitda"].iloc[-1])
            tv = final_ebitda * exit_multiple
        else:
            # ESTIMATION: suppose ebitda ~= fcf / 0.7
            est_ebitda = final_fcf / 0.7  # ESTIMATION
            tv = est_ebitda * exit_multiple

    # actualiser la TV (au dernier horizon)
    tv_discount = tv / ((1 + wacc) ** len(fcfs))

    enterprise_value = pv_cashflows + tv_discount

    # Ajuster dette nette -> equity value
    equity_value = enterprise_value - last_reported_net_debt

    per_share = None
    if shares_outstanding:
        per_share = equity_value / shares_outstanding

    return {
        "pv_cashflows": pv_cashflows,
        "terminal_value": tv,
        "pv_terminal_value": tv_discount,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "per_share": per_share,
        "wacc_used": wacc,
        "terminal_method": terminal_method
    }

# ---------------------------
# 3) Sensitivity / grille
# ---------------------------
def sensitivity_analysis(df_proj: pd.DataFrame,
                         wacc_range: list,
                         terminal_param_range: list,
                         terminal_type: str = "gordon") -> pd.DataFrame:
    """
    Calcule une matrice sensibilité : index = wacc, columns = terminal_param (growth or multiple)
    terminal_type: 'gordon' (terminal_param_range = growth rates) or 'exit' (terminal_param_range = multiples)
    """
    results = []
    for w in wacc_range:
        row = {"wacc": w}
        for p in terminal_param_range:
            if terminal_type == "gordon":
                res = dcf_valuation(df_proj, w, terminal_method="gordon", terminal_growth=p)
            else:
                res = dcf_valuation(df_proj, w, terminal_method="exit_multiple", exit_multiple=p)
            row_key = f"{p}"
            row[row_key] = res["enterprise_value"]
        results.append(row)
    df = pd.DataFrame(results).set_index("wacc")
    return df

# ---------------------------
# 4) Comparables / multiples (basiques)
# ---------------------------
def get_comparables_multiples(ticker: str, peer_list: Optional[list] = None) -> pd.DataFrame:
    """
    Tente de récupérer des multiples simples pour une liste de peers.
    Si peer_list est None, on essaye d'interroger yahooquery pour obtenir peers (peut ne pas exister).
    Retourne DataFrame avec 'symbol','ev','ebitda','ev_ebitda','price','eps','pe'
    """
    t = Ticker(ticker)
    if peer_list is None:
        # tentative naive d'extraire peers via key_stats -> 'peers' (test selon API)
        try:
            ks = t.key_stats
            if isinstance(ks, dict):
                ks = ks.get(list(ks.keys())[0], {})
            peer_list = ks.get("peers", None)
        except Exception:
            peer_list = None

    if not peer_list:
        # si on n'a pas de peers, on renvoie DataFrame vide
        return pd.DataFrame()

    rows = []
    for peer in peer_list:
        try:
            pt = Ticker(peer)
            # récupérer EV (approximatif) et ebitda
            hist = pt.all_financial_data() if hasattr(pt, "all_financial_data") else None
            # fallback: on récupère market cap et net debt (ESTIMATIONS)
            quote = pt.summary_profile if hasattr(pt, "summary_profile") else pt.quote_type
            # Ici on se contente d'informations de base : prix & pe
            q = pt.price if hasattr(pt, "price") else None
            price = q.get(peer, {}).get("regularMarketPrice") if isinstance(q, dict) else None
            pe = q.get(peer, {}).get("trailingPE") if isinstance(q, dict) else None
            # MARK: we don't have perfect EV; put placeholders marked ESTIMATION
            rows.append({
                "symbol": peer,
                "price": price,
                "pe": pe,
                "ev_ebitda": None  # à calculer si on récupère EV et EBITDA
            })
        except Exception:
            continue
    return pd.DataFrame(rows)

# ---------------------------
# 5) Export / Reporting (Excel)
# ---------------------------
def export_report_excel(output_path: str,
                        df_proj: pd.DataFrame,
                        dcf_res: dict,
                        sensi_df: pd.DataFrame = None,
                        comps_df: pd.DataFrame = None) -> str:
    """
    Exporte un rapport simple en Excel (plusieurs feuilles) pour ensuite importer dans Power BI / générer PDF.
    """
    out = Path(output_path)
    _ensure_dir(out)
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df_proj.to_excel(writer, sheet_name="projections", index=False)
        pd.DataFrame([dcf_res]).to_excel(writer, sheet_name="dcf_summary", index=False)
        if sensi_df is not None:
            sensi_df.to_excel(writer, sheet_name="sensitivity")
        if comps_df is not None and not comps_df.empty:
            comps_df.to_excel(writer, sheet_name="comparables", index=False)
        # Optionnel: ajouter sommaire simple
        workbook = writer.book
        fmt = workbook.add_format({"bold": True})
        summary_sheet = workbook.add_worksheet("summary")
        writer.sheets["summary"] = summary_sheet
        summary_sheet.write(0, 0, "Enterprise Value", fmt)
        print("DCF result before export:", dcf_res)
        summary_sheet.write(0, 1, dcf_res.get("enterprise_value"))
        summary_sheet.write(1, 0, "Equity Value", fmt)
        summary_sheet.write(1, 1, dcf_res.get("equity_value"))
    return str(out)

# ---------------------------
# 6) Pipeline "one-call"
# ---------------------------
def pipeline_value_report(ticker: str,
                          years: int = 5,
                          revenue_growth: float = 0.05,
                          purchase_price: Optional[float] = None,
                          output_excel: Optional[str] = None) -> Dict[str, Any]:
    """
    Pipeline complet :
    - Récupère les données financières,
    - Calcule les ratios, projections, WACC,
    - Réalise un DCF avancé et une analyse de sensibilité,
    - Fait l'analyse par comparables,
    - Exporte éventuellement les résultats dans Excel.
    """
    # Importer localement pour éviter les dépendances circulaires
    from src.financial_analysis.financials_fmp import (
        get_financials,
        calculate_profitability_ratios,
        calculate_leverage_ratios,
        project_financials,
        calculate_lbo_ready_fcf
    )

    # ===========================
    # 1. Récupération des données financières
    # ===========================
    df_fin = get_financials(ticker)
    df_ratios = calculate_profitability_ratios(df_fin)
    df_leverage = calculate_leverage_ratios(df_fin)

    print("=== DF_FIN COLUMNS ===")
    print(df_fin.columns)
    print(df_fin.head(10))

    # Affichage des colonnes utiles pour debug
    debt_columns = [col for col in df_fin.columns if "debt" in col.lower()]
    cash_columns = [col for col in df_fin.columns if "cash" in col.lower()]
    print("Colonnes liées à la dette :", debt_columns)
    print("Colonnes liées au cash :", cash_columns)

    # ===========================
    # 2. Projections financières
    # ===========================
    df_proj = project_financials(df_ratios, years=years, revenue_growth=revenue_growth)
    # Calcul simplifié du Free Cash Flow
    tax_rate = 0.21  # estimation

    # approx dépréciation, quick & dirty
    df_proj["depreciation"] = df_proj["ebitda"] - df_proj["ebit"]

    # variation NWC
    df_proj["delta_nwc"] = df_proj["revenue"].diff() * 0.1
    df_proj["delta_nwc"] = df_proj["delta_nwc"].fillna(0)


    df_proj["nopat"] = df_proj["ebit"] * (1 - tax_rate)
    df_proj["fcf"] = df_proj["nopat"] + df_proj["depreciation"] - df_proj["capex"] - df_proj["delta_nwc"]


    net_debt = calculate_net_debt(df_fin)
    print("Net Debt final:", net_debt)

    # Calcul fiable du Market Cap
    market_cap = calculate_market_cap(ticker, df_fin)
    print("Market Cap final:", market_cap)

    # Vérification des valeurs critiques
    if market_cap is None or market_cap <= 0:
        raise ValueError("❌ Market Cap invalide ou manquant. Impossible de calculer le WACC.")

    if net_debt < 0:
        print("⚠️ Net Debt négative, fixée à 0 pour éviter des poids négatifs.")
        net_debt = 0.0

    # ===========================
    # 4. WACC
    # ===========================
    wacc_info = compute_wacc(ticker, equity_value=market_cap, debt_value=net_debt)
    print("WACC Info:", wacc_info)

    # ===========================
    # 5. DCF avancé
    # ===========================
    shares_outstanding = None
    if "basicaverageshares" in df_fin.columns:
        shares_outstanding = df_fin["basicaverageshares"].iloc[0]
    elif "dilutedaverageshares" in df_fin.columns:
        shares_outstanding = df_fin["dilutedaverageshares"].iloc[0]
    print("=== PROJECTIONS AVANT DCF ===")
    print(df_proj.head(10))
    dcf_res = dcf_valuation(
        df_proj,
        wacc_info["wacc"],
        terminal_method="gordon",
        terminal_growth=0.02,
        last_reported_net_debt=net_debt,
        shares_outstanding=shares_outstanding
    )

    # ===========================
    # 6. Sensitivity Analysis
    # ===========================
    wacc_range = [wacc_info["wacc"] - 0.01, wacc_info["wacc"], wacc_info["wacc"] + 0.01]
    growth_range = [0.01, 0.02, 0.03]
    sensi_df = sensitivity_analysis(df_proj, wacc_range, growth_range, terminal_type="gordon")

    # ===========================
    # 7. Comparables
    # ===========================
    comps_df = get_comparables_multiples(ticker)

    # ===========================
    # 8. Construction du résultat final
    # ===========================
    result = {
        "df_fin": df_fin,
        "df_ratios": df_ratios,
        "df_proj": df_proj,
        "wacc_info": wacc_info,
        "dcf_res": dcf_res,
        "sensitivity": sensi_df,
        "comparables": comps_df
    }

    # ===========================
    # 9. Export Excel
    # ===========================
    if output_excel:
        path = export_report_excel(output_excel, df_proj, dcf_res, sensi_df, comps_df)
        result["export_path"] = path

    return result

def calculate_net_debt(df_fin: pd.DataFrame) -> float:
    """
    Calcule la Net Debt à partir des colonnes disponibles dans df_fin.
    """
    # 1) Si netdebt existe déjà dans df_fin
    if "netdebt" in df_fin.columns:
        value = df_fin["netdebt"].iloc[0]
        if pd.notna(value):
            return float(value)
    res = compute_net_debt(df_fin)
    if pd.notna(res):
        return float(res)
    # 2) Sinon, on la calcule à partir de la dette totale - cash
    # ---- DETTE ----
    debt_candidates = [
        "totaldebt",
        "currentdebtandcapitalleaseobligation",
        "longtermdebtandcapitalleaseobligation",
        "currentdebt",
        "longtermdebt"
    ]
    total_debt = sum(df_fin[col].iloc[0] for col in debt_candidates if col in df_fin.columns and pd.notna(df_fin[col].iloc[0]))

    # ---- CASH ----
    cash_candidates = [
        "cashandcashequivalents",
        "cashcashequivalentsandshortterminvestments",
        "cashequivalents",
        "cashfinancial"
    ]
    total_cash = sum(df_fin[col].iloc[0] for col in cash_candidates if col in df_fin.columns and pd.notna(df_fin[col].iloc[0]))

    return float(total_debt - total_cash)

def compute_net_debt(df_fin):
    # Priorité : totaldebt si disponible, sinon somme current + longterm
    if "totaldebt" in df_fin.columns and pd.notna(df_fin["totaldebt"].iloc[-1]):
        total_debt = df_fin["totaldebt"].iloc[-1]
        print("TOTAL DEBT")
        print(total_debt)
    else:
        print("PAS DE TOTAL DEBT")
        total_debt = 0
        for col in ["currentdebt", "longtermdebt"]:
            if col in df_fin.columns and pd.notna(df_fin[col].iloc[-1]):
                total_debt += df_fin[col].iloc[-1]

    total_cash = 0
    for col in ["cashandcashequivalents", "cashcashequivalentsandshortterminvestments",
                "cashequivalents", "cashfinancial"]:
        if col in df_fin.columns and pd.notna(df_fin[col].iloc[-1]):
            total_cash += df_fin[col].iloc[-1]

    return float(total_debt - total_cash)


def calculate_market_cap(ticker: str, df_fin: pd.DataFrame) -> Optional[float]:
    """
    Essaie de récupérer le market cap via YahooQuery.
    Sinon le recalcule avec prix * basicaverageshares.
    """
    try:
        t = Ticker(ticker)
        ks = t.key_stats
        if isinstance(ks, dict):
            ks = ks.get(list(ks.keys())[0], {})
        market_cap = ks.get("marketcap")
        if market_cap is not None:
            return float(market_cap)
    except Exception:
        pass  # On tente une autre méthode

    # ---- Fallback ----
    # 1) Récupérer le nombre d'actions
    shares = None
    if "basicaverageshares" in df_fin.columns:
        shares = df_fin["basicaverageshares"].iloc[0]
    elif "dilutedaverageshares" in df_fin.columns:
        shares = df_fin["dilutedaverageshares"].iloc[0]

    if shares is None or pd.isna(shares):
        print("⚠️ Impossible de récupérer le nombre d'actions pour recalculer le Market Cap.")
        return None

    # 2) Récupérer le prix actuel via YahooQuery
    try:
        price_info = t.price
        price = price_info.get(ticker, {}).get("regularMarketPrice")
    except Exception:
        price = None

    if price is None or pd.isna(price):
        print("⚠️ Impossible de récupérer le prix actuel.")
        return None

    return float(price * shares)

