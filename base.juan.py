import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import calendar
from datetime import datetime, date

st.set_page_config(page_title="Painel Financeiro - Juan", layout="wide")

# --- AUTENTICAÇÃO ESTILIZADA ---
with st.container():
    st.markdown("""
    <style>
    .password-box {
        max-width: 500px;
        margin: auto;
        padding: 2rem;
        background-color: #1E1E1E;
        border-radius: 1rem;
        box-shadow: 0 0 20px rgba(255, 255, 255, 0.07);
        text-align: center;
    }
    .password-box h2 {
        color: #48a0ff;
        font-size: 2rem;
        margin-bottom: 0.2rem;
    }
    .password-box p {
        color: #ccc;
        margin-top: 0;
        font-size: 0.95rem;
    }
    </style>
    <div class="password-box">
        <h2>🔐 Bem-vindo ao seu painel financeiro</h2>
        <p>Digite a senha para acessar sua visão de fluxo de caixa</p>
    </div>
    """, unsafe_allow_html=True)

senha = st.text_input("", type="password", placeholder="Senha de acesso", key="senha_input")
if senha != "Ju020531":
    st.warning("Acesso negado. Informe a senha correta.")
    st.stop()

# --- LEITURA DOS DADOS VIA GOOGLE SHEETS (ABA 'dados_limpos') ---
sheet_id = "1t8OG-NgtqX-EGvegiUItogajyO9i_dAq-ERnkEKNSS0"
csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=dados_limpos"

try:
    df = pd.read_csv(csv_url)
except Exception as e:
    st.error(f"Erro ao carregar dados do Google Sheets (aba 'dados_limpos'). Verifica se a aba existe e se o acesso está público. Detalhe: {e}")
    st.stop()

# --- FUNÇÃO DE LIMPEZA DE VALOR (trata múltiplos pontos como milhares, último ponto decimal) ---
def clean_valor_string(s):
    s = str(s).strip()
    if s == "" or s.lower() in ["nan", "none"]:
        return np.nan
    s = s.replace(" ", "")
    # trata número com mais de um ponto: junta todos exceto o último como parte inteira
    if s.count(".") > 1:
        parts = s.split(".")
        inteiro = "".join(parts[:-1])
        decimal = parts[-1]
        s = f"{inteiro}.{decimal}"
    try:
        return float(s)
    except:
        return np.nan

# --- AJUSTES DE COLUNAS E TIPOS ---
colunas = {c.lower().strip(): c for c in df.columns}
nome_data = next((colunas[c] for c in colunas if 'data' in c), None)
nome_valor = next((colunas[c] for c in colunas if 'valor' in c), None)
nome_categoria = next((colunas[c] for c in colunas if 'categoria' in c), None)

if not nome_data or not nome_valor or not nome_categoria:
    st.error(f"Colunas obrigatórias não encontradas (data, valor, categoria). Colunas presentes: {list(df.columns)}")
    st.stop()

df = df.rename(columns={nome_data: 'data', nome_valor: 'valor', nome_categoria: 'categoria'})
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df['valor'] = df['valor'].apply(clean_valor_string)
df = df[~df['data'].isna()].copy()
df['mes'] = df['data'].dt.to_period("M").astype(str)

# --- ESTILO E FUNÇÕES DE FORMATAÇÃO ---
CUSTOM_BG = '#181C20'
TITULO_COR = 'white'
SUBTITULO_COR = '#48a0ff'
GRAF_COR = "#003366"
GRAF_AUX_COR = "#48a0ff"

def format_br(x):
    try:
        x = float(x)
        return f"{x:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')
    except:
        return ""

