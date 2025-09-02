import sys
import os
import csv
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QDialog, QDialogButtonBox, QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIntValidator

# Libs para extração de dados, precisam ser instaladas (`pip install PyPDF2 beautifulsoup4`)
import PyPDF2
from bs4 import BeautifulSoup

from database import cursor, conn


# --- Diálogos Auxiliares ---

class EditarResultadoDialog(QDialog):
    def __init__(self, etapa_id, categoria_id, piloto_id, piloto_nome, posicao, pole, melhor_volta, adv, parent=None):
        super().__init__(parent)
        self.etapa_id = etapa_id
        self.categoria_id = categoria_id
        self.piloto_id = piloto_id

        self.setWindowTitle("Editar Resultado")
        self.setModal(True)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Piloto: {piloto_nome.title()}"))

        layout.addWidget(QLabel("Posição:"))
        self.entry_posicao = QLineEdit(str(posicao))
        self.entry_posicao.setValidator(QIntValidator(1, 999))
        layout.addWidget(self.entry_posicao)

        self.check_pole = QCheckBox("Pole Position")
        self.check_pole.setChecked(pole == "Sim")
        layout.addWidget(self.check_pole)

        self.check_melhor_volta = QCheckBox("Melhor Volta")
        self.check_melhor_volta.setChecked(melhor_volta == "Sim")
        layout.addWidget(self.check_melhor_volta)

        self.check_adv = QCheckBox("Recebeu ADV (Advertência)")
        self.check_adv.setChecked(adv == "Sim")
        layout.addWidget(self.check_adv)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        try:
            posicao = int(self.entry_posicao.text())
            pole = 1 if self.check_pole.isChecked() else 0
            melhor_volta = 1 if self.check_melhor_volta.isChecked() else 0
            adv = 1 if self.check_adv.isChecked() else 0

            cursor.execute("""
                UPDATE resultados_etapas
                SET posicao = ?, pole_position = ?, melhor_volta = ?, adv = ?
                WHERE etapa_id = ? AND piloto_id = ? AND categoria_id = ?
            """, (posicao, pole, melhor_volta, adv, self.etapa_id, self.piloto_id, self.categoria_id))
            conn.commit()
            super().accept()
        except ValueError:
            QMessageBox.warning(self, "Erro", "Por favor, insira um número válido para a posição.")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao salvar alterações: {e}")


