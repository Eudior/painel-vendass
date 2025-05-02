import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# --- Configuração da Página e Título ---
st.set_page_config(page_title="Painel de Metas de Vendas", layout="wide")
st.title("📊 Painel de Metas de Vendas")

# --- Constantes e Configurações ---
# Extrair ID da planilha da URL fornecida
GOOGLE_SHEET_URL_PROVIDED = "https://docs.google.com/spreadsheets/d/1bnqOqnJ3C9SXpJZ6txLtOu-pI7NYb6Yy/"
# Extraindo o ID de forma mais robusta
try:
    sheet_id = GOOGLE_SHEET_URL_PROVIDED.split("/d/")[1].split("/")[0]
except IndexError:
    st.error("Não foi possível extrair o ID da planilha da URL fornecida.")
    st.stop()

BASE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="
DEFAULT_VENDEDOR = "Sarah" # Pode ser alterado ou selecionado dinamicamente no futuro

# --- Carregamento de Dados via URL CSV --- 
@st.cache_data(ttl=600) # Cache por 10 minutos
def load_data_from_csv(sheet_name):
    try:
        csv_url = BASE_CSV_URL + urllib.parse.quote(sheet_name)
        df = pd.read_csv(csv_url)
        st.success(f"Dados da aba ", sheet_name, " carregados com sucesso via CSV URL!")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da aba ", sheet_name, " via URL CSV: {e}. Verifique se a planilha está compartilhada como \"Qualquer pessoa com o link pode visualizar\" e se o nome da aba está correto.")
        return pd.DataFrame()

metas_df_raw = load_data_from_csv("Metas")
vendas_df_raw = load_data_from_csv("Vendas")

