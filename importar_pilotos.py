import sys
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import cursor, conn


class ImportarPilotosWidget(QWidget):
    """
    Widget para importar uma lista de pilotos de um arquivo .txt ou .csv
    e associá-los a uma categoria específica.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.categorias_map = {}  # Dicionário para mapear nome da categoria para ID
        self.init_ui()
        self.carregar_categorias()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título
        label_titulo = QLabel("Importar Lista de Pilotos")
        font = QFont("Arial", 16, QFont.Weight.Bold)
        label_titulo.setFont(font)
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_titulo)

        # Seletor de Categoria
        label_categoria = QLabel("1. Selecione a categoria para associar os pilotos:")
        main_layout.addWidget(label_categoria)

        self.combo_categoria = QComboBox()
        main_layout.addWidget(self.combo_categoria)

        # Botão para selecionar arquivo
        label_arquivo = QLabel("2. Selecione o arquivo de texto (.txt) ou CSV (.csv):")
        main_layout.addWidget(label_arquivo)

        btn_selecionar_arquivo = QPushButton("Selecionar Arquivo e Importar")
        btn_selecionar_arquivo.clicked.connect(self.selecionar_e_importar_arquivo)
        main_layout.addWidget(btn_selecionar_arquivo)

        main_layout.addStretch()  # Empurra os widgets para cima

    def carregar_categorias(self):
        """Busca as categorias no banco de dados e preenche o QComboBox."""
        try:
            cursor.execute("SELECT id, nome FROM categorias ORDER BY nome")
            categorias = cursor.fetchall()
            self.combo_categoria.clear()
            self.categorias_map.clear()

            self.combo_categoria.addItem("-- Selecione uma categoria --")
            for cat_id, cat_nome in categorias:
                self.combo_categoria.addItem(cat_nome)
                self.categorias_map[cat_nome] = cat_id
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao carregar categorias: {e}")

    def selecionar_e_importar_arquivo(self):
        """Abre o diálogo de seleção de arquivo e inicia a importação."""
        categoria_nome = self.combo_categoria.currentText()
        if not categoria_nome or categoria_nome == "-- Selecione uma categoria --":
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione uma categoria antes de importar.")
            return

        categoria_id = self.categorias_map.get(categoria_nome)
        if categoria_id is None:
            QMessageBox.critical(self, "Erro", "A categoria selecionada é inválida.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Pilotos",
            "",  # Diretório inicial
            "Arquivos de Texto (*.txt);;Arquivos CSV (*.csv);;Todos os Arquivos (*)"
        )

        if file_path:
            self.importar_pilotos_do_arquivo(file_path, categoria_id)

    def importar_pilotos_do_arquivo(self, arquivo_path, categoria_id):
        """Lê o arquivo e insere os pilotos no banco de dados."""
        try:
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                linhas = f.readlines()

            pilotos = [linha.strip() for linha in linhas if linha.strip()]
            pilotos_importados = 0
            pilotos_associados = 0

            for nome in pilotos:
                nome_normalizado = nome.strip().lower()
                if not nome_normalizado:
                    continue

                # Verifica se o piloto já existe ou o insere
                cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome_normalizado,))
                piloto_result = cursor.fetchone()
                if piloto_result:
                    piloto_id = piloto_result[0]
                else:
                    cursor.execute("INSERT INTO pilotos (nome) VALUES (?)", (nome_normalizado,))
                    piloto_id = cursor.lastrowid
                    pilotos_importados += 1

                # Associa o piloto à categoria, ignorando se a associação já existir
                try:
                    cursor.execute(
                        "INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                        (piloto_id, categoria_id)
                    )
                    pilotos_associados += 1
                except sqlite3.IntegrityError:
                    # O piloto já estava associado a esta categoria, ignora o erro.
                    continue

            conn.commit()
            mensagem = (f"Importação concluída!\n\n"
                        f"- {pilotos_importados} novo(s) piloto(s) cadastrado(s).\n"
                        f"- {pilotos_associados} piloto(s) associado(s) à categoria.")
            QMessageBox.information(self, "Sucesso", mensagem)
        except Exception as e:
            QMessageBox.critical(self, "Erro na Importação", f"Ocorreu um erro ao importar os pilotos: {e}")


# Bloco para teste individual do widget
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow


    def setup_test_database():
        conn_test = sqlite3.connect(':memory:')
        cursor_test = conn_test.cursor()

        cursor_test.execute("CREATE TABLE categorias (id INTEGER PRIMARY KEY, nome TEXT UNIQUE)")
        cursor_test.execute("CREATE TABLE pilotos (id INTEGER PRIMARY KEY, nome TEXT UNIQUE)")
        cursor_test.execute("""
            CREATE TABLE pilotos_categorias (
                piloto_id INTEGER, 
                categoria_id INTEGER,
                PRIMARY KEY (piloto_id, categoria_id)
            )
        """)

        cursor_test.execute("INSERT INTO categorias (nome) VALUES ('Graduados'), ('Novatos')")
        cursor_test.execute("INSERT INTO pilotos (nome) VALUES ('ayrton senna')")
        cursor_test.execute("INSERT INTO pilotos_categorias VALUES (1, 1)")

        conn_test.commit()
        return conn_test, cursor_test


    conn, cursor = setup_test_database()

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Teste de Importação de Pilotos")
    window.setCentralWidget(ImportarPilotosWidget())
    window.resize(500, 300)
    window.show()
    sys.exit(app.exec())