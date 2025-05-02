import streamlit as st
import pandas as pd
import datetime
import locale
from babel.numbers import format_currency

# Configurações de idioma
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
st.set_page_config(page_title="Painel de Metas de Vendas", layout="centered")

# URL da planilha
sheet_url = "https://docs.google.com/spreadsheets/d/1VQbm73b0Nmm7vSHhSv99IaxlXiHn70wuqI8Nsbx8xug/edit#gid=0"
csv_url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")

# URLs das abas
vendas_url = csv_url + "0"           # Primeira aba (vendas)
metas_url = csv_url + "1066610443"   # Segunda aba (metas)

# Carrega os dados
df_vendas = pd.read_csv(vendas_url)
df_metas = pd.read_csv(metas_url)

# Converte colunas de data
df_vendas["Data"] = pd.to_datetime(df_vendas["Data"], dayfirst=True)
df_metas["Inicio"] = pd.to_datetime(df_metas["Inicio"], dayfirst=True, errors="coerce")
df_metas["Fim"] = pd.to_datetime(df_metas["Fim"], dayfirst=True, errors="coerce")

# Corrige valores com vírgulas e pontos
df_metas["Valor"] = pd.to_numeric(df_metas["Valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", "."), errors="coerce")
df_metas["Bonificacao"] = pd.to_numeric(df_metas["Bonificacao"].astype(str).str.replace(".", "", regex=False).str.replace(",", "."), errors="coerce")
df_vendas["Valor"] = pd.to_numeric(df_vendas["Valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", "."), errors="coerce")

# Filtros
vendedor = df_vendas["Vendedor"].iloc[0] if not df_vendas.empty else "Indefinido"
data_atual = datetime.datetime.now().date()

# Cálculo de metas mensais
meta_mensal = df_metas[df_metas["Tipo"] == "Mensal"]["Valor"].sum()
bon_mensal = df_metas[df_metas["Tipo"] == "Mensal"]["Bonificacao"].sum()
vendas_mes = df_vendas[df_vendas["Data"].dt.month == data_atual.month]["Valor"].sum()
progresso_mensal = min(vendas_mes / meta_mensal, 1.0) if meta_mensal > 0 else 0
bonus_mensal_atingido = vendas_mes >= meta_mensal

# Exibição topo
st.title("📈 Painel de Metas de Vendas")
st.markdown(f"**Vendedora:** {vendedor} — {data_atual.strftime('%B de %Y').capitalize()}")

st.markdown("---")
st.subheader("🎯 Meta Mensal")
st.markdown(f"""
- **Total vendido:** {format_currency(vendas_mes, 'BRL', locale='pt_BR')}
- **Meta:** {format_currency(meta_mensal, 'BRL', locale='pt_BR')}
- **Progresso:** {round(progresso_mensal * 100, 1)}%
- **Bonificação:** {"✅" if bonus_mensal_atingido else "❌"} {format_currency(bon_mensal if bonus_mensal_atingido else 0, 'BRL', locale='pt_BR')}
""")
st.progress(progresso_mensal)

# Semana atual com base nas datas preenchidas
semana_atual = None
for _, linha in df_metas[df_metas["Tipo"] == "Semanal"].iterrows():
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
    **Semana {int(semana_atual['Semana'])}:** {format_currency(vendas_semana, 'BRL', locale='pt_BR')} de {format_currency(semana_atual['Valor'], 'BRL', locale='pt_BR')} ({round(progresso_semana*100, 1)}%)
    
    **Bonificação:** {"✅" if bonus_atingido else "❌"} {format_currency(semana_atual['Bonificacao'] if bonus_atingido else 0, 'BRL', locale='pt_BR')}
    """)
    st.progress(progresso_semana)

# Exibe todas as semanas
st.markdown("---")
st.subheader("🗓️ Todas as Metas Semanais")
bonus_total = 0
bonus_ganho = 0

for _, linha in df_metas[df_metas["Tipo"] == "Semanal"].iterrows():
    ini = linha["Inicio"].date()
    fim = linha["Fim"].date()
    vendas = df_vendas[(df_vendas["Data"].dt.date >= ini) & (df_vendas["Data"].dt.date <= fim)]["Valor"].sum()
    progresso = min(vendas / linha["Valor"], 1.0) if linha["Valor"] > 0 else 0
    bonus = linha["Bonificacao"] if vendas >= linha["Valor"] else 0

    bonus_total += linha["Bonificacao"]
    bonus_ganho += bonus

    st.markdown(f"""
    **Semana {int(linha['Semana'])} ({ini.strftime('%d/%m')} a {fim.strftime('%d/%m')}):** {format_currency(vendas, 'BRL', locale='pt_BR')} de {format_currency(linha['Valor'], 'BRL', locale='pt_BR')} ({round(progresso*100, 1)}%)  
    **Bonificação:** {"✅" if bonus > 0 else "❌"} {format_currency(bonus, 'BRL', locale='pt_BR')}
    """)
    st.progress(progresso)

# Resumo de bonificações
st.markdown("---")
st.subheader("💰 Resumo de Bonificações")
st.info(f"""
**Total disponível:** {format_currency(bonus_total + bon_mensal, 'BRL', locale='pt_BR')}  
**Total conquistado:** {format_currency(bonus_ganho + (bon_mensal if bonus_mensal_atingido else 0), 'BRL', locale='pt_BR')}
""")
