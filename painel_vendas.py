import streamlit as st
import pandas as pd

# Link da planilha em formato CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VQbm73b0Nmm7vSHhSv99IaxlXiHn70wuqI8Nsbx8xug/export?format=csv"

st.set_page_config(page_title="Painel de Metas", layout="centered")
st.title("📊 Painel de Metas de Vendas - Sarah")

# Carrega os dados da planilha
@st.cache_data(ttl=0)
def carregar_dados():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [col.strip().capitalize() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = carregar_dados()

# Validação das colunas
if not all(col in df.columns for col in ["Data", "Vendedor", "Valor"]):
    st.error("Colunas obrigatórias: Data, Vendedor, Valor")
    st.stop()

# Processa os dados
df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors='coerce')
df["Semana"] = df["Data"].dt.isocalendar().week

# Meta mensal
meta_mensal = 55464.00
vendas_mensais = df["Valor"].sum()
progresso_mensal = min(vendas_mensais / meta_mensal, 1.0)

st.subheader("🎯 Meta Mensal")
st.write(f"Vendas: **R$ {vendas_mensais:,.2f}** de R$ {meta_mensal:,.2f}")
st.progress(progresso_mensal)

# Metas semanais fixas (baseadas em semanas ISO)
metas_semanais = {
    18: 12643.00,
    19: 11362.00,
    20: 22802.00,
    21: 8658.00
}

st.markdown("---")
st.subheader("📆 Progresso Semanal")

for semana, meta in metas_semanais.items():
    vendas = df[df["Semana"] == semana]["Valor"].sum()
    progresso = min(vendas / meta, 1.0)
    st.write(f"**Semana {semana}** — Vendas: R$ {vendas:,.2f} / Meta: R$ {meta:,.2f}")
    st.progress(progresso)
