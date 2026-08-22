import streamlit as st
import pandas as pd
import io
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# ---------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA E CSS DE IMPRESSÃO
# ---------------------------------------------------------
st.set_page_config(page_title="Relatório Mensal para Prefeituras", layout="wide")

st.markdown("""
    <style>
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

        /* REGRAS DE IMPRESSÃO EM PAPEL TIMBRADO (A4 VERTICAL) */
        @media print {
            header, footer, nav, button, .stButton, .stDownloadButton, 
            [data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stTabs"], 
            iframe, .stAppHeader, .stElementContainer, h1, h2, h3, .stMarkdown {
                display: none !important;
            }

            .print-area, .print-area * {
                display: block !important;
                visibility: visible !important;
            }

            .print-area {
                position: absolute !important;
                left: 0 !important;
                top: 0 !important;
                width: 100% !important;
            }

            @page {
                size: A4 portrait;
                margin-top: 2.0cm;
                margin-bottom: 2.0cm;
                margin-left: 1.3cm;
                margin-right: 1.3cm;
            }

            table.print-table {
                width: 100% !important;
                border-collapse: collapse !important;
                margin-bottom: 20px !important;
            }

            table.print-table th, table.print-table td {
                border-bottom: 1px solid #000 !important;
                padding: 6px 8px !important;
                font-size: 9.5pt !important;
                color: #000 !important;
                text-align: left !important;
            }

            table.print-table th {
                background-color: #f0f0f0 !important;
                font-weight: bold !important;
            }

            .summary-box-print {
                border: 1px solid #000 !important;
                padding: 10px !important;
                margin-top: 15px !important;
                background-color: #fff !important;
            }

            .total-banner-print {
                background-color: #f0f0f0 !important;
                color: #000 !important;
                border: 1px solid #000 !important;
                padding: 8px !important;
                font-weight: bold !important;
                text-align: right !important;
                margin-top: 10px !important;
            }
        }

        .print-area { display: none; }
    </style>
""", unsafe_allow_html=True)

st.title("📋 Relatório Mensal para Prefeituras")

# ---------------------------------------------------------
# BANCO DE DADOS EM MEMÓRIA & HISTÓRICO
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

if "historico_atendimentos" not in st.session_state:
    st.session_state.historico_atendimentos = []

def salvar_estado_historico():
    st.session_state.historico_atendimentos.append(list(st.session_state.atendimentos))

# ---------------------------------------------------------
# NAVEGAÇÃO POR ABAS
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📋 Novo Atendimento", 
    "🖨️ Relatório Mensal & Impressão", 
    "⚙️ Alterar / Cadastrar Preços"
])

