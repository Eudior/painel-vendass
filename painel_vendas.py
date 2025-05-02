import streamlit as st
import pandas as pd

# Link para sua planilha no formato CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VQbm73b0Nmm7vSHhSv99IaxlXiHn70wuqI8Nsbx8xug/export?format=csv"

st.title("Painel de Metas de Vendas - Sarah")

@st.cache_data(ttl=600)
def carregar_dados():
    return pd.read_csv(SHEET_URL)

df = carregar_dados()

df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
df['Semana'] = df['Data'].dt.isocalendar().week

# Meta mensal
meta_mensal = 55464.00
vendas_mensais = df['Valor'].sum()
progresso_mensal = min(vendas_mensais / meta_mensal, 1.0)

st.subheader("Meta Mensal")
st.progress(progresso_mensal)
st.write(f"Vendas: R$ {vendas_mensais:,.2f} / Meta: R$ {meta_mensal:,.2f} ({progresso_mensal*100:.2f}%)")

# Metas semanais (por número ISO da semana)
metas_semanais = {
    18: 12643.00,
    19: 11362.00,
    20: 22802.00,
    21: 8658.00
}

for semana, meta in metas_semanais.items():
    vendas = df[df['Semana'] == semana]['Valor'].sum()
    progresso = min(vendas / meta, 1.0) if meta > 0 else 0
    st.subheader(f"Semana {semana}")
    st.progress(progresso)
    st.write(f"Vendas: R$ {vendas:,.2f} / Meta: R$ {meta:,.2f} ({progresso*100:.2f}%)")
