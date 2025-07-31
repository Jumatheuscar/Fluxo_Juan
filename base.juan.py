import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import calendar
from datetime import datetime, date

# Define aqui o nome do arquivo .xlsx que está na pasta
ARQUIVO_DADOS = r"C:\Users\juanc\OneDrive\Juan\Financeiro\teste py\extrato.xlsx"  # Troque pelo nome do seu arquivo (.xlsx) se for diferente
#abc
# --- Leitura do Excel, tratamento automático ---
try:
    df = pd.read_excel(ARQUIVO_DADOS)
except Exception as e:
    st.error(f"Erro ao ler o arquivo {ARQUIVO_DADOS}: {e}")
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

# --- Ajustes de tipo ---
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df[~df['data'].isna()].copy()
df['mes'] = df['data'].dt.to_period("M").astype(str)

# --- Customização de cores e títulos ---
CUSTOM_BG = '#181C20'
TITULO_COR = 'white'
SUBTITULO_COR = '#48a0ff'
METRIC_COR = 'white'
GRAF_COR = "#003366"
GRAF_AUX_COR = "#48a0ff"

st.markdown(
    f"<h1 style='color:{TITULO_COR}; font-size:2.7rem;'>Fluxo de Caixa Pessoal — Painel Juan</h1>",
    unsafe_allow_html=True
)
st.markdown(
    f"<p style='font-size:1.2rem; color:{SUBTITULO_COR};'>Acompanhe sua saúde financeira com estilo e controle.</p>",
    unsafe_allow_html=True
)
st.sidebar.markdown("---")
st.sidebar.markdown(f"<span style='color:{TITULO_COR};'>Selecione o mês</span>", unsafe_allow_html=True)

# --- FILTRO DE MÊS ---
meses_disponiveis = sorted(df['mes'].unique())
if not meses_disponiveis:
    st.warning("Nenhum dado encontrado na base.")
    st.stop()
mes_selecionado = st.sidebar.selectbox("Mês:", meses_disponiveis, index=len(meses_disponiveis)-1)
df_mes = df[df['mes'] == mes_selecionado].copy()

# --- DADOS PARA RESUMO DO MÊS ---
ano, mes = map(int, mes_selecionado.split('-'))
primeiro_dia = date(ano, mes, 1)
ultimo_dia = calendar.monthrange(ano, mes)[1]
ultimo_dia_mes = date(ano, mes, ultimo_dia)
datas_do_mes = pd.date_range(primeiro_dia, ultimo_dia_mes)
hoje = date.today()
if (ano < hoje.year) or (ano == hoje.year and mes < hoje.month):
    dias_restantes = 0
else:
    dias_restantes = max((ultimo_dia_mes - hoje).days + 1, 0) if (ano == hoje.year and mes == hoje.month) else ultimo_dia
total_entradas = df_mes[df_mes['valor'] > 0]['valor'].sum()
total_saidas = df_mes[df_mes['valor'] < 0]['valor'].sum()
saldo_final_mes = total_entradas + total_saidas
valor_por_dia = saldo_final_mes / dias_restantes if dias_restantes > 0 else 0

# --- RESUMO DO MÊS ---
st.markdown(f"<h3 style='color:{TITULO_COR};'>Resumo do mês selecionado</h3>", unsafe_allow_html=True)
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
st.markdown("---")

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
st.markdown("---")

# --- FLUXO DE CAIXA DO MÊS ---
st.markdown(f"<h3 style='color:{TITULO_COR};'>Fluxo de Caixa do mês</h3>", unsafe_allow_html=True)
cats_entradas = [c for c in df_mes['categoria'].unique() if df_mes[df_mes['categoria'] == c]['valor'].sum() > 0]
cats_saidas = [c for c in df_mes['categoria'].unique() if c not in cats_entradas]
cats_entradas.sort()
cats_saidas.sort()
matriz_entrada = pd.DataFrame(index=cats_entradas, columns=datas_do_mes)
for cat in cats_entradas:
    for dt in datas_do_mes:
        valor = df_mes[(df_mes['categoria'] == cat) & (df_mes['data'] == dt)]['valor'].sum()
        matriz_entrada.at[cat, dt] = valor
matriz_entrada = matriz_entrada.fillna(0)
matriz_saida = pd.DataFrame(index=cats_saidas, columns=datas_do_mes)
for cat in cats_saidas:
    for dt in datas_do_mes:
        valor = df_mes[(df_mes['categoria'] == cat) & (df_mes['data'] == dt)]['valor'].sum()
        matriz_saida.at[cat, dt] = valor
matriz_saida = matriz_saida.fillna(0)
linha_branca = pd.DataFrame(index=[''], columns=datas_do_mes)
linha_branca.iloc[:, :] = np.nan
matriz = pd.concat([matriz_entrada, linha_branca, matriz_saida])
saldos = []
for data_ in datas_do_mes:
    soma_ate_hoje = df_mes[df_mes['data'].dt.date <= data_.date()]['valor'].sum()
    saldos.append(soma_ate_hoje)
saldo_final_df = pd.DataFrame([saldos], index=['Saldo Final'], columns=datas_do_mes)
matriz_final = pd.concat([matriz, saldo_final_df])

def format_br(x):
    try:
        x = float(x)
        return f"{x:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')
    except Exception:
        return ""

matriz_final.columns = [d.strftime('%d/%m/%Y') for d in matriz_final.columns]
st.dataframe(
    matriz_final.style.format(format_br),
    use_container_width=True
)

st.caption("Entradas, linha separadora, saídas e saldo final até o último dia do mês. Painel largo e funcional.")
st.sidebar.caption("Use o painel para tomar decisões melhores.")





