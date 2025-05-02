import streamlit as st
import pandas as pd
from datetime import datetime

BASE_URL = "https://docs.google.com/spreadsheets/d/1VQbm73b0Nmm7vSHhSv99IaxlXiHn70wuqI8Nsbx8xug/gviz/tq?tqx=out:csv&sheet="

st.set_page_config(page_title="Painel de Vendas", layout="centered")

mes_ano = datetime.now().strftime("%B de %Y").title()
st.markdown(f"<h1 style='text-align: center; color: #444;'>📈 Painel de Metas de Vendas</h1>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align: center; color: #666;'>Vendedora: Sarah — {mes_ano}</h4>", unsafe_allow_html=True)
st.markdown("---")

@st.cache_data(ttl=0)
def carregar_aba(nome_aba):
    url = BASE_URL + nome_aba
    return pd.read_csv(url)

df_vendas = carregar_aba("vendas")
df_metas = carregar_aba("metas")

df_vendas.columns = [col.strip().capitalize() for col in df_vendas.columns]
df_metas.columns = [col.strip().capitalize() for col in df_metas.columns]

# Validação
required_vendas = {"Data", "Vendedor", "Valor"}
required_metas = {"Tipo", "Semana", "Valor", "Bonificacao"}

if not required_vendas.issubset(set(df_vendas.columns)):
    st.error("A aba 'vendas' deve conter: Data, Vendedor
