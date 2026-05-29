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
    if not dados_trends:
        return ""
        
    df = pd.DataFrame(dados_trends)
    fig = px.line(df, x='period', y='total', 
                  title="Evolução Mensal de Utilização",
                  markers=True)
    
    return fig.to_html(full_html=False)
def grafico_rentabilidade_dispositivos(Utilization, Device):
    df_util = pd.DataFrame([{'dev_id': u.device_id, 'amt': u.amount} for u in Utilization.obj.values()])
    df_dev = pd.DataFrame([{'id': d.id, 'cat': d.category} for d in Device.obj.values()])
  
    df = pd.merge(df_util, df_dev, left_on='dev_id', right_on='id')
    resumo = df.groupby('cat').agg({'amt': 'sum', 'dev_id': 'count'}).reset_index()
    resumo.columns = ['Categoria', 'Custo_Total', 'Frequencia']
    
    fig = px.scatter(resumo, x="Frequencia", y="Custo_Total", size="Custo_Total", 
                     color="Categoria", hover_name="Categoria",
                     title="Análise de Rentabilidade: Uso vs Investimento")
    
    return fig.to_html(full_html=False)

def detetar_alertas_gastos(efficiency_data):
    if not efficiency_data:
        return []
    df = pd.DataFrame(efficiency_data)
    limite = df['total_spend'].mean() * 1.2
    alertas = df[df['total_spend'] > limite]
    return alertas[['name', 'total_spend']].to_dict(orient='records')


