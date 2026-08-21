import streamlit as st
import pandas as pd
import io
from datetime import datetime

# ---------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA E CSS DE IMPRESSÃO
# ---------------------------------------------------------
st.set_page_config(page_title="Gestão de Atendimentos", layout="wide")

# CSS focado em ocultar títulos/menus e aplicar as margens exatas na impressão
st.markdown("""
    <style>
        /* Oculta o cabeçalho impresso na tela normal */
        .print-only { display: none; }
        
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

        /* REGRAS RÍGIDAS DE IMPRESSÃO EM PAPEL TIMBRADO (A4 VERTICAL) */
        @media print {
            /* Oculta todos os componentes, abas, botões e títulos do Streamlit */
            header, footer, nav, button, .stButton, .stDownloadButton, 
            [data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stTabs"], 
            iframe, .stAppHeader, .stElementContainer:has(button), h1, h2, h3, .stMarkdown:has(h1) {
                display: none !important;
                visibility: hidden !important;
            }

            /* Força a visibilidade exclusiva da área de impressão */
            html, body, .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
                background: white !important;
                color: black !important;
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
                height: auto !important;
                overflow: visible !important;
            }

            @page {
                size: A4 portrait;
                margin-top: 2.0cm;
                margin-bottom: 2.0cm;
                margin-left: 1.3cm;
                margin-right: 1.3cm;
            }

            .print-only {
                display: block !important;
                visibility: visible !important;
            }

            .content-container {
                display: block !important;
                visibility: visible !important;
                padding-top: 0.8cm;
                padding-bottom: 0.8cm;
            }

            /* Estilização da Tabela para Impressão */
            .print-table {
                width: 100% !important;
                border-collapse: collapse !important;
                margin-bottom: 20px !important;
            }

            .print-table th, .print-table td {
                border-bottom: 1px solid #000 !important;
                padding: 6px 8px !important;
                font-size: 9.5pt !important;
                color: #000 !important;
                text-align: left !important;
            }

            .print-table th {
                background-color: #f0f0f0 !important;
                font-weight: bold !important;
            }

            .summary-box {
                border: 1px solid #000 !important;
                background-color: #fff !important;
                padding: 10px !important;
                margin-top: 15px !important;
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
    
    with st.form("form_atendimento", clear_on_submit=True):
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

        btn_salvar = st.form_submit_button("💾 Salvar Atendimento e Cadastrar Novo Paciente", type="primary", use_container_width=True)

        if btn_salvar:
            if nome_paciente and procs_sel:
                valor_total = sum(st.session_state.procedimentos[p]['valor'] for p in procs_sel)
                
                st.session_state.atendimentos.append({
                    "DATA": data_atend.strftime("%d/%m/%Y"),
                    "NOME DO PACIENTE": nome_paciente.upper().strip(),
                    "PROCEDIMENTO": "/".join(procs_sel),
                    "VALOR": valor_total,
                    "ITENS": procs_sel
                })
                st.success(f"✅ Atendimento de **{nome_paciente.upper()}** registrado com sucesso!")
            else:
                st.error("⚠️ Preencha o nome do paciente e selecione ao menos um procedimento.")

# ---------------------------------------------------------
# ABA 2: RELATÓRIO MENSAL, EXPORTAÇÃO EXCEL E IMPRESSÃO
# ---------------------------------------------------------
with tab2:
    st.subheader("Relatório Mensal de Atendimentos")
    
    if st.session_state.atendimentos:
        df_editor = pd.DataFrame(st.session_state.atendimentos)
        
        # Cálculo prévio dos totais para exibição e exportação
        total_pacientes = len(df_editor)
        valor_total_geral = df_editor["VALOR"].sum() if not df_editor.empty else 0.0
        
        contagem_procs = {}
        soma_procs = {}
        
        for record in st.session_state.atendimentos:
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

        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            st.components.v1.html(
                """
                <button onclick="window.parent.print()" style="
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 5px;
                    cursor: pointer;
                    width: 100%;">
                    🖨️ IMPRIMIR EM PAPEL TIMBRADO
                </button>
                """,
                height=50
            )
            
        with col_btn2:
            # Geração do Excel contendo a Tabela e o Quadro de Totais no final
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # 1. Tabela Principal de Atendimentos
                df_editor[["DATA", "NOME DO PACIENTE", "PROCEDIMENTO", "VALOR"]].to_excel(
                    writer, index=False, sheet_name='Relatorio_Mensal', startrow=0
                )
                
                # 2. Inserção do Quadro de Totais abaixo dos lançamentos
                sheet = writer.sheets['Relatorio_Mensal']
                start_row = len(df_editor) + 3
                
                sheet.cell(row=start_row, column=1, value="--- RESUMO DE FECHAMENTO MENSAL ---")
                sheet.cell(row=start_row+1, column=1, value="TOTAL DE PACIENTES:")
                sheet.cell(row=start_row+1, column=2, value=f"{total_pacientes} Pacientes")
                
                current_r = start_row + 2
                for proc_nome, qtd in contagem_procs.items():
                    val_subtotal = soma_procs[proc_nome]
                    sheet.cell(row=current_r, column=1, value=f"{qtd}x {proc_nome}:")
                    sheet.cell(row=current_r, column=2, value=val_subtotal)
                    current_r += 1
                
                sheet.cell(row=current_r+1, column=1, value="VALOR TOTAL A RECEBER:")
                sheet.cell(row=current_r+1, column=2, value=valor_total_geral)
                
            buffer.seek(0)
            
            st.download_button(
                label="📊 BAIXAR TABELA EM EXCEL (.XLSX)",
                data=buffer,
                file_name=f"relatorio_atendimentos_{datetime.now().strftime('%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        st.markdown("---")
        st.markdown("### ✏️ Gerenciar e Excluir Registros Duplicados")
        
        df_atualizado = st.data_editor(
            df_editor[["DATA", "NOME DO PACIENTE", "PROCEDIMENTO", "VALOR"]],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_atendimentos"
        )
        
        if st.button("🔄 Atualizar Totais após Exclusões"):
            st.session_state.atendimentos = df_atualizado.to_dict("records")
            st.rerun()

        st.markdown("---")
        
        # ---------------------------------------------------------
        # ÁREA DE IMPRESSÃO - HTML PURO (Sem Títulos Externos)
        # ---------------------------------------------------------
        # Monta a estrutura em HTML puro para garantir exibição na caixa de impressão do navegador
        linhas_html = ""
        for _, row in df_editor.iterrows():
            linhas_html += f"""
            <tr>
                <td>{row['DATA']}</td>
                <td>{row['NOME DO PACIENTE']}</td>
                <td>{row['PROCEDIMENTO']}</td>
                <td style="text-align: right;">R$ {row['VALOR']:.2f}</td>
            </tr>
            """

        detalhes_totais_html = ""
        for proc_nome, qtd in contagem_procs.items():
            val_subtotal = soma_procs[proc_nome]
            detalhes_totais_html += f"<div>• <strong>{qtd}x</strong> {proc_nome}: R$ {val_subtotal:.2f}</div>"

        html_impressao = f"""
        <div class="print-only content-container">
            <table class="print-table">
                <thead>
                    <tr>
                        <th>DATA</th>
                        <th>NOME DO PACIENTE</th>
                        <th>PROCEDIMENTO</th>
                        <th style="text-align: right;">VALOR</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_html}
                </tbody>
            </table>

            <div class="summary-box">
                <div style="font-size: 11pt; font-weight: bold; margin-bottom: 5px;">RESUMO DE FECHAMENTO MENSAL</div>
                <div>• <strong>TOTAL DE PACIENTES ATENDIDOS:</strong> {total_pacientes} Pacientes</div>
                <hr style="margin: 8px 0; border: 0; border-top: 1px solid #ccc;">
                <div><strong>Detalhamento de Procedimentos Realizados:</strong></div>
                {detalhes_totais_html}
                <div class="total-banner" style="margin-top: 10px; font-weight: bold;">
                    VALOR TOTAL A RECEBER: R$ {valor_total_geral:.2f}
                </div>
            </div>
        </div>
        """
        
        st.markdown(html_impressao, unsafe_allow_html=True)

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
