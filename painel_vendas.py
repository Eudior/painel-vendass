import streamlit as st
import pandas as pd

# URL base das abas
BASE_URL = "https://docs.google.com/spreadsheets/d/1VQbm73b0Nmm7vSHhSv99IaxlXiHn70wuqI8Nsbx8xug/gviz/tq?tqx=out:csv&sheet="

# Configurações de página
st.set_page_config(page_title="Painel de Vendas", layout="centered")
st.markdown("<h1 style='text-align: center; color: #444;'>📈 Painel de Metas de Vendas</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #888;'>Vendedora: Sarah</h3>", unsafe_allow_html=True)
st.markdown("---")

# Função para carregar abas
@st.cache_data(ttl=0)
def carregar_aba(nome_aba):
    url = BASE_URL + nome_aba
    return pd.read_csv(url)

# Carrega dados
df_vendas = carregar_aba("vendas")
df_metas = carregar_aba("metas")

# Normaliza colunas
df_vendas.columns = [col.strip().capitalize() for col in df_vendas.columns]
df_metas.columns = [col.strip().capitalize() for col in df_metas.columns]

# Valida colunas
if not all(col in df_vendas.columns for col in ["Data", "Vendedor", "Valor"]):
    st.error("A aba 'vendas' precisa conter: Data, Vendedor, Valor")
    st.stop()

if not all(col in df_metas.columns for col in ["Tipo", "Semana", "Valor"]):
    st.error("A aba 'metas' precisa conter: Tipo, Semana, Valor")
    st.stop()

# Processa vendas
df_vendas["Data"] = pd.to_datetime(df_vendas["Data"], dayfirst=True, errors="coerce")
df_vendas["Semana"] = df_vendas["Data"].dt.isocalendar().week
df_vendas["Ano"] = df_vendas["Data"].dt.year

# ==== METAS ====
meta_mensal_row = df_metas[df_metas["Tipo"].str.lower() == "mensal"]
meta_mensal = float(meta_mensal_row["Valor"].values[0]) if not meta_mensal_row.empty else 0
vendas_mensais = df_vendas["Valor"].sum()
progresso_mensal = min(vendas_mensais / meta_mensal, 1.0) if meta_mensal > 0 else 0

# ==== VISUAL MENSAL ====
st.markdown("### 🎯 Meta Mensal")
st.markdown(f"""
<div style='background-color: #f9f9f9; padding: 15px; border-radius: 10px;'>
    <b>Total vendido:</b> R$ {vendas_mensais:,.2f} <br>
    <b>Meta mensal:</b> R$ {meta_mensal:,.2f} <br>
    <b>Progresso:</b> {progresso_mensal*100:.1f}%
</div>
""", unsafe_allow_html=True)

# Barra de progresso mais grossa
st.markdown(f"""
<div style='margin-top: 10px; height: 30px; background-color: #eee; border-radius: 5px;'>
  <div style='width: {progresso_mensal*100:.1f}%; height: 100%; background-color: #4CAF50; border-radius: 5px; text-align: right; color: white; padding-right: 10px; line-height: 30px;'>
    {progresso_mensal*100:.1f}%
  </div>
</div>
""", unsafe_allow_html=True)

# ==== VISUAL SEMANAL ====
st.markdown("---")
st.markdown("### 📅 Metas Semanais")

metas_semanais = df_metas[df_metas["Tipo"].str.lower() == "semanal"]

for _, linha in metas_semanais.iterrows():
    semana = int(linha["Semana"])
    meta = float(linha["Valor"])
    vendas = df_vendas[df_vendas["Semana"] == semana]["Valor"].sum()
    progresso = min(vendas / meta, 1.0) if meta > 0 else 0

    st.markdown(f"""
    <div style='margin-bottom: 8px;'>
        <b>Semana {semana}:</b> R$ {vendas:,.2f} de R$ {meta:,.2f} ({progresso*100:.1f}%)
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='margin-bottom: 25px; height: 25px; background-color: #ddd; border-radius: 5px;'>
      <div style='width: {progresso*100:.1f}%; height: 100%; background-color: #2196F3; border-radius: 5px; text-align: right; color: white; padding-right: 8px; line-height: 25px;'>
        {progresso*100:.1f}%
      </div>
    </div>
    """, unsafe_allow_html=True)
