import streamlit as st
import pandas as pd
import datetime as dt
from datetime import datetime
import locale

# ========================
# CONFIGURAÇÕES INICIAIS
# ========================

st.set_page_config(page_title="Painel de Vendas", layout="centered")

# Remove qualquer locale que pode causar erro no Streamlit
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    pass

# ========================
# CARREGAR DADOS
# ========================

# LINK DA PLANILHA NO FORMATO CSV
URL_BASE = "https://docs.google.com/spreadsheets/d/1VQbm73b0Nmm7vSHhSv99laxlXiHn70wuqI8Nsbx8xug/export?format=csv&gid="

URL_VENDAS = URL_BASE + "0"          # aba 'vendas'
URL_METAS = URL_BASE + "1066610443"  # aba 'metas'

# Carregando os dados
df_vendas = pd.read_csv(URL_VENDAS, parse_dates=["Data"], dayfirst=True)
df_metas = pd.read_csv(URL_METAS, dayfirst=True)

# Ajustar formatação numérica (vírgula -> ponto)
df_vendas["Valor"] = df_vendas["Valor"].astype(str).str.replace(",", ".").astype(float)
df_metas["Valor"] = df_metas["Valor"].astype(str).str.replace(",", ".").astype(float)
df_metas["Bonificacao"] = df_metas["Bonificacao"].fillna(0).astype(str).str.replace(",", ".").astype(float)

# Garantir que datas de início e fim existam nas metas semanais
df_metas["Inicio"] = pd.to_datetime(df_metas["Inicio"], dayfirst=True, errors="coerce")
df_metas["Fim"] = pd.to_datetime(df_metas["Fim"], dayfirst=True, errors="coerce")

# ========================
# INÍCIO DA INTERFACE
# ========================

vendedora = df_vendas["Vendedor"].iloc[0]
hoje = dt.date.today()
mes_atual = hoje.strftime('%B').capitalize()
ano_atual = hoje.year

st.title("📈 Painel de Metas de Vendas")
st.markdown(f"**Vendedora:** {vendedora} — {mes_atual} de {ano_atual}")
st.divider()

# ========================
# META MENSAL
# ========================

meta_mensal = df_metas.query("Tipo == 'Mensal'")["Valor"].sum()
bonif_mensal = df_metas.query("Tipo == 'Mensal'")["Bonificacao"].sum()

vendas_mes = df_vendas[df_vendas["Data"].dt.month == hoje.month]["Valor"].sum()
progresso_mensal = min(vendas_mes / meta_mensal, 1.0)

atingiu_bonif_mensal = vendas_mes >= meta_mensal
bonus_mensal = bonif_mensal if atingiu_bonif_mensal else 0

with st.container():
    st.subheader("🎯 Meta Mensal")
    st.markdown(f"""
        <div style='background-color:#f9f9f9;padding:10px;border-radius:8px'>
        <b>Total vendido:</b> R$ {vendas_mes:,.2f}<br>
        <b>Meta:</b> R$ {meta_mensal:,.2f}<br>
        <b>Progresso:</b> {progresso_mensal*100:.1f}%<br>
        <b>Bonificação:</b> {"✅" if atingiu_bonif_mensal else "❌"} R$ {bonus_mensal:,.2f}
        </div>
    """, unsafe_allow_html=True)
    st.progress(progresso_mensal)

# ========================
# SEMANA ATUAL
# ========================

semana_atual = df_metas[
    (df_metas["Tipo"] == "Semanal") &
    (df_metas["Inicio"] <= hoje) &
    (df_metas["Fim"] >= hoje)
]

with st.container():
    st.subheader("🟢 Semana Atual")
    if not semana_atual.empty:
        linha = semana_atual.iloc[0]
        vendas_semana = df_vendas[
            (df_vendas["Data"].dt.date >= linha["Inicio"].date()) &
            (df_vendas["Data"].dt.date <= linha["Fim"].date())
        ]["Valor"].sum()
        progresso = min(vendas_semana / linha["Valor"], 1.0)
        bonus = linha["Bonificacao"] if vendas_semana >= linha["Valor"] else 0

        st.markdown(f"**Semana {linha['Semana']}:** R$ {vendas_semana:,.2f} de R$ {linha['Valor']:,.2f} ({progresso*100:.1f}%)")
        st.markdown(f"**Bonificação:** {'✅' if bonus > 0 else '❌'} R$ {bonus:,.2f}")
        st.progress(progresso)
    else:
        st.info("Nenhuma semana ativa no momento.")

# ========================
# TODAS AS SEMANAIS
# ========================

st.divider()
st.subheader("🗓️ Todas as Metas Semanais")

total_bonificacao = 0
total_conquistado = 0

for _, linha in df_metas[df_metas["Tipo"] == "Semanal"].iterrows():
    vendas = df_vendas[
        (df_vendas["Data"] >= linha["Inicio"]) &
        (df_vendas["Data"] <= linha["Fim"])
    ]["Valor"].sum()

    progresso = min(vendas / linha["Valor"], 1.0)
    bonificacao = linha["Bonificacao"]
    conquistado = bonificacao if vendas >= linha["Valor"] else 0
    total_bonificacao += bonificacao
    total_conquistado += conquistado

    st.markdown(f"**Semana {int(linha['Semana'])} ({linha['Inicio'].strftime('%d/%m')} a {linha['Fim'].strftime('%d/%m')}):** R$ {vendas:,.2f} de R$ {linha['Valor']:,.2f} ({progresso*100:.1f}%)")
    st.markdown(f"Bonificação: {'✅' if conquistado > 0 else '❌'} R$ {conquistado:,.2f}")
    st.progress(progresso)

# ========================
# RESUMO FINAL
# ========================

st.divider()
with st.container():
    st.subheader("💰 Resumo de Bonificações")
    st.markdown(f"""
        <div style='background-color:#f0f8ff;padding:10px;border-radius:8px'>
        <b>Total disponível:</b> R$ {total_bonificacao + bonif_mensal:,.2f}<br>
        <b>Total conquistado:</b> R$ {total_conquistado + bonus_mensal:,.2f}
        </div>
    """, unsafe_allow_html=True)
