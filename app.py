import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gestão de Atendimentos", layout="wide")
st.title("🩺 Sistema de Atendimentos de Enfermagem")

# Tabela de preços base
if "procedimentos" not in st.session_state:
    st.session_state.procedimentos = {
        "CONS": {"nome": "Consulta", "valor": 45.00},
        "TON": {"nome": "Tonometria", "valor": 15.17},
        "BIO": {"nome": "Biomicroscopia", "valor": 55.53},
        "MR": {"nome": "Mapeamento de Retina", "valor": 50.00}
    }

if "atendimentos" not in st.session_state:
    st.session_state.atendimentos = []

tab1, tab2, tab3 = st.tabs(["📋 Novo Atendimento", "🖨️ Relatório Mensal", "⚙️ Cadastrar Preços"])

with tab1:
    data_atend = st.date_input("Data", datetime.now())
    nome_paciente = st.text_input("Nome do Paciente")
    opcoes = list(st.session_state.procedimentos.keys())
    
    procs_sel = st.multiselect(
        "Procedimentos", 
        options=opcoes,
        format_func=lambda x: f"{x} - {st.session_state.procedimentos[x]['nome']} (R$ {st.session_state.procedimentos[x]['valor']:.2f})"
    )
    
    valor_total = sum(st.session_state.procedimentos[p]['valor'] for p in procs_sel)
    st.write(f"**Valor do Atendimento:** R$ {valor_total:.2f}")
    
    if st.button("Salvar Atendimento", type="primary"):
        if nome_paciente and procs_sel:
            st.session_state.atendimentos.append({
                "data": data_atend.strftime("%d/%m/%Y"),
                "paciente": nome_paciente.upper(),
                "procedimento": "/".join(procs_sel),
                "valor": valor_total
            })
            st.success("Atendimento registrado com sucesso!")

with tab2:
    if st.session_state.atendimentos:
        df = pd.DataFrame(st.session_state.atendimentos)
        st.dataframe(df, use_container_width=True)
        st.write(f"**Total de Pacientes:** {len(df)}")
        st.write(f"**Total a Receber:** R$ {df['valor'].sum():.2f}")
    else:
        st.info("Nenhum atendimento registrado.")

with tab3:
    with st.form("add_proc"):
        sigla = st.text_input("Sigla (ex: CONS)").upper()
        nome = st.text_input("Nome do Procedimento")
        valor = st.number_input("Valor R$", min_value=0.0, step=1.0)
        if st.form_submit_button("Salvar / Alterar Procedimento"):
            if sigla and nome:
                st.session_state.procedimentos[sigla] = {"nome": nome, "valor": valor}
                st.success(f"Procedimento {sigla} salvo com sucesso!")