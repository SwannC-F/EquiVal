import pandas as pd
import numpy as np
import yfinance as yf
import requests
import matplotlib
import plotly
import streamlit
import openpyxl
import xlsxwriter

def test_imports():
    # Juste vérifier que tout s'importe sans erreur
    assert pd.__version__ is not None
    assert np.__version__ is not None
    assert yf.__version__ is not None
    assert requests.__version__ is not None
    assert matplotlib.__version__ is not None
    assert plotly.__version__ is not None
    assert streamlit.__version__ is not None
    assert openpyxl.__version__ is not None
    assert xlsxwriter.__version__ is not None