# ---------------------------------------------------------
# ABA 1: LANÇAMENTO DE ATENDIMENTOS
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
                format_func=lambda x: f"{x} - {st.session_state.procedimentos[x]['nome']} (R$ {st.session_state.procedimentos[x]['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + ")"
            )

        btn_salvar = st.form_submit_button("💾 Salvar Atendimento e Cadastrar Novo Paciente", type="primary", use_container_width=True)

        if nome_paciente:
            nome_limpo = nome_paciente.upper().strip()
            nomes_existentes = [a["NOME DO PACIENTE"] for a in st.session_state.atendimentos]
            if nome_limpo in nomes_existentes:
                st.warning(f"⚠️ Atenção: O paciente **{nome_limpo}** já possui atendimento cadastrado neste mês.")

        if btn_salvar:
            if nome_paciente and procs_sel:
                valor_total = sum(st.session_state.procedimentos[p]['valor'] for p in procs_sel)
                
                salvar_estado_historico()
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
# ABA 2: RELATÓRIO MENSAL & IMPRESSÃO
# ---------------------------------------------------------
with tab2:
    st.subheader("Relatório Mensal de Atendimentos")
    
    if st.session_state.atendimentos:
        col_tit, col_desf = st.columns([3, 1])
        with col_tit:
            st.markdown("### ✏️ Tabela de Atendimentos (Edições e Exclusões Automáticas)")
        with col_desf:
            if st.button("↩️ Desfazer Exclusão", use_container_width=True):
                if st.session_state.historico_atendimentos:
                    st.session_state.atendimentos = st.session_state.historico_atendimentos.pop()
                    st.success("Ação desfeita!")
                    st.rerun()

        # Tabela editável com sincronização automática
        df_editor_input = pd.DataFrame(st.session_state.atendimentos)[["DATA", "NOME DO PACIENTE", "PROCEDIMENTO", "VALOR"]]
        
        df_atualizado = st.data_editor(
            df_editor_input,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_atendimentos"
        )

        # Sincronização automática em tempo real na memória
        novos_dados = df_atualizado.to_dict("records")
        if novos_dados != st.session_state.atendimentos:
            salvar_estado_historico()
            st.session_state.atendimentos = novos_dados
            st.rerun()

        df_final = pd.DataFrame(st.session_state.atendimentos)
        total_pacientes = len(df_final)
        valor_total_geral = df_final["VALOR"].sum() if not df_final.empty else 0.0
        
        contagem_procs = {}
        soma_procs = {}
        
        for _, row in df_final.iterrows():
            proc_str = str(row.get("PROCEDIMENTO", ""))
            itens = [p.strip() for p in proc_str.split("/") if p.strip()]
            
            for sigla in itens:
                val = st.session_state.procedimentos.get(sigla, {}).get("valor", 0.0)
                nome_p = st.session_state.procedimentos.get(sigla, {}).get("nome", sigla)
                
                chave = f"{sigla} ({nome_p})"
                contagem_procs[chave] = contagem_procs.get(chave, 0) + 1
                soma_procs[chave] = soma_procs.get(chave, 0.0) + val

        st.markdown("---")
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            st.markdown("""
                <button onclick="window.print()" style="
                    background-color: #28a745; color: white; border: none;
                    padding: 12px 20px; font-size: 16px; font-weight: bold;
                    border-radius: 5px; cursor: pointer; width: 100%;">
                    🖨️ IMPRIMIR EM PAPEL TIMBRADO
                </button>
            """, unsafe_allow_html=True)
            
        with col_btn2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_excel = df_final[["DATA", "NOME DO PACIENTE", "PROCEDIMENTO", "VALOR"]].copy()
                df_excel.to_excel(writer, index=False, sheet_name='Relatorio_Mensal', startrow=0)
                
                sheet = writer.sheets['Relatorio_Mensal']
                
                header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                bold_font = Font(name="Calibri", size=11, bold=True)
                thin_border = Border(
                    left=Side(style='thin', color='D9D9D9'),
                    right=Side(style='thin', color='D9D9D9'),
                    top=Side(style='thin', color='D9D9D9'),
                    bottom=Side(style='thin', color='D9D9D9')
                )

                for col_num in range(1, 5):
                    cell = sheet.cell(row=1, column=col_num)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center" if col_num in [1, 4] else "left", vertical="center")

                for row_num in range(2, len(df_excel) + 2):
                    for col_num in range(1, 5):
                        cell = sheet.cell(row=row_num, column=col_num)
                        cell.border = thin_border
                        if col_num == 4:
                            cell.number_format = 'R$ #,##0.00'
                            cell.alignment = Alignment(horizontal="right")
                        elif col_num == 1:
                            cell.alignment = Alignment(horizontal="center")

                start_row = len(df_excel) + 3
                sheet.cell(row=start_row, column=1, value="RESUMO DE FECHAMENTO MENSAL").font = bold_font
                sheet.cell(row=start_row+1, column=1, value="TOTAL DE PACIENTES:").font = bold_font
                sheet.cell(row=start_row+1, column=2, value=f"{total_pacientes} Pacientes")
                
                current_r = start_row + 2
                for proc_nome, qtd in contagem_procs.items():
                    val_subtotal = soma_procs[proc_nome]
                    sheet.cell(row=current_r, column=1, value=f"{qtd}x {proc_nome}:")
                    c_val = sheet.cell(row=current_r, column=2, value=val_subtotal)
                    c_val.number_format = 'R$ #,##0.00'
                    current_r += 1
                
                sheet.cell(row=current_r+1, column=1, value="VALOR TOTAL A RECEBER:").font = bold_font
                c_tot = sheet.cell(row=current_r+1, column=2, value=valor_total_geral)
                c_tot.font = bold_font
                c_tot.number_format = 'R$ #,##0.00'

                for col in sheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = col[0].column_letter
                    sheet.column_dimensions[col_letter].width = max(max_len + 4, 15)
                
            buffer.seek(0)
            
            st.download_button(
                label="📊 BAIXAR PLANILHA FORMATADA EM EXCEL (.XLSX)",
                data=buffer,
                file_name=f"relatorio_atendimentos_{datetime.now().strftime('%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        st.markdown("---")
        
        # ---------------------------------------------------------
        # VISUALIZAÇÃO NA TELA E IMPRESSÃO
        # ---------------------------------------------------------
        st.subheader("📄 Visualização do Relatório Mensal")
        
        df_screen = df_final[["DATA", "NOME DO PACIENTE", "PROCEDIMENTO", "VALOR"]].copy()
        df_screen["VALOR"] = df_screen["VALOR"].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        st.table(df_screen)

        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.markdown("### 📊 RESUMO DE FECHAMENTO MENSAL")
        st.write(f"• **TOTAL DE PACIENTES ATENDIDOS:** {total_pacientes} Pacientes")
        st.markdown("---")
        st.markdown("**Detalhamento de Procedimentos Realizados:**")
        
        if contagem_procs:
            for proc_nome, qtd in contagem_procs.items():
                val_subtotal = soma_procs[proc_nome]
                val_fmt = f"R$ {val_subtotal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                st.write(f"• **{qtd}x** {proc_nome}: **{val_fmt}**")

        val_total_fmt = f"R$ {valor_total_geral:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        st.markdown(f'<div class="total-banner">VALOR TOTAL A RECEBER: {val_total_fmt}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------------------------------------
        # ESTRUTURA EXCLUSIVA PARA A IMPRESSÃO
        # ---------------------------------------------------------
        linhas_html = ""
        for _, row in df_final.iterrows():
            v_fmt = f"R$ {row['VALOR']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            linhas_html += f"<tr><td>{row['DATA']}</td><td>{row['NOME DO PACIENTE']}</td><td>{row['PROCEDIMENTO']}</td><td style='text-align: right;'>{v_fmt}</td></tr>"

        detalhes_html = ""
        for proc_nome, qtd in contagem_procs.items():
            val_subtotal = soma_procs[proc_nome]
            v_sub_fmt = f"R$ {val_subtotal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            detalhes_html += f"<div>• <strong>{qtd}x</strong> {proc_nome}: {v_sub_fmt}</div>"

        html_print = f"""
        <div class="print-area">
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
            <div class="summary-box-print">
                <strong>RESUMO DE FECHAMENTO MENSAL</strong><br>
                • <strong>TOTAL DE PACIENTES ATENDIDOS:</strong> {total_pacientes} Pacientes<br><br>
                <strong>Detalhamento de Procedimentos Realizados:</strong><br>
                {detalhes_html}
                <div class="total-banner-print">
                    VALOR TOTAL A RECEBER: {val_total_fmt}
                </div>
            </div>
        </div>
        """
        st.markdown(html_print, unsafe_allow_html=True)

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
    df_precos["Valor (R$)"] = df_precos["Valor (R$)"].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.table(df_precos)
