# Planilha Editavel Google Sheets: <https://docs.google.com/spreadsheets/d/1ulLsJgPzUlE5LGXyx2r_uAQMeJhToK9acA6SaumntVA/edit?resourcekey#gid=25369857>
# Formulario: <https://docs.google.com/forms/d/e/1FAIpQLSf5aE3ymUu7xF64N18XI0Iv-MNtxj3Avw909N5wvs-XVZzJTw/viewform>

import os
import re
import time
import requests # pip install requests
import pandas as pd # pip install pandas
import numpy as np # pip install numpy
import streamlit as st # pip install streamlit
from datetime import datetime
# from unidecode import unidecode
from rich.console import Console # pip install rich
from io import StringIO, BytesIO
import matplotlib.pyplot as plt # pip install matplotlib
import plotly.express as px # pip install plotly
import plotly.graph_objects as go
import seaborn as sns # pip install seaborn


local_data_filename = 'data/data.parquet'
local_nps_filename = 'data/nps.parquet'

# ! TODO: remover essa linha apos finalizar o desenvolvimento
if os.path.exists('data'):
    os.system('rm -rf data')


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
        
        # classificar a nota do nps
        df['classe'] = np.where(df['nps'] >= 9, 'promotor', np.where(df['nps'] >= 7, 'neutro', 'detrator'))
        # alterar a ordem da coluna classe para ficar na 3a posição
        df = df[['data', 'local', 'nps', 'classe', 'tipo', 'elogio', 'sugestao', 'reclamacao', 'nome', 'telefone', 'email', 'ano', 'mes', 'ano_mes']]
        
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
        'ano_mes', 'nps', 'classificacao', 'total', 'promotores', 'percentual_promotores',
        'neutros', 'percentual_neutros', 'detratores', 'percentual_detratores'
    ])

if os.path.exists(local_nps_filename):
    console.log('- Obtendo o NPS em cache')
    df_nps = pd.read_parquet(local_nps_filename)
else:
    console.log('- Calculando o NPS')
    # para cada periodo, calcular o nps
    for periodo in periodos:
        df_periodo = df.query("ano_mes == @periodo", engine="python")
        
        # quantificar os promotores, neutros e detratores
        df_promotores = df_periodo.query("nps >= 9", engine="python")
        df_neutros = df_periodo.query("nps >= 7 and nps <= 8", engine="python")
        df_detratores = df_periodo.query("nps <= 6", engine="python")
        
        # calcular as proporções
        total_manifestacoes = len(df_periodo)
        percentual_promotores = (len(df_promotores) / total_manifestacoes)
        percentual_neutros = (len(df_neutros) / total_manifestacoes)
        percentual_detratores = (len(df_detratores) / total_manifestacoes)
        
        # calcular o score
        score_nps = percentual_promotores - percentual_detratores
        
        # classificar o score
        if score_nps >= 0.75:
            classificacao = 'Excelência'
        elif score_nps >= 0.5:
            classificacao = 'Qualidade'
        elif score_nps >= 0.25:
            classificacao = 'Aperfeiçoamento'
        else:
            classificacao = 'Crítica'
        
        nps_dict = {
            'ano_mes': periodo,
            'nps': round(score_nps * 100, 2),
            'classificacao': classificacao,
            'total': total_manifestacoes,
            'promotores': len(df_promotores),
            'percentual_promotores': f'{round(percentual_promotores * 100, 2)}%',
            'neutros': len(df_neutros),
            'percentual_neutros': f'{round(percentual_neutros * 100, 2)}%',
            'detratores': len(df_detratores),
            'percentual_detratores': f'{round(percentual_detratores * 100, 2)}%'
        }
        df_nps = pd.concat([df_nps, pd.DataFrame([nps_dict])], ignore_index=True)
    # armazenar em cache
    console.log('- Armazenando o NPS em cache')
    df_nps.to_parquet(local_nps_filename, index=False)

# imprimindo o nps no console
console.log(df_nps)

# SIDEBAR ============================================================================================================
with st.sidebar.title("Filtros"):
    input_periodo = st.sidebar.selectbox("Qual período você deseja consultar?", periodos)
    input_local = st.sidebar.multiselect("Local informado pelo usuário", locais, default=locais)


