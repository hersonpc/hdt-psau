# Planilha Editavel Google Sheets: <https://docs.google.com/spreadsheets/d/1ulLsJgPzUlE5LGXyx2r_uAQMeJhToK9acA6SaumntVA/edit?resourcekey#gid=25369857>
# Formulario: <https://docs.google.com/forms/d/e/1FAIpQLSf5aE3ymUu7xF64N18XI0Iv-MNtxj3Avw909N5wvs-XVZzJTw/viewform>

import os
import re
import time
import requests # pip install requests
import pandas as pd # pip install pandas
import numpy as np # pip install numpy
import streamlit as st # pip install streamlit
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from rich.console import Console # pip install rich
import matplotlib.pyplot as plt # pip install matplotlib
import plotly.express as px # pip install plotly
import plotly.graph_objects as go
import seaborn as sns # pip install seaborn
from jinja2 import Template  # pip install Jinja2



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
        
        df['local'] = df['local'].str.strip().str.upper()
        
        df['com_opiniao'] = np.where(df['elogio'].notna() | df['sugestao'].notna() | df['reclamacao'].notna(), 1, 0)
        df['sem_opiniao'] = np.where(df['elogio'].isna() & df['sugestao'].isna() & df['reclamacao'].isna(), 1, 0)
        
        # criar coluna de ano, mes e "ano/mes"
        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        df['periodo'] = df['data'].dt.strftime('%Y/%m')
        
        # deferminar a tipificação da manifestação
        df['tipo'] = np.where(df['elogio'].notna(), 'elogio', np.where(df['sugestao'].notna(), 'sugestao', np.where(df['reclamacao'].notna(), 'reclamacao', 'sem opinião')))
        
        # classificar a nota do nps
        df['classe'] = np.where(df['nps'] >= 9, 'promotor', np.where(df['nps'] >= 7, 'neutro', 'detrator'))
        
        # criar o campo 'flag' com bolinha verde se a classificação for 'promotor', azul se for 'neutro' e vermelha se for 'detrator'
        df['flag'] = np.where(df['classe'] == 'promotor', '🟢', np.where(df['classe'] == 'neutro', '🔵', '🔴'))
        
        # alterar a ordem da coluna classe para ficar na 3a posição
        df = df[[
            'data', 'local', 'nps', 'classe', 'flag', 'tipo', 'elogio', 
            'sugestao', 'reclamacao', 'com_opiniao', 'sem_opiniao', 'nome', 
            'telefone', 'email', 'ano', 'mes', 'periodo'
        ]]
        
        # ordenar por data
        df.sort_values(by=['data'], inplace=True, ascending=False)
        
        # estabelendo o valor padrão para os campos vazios
        df.fillna('-', inplace=True)

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

def agrupar_por_setor(df):
    # agrupar para cada local e totalizar a quantidade de Elogios, Sugestões e Reclamações em um único dataframe
    df_grupos_locais = df.groupby(['tipo','local']).agg({
        'data': 'count',
    }).reset_index()
    # sort por tipo
    # st.write(df_grupos_locais)

    df_grupos_locais_pivot = df_grupos_locais.pivot(index='local', columns='tipo', values='data').reset_index()
    df_grupos_locais_pivot = df_grupos_locais_pivot[['local', 'elogio', 'sugestao', 'reclamacao', 'sem opinião']]
    df_grupos_locais_pivot['total'] = df_grupos_locais_pivot[['elogio', 'sugestao', 'reclamacao', 'sem opinião']].sum(axis=1)
    df_grupos_locais_pivot['proporcao'] = round(df_grupos_locais_pivot['total'] / len(df) * 100, 1)

    # Substitua valores NaN por 0 (se necessário)
    df_grupos_locais_pivot = df_grupos_locais_pivot.fillna(0)
    
    df_grupos_locais_pivot['elogio'] = df_grupos_locais_pivot['elogio'].astype(int)
    df_grupos_locais_pivot['sugestao'] = df_grupos_locais_pivot['sugestao'].astype(int)
    df_grupos_locais_pivot['reclamacao'] = df_grupos_locais_pivot['reclamacao'].astype(int)
    df_grupos_locais_pivot['sem opinião'] = df_grupos_locais_pivot['sem opinião'].astype(int)
    df_grupos_locais_pivot['total'] = df_grupos_locais_pivot['total'].astype(int)
    df_grupos_locais_pivot['str_proporcao'] = df_grupos_locais_pivot['proporcao'].astype(str) + '%'

    return df_grupos_locais_pivot

