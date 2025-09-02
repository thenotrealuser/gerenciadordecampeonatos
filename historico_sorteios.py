import sys
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import cursor, conn


class HistoricoSorteiosWidget(QWidget):
    """
    Widget para exibir o histórico de todos os sorteios de karts realizados.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.carregar_historico()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Título
        label_titulo = QLabel("Histórico de Sorteios")
        font = QFont("Arial", 16, QFont.Weight.Bold)
        label_titulo.setFont(font)
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_titulo)

        # Tabela para exibir o histórico
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Categoria", "Piloto", "Kart", "Data do Sorteio"])

        # Ajuste das colunas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        main_layout.addWidget(self.table)

    def carregar_historico(self):
        """
        Carrega os dados de sorteios do banco de dados e preenche a tabela.
        A consulta foi otimizada para usar JOINs, evitando múltiplas queries em um loop.
        """
        try:
            self.table.setRowCount(0)

            query = """
                SELECT 
                    c.nome AS categoria_nome, 
                    p.nome AS piloto_nome, 
                    h.kart, 
                    h.data_sorteio
                FROM historico_sorteios h
                JOIN categorias c ON h.categoria_id = c.id
                JOIN pilotos p ON h.piloto_id = p.id
                ORDER BY h.data_sorteio DESC
            """

            cursor.execute(query)
            sorteios = cursor.fetchall()

            for row_num, sorteio_data in enumerate(sorteios):
                self.table.insertRow(row_num)
                categoria, piloto, kart, data = sorteio_data

                self.table.setItem(row_num, 0, QTableWidgetItem(str(categoria)))
                self.table.setItem(row_num, 1, QTableWidgetItem(str(piloto)))
                self.table.setItem(row_num, 2, QTableWidgetItem(str(kart)))
                self.table.setItem(row_num, 3, QTableWidgetItem(str(data)))

        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao carregar o histórico de sorteios: {e}")


# Bloco para teste individual do widget
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow


    def setup_test_database():
        conn_test = sqlite3.connect(':memory:')  # Banco de dados em memória para teste
        cursor_test = conn_test.cursor()

        # Criar tabelas
        cursor_test.execute("CREATE TABLE categorias (id INTEGER PRIMARY KEY, nome TEXT)")
        cursor_test.execute("CREATE TABLE pilotos (id INTEGER PRIMARY KEY, nome TEXT)")
        cursor_test.execute("""
            CREATE TABLE historico_sorteios (
                id INTEGER PRIMARY KEY, 
                categoria_id INTEGER, 
                piloto_id INTEGER, 
                kart INTEGER, 
                data_sorteio TEXT
            )
        """)

        # Inserir dados de exemplo
        cursor_test.execute("INSERT INTO categorias VALUES (1, 'Graduados'), (2, 'Novatos')")
        cursor_test.execute(
            "INSERT INTO pilotos VALUES (10, 'Ayrton Senna'), (11, 'Alain Prost'), (12, 'Nelson Piquet')")
        cursor_test.execute("INSERT INTO historico_sorteios VALUES (1, 1, 10, 25, '2025-08-30 10:00:00')")
        cursor_test.execute("INSERT INTO historico_sorteios VALUES (2, 2, 11, 12, '2025-08-30 10:05:00')")
        cursor_test.execute("INSERT INTO historico_sorteios VALUES (3, 1, 12, 7, '2025-08-23 11:00:00')")

        conn_test.commit()
        return conn_test, cursor_test


    conn, cursor = setup_test_database()

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Teste do Histórico de Sorteios")
    window.setCentralWidget(HistoricoSorteiosWidget())
    window.resize(700, 500)
    window.show()
    sys.exit(app.exec())