import sys
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QDialog,
    QLineEdit, QListWidget, QGroupBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIntValidator
from database import cursor, conn


class AdicionarPosicaoDialog(QDialog):
    """
    Janela de diálogo para adicionar uma nova pontuação para uma posição específica.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Posição")
        self.setModal(True)
        self.setFixedSize(300, 220)

        layout = QVBoxLayout(self)

        # Campo para Posição
        label_posicao = QLabel("Posição (nº):")
        self.entry_posicao = QLineEdit()
        self.entry_posicao.setPlaceholderText("Ex: 1")
        self.entry_posicao.setValidator(QIntValidator(1, 999))  # Aceita apenas inteiros positivos

        # Campo para Pontos
        label_pontos = QLabel("Pontos:")
        self.entry_pontos = QLineEdit()
        self.entry_pontos.setPlaceholderText("Ex: 25")
        self.entry_pontos.setValidator(QIntValidator(0, 9999))  # Aceita apenas inteiros não-negativos

        layout.addWidget(label_posicao)
        layout.addWidget(self.entry_posicao)
        layout.addWidget(label_pontos)
        layout.addWidget(self.entry_pontos)
        layout.addStretch()

        # Botões de Salvar e Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self):
        """Retorna os dados inseridos pelo usuário."""
        posicao = self.entry_posicao.text()
        pontos = self.entry_pontos.text()
        if posicao and pontos:
            return int(posicao), int(pontos)
        return None, None


class SistemaPontuacaoWidget(QWidget):
    """
    Widget para configurar o sistema de pontuação padrão do campeonato.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.carregar_pontos()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Título
        label_titulo = QLabel("Sistema de Pontuação (Padrão para todas as categorias)")
        font = QFont("Arial", 16, QFont.Weight.Bold)
        label_titulo.setFont(font)
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_titulo)

        # Layout principal dividido em duas colunas
        h_layout = QHBoxLayout()

        # --- Coluna da Esquerda (Pontos por Posição) ---
        pontos_groupbox = QGroupBox("Pontos por Posição")
        pontos_layout = QVBoxLayout(pontos_groupbox)

        self.lista_pontos = QListWidget()
        pontos_layout.addWidget(self.lista_pontos)

        botoes_posicao_layout = QHBoxLayout()
        btn_adicionar_posicao = QPushButton("Adicionar Posição")
        btn_adicionar_posicao.clicked.connect(self.adicionar_posicao)
        self.btn_remover_posicao = QPushButton("Remover Posição Selecionada")
        self.btn_remover_posicao.clicked.connect(self.remover_posicao)

        botoes_posicao_layout.addWidget(btn_adicionar_posicao)
        botoes_posicao_layout.addWidget(self.btn_remover_posicao)
        pontos_layout.addLayout(botoes_posicao_layout)

        h_layout.addWidget(pontos_groupbox, 1)  # Ocupa 1/2 do espaço

        # --- Coluna da Direita (Pontos Extras) ---
        extras_groupbox = QGroupBox("Pontuação Extra")
        extras_layout = QVBoxLayout(extras_groupbox)
        extras_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        label_pole = QLabel("Pontos por Pole Position:")
        self.entry_pontos_pole = QLineEdit()
        self.entry_pontos_pole.setPlaceholderText("Ex: 3")
        self.entry_pontos_pole.setValidator(QIntValidator(0, 100))

        label_melhor_volta = QLabel("Pontos por Melhor Volta:")
        self.entry_pontos_melhor_volta = QLineEdit()
        self.entry_pontos_melhor_volta.setPlaceholderText("Ex: 5")
        self.entry_pontos_melhor_volta.setValidator(QIntValidator(0, 100))

        extras_layout.addWidget(label_pole)
        extras_layout.addWidget(self.entry_pontos_pole)
        extras_layout.addWidget(label_melhor_volta)
        extras_layout.addWidget(self.entry_pontos_melhor_volta)
        extras_layout.addStretch()

        btn_salvar_pontuacao = QPushButton("Salvar Pontuação Extra")
        btn_salvar_pontuacao.clicked.connect(self.salvar_pontuacao)
        extras_layout.addWidget(btn_salvar_pontuacao)

        h_layout.addWidget(extras_groupbox, 1)  # Ocupa 1/2 do espaço

        main_layout.addLayout(h_layout)

    def carregar_pontos(self):
        """Carrega as pontuações do banco de dados e atualiza a UI."""
        self.lista_pontos.clear()
        try:
            cursor.execute("SELECT posicao, pontos FROM sistema_pontuacao ORDER BY posicao")
            pontos = cursor.fetchall()
            for pos, pts in pontos:
                self.lista_pontos.addItem(f"{pos}º Lugar: {pts} pontos")

            cursor.execute("SELECT pole_position, melhor_volta FROM sistema_pontuacao_extras LIMIT 1")
            extras = cursor.fetchone()
            if extras:
                self.entry_pontos_pole.setText(str(extras[0]))
                self.entry_pontos_melhor_volta.setText(str(extras[1]))
            else:
                self.entry_pontos_pole.clear()
                self.entry_pontos_melhor_volta.clear()

        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Não foi possível carregar as pontuações: {e}")

    def adicionar_posicao(self):
        """Abre a janela de diálogo para adicionar uma nova posição e pontos."""
        dialog = AdicionarPosicaoDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            posicao, pontos = dialog.get_data()
            if posicao is not None:
                try:
                    cursor.execute("INSERT INTO sistema_pontuacao (posicao, pontos) VALUES (?, ?)", (posicao, pontos))
                    conn.commit()
                    QMessageBox.information(self, "Sucesso", "Pontos adicionados com sucesso.")
                    self.carregar_pontos()
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "Erro de Duplicidade", "Pontos para essa posição já estão configurados.")
                except Exception as e:
                    QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao salvar pontos: {e}")

    def remover_posicao(self):
        """Remove a pontuação da posição selecionada na lista."""
        item_selecionado = self.lista_pontos.currentItem()
        if not item_selecionado:
            QMessageBox.warning(self, "Seleção Necessária", "Selecione uma posição para remover.")
            return

        texto_item = item_selecionado.text()
        try:
            posicao = int(texto_item.split('º')[0])

            confirmacao = QMessageBox.question(self, "Confirmar Remoção",
                                               f"Tem certeza que deseja remover a pontuação para a {posicao}ª posição?",
                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if confirmacao == QMessageBox.StandardButton.Yes:
                cursor.execute("DELETE FROM sistema_pontuacao WHERE posicao = ?", (posicao,))
                conn.commit()
                self.carregar_pontos()
                QMessageBox.information(self, "Sucesso", "Pontos removidos com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao remover pontos: {e}")

    def salvar_pontuacao(self):
        """Salva os pontos extras para pole position e melhor volta."""
        try:
            pontos_pole_text = self.entry_pontos_pole.text()
            pontos_melhor_volta_text = self.entry_pontos_melhor_volta.text()

            # Define 0 se o campo estiver vazio
            pontos_pole = int(pontos_pole_text) if pontos_pole_text else 0
            pontos_melhor_volta = int(pontos_melhor_volta_text) if pontos_melhor_volta_text else 0

            # Garante que a tabela tenha uma linha (ID 1, por exemplo)
            cursor.execute("SELECT COUNT(*) FROM sistema_pontuacao_extras")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO sistema_pontuacao_extras (id, pole_position, melhor_volta) VALUES (1, ?, ?)",
                    (pontos_pole, pontos_melhor_volta))
            else:
                cursor.execute("UPDATE sistema_pontuacao_extras SET pole_position = ?, melhor_volta = ? WHERE id = 1",
                               (pontos_pole, pontos_melhor_volta))

            conn.commit()
            QMessageBox.information(self, "Sucesso", "Pontuação extra salva com sucesso!")
        except ValueError:
            QMessageBox.critical(self, "Erro de Entrada", "Por favor, insira valores numéricos válidos para os pontos.")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao salvar pontuação: {e}")


# Bloco para teste individual do widget (opcional)
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow


    # Configuração de banco de dados para teste
    def setup_test_database():
        conn_test = sqlite3.connect('campeonato_test.db')
        cursor_test = conn_test.cursor()
        cursor_test.execute('''
            CREATE TABLE IF NOT EXISTS sistema_pontuacao (
                posicao INTEGER PRIMARY KEY,
                pontos INTEGER NOT NULL
            );
        ''')
        cursor_test.execute('''
            CREATE TABLE IF NOT EXISTS sistema_pontuacao_extras (
                id INTEGER PRIMARY KEY DEFAULT 1,
                pole_position INTEGER DEFAULT 0,
                melhor_volta INTEGER DEFAULT 0
            );
        ''')
        conn_test.commit()
        return conn_test, cursor_test


    conn, cursor = setup_test_database()

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Teste do Sistema de Pontuação")
    window.setCentralWidget(SistemaPontuacaoWidget())
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())