import sys
import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices
from database import cursor, conn


class SistemaPagamentosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pilotos_data = {}
        self.init_ui()
        self.carregar_config_campeonato()
        self.carregar_categorias()
        self.atualizar_tabela()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Título Dinâmico
        self.label_titulo = QLabel("Sistema de Gerenciamento de Pagamentos")
        self.label_titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.label_titulo)

        # Controles e Filtros
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)

        controls_layout.addWidget(QLabel("Categoria:"))
        self.combo_categoria = QComboBox()
        controls_layout.addWidget(self.combo_categoria, 1)

        controls_layout.addWidget(QLabel("Tipo de Pagamento:"))
        self.combo_tipo_pagamento = QComboBox()
        controls_layout.addWidget(self.combo_tipo_pagamento, 1)

        self.label_etapa = QLabel("Etapa:")
        self.combo_etapa = QComboBox()
        self.label_etapa.setVisible(False)
        self.combo_etapa.setVisible(False)
        controls_layout.addWidget(self.label_etapa)
        controls_layout.addWidget(self.combo_etapa, 1)

        self.check_cobra_inscricao = QCheckBox("Cobrar Taxa de Inscrição no Campeonato")
        controls_layout.addWidget(self.check_cobra_inscricao)

        main_layout.addWidget(controls_frame)

        # Tabela de Pagamentos
        self.table_pagamentos = QTableWidget()
        self.table_pagamentos.setColumnCount(5)  # Adicionada coluna Comentários
        self.table_pagamentos.setHorizontalHeaderLabels(["Piloto", "Categoria", "Status", "Comprovante", "Comentários"])
        self.table_pagamentos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_pagamentos.horizontalHeader().setSectionResizeMode(4,
                                                                      QHeaderView.ResizeMode.Stretch)  # Coluna Comentários
        self.table_pagamentos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        main_layout.addWidget(self.table_pagamentos)

        # Conexões
        self.check_cobra_inscricao.stateChanged.connect(self.salvar_config_campeonato)
        self.combo_categoria.currentIndexChanged.connect(self.atualizar_tabela)
        self.combo_tipo_pagamento.currentIndexChanged.connect(self.toggle_etapa_filter)
        self.combo_etapa.currentIndexChanged.connect(self.atualizar_tabela)
        self.table_pagamentos.itemChanged.connect(self.salvar_comentario)  # Sinal para salvar comentários

    def carregar_categorias(self):
        # ... (sem alterações)
        self.combo_categoria.addItem("Todas as Categorias", userData=None)
        cursor.execute("SELECT id, nome FROM categorias ORDER BY nome")
        for cat_id, cat_nome in cursor.fetchall():
            self.combo_categoria.addItem(cat_nome, userData=cat_id)

    def carregar_etapas(self):
        # ... (sem alterações)
        self.combo_etapa.clear()
        self.combo_etapa.addItem("Selecione a Etapa", userData=None)
        cursor.execute("SELECT id, nome FROM etapas ORDER BY data")
        for etapa_id, etapa_nome in cursor.fetchall():
            self.combo_etapa.addItem(etapa_nome, userData=etapa_id)

    def carregar_config_campeonato(self):
        # ... (sem alterações)
        cursor.execute("SELECT cobra_inscricao FROM campeonato_config WHERE id = 1")
        config = cursor.fetchone()
        cobra_inscricao = bool(config[0]) if config else False
        # Bloqueia sinais para evitar disparo desnecessário do stateChanged
        self.check_cobra_inscricao.blockSignals(True)
        self.check_cobra_inscricao.setChecked(cobra_inscricao)
        self.check_cobra_inscricao.blockSignals(False)
        self.combo_tipo_pagamento.clear()
        if cobra_inscricao: self.combo_tipo_pagamento.addItem("Inscrição", userData="INSCRICAO")
        self.combo_tipo_pagamento.addItem("Pagamento por Etapa", userData="ETAPA")

    def salvar_config_campeonato(self):
        # ... (sem alterações)
        cobra_inscricao = self.check_cobra_inscricao.isChecked()
        cursor.execute("UPDATE campeonato_config SET cobra_inscricao = ? WHERE id = 1", (cobra_inscricao,))
        conn.commit()
        QMessageBox.information(self, "Configuração Salva", "A configuração de cobrança de inscrição foi atualizada.")
        self.carregar_config_campeonato()

    def toggle_etapa_filter(self):
        # ... (sem alterações)
        tipo_pagamento = self.combo_tipo_pagamento.currentData()
        is_etapa = (tipo_pagamento == "ETAPA")
        self.label_etapa.setVisible(is_etapa)
        self.combo_etapa.setVisible(is_etapa)
        if is_etapa and self.combo_etapa.count() == 0:
            self.carregar_etapas()
        self.atualizar_tabela()

    def atualizar_tabela(self):
        self.table_pagamentos.blockSignals(True)  # Bloqueia sinais durante o preenchimento

        categoria_id = self.combo_categoria.currentData()
        tipo_pagamento = self.combo_tipo_pagamento.currentData()
        etapa_id = self.combo_etapa.currentData()

        if tipo_pagamento == "ETAPA" and not etapa_id:
            self.table_pagamentos.setRowCount(0)
            self.atualizar_titulo()
            self.table_pagamentos.blockSignals(False)
            return

        query_pilotos = "SELECT p.id, p.nome, c.nome FROM pilotos p JOIN pilotos_categorias pc ON p.id = pc.piloto_id JOIN categorias c ON pc.categoria_id = c.id"
        params = []
        if categoria_id:
            query_pilotos += " WHERE c.id = ?"
            params.append(categoria_id)
        query_pilotos += " ORDER BY p.nome"

        cursor.execute(query_pilotos, params)
        pilotos = cursor.fetchall()
        self.table_pagamentos.setRowCount(len(pilotos))
        self.pilotos_data.clear()

        for row, (piloto_id, piloto_nome, cat_nome) in enumerate(pilotos):
            query_pagamento = "SELECT id, status, comprovante_path, comentarios FROM pagamentos WHERE piloto_id=? AND tipo=?"
            params_pagamento = [piloto_id, tipo_pagamento]
            if tipo_pagamento == "ETAPA":
                query_pagamento += " AND etapa_id=?"
                params_pagamento.append(etapa_id)

            cursor.execute(query_pagamento, params_pagamento)
            pagamento_data = cursor.fetchone()

            pagamento_id = pagamento_data[0] if pagamento_data else None
            status = pagamento_data[1] if pagamento_data else "Pendente"
            comprovante_path = pagamento_data[2] if pagamento_data else None
            comentarios = pagamento_data[3] if pagamento_data else ""

            self.pilotos_data[row] = {'piloto_id': piloto_id, 'pagamento_id': pagamento_id,
                                      'comprovante_path': comprovante_path}

            self.table_pagamentos.setItem(row, 0, QTableWidgetItem(piloto_nome.title()))
            self.table_pagamentos.setItem(row, 1, QTableWidgetItem(cat_nome))

            combo_status = QComboBox()
            combo_status.addItems(["Pendente", "Pago", "Prometeu Pagar"])
            combo_status.setCurrentText(status)
            combo_status.currentIndexChanged.connect(lambda _, r=row: self.salvar_status(r))
            self.table_pagamentos.setCellWidget(row, 2, combo_status)

            # Lógica dos botões de comprovante
            comprovante_widget = QWidget()
            comprovante_layout = QHBoxLayout(comprovante_widget)
            comprovante_layout.setContentsMargins(5, 0, 5, 0)
            btn_anexar = QPushButton("Anexar...")
            btn_anexar.clicked.connect(lambda _, r=row: self.anexar_comprovante(r))
            comprovante_layout.addWidget(btn_anexar)
            if comprovante_path and os.path.exists(comprovante_path):
                btn_visualizar = QPushButton("Visualizar")
                btn_visualizar.clicked.connect(lambda _, r=row: self.visualizar_comprovante(r))
                comprovante_layout.addWidget(btn_visualizar)
                btn_salvar_como = QPushButton("Salvar Como...")
                btn_salvar_como.clicked.connect(lambda _, r=row: self.salvar_comprovante_como(r))
                comprovante_layout.addWidget(btn_salvar_como)
            self.table_pagamentos.setCellWidget(row, 3, comprovante_widget)

            # Célula de comentários editável
            item_comentario = QTableWidgetItem(comentarios)
            item_comentario.setFlags(item_comentario.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table_pagamentos.setItem(row, 4, item_comentario)

        self.atualizar_titulo()
        self.table_pagamentos.blockSignals(False)  # Reabilita sinais

    def garantir_registro_pagamento(self, row):
        """Cria um registro de pagamento se ele não existir, e retorna seu ID."""
        if self.pilotos_data[row].get('pagamento_id'):
            return self.pilotos_data[row]['pagamento_id']

        piloto_id = self.pilotos_data[row]['piloto_id']
        tipo_pagamento = self.combo_tipo_pagamento.currentData()
        etapa_id = self.combo_etapa.currentData() if tipo_pagamento == "ETAPA" else None

        cursor.execute("INSERT INTO pagamentos (piloto_id, tipo, etapa_id) VALUES (?, ?, ?)",
                       (piloto_id, tipo_pagamento, etapa_id))
        conn.commit()
        pagamento_id = cursor.lastrowid
        self.pilotos_data[row]['pagamento_id'] = pagamento_id
        return pagamento_id

    def salvar_status(self, row):
        pagamento_id = self.garantir_registro_pagamento(row)
        combo_status = self.table_pagamentos.cellWidget(row, 2)
        novo_status = combo_status.currentText()
        cursor.execute("UPDATE pagamentos SET status = ? WHERE id = ?", (novo_status, pagamento_id))
        conn.commit()

    def salvar_comentario(self, item):
        if item.column() != 4: return  # Garante que só atue na coluna de comentários

        row = item.row()
        pagamento_id = self.garantir_registro_pagamento(row)
        novo_comentario = item.text()
        cursor.execute("UPDATE pagamentos SET comentarios = ? WHERE id = ?", (novo_comentario, pagamento_id))
        conn.commit()

    def anexar_comprovante(self, row):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Comprovante", "", "Todos os Arquivos (*)")
        if not file_path: return

        pagamento_id = self.garantir_registro_pagamento(row)

        comprovantes_dir = "comprovantes"
        os.makedirs(comprovantes_dir, exist_ok=True)

        _, ext = os.path.splitext(file_path)
        new_filename = f"pagamento_{pagamento_id}{ext}"
        dest_path = os.path.join(comprovantes_dir, new_filename)
        shutil.copy(file_path, dest_path)

        cursor.execute("UPDATE pagamentos SET comprovante_path = ? WHERE id = ?", (dest_path, pagamento_id))
        conn.commit()
        QMessageBox.information(self, "Sucesso", "Comprovante anexado!")
        self.atualizar_tabela()

    def visualizar_comprovante(self, row):
        path = self.pilotos_data[row].get('comprovante_path')
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(path)))
        else:
            QMessageBox.warning(self, "Erro", "Arquivo do comprovante não encontrado.")

    def salvar_comprovante_como(self, row):
        src_path = self.pilotos_data[row].get('comprovante_path')
        if not src_path or not os.path.exists(src_path):
            QMessageBox.warning(self, "Erro", "Arquivo do comprovante não encontrado.")
            return

        _, ext = os.path.splitext(src_path)
        dest_path, _ = QFileDialog.getSaveFileName(self, "Salvar Comprovante Como...", f"comprovante{ext}",
                                                   f"Arquivos (*{ext})")
        if dest_path:
            shutil.copy(src_path, dest_path)
            QMessageBox.information(self, "Sucesso", f"Comprovante salvo em:\n{dest_path}")

    def atualizar_titulo(self):
        base_title = "Situação de Pagamento"
        tipo_pagamento_txt = self.combo_tipo_pagamento.currentText()
        etapa_txt = self.combo_etapa.currentText()

        if self.combo_tipo_pagamento.currentData() == "INSCRICAO":
            self.label_titulo.setText(f"{base_title}: {tipo_pagamento_txt} no Campeonato")
        elif self.combo_tipo_pagamento.currentData() == "ETAPA" and self.combo_etapa.currentData() is not None:
            self.label_titulo.setText(f"{base_title}: {etapa_txt}")
        else:
            self.label_titulo.setText(base_title)