# --- Pré-processamento e Lógica Principal --- 
if not metas_df_raw.empty and not vendas_df_raw.empty:
    metas_df = metas_df_raw.copy()
    vendas_df = vendas_df_raw.copy()
    try:
        # --- Pré-processamento --- 
        # Renomear colunas para garantir consistência (remover espaços extras, capitalizar)
        metas_df.columns = [col.strip() for col in metas_df.columns]
        vendas_df.columns = [col.strip() for col in vendas_df.columns]
        
        # Verificar colunas essenciais
        required_metas_cols = {"Ano", "Mês", "Vendedor", "Meta_Mensal", "Bonus_Mensal", "Semana", "Inicio_Semana", "Fim_Semana", "Meta_Semanal", "Bonus_Semanal"}
        required_vendas_cols = {"Data", "Vendedor", "Valor"}
        
        if not required_metas_cols.issubset(metas_df.columns):
            st.error(f"Colunas faltando na aba \"Metas\". Necessário: {required_metas_cols}. Encontrado: {set(metas_df.columns)}")
            st.stop()
        if not required_vendas_cols.issubset(vendas_df.columns):
            st.error(f"Colunas faltando na aba \"Vendas\". Necessário: {required_vendas_cols}. Encontrado: {set(vendas_df.columns)}")
            st.stop()

        # Converter colunas de data para datetime
        metas_df["Inicio_Semana"] = pd.to_datetime(metas_df["Inicio_Semana"], dayfirst=True, errors=\'coerce\')
        metas_df["Fim_Semana"] = pd.to_datetime(metas_df["Fim_Semana"], dayfirst=True, errors=\'coerce\')
        vendas_df["Data"] = pd.to_datetime(vendas_df["Data"], dayfirst=True, errors=\'coerce\')
        
        # Remover linhas onde a conversão de data falhou
        metas_df.dropna(subset=["Inicio_Semana", "Fim_Semana"], inplace=True)
        vendas_df.dropna(subset=["Data"], inplace=True)

        # Converter colunas numéricas (tratando possíveis erros e vírgulas)
        cols_numericas_metas = ["Meta_Mensal", "Bonus_Mensal", "Meta_Semanal", "Bonus_Semanal"]
        for col in cols_numericas_metas:
            # Tratar strings com vírgula como separador decimal antes de converter
            if metas_df[col].dtype == \'object\':
                 metas_df[col] = metas_df[col].astype(str).str.replace(\\,\".\", regex=False)
            metas_df[col] = pd.to_numeric(metas_df[col], errors=\'coerce\').fillna(0)
            
        cols_numericas_vendas = ["Valor"]
        for col in cols_numericas_vendas:
             if vendas_df[col].dtype == \'object\':
                 vendas_df[col] = vendas_df[col].astype(str).str.replace(\\,\".\", regex=False)
             vendas_df[col] = pd.to_numeric(vendas_df[col], errors=\'coerce\').fillna(0)

        # Converter colunas de Ano e Mês para numérico em Metas
        metas_df["Ano"] = pd.to_numeric(metas_df["Ano"], errors=\'coerce\').fillna(0).astype(int)
        metas_df["Mês"] = pd.to_numeric(metas_df["Mês"], errors=\'coerce\').fillna(0).astype(int)

    except Exception as e:
        st.error(f"Erro durante o pré-processamento dos dados: {e}")
        st.stop()

    # --- Lógica Principal (continua igual) --- 
    # Obter data atual
    hoje = datetime.now().date()
    mes_atual = hoje.month
    ano_atual = hoje.year

    st.subheader(f"Vendedora: {DEFAULT_VENDEDOR} — {hoje.strftime(\'%B de %Y\')}")

    # Filtrar dados para o mês/ano/vendedor atual
    metas_mes_atual = metas_df[
        (metas_df["Ano"] == ano_atual) &
        (metas_df["Mês"] == mes_atual) &
        (metas_df["Vendedor"] == DEFAULT_VENDEDOR)
    ].copy()
    
    vendas_mes_atual = vendas_df[
        (vendas_df["Data"].dt.year == ano_atual) &
        (vendas_df["Data"].dt.month == mes_atual) &
        (vendas_df["Vendedor"] == DEFAULT_VENDEDOR)
    ].copy()

    if metas_mes_atual.empty:
        st.warning(f"Nenhuma meta encontrada para {DEFAULT_VENDEDOR} em {mes_atual}/{ano_atual}.")
    else:
        # --- Meta Mensal ---
        st.markdown("## 🎯 Meta Mensal")
        meta_mensal_valor = metas_mes_atual["Meta_Mensal"].iloc[0]
        bonus_mensal_valor = metas_mes_atual["Bonus_Mensal"].iloc[0]
        total_vendido_mes = vendas_mes_atual["Valor"].sum()
        progresso_mensal = (total_vendido_mes / meta_mensal_valor) * 100 if meta_mensal_valor > 0 else 0
        bonus_mensal_atingido = total_vendido_mes >= meta_mensal_valor

        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("Total vendido", f"R$ {total_vendido_mes:,.2f}".replace(",", "."))
            st.metric("Meta", f"R$ {meta_mensal_valor:,.2f}".replace(",", "."))
            st.metric("Progresso", f"{progresso_mensal:.1f}%")
            bonus_txt = f"✅ R$ {bonus_mensal_valor:,.2f}".replace(",", ".") if bonus_mensal_atingido else f"❌ R$ {bonus_mensal_valor:,.2f}".replace(",", ".")
            st.metric("Bonificação", bonus_txt)
        with col2:
            st.progress(min(progresso_mensal / 100, 1.0))

        st.divider()

        # --- Semana Atual ---
        st.markdown("## 🟢 Semana Atual")
        # Certifique-se que \'hoje\' é um objeto date, não datetime
        hoje_date = hoje if isinstance(hoje, datetime.date.__class__) else hoje.date()
        semana_atual_df = metas_mes_atual[
            (metas_mes_atual["Inicio_Semana"].dt.date <= hoje_date) &
            (metas_mes_atual["Fim_Semana"].dt.date >= hoje_date)
        ]

        if not semana_atual_df.empty:
            semana_atual_info = semana_atual_df.iloc[0]
            inicio_sem = semana_atual_info["Inicio_Semana"].strftime("%d/%m")
            fim_sem = semana_atual_info["Fim_Semana"].strftime("%d/%m")
            meta_sem_valor = semana_atual_info["Meta_Semanal"]
            bonus_sem_valor = semana_atual_info["Bonus_Semanal"]
            num_semana = semana_atual_info["Semana"]

            vendas_semana_atual = vendas_mes_atual[
                (vendas_mes_atual["Data"] >= semana_atual_info["Inicio_Semana"]) &
                (vendas_mes_atual["Data"] <= semana_atual_info["Fim_Semana"])
            ]
            total_vendido_sem = vendas_semana_atual["Valor"].sum()
            progresso_sem = (total_vendido_sem / meta_sem_valor) * 100 if meta_sem_valor > 0 else 0
            bonus_sem_atingido = total_vendido_sem >= meta_sem_valor

            st.write(f"**Semana {num_semana} ({inicio_sem} a {fim_sem})**")
            col1_sem, col2_sem = st.columns([3, 1])
            with col1_sem:
                st.metric("Vendido na Semana", f"R$ {total_vendido_sem:,.2f}".replace(",", "."))
                st.metric("Meta Semanal", f"R$ {meta_sem_valor:,.2f}".replace(",", "."))
                bonus_sem_txt = f"✅ R$ {bonus_sem_valor:,.2f}".replace(",", ".") if bonus_sem_atingido else f"❌ R$ {bonus_sem_valor:,.2f}".replace(",", ".")
                st.metric("Bonificação Semanal", bonus_sem_txt)
            with col2_sem:
                st.progress(min(progresso_sem / 100, 1.0))
                st.write(f"{progresso_sem:.1f}% atingido")
        else:
            st.info("Não há informações de meta para a semana atual.")

        st.divider()

        # --- Todas as Metas Semanais ---
        st.markdown(f"## 🗓️ Todas as Metas Semanais de {hoje.strftime(\'%B\')}")
        total_bonus_semanal_ganho = 0

        for index, semana_info in metas_mes_atual.sort_values(by="Semana").iterrows():
            inicio_sem = semana_info["Inicio_Semana"].strftime("%d/%m")
            fim_sem = semana_info["Fim_Semana"].strftime("%d/%m")
            meta_sem_valor = semana_info["Meta_Semanal"]
            bonus_sem_valor = semana_info["Bonus_Semanal"]
            num_semana = semana_info["Semana"]

            vendas_na_semana = vendas_mes_atual[
                (vendas_mes_atual["Data"] >= semana_info["Inicio_Semana"]) &
                (vendas_mes_atual["Data"] <= semana_info["Fim_Semana"])
            ]
            total_vendido_sem = vendas_na_semana["Valor"].sum()
            progresso_sem = (total_vendido_sem / meta_sem_valor) * 100 if meta_sem_valor > 0 else 0
            bonus_sem_atingido = total_vendido_sem >= meta_sem_valor
            if bonus_sem_atingido:
                total_bonus_semanal_ganho += bonus_sem_valor

            st.write(f"**Semana {num_semana} ({inicio_sem} a {fim_sem})**")
            col1_ts, col2_ts = st.columns([3, 1])
            with col1_ts:
                st.write(f"Vendido: R$ {total_vendido_sem:,.2f} / Meta: R$ {meta_sem_valor:,.2f} ({progresso_sem:.1f}%)".replace(",", "."))
                bonus_sem_txt = f"✅ R$ {bonus_sem_valor:,.2f}".replace(",", ".") if bonus_sem_atingido else f"❌ R$ {bonus_sem_valor:,.2f}".replace(",", ".")
                st.write(f"Bonificação: {bonus_sem_txt}")
            with col2_ts:
                st.progress(min(progresso_sem / 100, 1.0))
            st.write("---") # Separador visual entre semanas

        st.divider()
        # --- Resumo Bonificações ---
        st.markdown("## 💰 Resumo Bonificações do Mês")
        bonus_mensal_ganho = bonus_mensal_valor if bonus_mensal_atingido else 0
        total_bonus = total_bonus_semanal_ganho + bonus_mensal_ganho

        st.metric("Total Bônus Semanais Ganhos", f"R$ {total_bonus_semanal_ganho:,.2f}".replace(",", "."))
        st.metric("Bônus Mensal Ganho", f"R$ {bonus_mensal_ganho:,.2f}".replace(",", "."))
        st.metric("**Total de Bônus no Mês**", f"**R$ {total_bonus:,.2f}**".replace(",", "."))

else:
    # Exibir mensagem apenas se os dataframes estiverem vazios APÓS a tentativa de carregamento
    st.error("Não foi possível carregar os dados de uma ou ambas as abas da planilha (Metas, Vendas). Verifique as mensagens de erro acima, o compartilhamento da planilha e os nomes das abas.")

# --- Rodapé ---
st.caption("Desenvolvido por Manus (versão simplificada)")

