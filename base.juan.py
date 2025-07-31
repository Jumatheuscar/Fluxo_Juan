import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import calendar
from datetime import datetime, date

# --- AUTENTICAÇÃO SIMPLES ---
senha = st.text_input("Digite a senha para acessar o painel:", type="password")
if senha != "Ju020531":
    st.warning("Acesso negado. Informe a senha correta.")
    st.stop()

# --- LEITURA DOS DADOS VIA GOOGLE SHEETS ---
sheet_url = "https://docs.google.com/spreadsheets/d/1t8OG-NgtqX-EGvegiUItogajyO9i_dAq-ERnkEKNSS0"
csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")

try:
    df = pd.read_csv(csv_url)
except Exception as e:
    st.error(f"Erro ao carregar dados do Google Sheets: {e}")
    st.stop()

# --- Ajuste de NOMES de coluna automaticamente ---
colunas = {c.lower().strip(): c for c in df.columns}
nome_data = next((colunas[c] for c in colunas if 'data' in c), None)
nome_valor = next((colunas[c] for c in colunas if 'valor' in c), None)
nome_categoria = next((colunas[c] for c in colunas if 'categoria' in c), None)

if not nome_data or not nome_valor or not nome_categoria:
    st.error(f"Colunas obrigatórias não encontradas (data, valor, categoria).\nColunas encontradas: {list(df.columns)}")
    st.stop()

df = df.rename(columns={nome_data: 'data', nome_valor: 'valor', nome_categoria: 'categoria'})
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df[~df['data'].isna()].copy()
df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
df['mes'] = df['data'].dt.to_period("M").astype(str)

# --- Customização de Cores e Textos ---
CUSTOM_BG = '#181C20'
TITULO_COR = 'white'
SUBTITULO_COR = '#48a0ff'
METRIC_COR = 'white'
GRAF_COR = "#003366"
GRAF_AUX_COR = "#48a0ff"

# --- Título ---
st.markdown(f"<h1 style='color:{TITULO_COR}; font-size:2.7rem;'>Fluxo de Caixa Pessoal — Painel Juan</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-size:1.2rem; color:{SUBTITULO_COR};'>Acompanhe sua saúde financeira com estilo e controle.</p>", unsafe_allow_html=True)

# --- FILTRO DE MÊS ---
st.sidebar.markdown("---")
st.sidebar.markdown(f"<span style='color:{TITULO_COR};'>Selecione o mês</span>", unsafe_allow_html=True)
meses_disponiveis = sorted(df['mes'].unique())
if not meses_disponiveis:
    st.warning("Nenhum dado encontrado na base.")
    st.stop()
mes_selecionado = st.sidebar.selectbox("Mês:", meses_disponiveis, index=len(meses_disponiveis)-1)
df_mes = df[df['mes'] == mes_selecionado].copy()

# --- RESUMO DO MÊS ---
ano, mes = map(int, mes_selecionado.split('-'))
primeiro_dia = date(ano, mes, 1)
ultimo_dia = calendar.monthrange(ano, mes)[1]
ultimo_dia_mes = date(ano, mes, ultimo_dia)
datas_do_mes = pd.date_range(primeiro_dia, ultimo_dia_mes)
hoje = date.today()
dias_restantes = max((ultimo_dia_mes - hoje).days + 1, 0) if (ano == hoje.year and mes == hoje.month) else 0
total_entradas = df_mes[df_mes['valor'] > 0]['valor'].sum()
total_saidas = df_mes[df_mes['valor'] < 0]['valor'].sum()
saldo_final_mes = total_entradas + total_saidas
valor_por_dia = saldo_final_mes / dias_restantes if dias_restantes > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Entradas (R$)", f"{total_entradas:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ','))
col2.metric("Saídas (R$)", f"{abs(total_saidas):,.2f}".replace('.', 'X').replace(',', '.').replace('X', ','))
col3.metric("Saldo Final (R$)", f"{saldo_final_mes:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ','))
col4.metric("Dias p/ fim do mês", str(dias_restantes))
col5.metric("Saldo/dia restante", f"R$ {valor_por_dia:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ','))

# --- GRÁFICO POR CATEGORIA ---
st.markdown(f"<h3 style='color:{TITULO_COR};'>Gastos por categoria (apenas despesas)</h3>", unsafe_allow_html=True)
gcat = df_mes[df_mes['valor'] < 0].groupby('categoria')['valor'].sum().sort_values()
if not gcat.empty:
    fig, ax = plt.subplots(figsize=(10, 4))
    bars = ax.barh(gcat.index, gcat.abs(), color=GRAF_COR, alpha=0.85, height=0.55)
    for i, v in enumerate(gcat.abs()):
        ax.text(v + max(gcat.abs()) * 0.012, i, f'R$ {v:,.2f}'.replace('.', 'X').replace(',', '.').replace('X', ','), va='center', color=GRAF_AUX_COR, fontsize=12, fontweight='bold')
    ax.set_title("Despesas por Categoria", color=TITULO_COR, fontsize=13)
    ax.set_xlabel('Valor gasto (R$)', color=TITULO_COR)
    ax.set_ylabel('Categoria', color=TITULO_COR)
    ax.tick_params(colors=TITULO_COR)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.patch.set_facecolor(CUSTOM_BG)
    ax.set_facecolor(CUSTOM_BG)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
else:
    st.info("Nenhuma despesa registrada para esse mês.")

# --- TABELA DE GASTOS ---
st.markdown(f"<h3 style='color:{TITULO_COR};'>Tabela de gastos</h3>", unsafe_allow_html=True)
categorias_unicas = df_mes['categoria'].unique()
cat_filtrada = st.selectbox("Filtrar categoria:", np.append(["Todas"], categorias_unicas))
if cat_filtrada == "Todas":
    df_tabela = df_mes.copy()
    total_filtro = df_mes["valor"].sum()
else:
    df_tabela = df_mes[df_mes['categoria'] == cat_filtrada].copy()
    total_filtro = df_mes[df_mes["categoria"] == cat_filtrada]["valor"].sum()
df_tabela['data'] = df_tabela['data'].dt.strftime('%d/%m/%Y')
df_tabela['valor'] = df_tabela['valor'].apply(lambda x: f"{x:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ','))
st.dataframe(df_tabela[["data", "categoria", "valor"]], use_container_width=True)
st.info(f"Total do filtro atual: R$ {total_filtro:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ','))