def calcular_nps():
    df_nps = pd.DataFrame(columns=[
        'periodo', 'nps', 'classificacao', 'total', 'promotores', 'percentual_promotores',
        'neutros', 'percentual_neutros', 'detratores', 'percentual_detratores'
    ])

    if os.path.exists(local_nps_filename):
        console.log('- Obtendo o NPS em cache')
        df_nps = pd.read_parquet(local_nps_filename)
    else:
        console.log('- Calculando o NPS')
        # para cada periodo, calcular o nps
        for periodo in periodos:
            df_periodo = df.query("periodo == @periodo", engine="python")
            
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
                'periodo': periodo,
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
    return df_nps

def grafico_evolucao_diario(df):
    # criar um grafico com plotly monstrando a quantidade de manifestações por dia
    # df_por_data = df.groupby(df['data'].dt.date).size().reset_index(name='total')
    
    data_minima = df['data'].min().date()
    data_maxima = datetime.today().date()
    
    # Crie um DataFrame com todas as datas no intervalo desejado
    datas_todas = pd.date_range(start=data_minima, end=data_maxima, freq='D').date
    df_datas_todas = pd.DataFrame({'data': datas_todas})
    df_por_data = df_datas_todas.merge(df.groupby(df['data'].dt.date).size().reset_index(name='total'), how='left', on='data')

    df_por_data['total'].fillna(0, inplace=True) # substituir os valores nulos por zero

    # st.write(df_por_data)


    # Criando o gráfico de linhas
    fig = px.line(df_por_data, x='data', y='total', markers=True, labels={'total': 'Quantidade Manifestações', 'data': 'Data'})

    maximo_apurados_em_uma_data = df_por_data['total'].max()
    if maximo_apurados_em_uma_data <= 10:
        ticks_espacamento = 1
    else:
        ticks_espacamento = 10 #int(maximo_apurados_em_uma_data / 4)
    st.write(f'ticks_espacamento: {ticks_espacamento}, max: {maximo_apurados_em_uma_data}')
    
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
            dtick=ticks_espacamento
        ),
        height=350
    )

    # Formatando a data
    fig.update_layout(xaxis=dict(tickformat='%d\n%b-%Y', tickmode='linear'))

    # Adicionando pontos mais evidentes
    fig.update_traces(marker=dict(size=8, line=dict(width=2, color='DarkSlateGray')))
    
    return fig

def grafico_composicao_setores(df):
    df = df.sort_values('Total de manifestações', ascending=False)
    ordem_categorias = df['local'].tolist()
    

    # Crie um gráfico de barras com Plotly Express
    fig = px.bar(
        df,
        x='local',
        y='% Composição',
        title='Proporção das manifestações dos usuários por setor',
        labels={'% Composição': 'Proporção de Composição', 'local': 'Setores'},
        hover_data=['Elogios', 'Sugestões', 'Reclamações', 'Total de manifestações', 'Com Opinião', 'Sem Opinião'],
        color_continuous_scale='Blues',
        category_orders={'local': ordem_categorias}  # Defina a ordem das categorias
    )
    
    # definir o eixo y como percentual
    # fig.update_yaxes(tickformat="%")

    # # Exiba o gráfico
    # fig.show()
    return fig




st.title('Dashboard - PSAU')
st.subheader('Pesquisa de Satisfação dos Usuários')
st.markdown(f'<h5 style="color: #6880c7;">{hospital_nome}</h5>', unsafe_allow_html=True)
# st.markdown(f'<h2 style="color: firebrick;text-align:center;border-bottom: 4px solid firebrick;margin-bottom: 1rem;padding: .5rem;">{sel_setor.upper()}<>


df = get_data()
df_full = df.copy()
periodos = df['periodo'].unique()
locais = df['local'].unique()


with st.spinner('Processando...'):
    df_nps = calcular_nps()

    # imprimindo o nps no console
    console.log(df_nps)