# --- CABEÇALHO ---
st.markdown(f"<h1 style='color:{TITULO_COR}; font-size:2.7rem;'>Fluxo de Caixa Pessoal — Painel Juan</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-size:1.1rem; color:{SUBTITULO_COR};'>Acompanhe sua saúde financeira com estilo, comparação e contexto.</p>", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.markdown(f"<span style='color:{TITULO_COR}; font-weight:600;'>Selecione o mês</span>", unsafe_allow_html=True)
meses_disponiveis = sorted(df['mes'].unique())
if not meses_disponiveis:
    st.warning("Nenhum dado disponível.")
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
col1.metric("Entradas (R$)", format_br(total_entradas))
col2.metric("Saídas (R$)", format_br(abs(total_saidas)))
col3.metric("Saldo Final (R$)", format_br(saldo_final_mes))
col4.metric("Dias p/ fim do mês", str(dias_restantes))
col5.metric("Saldo/dia restante", f"R$ {format_br(valor_por_dia)}")

# --- GRÁFICO DE DESPESAS POR CATEGORIA ---
st.markdown(f"<h3 style='color:{TITULO_COR}; margin-top:1.5rem;'>Gastos por categoria (apenas despesas)</h3>", unsafe_allow_html=True)
gcat = df_mes[df_mes['valor'] < 0].groupby('categoria')['valor'].sum().sort_values()
if not gcat.empty:
    fig, ax = plt.subplots(figsize=(10, 4))
    bars = ax.barh(gcat.index, gcat.abs(), color=GRAF_COR, alpha=0.85, height=0.55)
    for i, v in enumerate(gcat.abs()):
        ax.text(v + max(gcat.abs()) * 0.01, i, f"R$ {format_br(v)}", va='center', color=GRAF_AUX_COR, fontsize=11, fontweight='bold')
    ax.set_title("Despesas por Categoria", color=TITULO_COR, fontsize=14)
    ax.set_xlabel("Valor gasto (R$)", color=TITULO_COR)
    ax.set_ylabel("Categoria", color=TITULO_COR)
    ax.tick_params(colors=TITULO_COR)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.patch.set_facecolor(CUSTOM_BG)
    ax.set_facecolor(CUSTOM_BG)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
else:
    st.info("Nenhuma despesa registrada para esse mês.")

# --- GASTO MÉDIO MENSAL POR CATEGORIA ---
st.markdown(f"<h3 style='color:{TITULO_COR}; margin-top:1.5rem;'>Gasto médio mensal por categoria</h3>", unsafe_allow_html=True)
media_mensal = df[df['valor'] < 0].groupby('categoria')['valor'].mean().abs().reset_index()
media_mensal.columns = ['Categoria', 'Gasto Médio (R$)']
media_mensal['Gasto Médio (R$)'] = media_mensal['Gasto Médio (R$)'].apply(lambda x: f"R$ {format_br(x)}")
st.dataframe(media_mensal, use_container_width=True)

# --- COMPARATIVO MÊS A MÊS (diferença por categoria) ---
st.markdown(f"<h3 style='color:{TITULO_COR}; margin-top:1.5rem;'>Comparativo de gastos por mês (diferença vs mês anterior)</h3>", unsafe_allow_html=True)
gastos_mensais = df[df['valor'] < 0].groupby(['mes', 'categoria'])['valor'].sum().unstack(fill_value=0)
comparativo = gastos_mensais.T.diff(axis=1).T.fillna(0)

def formata_diff(x):
    if x > 0:
        return f"↑ R$ {format_br(abs(x))}"
    elif x < 0:
        return f"↓ R$ {format_br(abs(x))}"
    else:
        return "—"

comparativo_display = comparativo.copy().applymap(formata_diff)
st.dataframe(comparativo_display, use_container_width=True)

# --- TABELA FILTRÁVEL DE GASTOS ---
st.markdown(f"<h3 style='color:{TITULO_COR}; margin-top:1.5rem;'>Tabela de gastos</h3>", unsafe_allow_html=True)
categorias_unicas = df_mes['categoria'].unique()
cat_filtrada = st.selectbox("Filtrar categoria:", np.append(["Todas"], categorias_unicas))
if cat_filtrada == "Todas":
    df_tabela = df_mes.copy()
    total_filtro = df_mes["valor"].sum()
else:
    df_tabela = df_mes[df_mes['categoria'] == cat_filtrada].copy()
    total_filtro = df_mes[df_mes['categoria'] == cat_filtrada]["valor"].sum()

df_tabela['data'] = df_tabela['data'].dt.strftime('%d/%m/%Y')
df_tabela['valor_formatado'] = df_tabela['valor'].apply(lambda x: f"R$ {format_br(x)}")
st.dataframe(df_tabela[["data", "categoria", "valor_formatado"]].rename(columns={"valor_formatado": "valor"}), use_container_width=True)
st.info(f"Total do filtro atual: R$ {format_br(total_filtro)}")

st.markdown("---")

# --- FLUXO DE CAIXA DETALHADO ---
st.markdown(f"<h3 style='color:{TITULO_COR};'>Fluxo de Caixa do mês</h3>", unsafe_allow_html=True)
cats_entradas = [c for c in df_mes['categoria'].unique() if df_mes[df_mes['categoria'] == c]['valor'].sum() > 0]
cats_saidas = [c for c in df_mes['categoria'].unique() if c not in cats_entradas]
cats_entradas.sort()
cats_saidas.sort()

matriz_entrada = pd.DataFrame(index=cats_entradas, columns=datas_do_mes)
for cat in cats_entradas:
    for dt in datas_do_mes:
        valor = df_mes[(df_mes['categoria'] == cat) & (df_mes['data'].dt.date == dt.date())]['valor'].sum()
        matriz_entrada.at[cat, dt] = valor
matriz_entrada = matriz_entrada.fillna(0)

matriz_saida = pd.DataFrame(index=cats_saidas, columns=datas_do_mes)
for cat in cats_saidas:
    for dt in datas_do_mes:
        valor = df_mes[(df_mes['categoria'] == cat) & (df_mes['data'].dt.date == dt.date())]['valor'].sum()
        matriz_saida.at[cat, dt] = valor
matriz_saida = matriz_saida.fillna(0)

linha_branca = pd.DataFrame(index=[''], columns=datas_do_mes)
linha_branca.iloc[:, :] = np.nan

saldos = []
for data_ in datas_do_mes:
    soma_ate_hoje = df_mes[df_mes['data'].dt.date <= data_.date()]['valor'].sum()
    saldos.append(soma_ate_hoje)
saldo_final_df = pd.DataFrame([saldos], index=['Saldo Final'], columns=datas_do_mes)

matriz_final = pd.concat([matriz_entrada, linha_branca, matriz_saida, saldo_final_df])
matriz_final.columns = [d.strftime('%d/%m/%Y') for d in matriz_final.columns]

styled = matriz_final.style.format(lambda x: format_br(x) if pd.notna(x) else "").set_properties(**{
    "background-color": CUSTOM_BG,
    "color": "white",
    "font-family": "monospace"
})
st.dataframe(styled, use_container_width=True)
st.caption("Entradas, separador, saídas e saldo acumulado por dia.")

st.sidebar.caption("Use o painel para tomar decisões melhores.")
