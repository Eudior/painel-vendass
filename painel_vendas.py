import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import json
import os

# --- Configuração da Página e Título ---
st.set_page_config(page_title="Painel de Metas de Vendas", layout="wide")
st.title("📊 Painel de Metas de Vendas")

# --- Constantes e Configurações ---
# Tentar obter o URL da planilha das secrets do Streamlit ou usar um placeholder
# GOOGLE_SHEET_URL = st.secrets.get("GOOGLE_SHEET_URL", "URL_DA_SUA_PLANILHA_AQUI")
# Por enquanto, usar o URL fornecido diretamente (menos seguro para produção)
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1bnqOqnJ3C9SXpJZ6txLtOu-pI7NYb6Yy/edit?usp=sharing&ouid=114833001856673794923&rtpof=true&sd=true"
CREDS_JSON_STRING = st.secrets.get("GOOGLE_CREDS_JSON")
DEFAULT_VENDEDOR = "Sarah" # Pode ser alterado ou selecionado dinamicamente no futuro

# --- Autenticação e Carregamento de Dados --- 
@st.cache_data(ttl=600) # Cache por 10 minutos
def load_data(sheet_url):
    try:
        # Tentar autenticar com credenciais se disponíveis
        if CREDS_JSON_STRING:
            creds_dict = json.loads(CREDS_JSON_STRING)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
            gc = gspread.authorize(creds)
            spreadsheet = gc.open_by_url(sheet_url)
            st.success("Autenticado com sucesso via Service Account!")
        else:
            # Tentar acesso público (pode falhar dependendo das permissões)
            st.warning("Tentando acesso público à planilha. Para maior confiabilidade, configure as credenciais do Google Service Account nos Secrets do Streamlit.")
            gc = gspread.service_account()
            spreadsheet = gc.open_by_url(sheet_url)
            
        metas_ws = spreadsheet.worksheet("Metas")
        vendas_ws = spreadsheet.worksheet("Vendas")
        
        metas_df = pd.DataFrame(metas_ws.get_all_records())
        vendas_df = pd.DataFrame(vendas_ws.get_all_records())
        
        # --- Pré-processamento --- 
        # Converter colunas de data para datetime
        metas_df["Inicio_Semana"] = pd.to_datetime(metas_df["Inicio_Semana"], dayfirst=True, errors='coerce')
        metas_df["Fim_Semana"] = pd.to_datetime(metas_df["Fim_Semana"], dayfirst=True, errors='coerce')
        vendas_df["Data"] = pd.to_datetime(vendas_df["Data"], dayfirst=True, errors='coerce')
        
        # Remover linhas onde a conversão de data falhou
        metas_df.dropna(subset=["Inicio_Semana", "Fim_Semana"], inplace=True)
        vendas_df.dropna(subset=["Data"], inplace=True)

        # Converter colunas numéricas (tratando possíveis erros)
        cols_numericas_metas = ["Meta_Mensal", "Bonus_Mensal", "Meta_Semanal", "Bonus_Semanal"]
        for col in cols_numericas_metas:
            metas_df[col] = pd.to_numeric(metas_df[col], errors='coerce').fillna(0)
            
        cols_numericas_vendas = ["Valor"]
        for col in cols_numericas_vendas:
            vendas_df[col] = pd.to_numeric(vendas_df[col], errors='coerce').fillna(0)
            
        return metas_df, vendas_df

    except gspread.exceptions.APIError as e:
        st.error(f"Erro de API do Google Sheets: {e}. Verifique se a URL está correta e se a API Google Sheets está habilitada no seu projeto Google Cloud.")
        return pd.DataFrame(), pd.DataFrame()
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Planilha não encontrada na URL: {sheet_url}. Verifique o link.")
        return pd.DataFrame(), pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound as e:
        st.error(f"Aba não encontrada na planilha: {e}. Verifique se as abas 'Metas' e 'Vendas' existem.")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        # Tentar carregar dados locais como fallback (se existirem)
        try:
            metas_df = pd.read_excel("planilha_metas_modelo.xlsx", sheet_name="Metas")
            vendas_df = pd.read_excel("planilha_metas_modelo.xlsx", sheet_name="Vendas")
            st.warning("Carregando dados do arquivo local 'planilha_metas_modelo.xlsx' como fallback.")
            # Repetir pré-processamento para dados locais
            metas_df["Inicio_Semana"] = pd.to_datetime(metas_df["Inicio_Semana"], dayfirst=True, errors='coerce')
            metas_df["Fim_Semana"] = pd.to_datetime(metas_df["Fim_Semana"], dayfirst=True, errors='coerce')
            vendas_df["Data"] = pd.to_datetime(vendas_df["Data"], dayfirst=True, errors='coerce')
            metas_df.dropna(subset=["Inicio_Semana", "Fim_Semana"], inplace=True)
            vendas_df.dropna(subset=["Data"], inplace=True)
            cols_numericas_metas = ["Meta_Mensal", "Bonus_Mensal", "Meta_Semanal", "Bonus_Semanal"]
            for col in cols_numericas_metas:
                metas_df[col] = pd.to_numeric(metas_df[col], errors='coerce').fillna(0)
            cols_numericas_vendas = ["Valor"]
            for col in cols_numericas_vendas:
                vendas_df[col] = pd.to_numeric(vendas_df[col], errors='coerce').fillna(0)
            return metas_df, vendas_df
        except FileNotFoundError:
            st.error("Arquivo local 'planilha_metas_modelo.xlsx' não encontrado. Não foi possível carregar dados.")
            return pd.DataFrame(), pd.DataFrame()
        except Exception as fallback_e:
            st.error(f"Erro ao carregar dados locais: {fallback_e}")
            return pd.DataFrame(), pd.DataFrame()

metas_df, vendas_df = load_data(GOOGLE_SHEET_URL)

# --- Lógica Principal --- 
if not metas_df.empty and not vendas_df.empty:
    # Obter data atual
    hoje = datetime.now().date()
    mes_atual = hoje.month
    ano_atual = hoje.year

    st.subheader(f"Vendedora: {DEFAULT_VENDEDOR} — {hoje.strftime('%B de %Y')}")

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
        # Certifique-se que 'hoje' é um objeto date, não datetime
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
        st.markdown(f"## 🗓️ Todas as Metas Semanais de {hoje.strftime('%B')}")
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
    if metas_df.empty or vendas_df.empty:
      st.error("Não foi possível carregar os dados da planilha ou do arquivo local. Verifique as mensagens de erro acima e as permissões da planilha.")

# --- Rodapé ---
st.caption("Desenvolvido por Manus")

