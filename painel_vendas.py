import streamlit as st
import pandas as pd
from datetime import datetime

BASE_URL = "https://docs.google.com/spreadsheets/d/1VQbm73b0Nmm7vSHhSv99IaxlXiHn70wuqI8Nsbx8xug/gviz/tq?tqx=out:csv&sheet="

st.set_page_config(page_title="Painel de Vendas", layout="centered")

# Mês exibido
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
    st.error("A aba 'vendas' deve conter: Data, Vendedor, Valor")
    st.stop()

if not required_metas.issubset(set(df_metas.columns)):
    st.error("A aba 'metas' deve conter: Tipo, Semana, Valor, Bonificacao")
    st.stop()

# Processa dados
df_vendas["Data"] = pd.to_datetime(df_vendas["Data"], dayfirst=True, errors="coerce")
df_vendas["Semana"] = df_vendas["Data"].dt.day.map(lambda d: 1 if d <= 7 else 2 if d <= 14 else 3 if d <= 21 else 4)
semana_hoje = datetime.now().day
semana_atual = 1 if semana_hoje <= 7 else 2 if semana_hoje <= 14 else 3 if semana_hoje <= 21 else 4

# META MENSAL
meta_mensal_row = df_metas[df_metas["Tipo"].str.lower() == "mensal"]
meta_mensal = float(meta_mensal_row["Valor"].values[0])
bonus_mensal = float(meta_mensal_row["Bonificacao"].values[0])
vendas_mensais = df_vendas["Valor"].sum()
progresso_mensal = min(vendas_mensais / meta_mensal, 1.0)
bonus_mensal_conquistado = bonus_mensal if progresso_mensal >= 1 else 0

# VISUAL - MENSAL
st.subheader("🎯 Meta Mensal")
st.markdown(f"""
<div style='background-color: #f9f9f9; padding: 15px; border-radius: 10px;'>
    <b>Total vendido:</b> R$ {vendas_mensais:,.2f}<br>
    <b>Meta:</b> R$ {meta_mensal:,.2f}<br>
    <b>Progresso:</b> {progresso_mensal*100:.1f}%<br>
    <b>Bonificação:</b> {"✅ R$ {:,.2f}".format(bonus_mensal) if progresso_mensal >= 1 else "❌ R$ 0,00"}
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style='margin-top: 10px; height: 30px; background-color: #eee; border-radius: 5px;'>
  <div style='width: {progresso_mensal*100:.1f}%; height: 100%; background-color: #4CAF50; border-radius: 5px; text-align: right; color: white; padding-right: 10px; line-height: 30px;'>
    {progresso_mensal*100:.1f}%
  </div>
</div>
""", unsafe_allow_html=True)

# METAS SEMANAIS
st.markdown("---")
st.subheader("📅 Metas Semanais")

total_bonus_disponivel = bonus_mensal
total_bonus_conquistado = bonus_mensal_conquistado

metas_semanais = df_metas[df_metas["Tipo"].str.lower() == "semanal"]

for _, linha in metas_semanais.iterrows():
    try:
        semana = int(str(linha["Semana"]).strip())
        meta = float(linha["Valor"])
        bonus = float(linha["Bonificacao"])
    except:
        continue

    vendas = df_vendas[df_vendas["Semana"] == semana]["Valor"].sum()
    progresso = min(vendas / meta, 1.0) if meta > 0 else 0
    conquistou = progresso >= 1
    total_bonus_disponivel += bonus
    if conquistou:
        total_bonus_conquistado += bonus

    destaque = "⚡ " if semana == semana_atual else ""
    cor_barra = "#28a745" if conquistou else "#007BFF"

    st.markdown(f"""
    <div style='margin-bottom: 8px;'>
        <b>{destaque}Semana {semana}:</b> R$ {vendas:,.2f} de R$ {meta:,.2f} ({progresso*100:.1f}%)<br>
        <b>Bonificação:</b> {"✅ R$ {:,.2f}".format(bonus) if conquistou else "❌ R$ 0,00"}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='margin-bottom: 25px; height: 25px; background-color: #ddd; border-radius: 5px;'>
      <div style='width: {progresso*100:.1f}%; height: 100%; background-color: {cor_barra}; border-radius: 5px; text-align: right; color: white; padding-right: 8px; line-height: 25px;'>
        {progresso*100:.1f}%
      </div>
    </div>
    """, unsafe_allow_html=True)

# TOTAL DE BONIFICAÇÕES
st.markdown("---")
st.subheader("💰 Resumo de Bonificações")

st.markdown(f"""
<div style='background-color: #f0f8ff; padding: 15px; border-radius: 10px;'>
    <b>Total disponível:</b> R$ {total_bonus_disponivel:,.2f} <br>
    <b>Total conquistado:</b> R$ {total_bonus_conquistado:,.2f}
</div>
""", unsafe_allow_html=True)
