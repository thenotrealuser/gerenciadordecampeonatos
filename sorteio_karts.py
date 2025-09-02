import sys
import sqlite3
import random
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QScrollArea, QFrame, QMessageBox, QDialog, QDialogButtonBox, QLineEdit,
    QTextEdit
)
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen

from database import cursor, conn


# --- Widget Personalizado para a Grade de Karts (substitui o Canvas) ---

class KartGridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.karts = list(range(1, 101))
        self.disponiveis = set()
        self.kart_rects = {}  # Armazena os retângulos de cada kart para detecção de clique
        self.setMinimumSize(600, 300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rows, cols = 10, 10
        radius = 15
        padding = 20

        spacing_x = (self.width() - 2 * padding - cols * 2 * radius) / (cols - 1) if cols > 1 else 0
        spacing_y = (self.height() - 2 * padding - rows * 2 * radius) / (rows - 1) if rows > 1 else 0

        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)

        self.kart_rects.clear()

        for i, kart_num in enumerate(self.karts):
            row = i // cols
            col = i % cols
            x = int(padding + col * (2 * radius + spacing_x))
            y = int(padding + row * (2 * radius + spacing_y))

            rect = QRect(x, y, 2 * radius, 2 * radius)
            self.kart_rects[kart_num] = rect

            if kart_num in self.disponiveis:
                painter.setBrush(QBrush(QColor("#28a745")))  # Verde
            else:
                painter.setBrush(QBrush(QColor("#dc3545")))  # Vermelho

            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.drawEllipse(rect)

            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(kart_num))

    def mousePressEvent(self, event):
        click_pos = event.pos()
        for kart_num, rect in self.kart_rects.items():
            if rect.contains(click_pos):
                self.toggle_kart(kart_num)
                break

    def toggle_kart(self, kart_num):
        if kart_num in self.disponiveis:
            self.disponiveis.remove(kart_num)
        else:
            self.disponiveis.add(kart_num)
        self.update()  # Repinta o widget

    def reset_karts(self):
        self.disponiveis.clear()
        self.update()


# --- Diálogos Auxiliares ---

