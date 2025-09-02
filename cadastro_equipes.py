import sys
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import cursor, conn


class CadastroTimesWidget(QWidget):
    """
    Widget para o cadastro, edição e remoção de times (equipes) do campeonato.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.carregar_times()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Título
        label_titulo = QLabel("Cadastro de Times")
        font = QFont("Arial", 16, QFont.Weight.Bold)
        label_titulo.setFont(font)
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_titulo)

        # Seção de Cadastro
        cadastro_layout = QHBoxLayout()
        label_nome_time = QLabel("Nome do Time:")
        self.entry_nome_time = QLineEdit()
        self.entry_nome_time.setPlaceholderText("Digite o nome do time")
        self.entry_nome_time.returnPressed.connect(self.salvar_time)  # Salva ao pressionar Enter
        btn_salvar_time = QPushButton("Salvar Time")
        btn_salvar_time.clicked.connect(self.salvar_time)

        cadastro_layout.addWidget(label_nome_time)
        cadastro_layout.addWidget(self.entry_nome_time)
        cadastro_layout.addWidget(btn_salvar_time)
        main_layout.addLayout(cadastro_layout)

        # Seção da Lista de Times
        label_lista_times = QLabel("Times Cadastrados")
        font_lista = QFont("Arial", 12, QFont.Weight.Bold)
        label_lista_times.setFont(font_lista)
        main_layout.addWidget(label_lista_times, 0, Qt.AlignmentFlag.AlignLeft)

        self.table = QTableWidget()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Nome"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table)

        # Botões de Ação (Editar, Remover)
        botoes_acao_layout = QHBoxLayout()
        btn_editar_time = QPushButton("Editar Time Selecionado")
        btn_editar_time.clicked.connect(self.editar_time)
        btn_remover_time = QPushButton("Remover Time(s) Selecionado(s)")
        btn_remover_time.clicked.connect(self.remover_time)

        botoes_acao_layout.addStretch()
        botoes_acao_layout.addWidget(btn_editar_time)
        botoes_acao_layout.addWidget(btn_remover_time)
        main_layout.addLayout(botoes_acao_layout)

    def salvar_time(self):
        """Salva um novo time no banco de dados."""
        nome_time = self.entry_nome_time.text().strip()
        if not nome_time:
            QMessageBox.warning(self, "Campo Vazio", "O nome do time é obrigatório.")
            return

        try:
            cursor.execute("SELECT id FROM times WHERE LOWER(nome) = ?", (nome_time.lower(),))
            if cursor.fetchone():
                QMessageBox.warning(self, "Nome Duplicado", "Já existe um time com esse nome.")
                return

            cursor.execute("INSERT INTO times (nome) VALUES (?)", (nome_time,))
            conn.commit()
            QMessageBox.information(self, "Sucesso", "Time cadastrado com sucesso!")
            self.entry_nome_time.clear()
            self.carregar_times()
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao salvar time: {e}")

    def carregar_times(self):
        """Carrega e exibe a lista de times cadastrados na tabela."""
        try:
            self.table.setRowCount(0)
            cursor.execute("SELECT nome FROM times ORDER BY nome")
            times = cursor.fetchall()
            for row_num, time_data in enumerate(times):
                self.table.insertRow(row_num)
                self.table.setItem(row_num, 0, QTableWidgetItem(time_data[0]))
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao carregar times: {e}")

    def editar_time(self):
        """Abre um diálogo para editar o nome do time selecionado."""
        selected_rows = self.table.selectionModel().selectedRows()
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Seleção Inválida", "Selecione exatamente um time para editar.")
            return

        selected_row = selected_rows[0].row()
        nome_atual = self.table.item(selected_row, 0).text()

        novo_nome, ok = QInputDialog.getText(self, "Editar Time", f"Digite o novo nome para '{nome_atual}':",
                                             text=nome_atual)

        if ok and novo_nome.strip():
            novo_nome = novo_nome.strip()
            if novo_nome.lower() == nome_atual.lower():
                return  # Nenhuma alteração

            try:
                cursor.execute("SELECT id FROM times WHERE LOWER(nome) = ?", (novo_nome.lower(),))
                if cursor.fetchone():
                    QMessageBox.warning(self, "Nome Duplicado", "Já existe um time com esse nome.")
                    return

                cursor.execute("UPDATE times SET nome = ? WHERE nome = ?", (novo_nome, nome_atual))
                conn.commit()
                QMessageBox.information(self, "Sucesso", "Time atualizado com sucesso!")
                self.carregar_times()
            except Exception as e:
                QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao editar time: {e}")

    def remover_time(self):
        """Remove os times selecionados do banco de dados."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Seleção Necessária", "Selecione um ou mais times para remover.")
            return

        nomes_times = [self.table.item(row.row(), 0).text() for row in selected_rows]

        confirmacao = QMessageBox.question(self, "Confirmar Remoção",
                                           f"Tem certeza que deseja remover os seguintes times?\n\n- {', '.join(nomes_times)}\n\nEsta ação não pode ser desfeita.",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirmacao == QMessageBox.StandardButton.Yes:
            try:
                for nome_time in nomes_times:
                    cursor.execute("SELECT id FROM times WHERE nome = ?", (nome_time,))
                    time = cursor.fetchone()
                    if time:
                        time_id = time[0]
                        # Remove associações de pilotos com este time
                        cursor.execute("DELETE FROM pilotos_times WHERE time_id = ?", (time_id,))
                        # Remove o time
                        cursor.execute("DELETE FROM times WHERE id = ?", (time_id,))

                conn.commit()
                QMessageBox.information(self, "Sucesso", "Times removidos com sucesso!")
                self.carregar_times()
            except Exception as e:
                QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao remover times: {e}")


# Bloco para teste individual do widget
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow


    def setup_test_database():
        conn_test = sqlite3.connect('campeonato_test.db')
        cursor_test = conn_test.cursor()
        cursor_test.execute('''
            CREATE TABLE IF NOT EXISTS times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL
            );
        ''')
        cursor_test.execute('''
            CREATE TABLE IF NOT EXISTS pilotos_times (
                piloto_id INTEGER UNIQUE,
                time_id INTEGER,
                FOREIGN KEY (piloto_id) REFERENCES pilotos(id),
                FOREIGN KEY (time_id) REFERENCES times(id)
            );
        ''')
        conn_test.commit()
        return conn_test, cursor_test


    conn, cursor = setup_test_database()

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Teste do Cadastro de Times")
    window.setCentralWidget(CadastroTimesWidget())
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec())