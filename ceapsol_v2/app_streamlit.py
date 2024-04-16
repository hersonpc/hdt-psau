## Dashboard PSAU CEAPSOL v2
## Autor.: Herson Melo
## Date.......: 2024-04-16
## Fonte......: !TROCAR
## Formulario.: https://docs.google.com/forms/d/e/1FAIpQLScE1q_3qImloxU4V5qfEvNBW_iPytjbzHIYYY_v6WNQ7Kzd-g/viewform
## QRCode.....: !TROCAR https://feedback.isgsaude.org/psau/hdt
##
## Publicado..: https://psau.ceapsol.org.br/
##

import os
import time
import json
import base64
import requests # pip install requests
import pandas as pd # pip install pandas
import numpy as np # pip install numpy
import streamlit as st # pip install streamlit
import schedule # pip install schedule
import threading
from io import BytesIO
from datetime import datetime, timedelta
from rich.console import Console # pip install rich
import matplotlib.pyplot as plt # pip install matplotlib
import plotly.express as px # pip install plotly
import plotly.graph_objects as go
import seaborn as sns # pip install seaborn
from jinja2 import Template  # pip install Jinja2

if 'input_visualizacao' not in st.session_state:
    st.session_state['input_visualizacao'] = 'Institucional'
if 'input_periodo' not in st.session_state:
    st.session_state['input_periodo'] = None
if 'input_setor' not in st.session_state:
    st.session_state['input_setor'] = []

class Log():
    def __init__(self):
        self.console = Console()

    def debug(self, message):
        self.console.log(f'[magenta dim]debug[/] {message}')
    def info(self, message):
        self.console.log(f'[green]info[/] {message}')
    def warning(self, message):
        self.console.log(f'[yellow]warn[/] {message}')
    def error(self, message):
        self.console.log(f'[red]error[/] {message}')
log = Log()