# aplicando filtros nos dados ========================================================================================
df = df.query("ano_mes == @input_periodo and local in @input_local", engine="python")
df_nps = df_nps.query("ano_mes == @input_periodo", engine="python")
df_elogios = df.query("not elogio.isna()", engine="python").drop(['tipo', 'sugestao', 'reclamacao', 'ano', 'mes', 'ano_mes'], axis=1)
df_sugestao = df.query("not sugestao.isna()", engine="python").drop(['tipo', 'elogio', 'reclamacao', 'ano', 'mes', 'ano_mes'], axis=1)
df_reclamacao = df.query("not reclamacao.isna()", engine="python").drop(['tipo', 'elogio', 'sugestao', 'ano', 'mes', 'ano_mes'], axis=1)

# agrupar para cada local e totalizar a quantidade de Elogios, Sugestões e Reclamações em um único dataframe
df_grupos_locais = df.groupby(['local']).agg({
    'elogio': 'count',
    'sugestao': 'count',
    'reclamacao': 'count'
}).reset_index()
# definir a coluna "local" como index
df_grupos_locais.set_index('local', inplace=True)

# Defina uma paleta de cores usando seaborn
color_palette = sns.color_palette("Blues", as_cmap=True)

# Aplique as cores com base nos valores
df_grupos_locais_styled = df_grupos_locais.style.background_gradient(cmap=color_palette, axis=0)


console.log(df_grupos_locais)


total_manifestacoes = len(df)
total_elogios = len(df_elogios)
total_sugestoes = len(df_sugestao)
total_reclamacoes = len(df_reclamacao)

# obter o "nps" da primeira linha
nota_nps = df_nps['nps'].iloc[0]
classificacao_nps = df_nps['classificacao'].iloc[0]

# apresentação do nps ================================================================================================
indicadores = st.columns(4)
with indicadores[0]:
    st.metric(label="NPS", value=nota_nps)
with indicadores[1]:
    st.metric(label="Zona de classificação", value=classificacao_nps)

# apresentação quantitativa dos dados ================================================================================
indicadores = st.columns(4)
with indicadores[0]:
    st.metric(label="Total Manifestações", value=total_manifestacoes)
with indicadores[1]:
    st.metric(label="Total Elogios", value=total_elogios)
with indicadores[2]:
    st.metric(label="Total Sugestões", value=total_sugestoes)
with indicadores[3]:
    st.metric(label="Total Reclamações", value=total_reclamacoes)


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



# with st.expander("NPS: Net Promoter Score", expanded=True):
with st.expander("NPS", expanded=False):
    st.write(f"""#### O que é o NPS?  
O Net Promoter Score (NPS) é uma metodologia de satisfação de clientes desenvolvida para avaliar o grau de fidelidade dos clientes de qualquer perfil de empresa.
Para calcular o NPS, é realizada uma única pergunta ao cliente: “Em uma escala de 0 a 10, o quanto você indicaria nossa empresa para um amigo?”.

A partir da resposta, os clientes são divididos em 3 categorias:

- Notas de 0 a 6: Detratores
- Notas de 7 a 8: Neutros
- Notas de 9 a 10: Promotores

O cálculo do NPS é feito subtraindo o percentual de clientes detratores do percentual de clientes promotores. O resultado varia de -100 a 100.

Quanto mais alto o NPS, maior é a satisfação dos clientes e maior a tendência de recomendação da empresa para amigos e familiares.

#### Como calcular o NPS?

O calculo da nota do NPS é feito da seguinte forma:

- NPS = % de promotores - % de detratores

Onde:

- % de promotores = (total de promotores / total de manifestações) * 100
- % de detratores = (total de detratores / total de manifestações) * 100


#### Extratificando o período {input_periodo}:
""")
    st.subheader(f"")
    st.table(df_nps)


with st.expander("Manifestações por tipo", expanded=True):
    tab_tipos = st.tabs(["Manifestações por setores", f"Elogios ({total_elogios})", f"Sugestões ({total_sugestoes})", f"Reclamações ({total_reclamacoes})"])
    with tab_tipos[0]:
        st.table(df_grupos_locais)
        
    with tab_tipos[1]:
        st.table(df_elogios)

    with tab_tipos[2]:
        st.table(df_sugestao)

    with tab_tipos[3]:
        st.table(df_reclamacao)




