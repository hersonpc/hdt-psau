# Planilha Editavel Google Sheets: <https://docs.google.com/spreadsheets/d/1ulLsJgPzUlE5LGXyx2r_uAQMeJhToK9acA6SaumntVA/edit?resourcekey#gid=25369857>
# Formulario: <https://docs.google.com/forms/d/e/1FAIpQLSf5aE3ymUu7xF64N18XI0Iv-MNtxj3Avw909N5wvs-XVZzJTw/viewform>

import os
import re
import time
import requests
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
# from unidecode import unidecode
from rich.console import Console
from io import StringIO, BytesIO
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

local_data_filename = 'data/data.parquet'
local_nps_filename = 'data/nps.parquet'

# verifica se a pasta "data" existe, se não existir, cria
if not os.path.exists('data'):
    os.makedirs('data')

url_formulario = 'https://docs.google.com/forms/d/e/1FAIpQLSf5aE3ymUu7xF64N18XI0Iv-MNtxj3Avw909N5wvs-XVZzJTw/viewform'
hospital_nome = "Hospital Estadual de Doenças Tropicais"
console = Console()

st.set_page_config(
    page_title="HDT PSAU v2",
    page_icon=':hospital:',
    layout="wide",
    # layout="centered",
    initial_sidebar_state="auto",
    menu_items=None)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden; }
    footer {visibility: hidden; }
    header {visibility: hidden; }
    </style>""", unsafe_allow_html=True)

def download_data():
    url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQnAgS3VcuLGyS6sLSCVo8d-_fT2E-X4L1rEYm6iRF8uYxkqfiIPaAgRtriSySK-lbH07fBysH92x9d/pub?gid=25369857&single=true&output=csv'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Accept-Charset': 'utf-8'
    }
    console.log(f"Obtendo dados de {url}")
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        df = pd.read_csv(BytesIO(response.content), sep=',')
        
        # renomear colunas
        df.columns = ["data", "local", "nps", "tipo", "elogio", "sugestao", "reclamacao", "nome", "telefone", "email"]

        # converter data para o tipo datetime
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y %H:%M:%S')
        
        # criar coluna de ano, mes e "ano/mes"
        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        df['ano_mes'] = df['data'].dt.strftime('%Y/%m')
        
        # ordenar por data
        df.sort_values(by=['data'], inplace=True, ascending=False)
        
        # armazenar em cache
        df.to_parquet(local_data_filename, index=False)
        return df
    
    raise Exception('Falha ao obter dados. Entre em contato com a equipe de TI.')

# @st.cache_data(ttl=60)
def get_data():
    
    if os.path.exists(local_data_filename):
        idade_arquivo = time.time() - os.path.getmtime(local_data_filename)
        # remover arquivo se tiver mais de 5 minutos
        console.log(f"{local_data_filename} criado há {round(idade_arquivo, 2)} min, criado em: {datetime.fromtimestamp(os.path.getmtime(local_data_filename)).strftime('%d/%m/%Y %H:%M')}")
        if (idade_arquivo > 1 * 60 * 60):
            os.remove(local_data_filename)

    if os.path.exists(local_data_filename):
        df = pd.read_parquet(local_data_filename)
    else:
        df = download_data()
    
    return df

st.title('Dashboard - PSAU')
st.subheader('Pesquisa de Satisfação dos Usuários')
st.markdown(f'<h5 style="color: #6880c7;">{hospital_nome}</h5>', unsafe_allow_html=True)
# st.markdown(f'<h2 style="color: firebrick;text-align:center;border-bottom: 4px solid firebrick;margin-bottom: 1rem;padding: .5rem;">{sel_setor.upper()}<>


df = get_data()
periodos = df['ano_mes'].unique()
locais = df['local'].unique()

df_nps = pd.DataFrame(columns=[
        'ano_mes', 'nps', 'promotores', 'percentual_promotores', 
        'neutros', 'percentual_neutros', 'detratores', 'percentual_detratores'
    ])
if not os.path.exists(local_nps_filename):
    print('- Calculando o NPS')
    # para cada periodo, calcular o nps
    for periodo in periodos:
        df_periodo = df.query("ano_mes == @periodo", engine="python")
        df_promotores = df_periodo.query("nps >= 9", engine="python")
        df_neutros = df_periodo.query("nps >= 7 and nps <= 8", engine="python")
        df_detratores = df_periodo.query("nps <= 6", engine="python")
        percentual_promotores = len(df_promotores) / len(df_periodo)
        percentual_neutros = len(df_neutros) / len(df_periodo)
        percentual_detratores = len(df_detratores) / len(df_periodo)
        score_nps = percentual_promotores - percentual_detratores
        nps_dict = {
            'ano_mes': periodo,
            'nps': score_nps,
            'promotores': len(df_promotores),
            'percentual_promotores': f'{round(percentual_promotores * 100, 2)}%',
            'neutros': len(df_neutros),
            'percentual_neutros': f'{round(percentual_neutros * 100, 2)}%',
            'detratores': len(df_detratores),
            'percentual_detratores': f'{round(percentual_detratores * 100, 2)}%'
        }
        df_nps = pd.concat([df_nps, pd.DataFrame([nps_dict])], ignore_index=True)
    # armazenar em cache
    print('- Armazenando o NPS em cache')
    df_nps.to_parquet(local_nps_filename, index=False)

# st.write(df)
# st.write(df.columns)
with st.sidebar.title("Filtros"):
    input_periodo = st.sidebar.selectbox("Qual período você deseja consultar?", periodos)
    input_local = st.sidebar.multiselect("Local informado pelo usuário", locais, default=locais)


# aplicando filtros nos dados
df = df.query("ano_mes == @input_periodo and local in @input_local", engine="python")
df_elogios = df.query("not elogio.isna()", engine="python").drop(['tipo', 'sugestao', 'reclamacao', 'ano', 'mes', 'ano_mes'], axis=1)
df_sugestao = df.query("not sugestao.isna()", engine="python").drop(['tipo', 'elogio', 'reclamacao', 'ano', 'mes', 'ano_mes'], axis=1)
df_reclamacao = df.query("not reclamacao.isna()", engine="python").drop(['tipo', 'elogio', 'sugestao', 'ano', 'mes', 'ano_mes'], axis=1)


indicadores = st.columns(4)
with indicadores[0]:
    st.metric(label="Total Manifestações", value=len(df))
with indicadores[1]:
    st.metric(label="Total Elogios", value=len(df_elogios))
with indicadores[2]:
    st.metric(label="Total Sugestões", value=len(df_sugestao))
with indicadores[3]:
    st.metric(label="Total Reclamações", value=len(df_reclamacao))


graficos = st.columns([4,2])
with graficos[0]:
    # with st.expander("Manifestações por dia"):
    # criar um grafico com plotly monstrando a quantidade de manifestações por dia
    df_por_data = df.groupby(df['data'].dt.date).size().reset_index(name='total')
    # st.write(df_por_data)


    # Criando o gráfico de linhas
    fig = px.line(df_por_data, x='data', y='total', markers=True, labels={'total': 'Quantidade Manifestações', 'data': 'Data'})

    maximo_apurados_em_uma_data = df_por_data['total'].max()
    if maximo_apurados_em_uma_data <= 10:
        ticks_espacamento = 1
    else:
        ticks_espacamento = 10 #int(maximo_apurados_em_uma_data / 4)
    # st.write(f'ticks_espacamento: {ticks_espacamento}, max: {maximo_apurados_em_uma_data}')
    
    # Configurando layout
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Total Manifestações",
        title="Evolução da quantidade de manifestações por dia",
        font=dict(
            family="Arial",
            size=12,
            color="#7f7f7f"
        ),
        yaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=maximo_apurados_em_uma_data
        ),
        height=350
    )

    # Formatando a data
    fig.update_layout(xaxis=dict(tickformat='%d\n%b-%Y', tickmode='linear'))

    # Adicionando pontos mais evidentes
    fig.update_traces(marker=dict(size=8, line=dict(width=2, color='DarkSlateGray')))

    # Exibindo o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)

with graficos[1]:
    # Supondo que df seja o seu DataFrame
    df_composicao = df[['elogio', 'sugestao', 'reclamacao']].count().reset_index(name='quantidade')
    df_composicao.columns = ['Tipo', 'Quantidade']

    # Mapeando as cores para cada tipo
    cores = {'elogio': 'limegreen', 'sugestao': 'royalblue', 'reclamacao': 'firebrick'}
    df_composicao['Cor'] = df_composicao['Tipo'].map(cores)

    # Criando o gráfico de pizza com cores personalizadas
    fig = px.pie(df_composicao, values='Quantidade', names='Tipo', title='Composição das manifestações',
                color='Tipo', color_discrete_map=cores, hole=.3, height=400)

    # Exibindo o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)



with st.expander("NPS: Net Promoter Score", expanded=True):
    st.write('NPS: Net Promoter Score')
    st.dataframe(df_nps)


with st.expander("Manifestações por tipo", expanded=True):
    tab_tipos = st.tabs(["Elogios", "Sugestões", "Reclamações"])
    with tab_tipos[0]:
        st.table(df_elogios)

    with tab_tipos[1]:
        st.table(df_sugestao)

    with tab_tipos[2]:
        st.table(df_reclamacao)




