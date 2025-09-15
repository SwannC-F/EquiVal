# EquiVal – Plateforme d’évaluation d’entreprises

## Présentation du projet
**EquiVal** est ma plateforme complète d’évaluation d’entreprises. L’idée est d’automatiser les calculs financiers essentiels et de simuler des opérations de M&A ou de LBO. Mon objectif est de créer un outil pratique qui me permette à la fois de **maîtriser la finance d’entreprise** et de démontrer mes compétences techniques pour des postes en Transaction Services (TS) ou Private Equity (PE).

Avec ce projet, je souhaite reproduire les étapes clés d’une **due diligence financière et d’une valorisation d’entreprise**, en combinant Python, Streamlit et Power BI pour avoir un outil interactif et visuel.

---

## Fonctionnalités principales

1. **Import et nettoyage automatique des données**  
   - Récupération des états financiers depuis CSV, Excel ou API (ex : `yfinance`)  
   - Nettoyage et préparation des données pour l’analyse  

2. **Calcul de l’EBITDA et ratios financiers**  
   - EBITDA et EBITDA margin  
   - Croissance de l’EBITDA  
   - Ratios clés : ROIC, Debt/EBITDA, Interest Coverage, Current Ratio, Quick Ratio  

3. **Analyse de flux de trésorerie (Cash Flow)**  
   - Free Cash Flow (FCF) calculé automatiquement  
   - Prévisions sur 3-5 ans pour la valorisation DCF  

4. **Valorisation DCF (Discounted Cash Flow)**  
   - Actualisation des flux futurs avec WACC  
   - Analyse de sensibilité : je peux tester différentes hypothèses  
   - Graphiques interactifs pour visualiser la valeur estimée  

5. **Valorisation par multiples**  
   - EV/EBITDA, P/E, EV/Sales  
   - Comparaison automatique avec les entreprises similaires  
   - Fourchettes de valorisation claires  

6. **Simulation LBO (Leveraged Buyout)**  
   - Plan de financement avec dette senior, mezzanine et fonds propres  
   - Calcul automatique de l’IRR pour l’investisseur  
   - Scénarios base / optimiste / pessimiste  
   - Simulation du multiple de sortie  

7. **Analyse de scénarios et sensibilité**  
   - Je teste automatiquement différentes hypothèses de croissance, marges et WACC  
   - Graphiques dynamiques pour visualiser l’impact sur la valeur ou IRR  

8. **Rapport automatique**  
   - Génération de tableaux financiers, ratios et graphiques  
   - Rapports PDF ou Excel prêts à présenter ou à utiliser en stage  

---

## Objectif pédagogique
- Apprendre et comprendre en profondeur les concepts de **finance d’entreprise et valorisation**  
- Développer mes compétences techniques en **Python, visualisation de données et automatisation**  
- Construire un projet concret pour mon **portfolio GitHub**, directement valorisable en entretien M&A ou PE  

---

## Stack technique
- **Langage** : Python 3.12  
- **Librairies** : `pandas`, `numpy`, `yfinance`, `requests`, `matplotlib`, `plotly`, `openpyxl`, `xlsxwriter`, `streamlit`  
- **Interface / visualisation** : Streamlit, éventuellement Power BI pour dashboards avancés  
- **Gestion de projet** : Git + GitHub, README détaillé, suivi hebdomadaire  

---

## Estimation de fin de tâches

| Tâche | Description | État | Date estimée de fin |
|-------|------------|------|------------------|
| Conception | Choix des sources de données, KPIs et maquette du dashboard | À faire | 31/10/2025 |
| Data & Backend | Import et nettoyage des données, calcul des ratios financiers | À faire | 15/11/2025 |
| Modèles financiers | Implémentation DCF et valorisation par multiples | À faire | 15/12/2025 |
| Reporting | Génération de rapports PDF/Excel | À faire | 22/12/2025 |
| Front-end / Dashboard | Intégration Streamlit / Power BI et finalisation | À faire | 15/01/2026 |
| Tests & Optimisation | Tests unitaires, reformatage code, corrections bugs | À faire | 22/01/2026 |
| Présentation / GitHub | README final, dépôt complet, mini pitch | À faire | 31/01/2026 |

---

## Progression hebdomadaire

### Semaine 1 (15/09/25 – 22/09/25)
- Objectifs de la semaine :Organiser l'architecture du repo   
- Tâches réalisées :  
- Difficultés rencontrées :  
- Points à améliorer / idées pour la semaine suivante :  

### Semaine 2 (date – date)
- Objectifs de la semaine :  
- Tâches réalisées :  
- Difficultés rencontrées :  
- Points à améliorer / idées pour la semaine suivante :  


---

## Installation et environnement

```bash
# Cloner le repo
git clone https://github.com/SwannC-F/EquiVal
cd equival

# Créer le virtualenv
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer le dashboard Streamlit
streamlit run src/app.py
