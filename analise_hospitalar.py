S# Módulo de análise estatística de dados hospitalares - Versão inicial
import pandas as pd
import plotly.express as px

def criar_grafico_gastos_plotly(dados_gastos):
    if not dados_gastos:
        return "<p>Sem dados para gerar gráfico.</p>"
    df = pd.DataFrame(dados_gastos)
    fig = px.bar(df, x='category', y='cost',
                 title="Custos por Categoria de Dispositivo",
                 labels={'category': 'Categoria', 'cost': 'Custo Total (€)'},
                 color='cost', color_continuous_scale='Blues')
    return fig.to_html(full_html=False)

def criar_grafico_tendencias(dados_trends):
    """Transforma as tendências mensais do app.py num gráfico de linhas."""
    if not dados_trends:
        return ""
        
    df = pd.DataFrame(dados_trends)
    fig = px.line(df, x='period', y='total', 
                  title="Evolução Mensal de Utilização",
                  markers=True)
    
    return fig.to_html(full_html=False)
