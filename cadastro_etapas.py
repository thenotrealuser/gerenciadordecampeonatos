import sys
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QMessageBox, QDialog, QDialogButtonBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from database import cursor, conn


class EditarEtapaDialog(QDialog):
    """
    Janela de diálogo para editar o nome e a data de uma etapa existente.
    """

    def __init__(self, nome_etapa, data_etapa, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Etapa")
        self.setModal(True)
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # Campo para Nome da Etapa
        layout.addWidget(QLabel("Nome da Etapa:"))
        self.entry_nome = QLineEdit(nome_etapa)
        layout.addWidget(self.entry_nome)

        # Campo para Data da Etapa
        layout.addWidget(QLabel("Data da Etapa:"))
        self.entry_data = QDateEdit()
        self.entry_data.setDisplayFormat("dd/MM/yyyy")
        self.entry_data.setDate(QDate.fromString(data_etapa, "dd/MM/yyyy"))
        self.entry_data.setCalendarPopup(True)
        layout.addWidget(self.entry_data)

        # Botões
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self):
        """Retorna os dados inseridos pelo usuário."""
        nome = self.entry_nome.text().strip()
        data = self.entry_data.date().toString("dd/MM/yyyy")
        if nome and data:
            return nome, data
        return None, None


class CadastroEtapasWidget(QWidget):
    """
    Widget para o cadastro, edição e remoção de etapas do campeonato.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.carregar_etapas()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Título
        label_titulo = QLabel("Cadastro de Etapas")
        font = QFont("Arial", 16, QFont.Weight.Bold)
        label_titulo.setFont(font)
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_titulo)

        # Seção de Cadastro
        cadastro_layout = QHBoxLayout()
        self.entry_nome = QLineEdit()
        self.entry_nome.setPlaceholderText("Nome da Etapa")
        self.entry_data = QDateEdit()
        self.entry_data.setDisplayFormat("dd/MM/yyyy")
        self.entry_data.setDate(QDate.currentDate())
        self.entry_data.setCalendarPopup(True)
        btn_salvar = QPushButton("Salvar Etapa")
        btn_salvar.clicked.connect(self.salvar_etapa)

        cadastro_layout.addWidget(QLabel("Nome:"))
        cadastro_layout.addWidget(self.entry_nome, 2)  # Ocupa mais espaço
        cadastro_layout.addWidget(QLabel("Data:"))
        cadastro_layout.addWidget(self.entry_data, 1)
        cadastro_layout.addWidget(btn_salvar, 1)
        main_layout.addLayout(cadastro_layout)

        # Tabela de Etapas Cadastradas
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Nome", "Data"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table)

        # Botões de Ação
        botoes_acao_layout = QHBoxLayout()
        btn_editar = QPushButton("Editar Etapa Selecionada")
        btn_editar.clicked.connect(self.editar_etapa)
        btn_remover = QPushButton("Remover Etapa Selecionada")
        btn_remover.clicked.connect(self.remover_etapa)

        botoes_acao_layout.addStretch()
        botoes_acao_layout.addWidget(btn_editar)
        botoes_acao_layout.addWidget(btn_remover)
        main_layout.addLayout(botoes_acao_layout)

    def carregar_etapas(self):
        """Carrega e exibe a lista de etapas cadastradas na tabela."""
        try:
            self.table.setRowCount(0)
            cursor.execute("SELECT nome, data FROM etapas ORDER BY data")
            etapas = cursor.fetchall()
            for row_num, etapa_data in enumerate(etapas):
                self.table.insertRow(row_num)
                self.table.setItem(row_num, 0, QTableWidgetItem(etapa_data[0]))
                self.table.setItem(row_num, 1, QTableWidgetItem(etapa_data[1]))
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao carregar etapas: {e}")

    def salvar_etapa(self):
        """Salva uma nova etapa no banco de dados."""
        nome = self.entry_nome.text().strip()
        data = self.entry_data.date().toString("dd/MM/yyyy")
        if not nome or not data:
            QMessageBox.warning(self, "Campos Vazios", "Nome e Data da etapa são obrigatórios.")
            return

        try:
            cursor.execute("INSERT INTO etapas (nome, data) VALUES (?, ?)", (nome, data))
            conn.commit()
            QMessageBox.information(self, "Sucesso", "Etapa cadastrada com sucesso!")
            self.entry_nome.clear()
            self.entry_data.setDate(QDate.currentDate())
            self.carregar_etapas()
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao salvar etapa: {e}")

    def editar_etapa(self):
        """Abre um diálogo para editar a etapa selecionada."""
        selected_rows = self.table.selectionModel().selectedRows()
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Seleção Inválida", "Selecione exatamente uma etapa para editar.")
            return

        selected_row = selected_rows[0].row()
        nome_antigo = self.table.item(selected_row, 0).text()
        data_antiga = self.table.item(selected_row, 1).text()

        dialog = EditarEtapaDialog(nome_antigo, data_antiga, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            novo_nome, nova_data = dialog.get_data()
            if novo_nome:
                try:
                    cursor.execute("UPDATE etapas SET nome = ?, data = ? WHERE nome = ?",
                                   (novo_nome, nova_data, nome_antigo))
                    conn.commit()
                    QMessageBox.information(self, "Sucesso", "Etapa atualizada com sucesso!")
                    self.carregar_etapas()
                except Exception as e:
                    QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao salvar alterações: {e}")

    def remover_etapa(self):
        """Remove a etapa selecionada do banco de dados."""
        selected_rows = self.table.selectionModel().selectedRows()
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Seleção Inválida", "Selecione exatamente uma etapa para remover.")
            return

        selected_row = selected_rows[0].row()
        nome_etapa = self.table.item(selected_row, 0).text()

        confirmacao = QMessageBox.question(self, "Confirmar Remoção",
                                           f"Tem certeza que deseja remover a etapa '{nome_etapa}'?\nIsso também removerá todos os resultados associados a ela.",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirmacao == QMessageBox.StandardButton.Yes:
            try:
                # Obter o ID da etapa para remover os resultados
                cursor.execute("SELECT id FROM etapas WHERE nome = ?", (nome_etapa,))
                etapa_id_result = cursor.fetchone()
                if etapa_id_result:
                    etapa_id = etapa_id_result[0]
                    # Remover resultados associados
                    cursor.execute("DELETE FROM resultados_etapas WHERE etapa_id = ?", (etapa_id,))

                # Remover a etapa
                cursor.execute("DELETE FROM etapas WHERE nome = ?", (nome_etapa,))

                conn.commit()
                QMessageBox.information(self, "Sucesso", "Etapa removida com sucesso!")
                self.carregar_etapas()
            except Exception as e:
                QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao remover etapa: {e}")


# Bloco para teste individual do widget
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow


    def setup_test_database():
        conn_test = sqlite3.connect('campeonato_test.db')
        cursor_test = conn_test.cursor()
        cursor_test.execute('''
            CREATE TABLE IF NOT EXISTS etapas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                data TEXT
            );
        ''')
        cursor_test.execute('''
            CREATE TABLE IF NOT EXISTS resultados_etapas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                etapa_id INTEGER,
                piloto_id INTEGER,
                categoria_id INTEGER,
                posicao INTEGER,
                pole_position BOOLEAN DEFAULT 0,
                melhor_volta BOOLEAN DEFAULT 0,
                adv BOOLEAN DEFAULT 0,
                importado_do_pdf BOOLEAN DEFAULT 0,
                FOREIGN KEY(etapa_id) REFERENCES etapas(id),
                FOREIGN KEY(piloto_id) REFERENCES pilotos(id),
                FOREIGN KEY(categoria_id) REFERENCES categorias(id)
            );
        ''')
        conn_test.commit()
        return conn_test, cursor_test


    conn, cursor = setup_test_database()

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Teste do Cadastro de Etapas")
    window.setCentralWidget(CadastroEtapasWidget())
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec())