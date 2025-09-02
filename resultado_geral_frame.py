import sys
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QLineEdit, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIntValidator
from database import cursor, conn

# Importações para o PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle, SimpleDocTemplate, Spacer


class ResultadoGeralWidget(QWidget):
    """
    Widget para calcular e exibir o resultado geral do campeonato,
    com opções de descarte e exportação para PDF.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Armazenar estado para recálculos e exportação
        self.pontuacao_final = {}
        self.pilotos_resultados_por_etapa = {}
        self.etapas_ordenadas = []
        self.descartes_aplicados = 0

        self.init_ui()
        self.carregar_categorias()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Título
        label_titulo = QLabel("Resultado Geral do Campeonato")
        label_titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_titulo)

        # Controles (Categoria e Descartes)
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Categoria:"))
        self.combo_categoria = QComboBox()
        self.combo_categoria.currentIndexChanged.connect(self.atualizar_resultado)
        controls_layout.addWidget(self.combo_categoria, 1)

        controls_layout.addStretch(1)

        # --- NOVOS CONTROLES DE DESCARTE AGRUPADOS ---
        descarte_group = QGroupBox("Regras de Descarte")
        descarte_layout = QHBoxLayout(descarte_group)

        descarte_layout.addWidget(QLabel("Nº de Descarte(s):"))
        self.entry_descartes = QLineEdit("0")
        self.entry_descartes.setValidator(QIntValidator(0, 99))
        self.entry_descartes.setFixedWidth(50)
        descarte_layout.addWidget(self.entry_descartes)

        # ***** NOVA OPÇÃO DE DESCARTE *****
        self.check_descartar_com_pontos = QCheckBox("Descartar apenas etapas concluídas (pontos > 0)")
        self.check_descartar_com_pontos.setToolTip(
            "Se marcado, ignora as não participações (0 pontos) e descarta os piores resultados das etapas que o piloto correu.\n"
            "Se desmarcado, as não participações serão as primeiras a serem descartadas."
        )
        descarte_layout.addWidget(self.check_descartar_com_pontos)

        btn_aplicar_descarte = QPushButton("Atualizar / Aplicar Regras")
        btn_aplicar_descarte.clicked.connect(self.atualizar_resultado)
        descarte_layout.addWidget(btn_aplicar_descarte)

        controls_layout.addWidget(descarte_group, 3)
        main_layout.addLayout(controls_layout)

        # Tabela de Resultados
        self.table_resultados = QTableWidget()
        self.table_resultados.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_resultados.setSortingEnabled(True)
        main_layout.addWidget(self.table_resultados)

        # Botão de Exportação
        btn_exportar_pdf = QPushButton("Exportar Resultado para PDF")
        btn_exportar_pdf.clicked.connect(self.exportar_para_pdf)
        main_layout.addWidget(btn_exportar_pdf, 0, Qt.AlignmentFlag.AlignRight)

    def carregar_categorias(self):
        self.combo_categoria.clear()
        self.combo_categoria.addItem("-- Selecione --", userData=None)
        cursor.execute("SELECT id, nome FROM categorias ORDER BY nome")
        for cat_id, cat_nome in cursor.fetchall():
            self.combo_categoria.addItem(cat_nome, userData=cat_id)

    def get_sistema_pontuacao(self):
        cursor.execute("SELECT posicao, pontos FROM sistema_pontuacao")
        sistema = {pos: pts for pos, pts in cursor.fetchall()}
        cursor.execute("SELECT pole_position, melhor_volta FROM sistema_pontuacao_extras")
        extras = cursor.fetchone()
        if extras:
            sistema["pole_position"] = extras[0]
            sistema["melhor_volta"] = extras[1]
        return sistema

    def atualizar_resultado(self):
        categoria_id = self.combo_categoria.currentData()
        if not categoria_id:
            self.table_resultados.setRowCount(0)
            self.table_resultados.setColumnCount(0)
            return

        try:
            self.descartes_aplicados = int(self.entry_descartes.text())
            ignorar_zeros_no_descarte = self.check_descartar_com_pontos.isChecked()
        except ValueError:
            self.descartes_aplicados = 0
            ignorar_zeros_no_descarte = False

        try:
            sistema_pontuacao = self.get_sistema_pontuacao()
            if not sistema_pontuacao:
                QMessageBox.warning(self, "Aviso", "Sistema de pontuação não configurado.")
                return

            # 1. Obter todos os resultados e etapas
            query = """
                SELECT p.nome, r.posicao, r.melhor_volta, r.pole_position, r.adv, e.nome, e.data
                FROM resultados_etapas r
                JOIN pilotos p ON r.piloto_id = p.id
                JOIN etapas e ON r.etapa_id = e.id
                WHERE r.categoria_id = ?
            """
            cursor.execute(query, (categoria_id,))
            resultados = cursor.fetchall()

            etapas_presentes = {}
            self.pilotos_resultados_por_etapa = {}

            # CORREÇÃO: Pega todos os pilotos da categoria para garantir que todos apareçam na lista final
            pilotos_na_categoria = {p[0] for p in cursor.execute(
                "SELECT p.nome FROM pilotos p JOIN pilotos_categorias pc ON p.id = pc.piloto_id WHERE pc.categoria_id = ?",
                (categoria_id,))}

            # Pré-popula o dicionário com todos os pilotos
            for piloto in pilotos_na_categoria:
                self.pilotos_resultados_por_etapa[piloto] = {}

            for nome_piloto, pos, mv, pole, adv, nome_etapa, data_etapa in resultados:
                total_pontos = sistema_pontuacao.get(pos, 0) + \
                               (sistema_pontuacao.get("melhor_volta", 0) if mv else 0) + \
                               (sistema_pontuacao.get("pole_position", 0) if pole else 0)

                self.pilotos_resultados_por_etapa[nome_piloto][nome_etapa] = {'pontos': total_pontos, 'adv': adv}
                if nome_etapa not in etapas_presentes:
                    etapas_presentes[nome_etapa] = data_etapa

            self.etapas_ordenadas = sorted(etapas_presentes, key=etapas_presentes.get)

            # 3. Aplicar descartes e calcular pontuação final
            self.pontuacao_final = {}
            for piloto, etapas_participadas in self.pilotos_resultados_por_etapa.items():

                # ***** LÓGICA DE DESCARTE ATUALIZADA *****
                pontuacoes = [etapa for etapa in etapas_participadas.values()]
                total_bruto = sum(p['pontos'] for p in pontuacoes)

                pontuacoes.sort(key=lambda x: (x['adv'], x['pontos']))

                pontos_a_descartar = 0
                descartes_efetivos = 0
                for resultado in pontuacoes:
                    if descartes_efetivos >= self.descartes_aplicados:
                        break

                    if resultado['adv']: continue  # Nunca descarta resultado com advertência

                    # NOVA REGRA: Pula resultados com 0 pontos se a opção estiver marcada
                    if ignorar_zeros_no_descarte and resultado['pontos'] == 0:
                        continue

                    pontos_a_descartar += resultado['pontos']
                    descartes_efetivos += 1

                self.pontuacao_final[piloto] = total_bruto - pontos_a_descartar

            self.exibir_na_tabela()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao calcular o resultado: {e}")

    def exibir_na_tabela(self):
        self.table_resultados.setSortingEnabled(False)
        self.table_resultados.setRowCount(0)
        headers = ["Pos", "Piloto"] + self.etapas_ordenadas + ["Pontos Totais"]
        self.table_resultados.setColumnCount(len(headers))
        self.table_resultados.setHorizontalHeaderLabels(headers)

        classificacao = sorted(self.pontuacao_final.items(), key=lambda item: item[1], reverse=True)

        for i, (piloto, pontos_totais) in enumerate(classificacao):
            self.table_resultados.insertRow(i)

            self.table_resultados.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table_resultados.setItem(i, 1, QTableWidgetItem(piloto.title()))

            # Colunas de Etapas
            for j, etapa_nome in enumerate(self.etapas_ordenadas):
                # CORREÇÃO: Mostra 0 se o piloto não participou da etapa
                pontos_etapa = self.pilotos_resultados_por_etapa[piloto].get(etapa_nome, {}).get('pontos', 0)
                etapa_item = QTableWidgetItem(str(pontos_etapa))
                etapa_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_resultados.setItem(i, 2 + j, etapa_item)

            total_item = QTableWidgetItem(str(pontos_totais))
            total_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.table_resultados.setItem(i, len(headers) - 1, total_item)

        self.table_resultados.resizeColumnsToContents()
        self.table_resultados.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_resultados.setSortingEnabled(True)

    def exportar_para_pdf(self):
        # (código interno sem alterações)
        categoria_nome = self.combo_categoria.currentText()
        if not self.pontuacao_final:
            QMessageBox.warning(self, "Aviso", f"Não há resultados para exportar para a categoria '{categoria_nome}'.")
            return
        default_filename = f"resultado_geral_{categoria_nome.replace(' ', '_')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", default_filename, "PDF Files (*.pdf)")
        if not file_path: return
        try:
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph(f"Resultado Geral - Categoria: {categoria_nome}", styles['Title']))
            if self.descartes_aplicados > 0:
                elements.append(
                    Paragraph(f"({self.descartes_aplicados} piores resultados descartados)", styles['Normal']))
            elements.append(Spacer(1, 12))
            header = ['Pos', 'Piloto'] + self.etapas_ordenadas + ['Total']
            table_data = [header]
            classificacao = sorted(self.pontuacao_final.items(), key=lambda item: item[1], reverse=True)
            for i, (piloto, pontos_totais) in enumerate(classificacao):
                row = [i + 1, piloto.title()]
                for etapa_nome in self.etapas_ordenadas:
                    pontos_etapa = self.pilotos_resultados_por_etapa[piloto].get(etapa_nome, {}).get('pontos', 0)
                    row.append(str(pontos_etapa))
                row.append(pontos_totais)
                table_data.append(row)
            table = Table(table_data)
            style = TableStyle(
                [('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                 ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                 ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                 ('BACKGROUND', (0, 1), (-1, -1), colors.beige), ('GRID', (0, 0), (-1, -1), 1, colors.black)])
            table.setStyle(style)
            elements.append(table)
            doc.build(elements)
            QMessageBox.information(self, "Sucesso", f"Resultado exportado com sucesso para:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Exportação", f"Não foi possível gerar o PDF: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QMainWindow()
    main_widget = ResultadoGeralWidget()
    window.setCentralWidget(main_widget)
    window.resize(1024, 768)
    window.show()
    sys.exit(app.exec())