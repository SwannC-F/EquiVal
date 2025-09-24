from src.valuation.dcf_and_reporting import pipeline_value_report
def test_dcf_and_report():
    res = pipeline_value_report("AAPL", years=5, revenue_growth=0.06, output_excel="data/outputs/AAPL_valuation.xlsx")
    print(res["dcf_res"])