class DataProcessor:
    def __init__(self):
        self.etl_log_filename = 'data/etl_log.json'
        self.raw_data_filename = 'data/raw_data.csv'
        self.clean_data_filename = 'data/clean_data.parquet'
        self.clean_data_periodos_filename = 'data/clean_data_periodos.parquet'
        self.clean_nps_data_filename = 'data/clena_nps.parquet'
        self.url_raw_data = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQnAgS3VcuLGyS6sLSCVo8d-_fT2E-X4L1rEYm6iRF8uYxkqfiIPaAgRtriSySK-lbH07fBysH92x9d/pub?gid=25369857&single=true&output=csv'
        self.ttl_tempo_cache = 1 * 60 * 60 # 1 hora

        self.df = None
        self.df_periodos = None

        # garantir que a pasta data exista
        if not os.path.exists('data'):
            os.makedirs('data')

    def download_raw_data(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Accept-Charset': 'utf-8'
        }
        try:
            log.debug("<ETL> [dim]Adiquirindo raw data")
            df = None
            response = None
            error = None

            response = requests.get(url, headers=headers)
            if response and response.status_code == 200:
                log.debug("<ETL> [dim]Download realizado com sucesso")
                try:
                    df = pd.read_csv(BytesIO(response.content), sep=',')

                    log.debug("<ETL> [dim]Armazenando dados brutos[/]")
                    df.to_csv(self.raw_data_filename, index=False)
                except Exception as e:
                    log.error(f'<ETL> [yellow]FALHA AO LER DADOS:[/] [red]{e}')
                    error = e
        except Exception as e:
            log.error(f'<ETL> [yellow]FALHA DOWNLOAD:[/] [red]{e}')
            error = e
        finally:
            encoded_content = base64.b64encode(response.content).decode('utf-8') if (response and response.status_code == 200) else None
            with open(self.etl_log_filename, 'w') as f:
                json_data = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'success' if response and response.status_code == 200 else 'error',
                    'response': {
                        'url': url,
                        'status_code': response.status_code if response else None,
                        'headers': dict(response.headers) if response else None,
                        'content': encoded_content,
                    },
                }
                if error:
                    json_data['error'] = str(error)
                f.write(json.dumps(json_data, indent=4))

        return df

    def process_and_cleaning_data(self, df):
        # Restante do código de processamento
        log.debug("<ETL> [dim]Processando e transformando os dados brutos")
        try:
            df.columns = [
                "data", "setor", "nps", "tipo", "elogio", 
                "sugestao", "reclamacao", "nome", "telefone", 
                "email"
            ]

            # converter data para o tipo datetime
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y %H:%M:%S')
            df['dia'] = df['data'].dt.date

            df['setor'] = df['setor'].str.strip().str.upper()

            # df['com_opiniao'] = np.where(df['elogio'].notna() | df['sugestao'].notna() | df['reclamacao'].notna(), 1, 0)
            # df['sem_opiniao'] = np.where(df['elogio'].isna() & df['sugestao'].isna() & df['reclamacao'].isna(), 1, 0)

            # criar coluna de ano, mes e "ano/mes"
            df['ano'] = df['data'].dt.year
            df['mes'] = df['data'].dt.month
            df['periodo'] = df['data'].dt.strftime('%Y/%m')

            # deferminar a tipificação da manifestação
            df['tipo'] = np.where(df['elogio'].notna(), 'elogio', np.where(df['sugestao'].notna(), 'sugestao', np.where(df['reclamacao'].notna(), 'reclamacao', 'preferiu nao informar')))
            df['manifestacao'] = np.where(df['elogio'].notna(), df['elogio'], np.where(df['sugestao'].notna(), df['sugestao'], np.where(df['reclamacao'].notna(), df['reclamacao'], '-')))

            # classificar a nota do nps
            df['classe'] = np.where(df['nps'] >= 9, 'promotor', np.where(df['nps'] >= 7, 'neutro', 'detrator'))

            df['nome'] = df['nome'].str.strip().str.title()
            df['email'] = df['email'].str.strip().str.lower()
            # remover todos caracteres não numéricos do campo telefone
            df['telefone'] = df['telefone'].str.replace(r'\D', '', regex=True)


            # criar o campo 'flag' com bolinha verde se a classificação for 'promotor', azul se for 'neutro' e vermelha se for 'detrator'
            df['flag'] = np.where(df['classe'] == 'promotor', '🟢', np.where(df['classe'] == 'neutro', '🔵', '🔴'))

            # alterar a ordem da coluna classe para ficar na 3a posição
            df = df[[
                'periodo', 'dia',
                'ano', 'mes',
                'data', 'setor', 'nps', 'classe', 
                'flag', 'tipo', 'manifestacao',
                'nome', 'telefone', 'email', 
                # 'elogio', 'sugestao', 'reclamacao', 
                # 'com_opiniao', 'sem_opiniao',
            ]]

            # index começando em 1
            df.index = np.arange(1, len(df) + 1)

            # ordenar inversamente por data
            df = df.sort_values(by=['data'], ascending=False)

            # estabelendo o valor padrão para os campos vazios
            df = df.fillna('-')

            # armazenar em cache
            log.debug("<ETL> [dim]Armazenando dados em cache[/]")
            df.to_parquet(self.clean_data_filename, index=False)
        except Exception as e:
            log.error(f'<ETL> [yellow]ERROR ETL:[/] [red]{e}[/]')
            st.error('Falha ao processar a preparação dos dados. Tente novamente mais tarde ou procure apoio do departamento de TI.')
            return None

        return df

    def process_statistics(self, df):
        log.debug("<ETL> [dim]Processando estatísticas...")
        if df is None or df.empty:
            self.df_periodos = None
        try:
            df_temp = (
                df.groupby(['periodo', 'tipo','setor'])
                .agg({ 'data': 'count' })
                .reset_index()
                .rename(columns={'data': 'n'})
            )
            # print(df_temp)
            # self.df_temp.info()

            log.debug("<ETL> [dim]Pivotando dados estatísticos...")
            df_pivot = (
                df_temp.pivot(
                    index=['periodo', 'setor'],
                    columns='tipo',
                    values='n'
                )
                .reset_index()
            )

            df_pivot['total'] = df_pivot[['elogio', 'sugestao', 'reclamacao', 'preferiu nao informar']].sum(axis=1)

            # calcular o total amostras em cada período
            df_totais_periodos = (
                df_pivot.groupby(['periodo'])
                .agg({ 'total': 'sum' })
                .reset_index()
                .rename(columns={'total': 'n_periodo'})
            )
            df_totais_periodos['n_periodo'] = df_totais_periodos['n_periodo'].astype(int)
            # log.debug("<ETL> [red]Totalização por período ==============================")
            # print(df_totais_periodos)

            for campo in ['elogio', 'sugestao', 'reclamacao', 'preferiu nao informar', 'total']:
                if campo in df_pivot.columns:
                    df_pivot[campo] = df_pivot[campo].fillna(0).astype(int)

            df_pivot = (
                df_pivot.sort_values(by=['periodo', 'setor'], ascending=True)
            )[['periodo', 'setor', 'elogio', 'sugestao', 'reclamacao', 'preferiu nao informar', 'total']]

            # merge com os totais
            df_pivot = pd.merge(
                df_pivot,
                df_totais_periodos,
                on='periodo',
                how='left'
            )
            df_pivot['proporcao'] = round(df_pivot['total'] / df_pivot['n_periodo'], 4)

            # index começando em 1
            df_pivot.index = np.arange(1, len(df_pivot) + 1)

            log.debug("<ETL> [yellow]Analítico por período ==============================")
            print(df_pivot)

            self.df_periodos = df_pivot

            if self.df_periodos is not None:
                self.df_periodos.to_parquet(self.clean_data_periodos_filename, index=False)
                log.debug("<ETL> [green dim]Estatísticas processadas com sucesso!")
        except Exception as e:
            log.error(f'<ETL> [yellow]ERROR ETL STATISTICS:[/] [red]{e}[/]')
            st.error('Falha ao processar as estatísticas. Tente novamente mais tarde ou procure apoio do departamento de TI.')

        return self.df_periodos

    def get_data(self):
        log.debug("[dim]Getting data")
        if os.path.exists(self.clean_data_filename):
            idade_arquivo = time.time() - os.path.getmtime(self.clean_data_filename)
            if idade_arquivo > self.ttl_tempo_cache:
                log.debug("<ETL> [yellow dim]Cache expired[/]")
                os.remove(self.clean_data_filename)

        if os.path.exists(self.clean_data_filename):
            df = pd.read_parquet(self.clean_data_filename)
        else:
            log.debug("<ETL> [yellow]Iniciando ETL")
            df_raw = self.download_raw_data(self.url_raw_data)
            df = self.process_and_cleaning_data(df_raw)
            self.process_statistics(df)
            log.debug("<ETL> [green]ETL concluido com sucesso!")

        return df

    def get_data_by_periodos(self):
        return self.df_periodos

