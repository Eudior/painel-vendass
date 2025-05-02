import streamlit as st
import pandas as pd
from datetime import datetime

# URL da planilha pública (substitua se trocar de planilha)
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

# Padroniza nomes de colunas
df_vendas.columns = [col.strip().capitalize() for col in df_vendas.columns]
df_metas.columns = [col.strip().capitalize() for col in df_metas.columns]

# Verificações mínimas
if not {"Data", "Vendedor", "Valor"}.issubset(df_vendas.columns):
    st.error("A aba 'vendas' deve conter as colunas: Data, Vendedor, Valor.")
    st.stop()

if not {"Tipo", "Semana", "Inicio", "Fim", "Valor", "Bonificacao"}.issubset(df_metas.columns):
    st.error("A aba 'metas' deve conter as colunas: Tipo, Semana, Inicio, Fim, Valor, Bonificacao.")
    st.stop()

# Converte datas
df_vendas["Data"] = pd.to_datetime(df_vendas["Data"], dayfirst=True, errors="coerce")
df_metas["Inicio"] = pd.to_datetime(df_metas["Inicio"], dayfirst=True, errors="coerce")
df_metas["Fim"] = pd.to_datetime(df_metas["Fim"], dayfirst=True, errors="coerce")

# Busca meta mensal
meta_mensal_row = df_metas[df_metas["Tipo"].str.lower() == "mensal"]
if meta_mensal_row.empty:
    st.warning("⚠️ Nenhuma meta mensal encontrada.")
    st.stop()

meta_mensal = float(meta_mensal_row["Valor"].values[0])
bonus_mensal = float(meta_mensal_row["Bonificacao"].values[0])
data_inicio_mes = meta_mensal_row["Inicio"].values[0]
data_fim_mes = meta_mensal_row["Fim"].values[0]

vendas_mes = df_vendas[
    (df_vendas["Data"] >= data_inicio_mes) &
    (df_vendas["Data"] <= data_fim_mes)
]["Valor"].sum()

progresso_mensal = min(vendas_mes / meta_mensal, 1.0)
bonus_mensal_ganho = bonus_mensal if progresso_mensal >= 1 else 0

# Exibição mensal
st.subheader("🎯 Meta Mensal")
st.markdown(f"""
<div style='background-color: #f9f9f9; padding: 15px; border-radius: 10px;'>
<b>Total vendido:</b> R$ {vendas_mes:,.2f}<br>
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

# Identifica semana atual com base na data de hoje
hoje = datetime.now().date()
semana_atual = df_metas[
    (df_metas["Tipo"].str.lower() == "semanal") &
    (df_metas["Inicio"].dt.date <= hoje) &
    (df_metas["Fim"].dt.date >= hoje)
]

# Bonificação total
bonus_total = bonus_mensal
bonus_conquistado = bonus_mensal_ganho

# Semana atual
st.markdown("---")
st.subheader("🟢 Semana Atual")

if not semana_atual.empty:
    linha = semana_atual.iloc[0]
    semana = int(linha["Semana"])
    meta = float(linha["Valor"])
    bonus = float(linha["Bonificacao"])
    vendas = df_vendas[
        (df_vendas["Data"] >= linha["Inicio"]) &
        (df_vendas["Data"] <= linha["Fim"])
    ]["Valor"].sum()

    progresso = min(vendas / meta, 1.0) if meta > 0 else 0
    conquistou = progresso >= 1
    bonus_total += bonus
    if conquistou:
        bonus_conquistado += bonus

    cor = "#28a745" if conquistou else "#007BFF"

    st.markdown(f"""
    <b>Semana {semana}:</b> R$ {vendas:,.2f} de R$ {meta:,.2f} ({progresso*100:.1f}%)<br>
    <b>Bonificação:</b> {"✅ R$ {:,.2f}".format(bonus) if conquistou else "❌ R$ 0,00"}
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='margin-top: 5px; height: 25px; background-color: #ddd; border-radius: 5px;'>
      <div style='width: {progresso*100:.1f}%; height: 100%; background-color: {cor}; border-radius: 5px; text-align: right; color: white; padding-right: 8px; line-height: 25px;'>
        {progresso*100:.1f}%
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Nenhuma semana atual dentro do período de hoje.")

# Exibe todas as metas semanais
st.markdown("---")
st.subheader("📅 Todas as Metas Semanais")

df_semanas = df_metas[df_metas["Tipo"].str.lower() == "semanal"]

for _, linha in df_semanas.iterrows():
    try:
        semana = int(str(linha["Semana"]).strip())
        meta = float(linha["Valor"])
        bonus = float(linha["Bonificacao"])
        vendas = df_vendas[
            (df_vendas["Data"] >= linha["Inicio"]) &
            (df_vendas["Data"] <= linha["Fim"])
        ]["Valor"].sum()
    except:
        continue

    progresso = min(vendas / meta, 1.0) if meta > 0 else 0
    conquistou = progresso >= 1
    bonus_total += bonus
    if conquistou:
        bonus_conquistado += bonus

    cor = "#28a745" if conquistou else "#007BFF"

    st.markdown(f"""
    <b>Semana {semana} ({linha["Inicio"].date():%d/%m} a {linha["Fim"].date():%d/%m}):</b> R$ {vendas:,.2f} de R$ {meta:,.2f} ({progresso*100:.1f}%)<br>
    <b>Bonificação:</b> {"✅ R$ {:,.2f}".format(bonus) if conquistou else "❌ R$ 0,00"}
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='margin-bottom: 25px; height: 25px; background-color: #ddd; border-radius: 5px;'>
      <div style='width: {progresso*100:.1f}%; height: 100%; background-color: {cor}; border-radius: 5px; text-align: right; color: white; padding-right: 8px; line-height: 25px;'>
        {progresso*100:.1f}%
      </div>
    </div>
    """, unsafe_allow_html=True)

# Resumo final
st.markdown("---")
st.subheader("💰 Resumo de Bonificações")
st.markdown(f"""
<div style='background-color: #f0f8ff; padding: 15px; border-radius: 10px;'>
<b>Total disponível:</b> R$ {bonus_total:,.2f} <br>
<b>Total conquistado:</b> R$ {bonus_conquistado:,.2f}
</div>
""", unsafe_allow_html=True)
