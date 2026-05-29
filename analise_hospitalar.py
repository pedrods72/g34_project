S# Módulo de análise estatística de dados hospitalares - Versão inicial
import pandas as pd
import plotly.express as px
import sqlite3
import os

# 1. Configurar o caminho para a base de dados
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'dados', 'HospitalData.db')

def carregar_dados(tabela):
    """Função para ler qualquer tabela da base de dados usando Pandas"""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
    conn.close()
    return df