class Dashboard:
    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.df = None
        self.nps_dict = {}

    def set_layout(self):
        """Configurando o layout do dashboard no Streamlit"""
        st.set_page_config(
            page_title="CEAP-SOL PSAU v2",
            page_icon=':hospital:',
            layout="wide",
            # layout="centered",
            initial_sidebar_state="auto",
            menu_items=None
        )
        st.markdown("""
            <style>
            #MainMenu {visibility: hidden; }
            footer {visibility: hidden; }
            header {visibility: hidden; }
            th {
                text-align: center !important;
                background-color: #f8f8f8;
                color: black !important;
                text-transform: uppercase;
            }
            </style>""", unsafe_allow_html=True
        )

    def load_data(self):
        self.df = self.data_processor.get_data()

    def load_nps_data(self, periodo):
        df_filtrado = (
            self.df
            .copy()
            .query('periodo == @periodo')
        )
        self.nps_dict = self.calculate_nps(df_filtrado)

    def calculate_nps(self, df):
        # Restante do código de cálculo do NPS
        detratores = df[df['classe'] == 'detrator']['nps'].count()
        neutros = df[df['classe'] == 'neutro']['nps'].count()
        promotores = df[df['classe'] == 'promotor']['nps'].count()

        qtde_total = detratores + neutros + promotores

        p_detratores = detratores / qtde_total
        p_neutros = neutros / qtde_total
        p_promotores = promotores / qtde_total

        score_nps = round((p_promotores - p_detratores) * 100, 2)

        # zonas de classificação
        if score_nps < 0:
            zona = 'Crítica'
        elif score_nps < 50:
            zona = 'Aperfeiçoamento'
        elif score_nps < 75:
            zona = 'Qualidade'
        else:
            zona = 'Excelência'

        nps_dict = {
            'detratores': detratores,
            'p_detratores': f'{p_detratores:.2%}',
            'neutros': neutros,
            'p_neutros': f'{p_neutros:.2%}',
            'promotores': promotores,
            'p_promotores': f'{p_promotores:.2%}',
            'total': qtde_total,
            'score': score_nps,
            'zona': zona,
        }
        return nps_dict

    def get_lista_periodos(self):
        if self.df is None or self.df.empty:
            return []
        if 'periodo' not in self.df.columns:
            st.error('Estrutura de dados inválida.')
            return []
        lista_periodos = self.df['periodo'].unique()
        return lista_periodos

    def get_lista_setores(self, df = None):
        if df is None:
            df = self.df
        if df is None or df.empty:
            return []
        if 'setor' not in df.columns:
            st.error('Estrutura de dados inválida.')
            return []
        lista_periodos = df['setor'].unique()
        return lista_periodos

    def render_dashboard(self):
        # st.title('Dashboard - PSAU')
        st.header('Dashboard - Pesquisa de Satisfação dos Usuários')
        st.markdown(f'<h4 style="color: #6880c7;">Centro Estadual de Atenção Prolongada e Casa de Apoio Condomínio Solidariedade</h4>', unsafe_allow_html=True)
        main_container = st.empty()

        with st.spinner('Processando dados...'):
            self.load_data()

            if self.df is None:
                st.error('Falha ao carregar dados. Tente novamente mais tarde ou procure apoio do departamento de TI.')
                st.stop()
                return

            with st.sidebar.title("Filtros"):
                input_visualizacao = st.sidebar.radio("Perspectiva de Visualização", ["Institucional"], index=0)
                # input_visualizacao = st.sidebar.radio("Perspectiva de Visualização", ["Institucional", "Setorial"], index=0)
                input_periodo = st.sidebar.selectbox("Qual período você deseja consultar?", self.get_lista_periodos())
                # input_setor = st.sidebar.multiselect("Setor informado pelo usuário", self.get_lista_setores(), default=self.get_lista_setores())

            st.sidebar.markdown('<br><br><a href="https://docs.google.com/forms/d/e/1FAIpQLScE1q_3qImloxU4V5qfEvNBW_iPytjbzHIYYY_v6WNQ7Kzd-g/viewform" target="_blank">Abrir formulário</a>', unsafe_allow_html=True)

            # calcular o NPS do período selecionado
            self.load_nps_data(periodo=input_periodo)

            # filtrando os dados
            df_filtrado = (
                self.df
                .copy()
                .query('periodo == @input_periodo')
            ).drop(columns=['dia', 'periodo', 'ano', 'mes'])
            df_filtrado['data'] = df_filtrado['data'].dt.strftime('%d/%m/%Y %H:%M:%S')

            df_estatisticas_filtrado = (
                self.data_processor.get_data_by_periodos()
                .copy()
                .query('periodo == @input_periodo')
            ).drop(columns=['periodo', 'n_periodo'])
            df_estatisticas_filtrado['proporcao'] = df_estatisticas_filtrado['proporcao'].apply(lambda x: f'{x:.2%}')

            df_manifestacoes_por_dia = (
                self.df
                .copy()
                .query('periodo == @input_periodo')
                .groupby(['dia'])
                .agg({ 'dia': 'count' })
                .rename(columns={'dia': 'n'})
                .reset_index()
            )
            df_manifestacoes_por_setor = (
                self.df
                .copy()
                .query('periodo == @input_periodo')
                .groupby(['setor'])
                .agg({ 'setor': 'count' })
                .rename(columns={'setor': 'n'})
                .reset_index()
            )

            with main_container:
                with st.container():
                    st.markdown(f'<br><h5>Período de análise <b style="color: firebrick">{input_periodo}</b></h5>', unsafe_allow_html=True)
                    tabs = st.tabs(["Visão geral", "Manifestações", 'Por setor', "NPS"])
                    with tabs[0]:
                        st.markdown('##### Visão geral das estatísticas do período')
                        cols = st.columns(5)
                        with cols[0]:
                            st.metric(label="Total de manifestações", value=df_estatisticas_filtrado['total'].sum())
                        with cols[1]:
                            st.metric(label="Elogios", value=df_estatisticas_filtrado['elogio'].sum())
                        with cols[2]:
                            st.metric(label="Sugestões", value=df_estatisticas_filtrado['sugestao'].sum())
                        with cols[3]:
                            st.metric(label="Reclamações", value=df_estatisticas_filtrado['reclamacao'].sum())
                        with cols[4]:
                            st.metric(label="Preferiu não informar", value=df_estatisticas_filtrado['preferiu nao informar'].sum())

                        df_apresentacao = (
                            df_estatisticas_filtrado.rename({
                                "preferiu nao informar": "não informou",
                                "elogio": "elogios",
                                "sugestao": "sugestões",
                                "reclamacao": "reclamações",
                                "proporcao": "% proporção",
                            }, axis=1)
                            .reset_index(drop=True)
                        )
                        df_apresentacao.index = np.arange(1, len(df_apresentacao) + 1)
                        st.table(df_apresentacao)
                        # st.markdown(f'<small>Quantidade de registros: {len(df_apresentacao)}</small>', unsafe_allow_html=True)

                        st.markdown('##### Volume de manifestações recebidas por dia')
                        # # grafico de scatter plot do df_manifestacoes_por_dia
                        # fig = px.scatter(
                        #     df_manifestacoes_por_dia,
                        #     x='dia',
                        #     y='n',
                        #     # color='n',
                        #     # color_continuous_scale='RdBu',
                        #     size='n',
                        #     title='Manifestações por dia',
                        #     labels={
                        #         'dia': 'Data',
                        #         'n': 'Quantidade de manifestações',
                        #     },
                        #     width=1000,
                        #     height=400,
                        # )
                        # fig.update_layout(
                        #     margin=dict(l=0, r=0, t=50, b=0),
                        #     # paper_bgcolor="LightSteelBlue",
                        # )
                        # st.plotly_chart(fig, use_container_width=True)

                        # criar um grafico de barras com o total de manifestações por dia
                        fig = px.bar(
                            df_manifestacoes_por_dia,
                            x='dia',
                            y='n',
                            color='n',
                            title='Quantidade de manifestações reportadas por dia',
                            labels={
                                'dia': 'Data',
                                'n': 'Quantidade de manifestações',
                            },
                            width=1000,
                            height=400,
                        )
                        fig.update_layout(
                            margin=dict(l=0, r=0, t=50, b=0),
                            # paper_bgcolor="LightSteelBlue",
                        )
                        st.plotly_chart(fig, use_container_width=True)


                    with tabs[1]:
                        st.markdown('##### Registros das manifestações dos usuários')
                        tabs_manifestacoes = st.tabs(["Todos", "Elogios", "Sugestões", "Reclamações", "Preferiu não informar"])
                        with tabs_manifestacoes[0]:
                            st.table(df_filtrado)
                            st.markdown(f'<small>Quantidade de registros: {len(df_filtrado)}</small>', unsafe_allow_html=True)
                        with tabs_manifestacoes[1]:
                            st.table(df_filtrado[df_filtrado['tipo'] == 'elogio'].drop(['tipo'], axis=1).replace(0, '-'))
                            st.markdown(f'<small>Quantidade de registros: {len(df_filtrado[df_filtrado["tipo"] == "elogio"])}</small>', unsafe_allow_html=True)
                        with tabs_manifestacoes[2]:
                            st.table(df_filtrado[df_filtrado['tipo'] == 'sugestao'].drop(['tipo'], axis=1).replace(0, '-'))
                            st.markdown(f'<small>Quantidade de registros: {len(df_filtrado[df_filtrado["tipo"] == "sugestao"])}</small>', unsafe_allow_html=True)
                        with tabs_manifestacoes[3]:
                            st.table(df_filtrado[df_filtrado['tipo'] == 'reclamacao'].drop(['tipo'], axis=1).replace(0, '-'))
                            st.markdown(f'<small>Quantidade de registros: {len(df_filtrado[df_filtrado["tipo"] == "reclamacao"])}</small>', unsafe_allow_html=True)
                        with tabs_manifestacoes[4]:
                            st.table(df_filtrado[df_filtrado['tipo'] == 'preferiu nao informar'].drop(['tipo'], axis=1).replace(0, '-'))
                            st.markdown(f'<small>Quantidade de registros: {len(df_filtrado[df_filtrado["tipo"] == "preferiu nao informar"])}</small>', unsafe_allow_html=True)

                    with tabs[2]:
                        # st.markdown('#### Manifestações x Setores')
                        # input_setor = st.selectbox("Qual setor você deseja consultar?", self.get_lista_setores())
                        # st.markdown(f'#### {input_setor}')
                        # st.table(df_filtrado[df_filtrado['setor'] == input_setor].drop(['setor'], axis=1).replace(0, '-'))
                        # st.markdown('<small><i>Selecione o setor para visualizar as manifestações:</i></small>', unsafe_allow_html=True)
                        fig = px.bar(
                            df_manifestacoes_por_setor,
                            x='setor',
                            y='n',
                            color='n',
                            title='Manifestações por setor',
                            labels={
                                'setor': 'Setor',
                                'n': 'Quantidade de manifestações',
                            },
                            width=1000,
                            height=400,
                        )
                        fig.update_layout(
                            margin=dict(l=0, r=0, t=50, b=0),
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        lista_setores = sorted(list(self.get_lista_setores(df_filtrado)))
                        tabs_setores = st.tabs(lista_setores)
                        for index, setor in enumerate(tabs_setores):
                            nome_setor = lista_setores[index]
                            with tabs_setores[index]:
                                # st.markdown(f'#### {nome_setor}')
                                # st.write('conteudo')
                                cols = st.columns(2)
                                with cols[0]:
                                    st.metric(label="Setor", value=nome_setor)
                                with cols[1]:
                                    st.metric(label="Total de manifestações", value=df_estatisticas_filtrado[df_estatisticas_filtrado['setor'] == nome_setor]['total'].sum())
                                st.table(df_filtrado[df_filtrado['setor'] == nome_setor].drop(['setor'], axis=1).replace(0, '-'))
                                # st.markdown(f'<small>Quantidade de registros: {len(df_estatisticas_filtrado[df_estatisticas_filtrado["setor"] == setor])}</small>', unsafe_allow_html=True)
                        # for setor in df_estatisticas_filtrado['setor'].unique():
                        #     with tabs_setores[df_estatisticas_filtrado['setor'].unique().tolist().index(setor)]:
                        #         st.table(df_estatisticas_filtrado[df_estatisticas_filtrado['setor'] == setor].replace(0, '-'))
                        #         st.markdown(f'<small>Quantidade de registros: {len(df_estatisticas_filtrado[df_estatisticas_filtrado["setor"] == setor])}</small>', unsafe_allow_html=True)

                    with tabs[3]:
                        st.markdown('##### Net Promoter Score')
                        cols = st.columns([3,1])
                        with cols[0]:
                            st.metric(label="Score NPS atual", value=self.nps_dict['score'])
                            st.metric(label="Zona classificação atual", value=self.nps_dict['zona'])
                        with cols[1]:
                            st.write(f'**Cálculo NPS**\n\nPromotores = **{self.nps_dict["promotores"]}** *({self.nps_dict["p_promotores"]})*\n\nNeutros = **{self.nps_dict["neutros"]}** *({self.nps_dict["p_neutros"]})*\n\n Detratores = **{self.nps_dict["detratores"]}** *({self.nps_dict["p_detratores"]})*\n\n {self.nps_dict["p_promotores"]} - {self.nps_dict["p_detratores"]} = **{self.nps_dict["score"]}**')
                        # st.write(self.nps_dict)


def clean_data():
    # TODO : Função para ser executada somente durando o desenvolvimento
    if os.path.exists('data'):
        os.system('rm -rf data')

def main():
    data_processor = DataProcessor()
    dashboard = Dashboard(data_processor)

    dashboard.set_layout()
    dashboard.render_dashboard()

if __name__ == "__main__":
    log.info("\n\n[red]" + "="*60 + "\n\n" + "[red underline]INICIALIZANDO DASHBOARD[/]\n\n" + "[red]" + "="*60 + "\n")
    clean_data()
    main()
