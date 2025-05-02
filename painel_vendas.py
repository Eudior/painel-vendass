import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Painel de Metas de Vendas", layout="centered")

# Função para traduzir mês para português
def formatar_data_extenso(data):
    return data.strftime("%d de %B de %Y").replace("January", "janeiro").replace("February", "fevereiro").replace("March", "março") \
        .replace("April", "abril").replace("May", "maio").replace("June", "junho") \
        .replace("July", "julho").replace("August", "agosto").replace("September", "setembro") \
        .replace("October", "outubro").replace("November", "novembro").replace("December", "dezembro")

# URL da planilha
sheet_url = "https://docs.google.com/spreadsheets/d/1VQbm73b0Nmm7vSHhSv99IaxlXiHn70wuqI8Nsbx8xug/edit#gid=0"
csv_url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")

# URLs das abas
vendas_url = csv_url + "0"
metas_url = csv_url + "1066610443"

# Carrega dados
df_vendas = pd.read_csv(vendas_url)
df_metas = pd.read_csv(metas_url)

# Converte datas
df_vendas["Data"] = pd.to_datetime(df_vendas["Data"], dayfirst=True)
df_metas["Inicio"] = pd.to_datetime(df_metas["Inicio"], dayfirst=True, errors="coerce")
df_metas["Fim"] = pd.to_datetime(df_metas["Fim"], dayfirst=True, errors="coerce")

# Corrige números com vírgula/ponto
df_metas["Valor"] = pd.to_numeric(df_metas["Valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", "."), errors="coerce")
df_metas["Bonificacao"] = pd.to_numeric(df_metas["Bonificacao"].astype(str).str.replace(".", "", regex=False).str.replace(",", "."), errors="coerce")
df_vendas["Valor"] = pd.to_numeric(df_vendas["Valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", "."), errors="coerce")

# Variáveis principais
vendedor = df_vendas["Vendedor"].iloc[0] if not df_vendas.empty else "Indefinido"
data_atual = datetime.now().date()

# Meta mensal
meta_mensal = df_metas[df_metas["Tipo"].str.lower() == "mensal"]["Valor"].sum()
bon_mensal = df_metas[df_metas["Tipo"].str.lower() == "mensal"]["Bonificacao"].sum()
vendas_mes = df_vendas[df_vendas["Data"].dt.month == data_atual.month]["Valor"].sum()
progresso_mensal = min(vendas_mes / meta_mensal, 1.0) if meta_mensal > 0 else 0
bonus_mensal_atingido = vendas_mes >= meta_mensal

# Exibição topo
st.title("📈 Painel de Metas de Vendas")
st.markdown(f"**Vendedora:** {vendedor} — {formatar_data_extenso(data_atual)[3:]}")

st.markdown("---")
st.subheader("🎯 Meta Mensal")
st.markdown(f"""
- **Total vendido:** R$ {vendas_mes:,.2f}
- **Meta:** R$ {meta_mensal:,.2f}
- **Progresso:** {round(progresso_mensal * 100, 1)}%
- **Bonificação:** {"✅" if bonus_mensal_atingido else "❌"} R$ {bon_mensal if bonus_mensal_atingido else 0:,.2f}
""")
st.progress(progresso_mensal)

# Semana atual
semana_atual = None
for _, linha in df_metas[df_metas["Tipo"].str.lower() == "semanal"].iterrows():
    if linha["Inicio"].date() <= data_atual <= linha["Fim"].date():
        semana_atual = linha
        break

if semana_atual is not None:
    vendas_semana = df_vendas[(df_vendas["Data"].dt.date >= semana_atual["Inicio"].date()) &
                               (df_vendas["Data"].dt.date <= semana_atual["Fim"].date())]["Valor"].sum()
    progresso_semana = min(vendas_semana / semana_atual["Valor"], 1.0) if semana_atual["Valor"] > 0 else 0
    bonus_atingido = vendas_semana >= semana_atual["Valor"]

    st.markdown("---")
    st.subheader("🟢 Semana Atual")
    st.markdown(f"""
    **Semana {int(semana_atual['Semana'])}:** R$ {vendas_semana:,.2f} de R$ {semana_atual['Valor']:,.2f} ({round(progresso_semana*100, 1)}%)  
    **Bonificação:** {"✅" if bonus_atingido else "❌"} R$ {semana_atual['Bonificacao'] if bonus_atingido else 0:,.2f}
    """)
    st.progress(progresso_semana)

# Metas semanais completas
st.markdown("---")
st.subheader("🗓️ Todas as Metas Semanais")
bonus_total = 0
bonus_ganho = 0

for _, linha in df_metas[df_metas["Tipo"].str.lower() == "semanal"].iterrows():
    ini = linha["Inicio"].date()
    fim = linha["Fim"].date()
    vendas = df_vendas[(df_vendas["Data"].dt.date >= ini) & (df_vendas["Data"].dt.date <= fim)]["Valor"].sum()
    progresso = min(vendas / linha["Valor"], 1.0) if linha["Valor"] > 0 else 0
    bonus = linha["Bonificacao"] if vendas >= linha["Valor"] else 0

    bonus_total += linha["Bonificacao"]
    bonus_ganho += bonus

    st.markdown(f"""
    **Semana {int(linha['Semana'])} ({ini.strftime('%d/%m')} a {fim.strftime('%d/%m')}):** R$ {vendas:,.2f} de R$ {linha['Valor']:,.2f} ({round(progresso*100, 1)}%)  
    **Bonificação:** {"✅" if bonus > 0 else "❌"} R$ {bonus:,.2f}
    """)
    st.progress(progresso)

# Resumo de bonificações
st.markdown("---")
st.subheader("💰 Resumo de Bonificações")
st.info(f"""
**Total disponível:** R$ {bonus_total + bon_mensal:,.2f}  
**Total conquistado:** R$ {bonus_ganho + (bon_mensal if bonus_mensal_atingido else 0):,.2f}
""")
