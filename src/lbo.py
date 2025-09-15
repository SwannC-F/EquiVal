# Simulation d’un LBO
def lbo_simulation(initial_ebitda: float, ebitda_growth: float, debt_ratio: float, entry_multiple: float, exit_multiple: float, years: int = 5) -> dict:
    """
    Simule un LBO sur 5 ans et calcule l'IRR pour l'investisseur.
    Retourne :
    - structure de financement
    - cash flows disponibles
    - IRR
    - Multiple of Money (MoM)
    """
