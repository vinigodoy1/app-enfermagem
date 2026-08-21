import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA E CSS DE IMPRESSÃO
# ---------------------------------------------------------
st.set_page_config(page_title="Gestão de Atendimentos", layout="wide")

# CSS para controlar a impressão física no papel timbrado
st.markdown("""
    <style>
        /* Estilos na tela normal */
        .print-header { display: none; }
        .summary-box {
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 16px;
            margin-top: 20px;
        }
        .total-banner {
            background-color: #0056b3;
            color: white;
            padding: 10px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 4px;
            margin-top: 10px;
            text-align: right;
        }

        /* REGRAS DE IMPRESSÃO - PAPEL TIMBRADO (A4) */
        @media print {
            /* Oculta menus, abas, botões e barras laterais do Streamlit */
            header, footer, .stButton, [data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stTabs"] {
                display: none !important;
            }
            
            @page {
                size: A4 portrait;
                margin-top: 2.0cm;
                margin-bottom: 2.0cm;
                margin-left: 1.3cm;
                margin-right: 1.3cm;
            }

            body {
                font-family: Arial, sans-serif;
                font-size: 10pt;
                color: #000;
                background: #fff;
            }

            .content-container {
                padding-top: 0.8cm;
                padding-bottom: 0.8cm;
            }

            .print-header {
                display: block !important;
                border-bottom: 2px solid #000;
                margin-bottom: 15px;
                padding-bottom: 5px;
            }

            table {
                width: 100% !important;
                border-collapse: collapse !important;
            }

            th, td {
                border-bottom: 1px solid #ddd !important;
                padding: 6px !important;
                font-size: 9.5pt !important;
            }

            .total-banner {
                background-color: #f0f0f0 !important;
                color: #000 !important;
                border: 1px solid #000 !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

st.title("🩺 Gestão de Atendimentos de Enfermagem")

# ---------------------------------------------------------
# BANCO DE DADOS EM MEMÓRIA
# ---------------------------------------------------------
if "procedimentos" not in st.session_state:
    st.session_state.procedimentos = {
        "CONS": {"nome": "Consulta", "valor": 45.00},
        "TON": {"nome": "Tonometria", "valor": 15.17},
        "BIO": {"nome": "Biomicroscopia", "valor": 55.53},
        "MR": {"nome": "Mapeamento de Retina", "valor": 50.00}
    }

if "atendimentos" not in st.session_state:
    st.session_state.atendimentos = []

# ---------------------------------------------------------
# NAVEGAÇÃO POR ABAS
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📋 Novo Atendimento", 
    "🖨️ Relatório Mensal & Impressão", 
    "⚙️ Alterar / Cadastrar Preços"
])

# ---------------------------------------------------------
# ABA 1: LANÇAMENTO DA ENFERMEIRA
# ---------------------------------------------------------
with tab1:
    st.subheader("Registrar Atendimento do Paciente")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        data_atend = st.date_input("Data do Atendimento", datetime.now())
        nome_paciente = st.text_input("Nome do Paciente")
    
    with col2:
        opcoes = list(st.session_state.procedimentos.keys())
        procs_sel = st.multiselect(
            "Selecione os Procedimentos:", 
            options=opcoes,
            format_func=lambda x: f"{x} - {st.session_state.procedimentos[x]['nome']} (R$ {st.session_state.procedimentos[x]['valor']:.2f})"
        )
        
        valor_total = sum(st.session_state.procedimentos[p]['valor'] for p in procs_sel)
        
        if procs_sel:
            st.markdown("**Conferência de Valores:**")
            for sigla in procs_sel:
                p = st.session_state.procedimentos[sigla]
                st.write(f"• **{sigla}** ({p['nome']}): R$ {p['valor']:.2f}")
            st.info(f"💰 **VALOR TOTAL:** R$ {valor_total:.2f}")

    if st.button("💾 Salvar Atendimento", type="primary"):
        if nome_paciente and procs_sel:
            st.session_state.atendimentos.append({
                "DATA": data_atend.strftime("%d/%m/%Y"),
                "NOME DO PACIENTE": nome_paciente.upper().strip(),
                "PROCEDIMENTO": "/".join(procs_sel),
                "VALOR": valor_total,
                "ITENS": procs_sel
            })
            st.success(f"Atendimento de **{nome_paciente}** registrado com sucesso!")
        else:
            st.error("Preencha o nome do paciente e selecione ao menos um procedimento.")

# ---------------------------------------------------------
# ABA 2: RELATÓRIO MENSAL, EXCLUSÃO E IMPRESSÃO
# ---------------------------------------------------------
with tab2:
    st.subheader("Relatório Mensal de Atendimentos")
    
    if st.session_state.atendimentos:
        # Botão para disparar a impressão nativa
        st.components.v1.html(
            """
            <button onclick="window.print()" style="
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
                cursor: pointer;
                margin-bottom: 15px;">
                🖨️ IMPRIMIR EM PAPEL TIMBRADO
            </button>
            """,
            height=60
        )
        
        st.markdown("---")
        
        # Gerenciamento de Duplicados (Edição/Exclusão)
        st.markdown("### ✏️ Gerenciar e Excluir Registros Duplicados")
        df_editor = pd.DataFrame(st.session_state.atendimentos)
        
        # Exibe a tabela interativa onde a enfermeira/administrador pode apagar linhas
        df_atualizado = st.data_editor(
            df_editor[["DATA", "NOME DO PACIENTE", "PROCEDIMENTO", "VALOR"]],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_atendimentos"
        )
        
        # Atualiza a lista interna com base na tabela editada
        if st.button("🔄 Atualizar Totais após Exclusões"):
            st.session_state.atendimentos = df_atualizado.to_dict("records")
            st.rerun()

        st.markdown("---")
        
        # ---------------------------------------------------------
        # ÁREA DE IMPRESSÃO (Visível na tela e na folha impressa)
        # ---------------------------------------------------------
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        
        # Cabeçalho do Relatório
        st.markdown("""
            <div class="print-header">
                <h2>RELATÓRIO MENSAL DE ATENDIMENTOS</h2>
                <p>Procedimentos de Enfermagem e Oftalmologia</p>
            </div>
        """, unsafe_allow_html=True)

        # Tabela Final
        st.table(df_atualizado)

        # ---------------------------------------------------------
        # DECOMPOSIÇÃO E CAMPOS DE TOTAIS
        # ---------------------------------------------------------
        total_pacientes = len(df_atualizado)
        valor_total_geral = df_atualizado["VALOR"].sum() if not df_atualizado.empty else 0.0
        
        # Contagem e Soma por Procedimento Individual
        contagem_procs = {}
        soma_procs = {}
        
        for record in st.session_state.atendimentos:
            # Obtém itens salvos ou decompõe a sigla
            itens = record.get("ITENS")
            if not itens and isinstance(record.get("PROCEDIMENTO"), str):
                itens = record["PROCEDIMENTO"].split("/")
            elif not itens:
                itens = []

            for sigla in itens:
                sigla_limpa = sigla.strip()
                val = st.session_state.procedimentos.get(sigla_limpa, {}).get("valor", 0.0)
                nome_p = st.session_state.procedimentos.get(sigla_limpa, {}).get("nome", sigla_limpa)
                
                chave = f"{sigla_limpa} ({nome_p})"
                contagem_procs[chave] = contagem_procs.get(chave, 0) + 1
                soma_procs[chave] = soma_procs.get(chave, 0.0) + val

        # Quadro de Resumo
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.markdown("### 📊 RESUMO DE FECHAMENTO MENSAL")
        st.write(f"• **TOTAL DE PACIENTES ATENDIDOS:** {total_pacientes} Pacientes")
        st.markdown("---")
        st.markdown("**Detalhamento de Procedimentos Realizados:**")
        
        if contagem_procs:
            for proc_nome, qtd in contagem_procs.items():
                val_subtotal = soma_procs[proc_nome]
                st.write(f"• **{qtd}x** {proc_nome}: **R$ {val_subtotal:.2f}**")
        else:
            st.write("Sem detalhamento disponível.")

        st.markdown(f'<div class="total-banner">VALOR TOTAL A RECEBER: R$ {valor_total_geral:.2f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("Nenhum atendimento cadastrado até o momento.")

# ---------------------------------------------------------
# ABA 3: ADMINISTRAÇÃO DE PREÇOS E CADASTRO
# ---------------------------------------------------------
with tab3:
    st.subheader("Cadastrar / Alterar Procedimentos")
    
    with st.form("form_proc"):
        sigla_in = st.text_input("Sigla do Procedimento (ex: CONS, TON, PA)").upper().strip()
        nome_in = st.text_input("Nome Completo do Procedimento")
        valor_in = st.number_input("Valor Unitário (R$)", min_value=0.0, step=1.0)
        
        if st.form_submit_button("💾 Salvar Procedimento"):
            if sigla_in and nome_in:
                st.session_state.procedimentos[sigla_in] = {"nome": nome_in, "valor": valor_in}
                st.success(f"Procedimento **{sigla_in}** cadastrado/atualizado com sucesso!")
            else:
                st.warning("Preencha a sigla e o nome do procedimento.")

    st.markdown("### Tabela de Preços Atual")
    df_precos = pd.DataFrame.from_dict(st.session_state.procedimentos, orient='index')
    df_precos.columns = ["Nome do Procedimento", "Valor (R$)"]
    st.table(df_precos)
