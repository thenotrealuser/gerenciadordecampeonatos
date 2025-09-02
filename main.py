import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel,
    QSplitter, QScrollArea, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# --- IMPORTS DOS WIDGETS ---
from cadastro_pilotos_categorias import CadastroCategoriasWidget, CadastroPilotosWidget
from cadastro_equipes import CadastroTimesWidget
from cadastro_etapas import CadastroEtapasWidget
from frame_resultado_etapas import ResultadosEtapasWidget
from resultado_geral_frame import ResultadoGeralWidget
from sorteio_karts import SorteioKartsWidget
from importar_pilotos import ImportarPilotosWidget
from sistema_pontuacao import SistemaPontuacaoWidget
from historico_sorteios import HistoricoSorteiosWidget
# A LINHA "from auth import LoginDialog" FOI REMOVIDA
# ---------------------------

from database import conn


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gerenciamento de Campeonato de Karts by :::Kimi Morgam:::")
        self.setMinimumSize(1280, 720)

        # --- TEMA ESTÁVEL CINZA ESCURO ---
        self.setStyleSheet("""
            QWidget {
                background-color: #333333;
                color: #F0F0F0;
                font-size: 14px;
                border: none;
            }
            QMainWindow, QDialog {
                background-color: #333333;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            #resetButton {
                background-color: #D32F2F;
            }
            #resetButton:hover {
                background-color: #B71C1C;
            }
            QLineEdit, QComboBox, QTextEdit, QDateEdit, QListWidget, QTableWidget, QGroupBox {
                background-color: #444444;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #555555;
                padding: 6px;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #0078D7;
            }
            QSplitter::handle {
                background-color: #555555;
            }
        """)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.setCentralWidget(splitter)

        # Menu Esquerdo
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setContentsMargins(10, 10, 10, 10)
        title_label = QLabel("MENU PRINCIPAL")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        menu_layout.addWidget(title_label)

        menu_scroll = QScrollArea()
        menu_scroll.setWidgetResizable(True)
        menu_scroll_widget = QWidget()
        menu_scroll_layout = QVBoxLayout(menu_scroll_widget)
        menu_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        buttons = [
            ("Cadastro de Categorias", self.show_cadastro_categorias),
            ("Cadastro de Pilotos", self.show_cadastro_pilotos),
            ("Cadastro de Times", self.show_cadastro_times),
            ("Cadastro de Etapas", self.show_cadastro_etapas),
            ("Resultados das Etapas", self.show_resultados_etapas),
            ("Resultado Geral", self.show_resultado_geral),
            ("Sorteio de Karts", self.show_sorteio_karts),
            ("Importar Pilotos", self.show_importar_pilotos),
            ("Sistema de Pontuação", self.show_sistema_pontuacao),
            ("Sistema de Pagamentos", self.show_sistema_pagamentos),
            ("Histórico de Sorteios", self.show_historico_sorteios),
            ("Resetar Campeonato", self.resetar_campeonato)
        ]

        for text, command in buttons:
            btn = QPushButton(text)
            if text == "Resetar Campeonato": btn.setObjectName("resetButton")
            btn.clicked.connect(command)
            menu_scroll_layout.addWidget(btn)

        menu_scroll.setWidget(menu_scroll_widget)
        menu_layout.addWidget(menu_scroll)
        splitter.addWidget(menu_widget)

        # Conteúdo Direito
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setWidget(self.content_widget)
        splitter.addWidget(content_scroll)
        splitter.setSizes([250, 800])
        self.show_cadastro_categorias()

    def clear_content(self):
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget: widget.deleteLater()

    def show_widget(self, widget_class):
        self.clear_content()
        widget = widget_class(self.content_widget)
        self.content_layout.addWidget(widget)

    def show_cadastro_categorias(self):
        self.show_widget(CadastroCategoriasWidget)

    def show_cadastro_pilotos(self):
        self.show_widget(CadastroPilotosWidget)

    def show_cadastro_times(self):
        self.show_widget(CadastroTimesWidget)

    def show_cadastro_etapas(self):
        self.show_widget(CadastroEtapasWidget)

    def show_resultados_etapas(self):
        self.show_widget(ResultadosEtapasWidget)

    def show_resultado_geral(self):
        self.show_widget(ResultadoGeralWidget)

    def show_sorteio_karts(self):
        self.show_widget(SorteioKartsWidget)

    def show_importar_pilotos(self):
        self.show_widget(ImportarPilotosWidget)

    def show_sistema_pontuacao(self):
        self.show_widget(SistemaPontuacaoWidget)

    def show_sistema_pagamentos(self):
        from sistema_pagamentos import SistemaPagamentosWidget; self.show_widget(SistemaPagamentosWidget)

    def show_historico_sorteios(self):
        self.show_widget(HistoricoSorteiosWidget)

    def resetar_campeonato(self):
        dialog = ResetarCampeonatoDialog(self)
        dialog.exec()

    def closeEvent(self, event):
        conn.close()
        event.accept()


class ResetarCampeonatoDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Resetar Campeonato")
        self.setFixedSize(400, 250)
        layout = QVBoxLayout(self)
        label = QLabel("Tem certeza que deseja resetar o campeonato?")
        label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(label)
        btn_confirmar = QPushButton("Confirmar")
        btn_confirmar.setObjectName("resetButton")
        btn_confirmar.clicked.connect(self.resetar)
        layout.addWidget(btn_confirmar)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        layout.addWidget(btn_cancelar)

    def resetar(self):
        from database import cursor
        try:
            tabelas = ["pagamentos", "campeonato_config", "resultados_etapas", "pilotos_categorias", "pilotos_times",
                       "historico_sorteios", "etapas", "pilotos", "categorias", "times", "sistema_pontuacao",
                       "sistema_pontuacao_extras"]
            for tabela in tabelas: cursor.execute(f"DELETE FROM {tabela}")
            cursor.execute("DELETE FROM sqlite_sequence")
            conn.commit()
            QMessageBox.information(self, "Sucesso", "O campeonato foi resetado com sucesso.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao resetar o campeonato: {e}")
            self.reject()


# ***** BLOCO DE INICIALIZAÇÃO ATUALIZADO (SEM LOGIN) *****
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())