class ManualInsertDialog(QDialog):
    def __init__(self, etapa_id, categoria_id, parent=None):
        super().__init__(parent)
        self.etapa_id = etapa_id
        self.categoria_id = categoria_id

        self.setWindowTitle("Inserir Resultado Manualmente")
        self.setModal(True)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Piloto:"))
        self.combo_piloto = QComboBox()
        self.carregar_pilotos()
        layout.addWidget(self.combo_piloto)

        layout.addWidget(QLabel("Posição:"))
        self.entry_posicao = QLineEdit()
        self.entry_posicao.setValidator(QIntValidator(1, 999))
        layout.addWidget(self.entry_posicao)

        self.check_pole = QCheckBox("Pole Position")
        layout.addWidget(self.check_pole)

        self.check_melhor_volta = QCheckBox("Melhor Volta")
        layout.addWidget(self.check_melhor_volta)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def carregar_pilotos(self):
        # Carrega pilotos que estão na categoria mas não têm resultado nesta etapa ainda
        query = """
            SELECT p.id, p.nome FROM pilotos p
            JOIN pilotos_categorias pc ON p.id = pc.piloto_id
            WHERE pc.categoria_id = ? AND p.id NOT IN (
                SELECT piloto_id FROM resultados_etapas WHERE etapa_id = ? AND categoria_id = ?
            )
            ORDER BY p.nome
        """
        cursor.execute(query, (self.categoria_id, self.etapa_id, self.categoria_id))
        for piloto_id, piloto_nome in cursor.fetchall():
            self.combo_piloto.addItem(piloto_nome.title(), userData=piloto_id)

    def accept(self):
        piloto_id = self.combo_piloto.currentData()
        posicao_str = self.entry_posicao.text()
        if not piloto_id or not posicao_str:
            QMessageBox.warning(self, "Erro", "Piloto e Posição são obrigatórios.")
            return

        try:
            posicao = int(posicao_str)
            pole = 1 if self.check_pole.isChecked() else 0
            melhor_volta = 1 if self.check_melhor_volta.isChecked() else 0

            # Lógica para evitar duplicidade de pole e melhor volta
            if pole:
                cursor.execute(
                    "SELECT 1 FROM resultados_etapas WHERE etapa_id=? AND categoria_id=? AND pole_position=1",
                    (self.etapa_id, self.categoria_id))
                if cursor.fetchone():
                    QMessageBox.warning(self, "Erro", "Já existe uma Pole Position atribuída nesta etapa.")
                    return
            if melhor_volta:
                cursor.execute("SELECT 1 FROM resultados_etapas WHERE etapa_id=? AND categoria_id=? AND melhor_volta=1",
                               (self.etapa_id, self.categoria_id))
                if cursor.fetchone():
                    QMessageBox.warning(self, "Erro", "Já existe uma Melhor Volta atribuída nesta etapa.")
                    return

            cursor.execute("""
                INSERT INTO resultados_etapas (etapa_id, piloto_id, categoria_id, posicao, pole_position, melhor_volta)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.etapa_id, piloto_id, self.categoria_id, posicao, pole, melhor_volta))
            conn.commit()
            super().accept()
        except ValueError:
            QMessageBox.warning(self, "Erro", "Posição deve ser um número válido.")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao inserir resultado: {e}")


# --- Widget Principal ---

class ResultadosEtapasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.etapa_id_atual = None
        self.categoria_id_atual = None
        self.init_ui()
        self.carregar_categorias()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Título
        label_titulo = QLabel("Resultados das Etapas")
        label_titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_titulo)

        # Controles
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Categoria:"))
        self.combo_categoria = QComboBox()
        controls_layout.addWidget(self.combo_categoria, 1)

        controls_layout.addWidget(QLabel("Etapa:"))
        self.combo_etapa = QComboBox()
        controls_layout.addWidget(self.combo_etapa, 2)
        main_layout.addLayout(controls_layout)

        # Tabela
        self.table_resultados = QTableWidget()
        self.table_resultados.setColumnCount(6)
        self.table_resultados.setHorizontalHeaderLabels(
            ["Piloto", "Posição", "Pole Position", "Melhor Volta", "ADV", "Categoria"])
        self.table_resultados.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_resultados.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_resultados.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_resultados.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table_resultados)

        # Botões de Ação
        botoes_layout = QHBoxLayout()
        btn_importar = QPushButton("Importar Resultados de Arquivo...")
        btn_desfazer = QPushButton("Desfazer Última Importação")
        botoes_layout.addWidget(btn_importar)
        botoes_layout.addWidget(btn_desfazer)
        botoes_layout.addStretch()
        btn_inserir = QPushButton("Inserir Manualmente")
        btn_editar = QPushButton("Editar Selecionado")
        botoes_layout.addWidget(btn_inserir)
        botoes_layout.addWidget(btn_editar)
        main_layout.addLayout(botoes_layout)

        # Conexões
        self.combo_categoria.currentIndexChanged.connect(self.atualizar_etapas)
        self.combo_etapa.currentIndexChanged.connect(self.carregar_resultados)
        btn_importar.clicked.connect(self.importar_arquivo)
        btn_desfazer.clicked.connect(self.desfazer_importacao)
        btn_inserir.clicked.connect(self.inserir_manual)
        btn_editar.clicked.connect(self.editar_resultado)

    # --- Métodos de Carregamento e Exibição ---

    def carregar_categorias(self):
        self.combo_categoria.clear()
        self.combo_categoria.addItem("-- Selecione --", userData=None)
        cursor.execute("SELECT id, nome FROM categorias ORDER BY nome")
        for cat_id, cat_nome in cursor.fetchall():
            self.combo_categoria.addItem(cat_nome, userData=cat_id)

    def atualizar_etapas(self):
        self.categoria_id_atual = self.combo_categoria.currentData()
        self.combo_etapa.clear()
        self.combo_etapa.addItem("-- Selecione --", userData=None)
        if self.categoria_id_atual:
            cursor.execute("SELECT id, nome FROM etapas ORDER BY data")
            for etapa_id, etapa_nome in cursor.fetchall():
                self.combo_etapa.addItem(etapa_nome, userData=etapa_id)
        self.carregar_resultados()

    def carregar_resultados(self):
        self.etapa_id_atual = self.combo_etapa.currentData()
        self.table_resultados.setRowCount(0)
        if not self.etapa_id_atual or not self.categoria_id_atual:
            return

        query = """
            SELECT p.nome, re.posicao, re.pole_position, re.melhor_volta, re.adv, c.nome
            FROM resultados_etapas re
            JOIN pilotos p ON p.id = re.piloto_id
            JOIN categorias c ON re.categoria_id = c.id
            WHERE re.etapa_id = ? AND re.categoria_id = ?
            ORDER BY re.posicao ASC
        """
        try:
            cursor.execute(query, (self.etapa_id_atual, self.categoria_id_atual))
            for i, row_data in enumerate(cursor.fetchall()):
                self.table_resultados.insertRow(i)
                piloto, pos, pole, mv, adv, cat = row_data
                self.table_resultados.setItem(i, 0, QTableWidgetItem(piloto.title()))
                self.table_resultados.setItem(i, 1, QTableWidgetItem(str(pos)))
                self.table_resultados.setItem(i, 2, QTableWidgetItem("Sim" if pole else "Não"))
                self.table_resultados.setItem(i, 3, QTableWidgetItem("Sim" if mv else "Não"))
                self.table_resultados.setItem(i, 4, QTableWidgetItem("Sim" if adv else "Não"))
                self.table_resultados.setItem(i, 5, QTableWidgetItem(cat))
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao carregar resultados: {e}")

    # --- Métodos de Extração (Lógica Pura) ---

    def extrair_dados_html(self, conteudo):
        soup = BeautifulSoup(conteudo, 'html.parser')
        dados = []
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 3:
                posicao = cols[0].text.strip()
                piloto_nome = cols[2].text.strip().lower()
                # Em HTML, não temos a info de melhor volta, então definimos como False
                dados.append({'posicao': int(posicao), 'nome': piloto_nome, 'melhor_volta': False})
        return dados

    def extrair_dados_pdf(self, conteudo):
        dados = []
        melhor_volta_piloto = ''
        linhas = conteudo.splitlines()

        for linha in linhas:
            if "MELHOR VOLTA:" in linha:
                try:
                    partes = linha.split(":", 1)[1]
                    melhor_volta_piloto = partes.split('(')[0].strip().lower()
                except IndexError:
                    pass
                continue

            partes = linha.strip().split()
            if len(partes) < 5: continue

            try:
                # Tentativa de identificar uma linha de resultado baseada em padrões
                posicao = int(partes[2])
                nome_parts = []
                for part in partes[4:]:
                    if part.isdigit() or part == 'SP': break
                    nome_parts.append(part)
                nome = ' '.join(nome_parts).strip().lower()
                if nome:
                    dados.append({'posicao': posicao, 'nome': nome, 'melhor_volta': False})
            except (ValueError, IndexError):
                continue

        # Atribui a melhor volta ao piloto correspondente
        for piloto_data in dados:
            if piloto_data['nome'] == melhor_volta_piloto:
                piloto_data['melhor_volta'] = True
        return dados

    def extrair_dados_csv(self, reader):
        dados = []
        next(reader, None)  # Pular cabeçalho
        for row in reader:
            try:
                posicao = int(row[0])
                piloto_nome = row[1].strip().lower()
                melhor_volta = 'melhor_volta' in row[2].lower()
                dados.append({'posicao': posicao, 'nome': piloto_nome, 'melhor_volta': melhor_volta})
            except (ValueError, IndexError):
                continue
        return dados

    # --- Métodos de Ação ---

    def importar_arquivo(self):
        if not self.etapa_id_atual or not self.categoria_id_atual:
            QMessageBox.warning(self, "Seleção Necessária", "Selecione uma categoria e uma etapa primeiro.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo de Resultados", "",
                                                   "Todos os Arquivos (*.pdf *.html *.csv)")
        if not file_path:
            return

        _, extensao = os.path.splitext(file_path)
        dados = []
        try:
            if extensao == ".pdf":
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    conteudo = "".join(page.extract_text() for page in reader.pages)
                    dados = self.extrair_dados_pdf(conteudo)
            elif extensao == ".html":
                with open(file_path, 'r', encoding='utf-8') as f:
                    dados = self.extrair_dados_html(f.read())
            elif extensao == ".csv":
                with open(file_path, 'r', encoding='utf-8') as f:
                    dados = self.extrair_dados_csv(csv.reader(f))
            else:
                QMessageBox.critical(self, "Erro", f"Formato de arquivo '{extensao}' não suportado.")
                return

            if not dados:
                QMessageBox.warning(self, "Aviso", "Nenhum dado de resultado válido foi extraído do arquivo.")
                return

            # Processar dados extraídos
            for item in dados:
                nome_piloto = item['nome']
                cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome_piloto,))
                piloto = cursor.fetchone()
                if not piloto:
                    cursor.execute("INSERT INTO pilotos (nome) VALUES (?)", (nome_piloto,))
                    piloto_id = cursor.lastrowid
                    cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                                   (piloto_id, self.categoria_id_atual))
                else:
                    piloto_id = piloto[0]

                cursor.execute("DELETE FROM resultados_etapas WHERE etapa_id=? AND piloto_id=?",
                               (self.etapa_id_atual, piloto_id))
                cursor.execute("""
                    INSERT INTO resultados_etapas (etapa_id, piloto_id, categoria_id, posicao, melhor_volta, importado_flag)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (self.etapa_id_atual, piloto_id, self.categoria_id_atual, item['posicao'], item['melhor_volta']))

            conn.commit()
            QMessageBox.information(self, "Sucesso", "Resultados importados com sucesso!")
            self.carregar_resultados()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erro de Importação", f"Ocorreu um erro: {e}")

    def desfazer_importacao(self):
        if not self.etapa_id_atual or not self.categoria_id_atual: return

        reply = QMessageBox.question(self, "Confirmar",
                                     "Tem certeza que deseja remover todos os resultados importados por arquivo para esta etapa/categoria?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                cursor.execute("DELETE FROM resultados_etapas WHERE etapa_id=? AND categoria_id=? AND importado_flag=1",
                               (self.etapa_id_atual, self.categoria_id_atual))
                conn.commit()
                QMessageBox.information(self, "Sucesso", "Importação desfeita com sucesso!")
                self.carregar_resultados()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao desfazer importação: {e}")

    def inserir_manual(self):
        if not self.etapa_id_atual or not self.categoria_id_atual:
            QMessageBox.warning(self, "Seleção Necessária", "Selecione uma categoria e uma etapa primeiro.")
            return

        dialog = ManualInsertDialog(self.etapa_id_atual, self.categoria_id_atual, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.carregar_resultados()

    def editar_resultado(self):
        selected_rows = self.table_resultados.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Seleção Inválida", "Selecione um resultado para editar.")
            return

        row = selected_rows[0].row()
        nome_piloto = self.table_resultados.item(row, 0).text()
        pos = self.table_resultados.item(row, 1).text()
        pole = self.table_resultados.item(row, 2).text()
        mv = self.table_resultados.item(row, 3).text()
        adv = self.table_resultados.item(row, 4).text()

        cursor.execute("SELECT id FROM pilotos WHERE LOWER(nome) = ?", (nome_piloto.lower(),))
        piloto_id_res = cursor.fetchone()
        if not piloto_id_res:
            QMessageBox.critical(self, "Erro", "Piloto não encontrado no banco de dados.")
            return
        piloto_id = piloto_id_res[0]

        dialog = EditarResultadoDialog(self.etapa_id_atual, self.categoria_id_atual, piloto_id, nome_piloto, pos, pole,
                                       mv, adv, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.carregar_resultados()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QMainWindow()
    # ... (Setup de banco de dados em memória para teste) ...
    main_widget = ResultadosEtapasWidget()
    window.setCentralWidget(main_widget)
    window.resize(1024, 768)
    window.show()
    sys.exit(app.exec())