# SIDEBAR ============================================================================================================
with st.sidebar.title("Filtros"):
    input_visualizacao = st.sidebar.radio("Perspectiva de Visualização", ["Instituciional", "Setorial"], index=0)
    # st.write(f"Visualização: {input_visualizacao}")
    input_periodo = st.sidebar.selectbox("Qual período você deseja consultar?", periodos)
    input_local = st.sidebar.multiselect("Local informado pelo usuário", locais, default=locais)


# aplicando filtros nos dados ========================================================================================
df = df.query("periodo == @input_periodo and local in @input_local", engine="python")
if df is None or df.empty:
    st.error("❌ Nenhum dado encontrado para os filtros selecionados. Considere alterar os filtros e tentar novamente.")
    st.stop()

# separando os dataframes
df_nps = df_nps.query("periodo == @input_periodo", engine="python")
df_elogios = df.query("tipo=='elogio'", engine="python").drop(['tipo', 'sugestao', 'reclamacao', 'com_opiniao', 'sem_opiniao', 'ano', 'mes', 'periodo'], axis=1)
df_sugestao = df.query("tipo=='sugestao'", engine="python").drop(['tipo', 'elogio', 'reclamacao', 'com_opiniao', 'sem_opiniao', 'ano', 'mes', 'periodo'], axis=1)
df_reclamacao = df.query("tipo=='reclamacao'", engine="python").drop(['tipo', 'elogio', 'sugestao', 'com_opiniao', 'sem_opiniao', 'ano', 'mes', 'periodo'], axis=1)
df_sem_opiniao = df.query("tipo=='sem opinião'", engine="python").drop(['tipo', 'ano', 'mes', 'elogio', 'sugestao', 'reclamacao', 'com_opiniao', 'sem_opiniao', 'periodo'], axis=1)



df_grupos_locais = df.groupby(['local']).agg({
    'elogio': 'count',
    'sugestao': 'count',
    'reclamacao': 'count',
    'com_opiniao': 'count',
    'sem_opiniao': 'count',
    'data': 'count',
}).reset_index()


df_grupos_locais.rename(columns={'data': 'total'}, inplace=True)

# calculando proporção do local
df_grupos_locais['proporcao'] = round(df_grupos_locais['total'] / len(df) * 100, 1)
df_grupos_locais['proporcao'] = df_grupos_locais['proporcao'].astype(str) + '%'
# calculando o total de manifestações por grupo
df_grupos_locais['com_opiniao'] = df_grupos_locais[['elogio', 'sugestao', 'reclamacao']].sum(axis=1)
df_grupos_locais['sem_opiniao'] = df_grupos_locais['total'] - df_grupos_locais['com_opiniao']

# renomeando
df_grupos_locais.rename(columns={
    'elogio': 'Elogios',
    'sugestao': 'Sugestões',
    'reclamacao': 'Reclamações',
    'total': 'Total de manifestações',
    'proporcao': '% Composição',
    'com_opiniao': 'Com Opinião',
    'sem_opiniao': 'Sem Opinião',
    }, inplace=True)

# definir a coluna "local" como index
# df_grupos_locais.set_index('local', inplace=True)

# Defina uma paleta de cores usando seaborn
color_palette = sns.color_palette("Blues", as_cmap=True)

# Aplique as cores com base nos valores
df_grupos_locais_styled = df_grupos_locais.style.background_gradient(cmap=color_palette, axis=0)


# console.log(df_grupos_locais)


total_manifestacoes = len(df)
total_elogios = len(df_elogios)
total_sugestoes = len(df_sugestao)
total_reclamacoes = len(df_reclamacao)
total_sem_opiniao = len(df_sem_opiniao)

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
indicadores = st.columns(5)
with indicadores[0]:
    st.metric(label="Total Manifestações", value=total_manifestacoes)
with indicadores[1]:
    st.metric(label="Total Elogios", value=total_elogios)
with indicadores[2]:
    st.metric(label="Total Sugestões", value=total_sugestoes)
with indicadores[3]:
    st.metric(label="Total Reclamações", value=total_reclamacoes)
with indicadores[4]:
    st.metric(label="Total Sem Opinião", value=total_sem_opiniao)