class ResultadoSorteioDialog(QDialog):
    def __init__(self, resultado_text, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setWindowTitle("Resultado do Sorteio")
        self.setMinimumSize(300, 400)

        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setPlainText(resultado_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        button_box = QDialogButtonBox()
        btn_sortear_novamente = button_box.addButton("Sortear Novamente", QDialogButtonBox.ButtonRole.ActionRole)
        btn_fechar = button_box.addButton("Fechar", QDialogButtonBox.ButtonRole.AcceptRole)
        layout.addWidget(button_box)

        btn_fechar.clicked.connect(self.accept)
        btn_sortear_novamente.clicked.connect(self.sortear_novamente)

    def sortear_novamente(self):
        self.parent_widget.sortear_karts()
        self.accept()


class AdicionarPilotoDialog(QDialog):
    def __init__(self, categoria_selecionada, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Piloto Avulso")
        self.setModal(True)
        self.categorias_map = {}

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Nome do Piloto:"))
        self.entry_nome = QLineEdit()
        layout.addWidget(self.entry_nome)

        layout.addWidget(QLabel("Adicionar à Categoria:"))
        self.combo_categoria = QComboBox()
        self.carregar_categorias(categoria_selecionada)
        layout.addWidget(self.combo_categoria)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def carregar_categorias(self, categoria_selecionada):
        cursor.execute("SELECT id, nome FROM categorias ORDER BY nome")
        for cat_id, cat_nome in cursor.fetchall():
            self.combo_categoria.addItem(cat_nome)
            self.categorias_map[cat_nome] = cat_id
        if categoria_selecionada:
            self.combo_categoria.setCurrentText(categoria_selecionada)

    def accept(self):
        nome = self.entry_nome.text().strip().lower()
        if not nome:
            QMessageBox.warning(self, "Erro", "O nome do piloto é obrigatório.")
            return

        categoria_nome = self.combo_categoria.currentText()
        categoria_id = self.categorias_map.get(categoria_nome)

        try:
            cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome,))
            piloto = cursor.fetchone()
            if piloto:
                piloto_id = piloto[0]
            else:
                cursor.execute("INSERT INTO pilotos (nome) VALUES (?)", (nome,))
                piloto_id = cursor.lastrowid

            cursor.execute("INSERT OR IGNORE INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                           (piloto_id, categoria_id))
            conn.commit()
            QMessageBox.information(self, "Sucesso", "Piloto cadastrado e adicionado à categoria com sucesso!")
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar piloto: {e}")


# --- Widget Principal ---

class SorteioKartsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.categoria_selecionada_id = None
        self.pilotos_disponiveis = {}
        self.piloto_widgets = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Coluna da Esquerda (Sorteio)
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        titulo = QLabel("Sorteio de Karts")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        left_layout.addWidget(titulo, 0, Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(QLabel("Selecione a Categoria:"))
        self.combo_categoria = QComboBox()
        self.carregar_categorias()
        self.combo_categoria.currentIndexChanged.connect(self.atualizar_pilotos)
        left_layout.addWidget(self.combo_categoria)

        self.kart_grid = KartGridWidget()
        left_layout.addWidget(self.kart_grid)

        btn_sortear = QPushButton("Sortear Karts")
        btn_sortear.clicked.connect(self.sortear_karts)
        left_layout.addWidget(btn_sortear)

        main_layout.addLayout(left_layout, 3)

        # Coluna da Direita (Pilotos)
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_frame)

        right_layout.addWidget(QLabel("Pilotos para Sorteio:"))
        self.pilotos_count_label = QLabel("Total de Pilotos: 0")
        right_layout.addWidget(self.pilotos_count_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.pilotos_scroll_content = QWidget()
        self.pilotos_layout = QVBoxLayout(self.pilotos_scroll_content)
        self.pilotos_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.pilotos_scroll_content)
        right_layout.addWidget(scroll_area)

        bottom_buttons_layout = QHBoxLayout()
        btn_adicionar_piloto = QPushButton("Adicionar Piloto")
        btn_recarregar = QPushButton("Recarregar Pilotos")
        bottom_buttons_layout.addWidget(btn_adicionar_piloto)
        bottom_buttons_layout.addWidget(btn_recarregar)
        right_layout.addLayout(bottom_buttons_layout)

        btn_adicionar_piloto.clicked.connect(self.abrir_janela_adicionar_piloto)
        btn_recarregar.clicked.connect(self.atualizar_pilotos)

        main_layout.addWidget(right_frame, 1)

    def carregar_categorias(self):
        self.combo_categoria.clear()
        self.combo_categoria.addItem("-- Selecione --")
        cursor.execute("SELECT id, nome FROM categorias ORDER BY nome")
        for cat_id, cat_nome in cursor.fetchall():
            self.combo_categoria.addItem(cat_nome, userData=cat_id)

    def atualizar_pilotos(self):
        # Limpa layout de pilotos
        for i in reversed(range(self.pilotos_layout.count())):
            self.pilotos_layout.itemAt(i).widget().setParent(None)
        self.pilotos_disponiveis.clear()
        self.piloto_widgets.clear()
        self.kart_grid.reset_karts()

        cat_id = self.combo_categoria.currentData()
        if not cat_id:
            self.categoria_selecionada_id = None
            self.atualizar_contador_pilotos()
            return
        self.categoria_selecionada_id = cat_id

        cursor.execute("""
            SELECT p.nome FROM pilotos p
            JOIN pilotos_categorias pc ON p.id = pc.piloto_id
            WHERE pc.categoria_id = ? ORDER BY p.nome
        """, (cat_id,))

        for row in cursor.fetchall():
            nome_piloto = row[0]
            self.pilotos_disponiveis[nome_piloto] = True

            # Cria widget para cada piloto
            piloto_widget = QWidget()
            piloto_layout = QHBoxLayout(piloto_widget)
            piloto_layout.setContentsMargins(0, 0, 0, 0)
            piloto_layout.addWidget(QLabel(nome_piloto))
            btn_toggle = QPushButton("V")
            btn_toggle.setCheckable(True)
            btn_toggle.setChecked(True)
            btn_toggle.setStyleSheet("background-color: #28a745;")
            btn_toggle.setFixedWidth(30)
            btn_toggle.clicked.connect(lambda state, p=nome_piloto, b=btn_toggle: self.toggle_piloto(p, b))
            piloto_layout.addWidget(btn_toggle)

            self.pilotos_layout.addWidget(piloto_widget)
            self.piloto_widgets[nome_piloto] = btn_toggle

        self.atualizar_contador_pilotos()

    def toggle_piloto(self, nome_piloto, button):
        is_disponivel = button.isChecked()
        self.pilotos_disponiveis[nome_piloto] = is_disponivel
        if is_disponivel:
            button.setText("V")
            button.setStyleSheet("background-color: #28a745;")
        else:
            button.setText("X")
            button.setStyleSheet("background-color: #dc3545;")
        self.atualizar_contador_pilotos()

    def atualizar_contador_pilotos(self):
        count = sum(self.pilotos_disponiveis.values())
        self.pilotos_count_label.setText(f"Total de Pilotos: {count}")

    def abrir_janela_adicionar_piloto(self):
        dialog = AdicionarPilotoDialog(self.combo_categoria.currentText(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.atualizar_pilotos()

    def sortear_karts(self):
        if not self.categoria_selecionada_id:
            QMessageBox.warning(self, "Erro", "Selecione uma categoria.")
            return

        pilotos_ativos = [p for p, d in self.pilotos_disponiveis.items() if d]
        karts_ativos = list(self.kart_grid.disponiveis)

        if not pilotos_ativos:
            QMessageBox.warning(self, "Aviso", "Nenhum piloto disponível para sorteio.")
            return
        if len(pilotos_ativos) > len(karts_ativos):
            QMessageBox.critical(self, "Erro", "Número de pilotos excede o número de karts disponíveis.")
            return

        random.shuffle(karts_ativos)
        sorteios = {piloto: karts_ativos[i] for i, piloto in enumerate(pilotos_ativos)}

        try:
            data_sorteio = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            for piloto, kart in sorteios.items():
                cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (piloto,))
                piloto_id = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO historico_sorteios (categoria_id, piloto_id, kart, data_sorteio) 
                    VALUES (?, ?, ?, ?)
                """, (self.categoria_selecionada_id, piloto_id, kart, data_sorteio))
            conn.commit()

            resultado_texto = "\n".join([f"{piloto.title()}: Kart {kart}" for piloto, kart in sorted(sorteios.items())])
            dialog = ResultadoSorteioDialog(resultado_texto, self)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao salvar sorteio: {e}")


# Bloco de teste
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QMainWindow()
    # Setup de DB em memória para teste
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE categorias (id INTEGER PRIMARY KEY, nome TEXT)")
    cursor.execute("CREATE TABLE pilotos (id INTEGER PRIMARY KEY, nome TEXT)")
    cursor.execute("CREATE TABLE pilotos_categorias (piloto_id INTEGER, categoria_id INTEGER)")
    cursor.execute(
        "CREATE TABLE historico_sorteios (id INTEGER PRIMARY KEY, categoria_id INTEGER, piloto_id INTEGER, kart INTEGER, data_sorteio TEXT)")
    cursor.execute("INSERT INTO categorias VALUES (1, 'Graduados'), (2, 'Novatos')")
    cursor.execute("INSERT INTO pilotos VALUES (1, 'kimi morgam'), (2, 'ana castela'), (3, 'fernanda morando')")
    cursor.execute("INSERT INTO pilotos_categorias VALUES (1, 1), (2, 2), (3, 1)")
    conn.commit()

    main_widget = SorteioKartsWidget()
    window.setCentralWidget(main_widget)
    window.resize(1024, 600)
    window.show()
    sys.exit(app.exec())