graficos = st.columns([4,2])
with graficos[0]:
    # criar um grafico com plotly monstrando a quantidade de manifestações por dia
    st.plotly_chart(grafico_evolucao_diario(df), use_container_width=True)

with graficos[1]:
    # Supondo que df seja o seu DataFrame
    df_composicao = df[['elogio', 'sugestao', 'reclamacao']].count().reset_index(name='quantidade')
    df_composicao.columns = ['Tipo', 'Quantidade']
    
    com_opiniao_total = df_composicao['Quantidade'].sum()
    # st.write(f"com_opiniao_total: {com_opiniao_total}")
    total_manifestacoes = len(df)

    # Mapeando as cores para cada tipo
    cores = {'elogio': 'limegreen', 'sugestao': 'royalblue', 'reclamacao': 'firebrick'}
    df_composicao['Cor'] = df_composicao['Tipo'].map(cores)
    # st.write(df)
    # st.write(df_composicao)
    # Criando o gráfico de pizza com cores personalizadas
    fig = px.pie(df_composicao, 
                    values='Quantidade', 
                    names='Tipo', 
                    title='Composição das manifestações',
                    color='Tipo', 
                    color_discrete_map=cores, 
                    # hover_data=['Quantidade'],
                    hole=.3, 
                    height=400)

    # Exibindo o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)



# with st.expander("NPS: Net Promoter Score", expanded=True):
with st.expander("NPS", expanded=False):
    
    
    # Lê o conteúdo do arquivo de modelo
    with open('markdown/nps.md', 'r', encoding='utf-8') as f:
        template_text = f.read()

    # Cria um objeto Template
    template = Template(template_text)

    # Renderiza o template com variáveis específicas
    rendered_text = template.render(input_periodo=input_periodo, df_nps=df_nps)

    st.write(rendered_text)

    st.table(df_nps)


with st.expander("Manifestações por tipo", expanded=True):
    
    tab_setores = "Manifestações por setores"
    tab_elogios = f"Elogios ({total_elogios})"
    tab_sugestoes = f"Sugestões ({total_sugestoes})"
    tab_reclamacoes = f"Reclamações ({total_reclamacoes})"
    tab_sem_opiniao = f"Sem Opinião ({total_sem_opiniao})"
    tab_todos_dados = f"Todos os dados ({len(df_full)})"
    
    tab_tipos = st.tabs([
        tab_setores, 
        tab_elogios,
        tab_sugestoes,
        tab_reclamacoes,
        tab_sem_opiniao,
        tab_todos_dados
    ])
    with tab_tipos[0]:
        st.plotly_chart(grafico_composicao_setores(df_grupos_locais), use_container_width=True)
        st.table(df_grupos_locais)
        st.table(agrupar_por_setor(df)[['local', 'elogio', 'sugestao', 'reclamacao', 'sem opinião', 'total', 'str_proporcao']])
        
    with tab_tipos[1]:
        st.write('Relação dos registros de elogios dos usuários')
        st.table(df_elogios)

    with tab_tipos[2]:
        st.write('Relação dos registros de sugestões dos usuários')
        st.table(df_sugestao)

    with tab_tipos[3]:
        st.write('Relação dos registros de reclamações dos usuários')
        st.table(df_reclamacao)

    with tab_tipos[4]:
        st.write('Relação dos registros sem opinião dos usuários')
        st.table(df_sem_opiniao)

    with tab_tipos[5]:
        st.write('Relação de todos os registros reportados pelos usuários')
        st.table(df_full)

with st.expander("Extratificação por setor"):
    for grupo in df_grupos_locais['local'].unique():
        st.write(f"<h4 style='color: firebrick'>{grupo}</h4>", unsafe_allow_html=True)
        
        st.write(f"<h6 style='color: #6f6f6f;'>Resumo do setor</h6>", unsafe_allow_html=True)
        df_setor = agrupar_por_setor(df).query("local == @grupo", engine="python")
        st.table(df_setor)
        
        st.write(f"<h6 style='color: #6f6f6f;'>Registros das manifestações dos usuários</h6>", unsafe_allow_html=True)
        st.table(df.query("local == @grupo", engine="python").drop(['tipo', 'ano', 'mes', 'periodo'], axis=1))
