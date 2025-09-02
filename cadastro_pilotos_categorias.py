import sys
import sqlite3
import difflib
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QCheckBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QMessageBox,
    QDialog, QDialogButtonBox, QComboBox, QListWidget, QScrollArea, QGroupBox,
    QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIntValidator
from database import cursor, conn


# (O widget CadastroCategoriasWidget e o diálogo EditarPilotoDialog não foram alterados,
# mas estão incluídos abaixo para que você possa substituir o arquivo inteiro)

# --- Widget para Cadastro de Categorias ---

class CadastroCategoriasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.atualizar_lista()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # ... (código interno sem alterações)
        label_titulo = QLabel("Cadastro de Categorias")
        label_titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_titulo)
        form_layout = QHBoxLayout()
        self.entry_nome = QLineEdit()
        self.entry_nome.setPlaceholderText("Nome da Categoria")
        self.checkbox_corrida_de_times = QCheckBox("Categoria de Times?")
        btn_salvar = QPushButton("Salvar Categoria")
        form_layout.addWidget(self.entry_nome, 2)
        form_layout.addWidget(self.checkbox_corrida_de_times, 1)
        form_layout.addWidget(btn_salvar, 1)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(QLabel("Categorias Cadastradas:"))
        self.categorias_listbox = QListWidget()
        main_layout.addWidget(self.categorias_listbox)
        btn_remover = QPushButton("Remover Categoria Selecionada")
        main_layout.addWidget(btn_remover, 0, Qt.AlignmentFlag.AlignRight)
        btn_salvar.clicked.connect(self.salvar_categoria)
        btn_remover.clicked.connect(self.remover_categoria)
        self.entry_nome.returnPressed.connect(self.salvar_categoria)

    def salvar_categoria(self):
        # ... (código interno sem alterações)
        nome_categoria = self.entry_nome.text().strip()
        corrida_de_times = self.checkbox_corrida_de_times.isChecked()
        if not nome_categoria:
            QMessageBox.warning(self, "Erro", "O nome da categoria não pode estar vazio.")
            return
        try:
            cursor.execute("INSERT INTO categorias (nome, corrida_de_times) VALUES (?, ?)",
                           (nome_categoria, corrida_de_times))
            conn.commit()
            QMessageBox.information(self, "Sucesso", "Categoria cadastrada com sucesso!")
            self.entry_nome.clear()
            self.checkbox_corrida_de_times.setChecked(False)
            self.atualizar_lista()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Erro", "Já existe uma categoria com esse nome.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar categoria: {e}")

    def atualizar_lista(self):
        # ... (código interno sem alterações)
        self.categorias_listbox.clear()
        cursor.execute("SELECT nome FROM categorias ORDER BY nome")
        categorias = cursor.fetchall()
        for cat in categorias:
            self.categorias_listbox.addItem(cat[0])

    def remover_categoria(self):
        # ... (código interno sem alterações)
        item_selecionado = self.categorias_listbox.currentItem()
        if not item_selecionado:
            QMessageBox.warning(self, "Erro", "Selecione uma categoria para remover.")
            return
        nome_cat = item_selecionado.text()
        confirm = QMessageBox.question(self, "Confirmar Remoção",
                                       f"Tem certeza que deseja remover a categoria '{nome_cat}'?\n"
                                       "TODOS os pilotos, resultados e sorteios associados a ela serão permanentemente excluídos.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                cursor.execute("SELECT id FROM categorias WHERE nome = ?", (nome_cat,))
                categoria_id = cursor.fetchone()[0]
                cursor.execute("DELETE FROM pilotos_categorias WHERE categoria_id = ?", (categoria_id,))
                cursor.execute("DELETE FROM resultados_etapas WHERE categoria_id = ?", (categoria_id,))
                cursor.execute("DELETE FROM historico_sorteios WHERE categoria_id = ?", (categoria_id,))
                cursor.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
                conn.commit()
                QMessageBox.information(self, "Sucesso", "Categoria e dados relacionados foram removidos com sucesso!")
                self.atualizar_lista()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao remover categoria: {e}")


# --- Diálogo para Editar Piloto ---

class EditarPilotoDialog(QDialog):
    # ... (código interno sem alterações)
    def __init__(self, nome_piloto, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.nome_piloto_original = nome_piloto
        self.piloto_id = self.get_piloto_id(nome_piloto)
        self.setWindowTitle(f"Editar Piloto - {nome_piloto}")
        self.setMinimumWidth(400)
        self.init_ui()
        self.carregar_dados_piloto()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Nome do Piloto:"))
        self.entry_nome = QLineEdit()
        layout.addWidget(self.entry_nome)
        layout.addWidget(QLabel("Time (opcional):"))
        self.combo_time = QComboBox()
        layout.addWidget(self.combo_time)
        group_box = QGroupBox("Categorias")
        self.categorias_layout = QVBoxLayout()
        group_box.setLayout(self.categorias_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(group_box)
        layout.addWidget(scroll_area)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_piloto_id(self, nome):
        cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome,))
        result = cursor.fetchone()
        return result[0] if result else None

    def carregar_dados_piloto(self):
        self.entry_nome.setText(self.nome_piloto_original)
        self.combo_time.addItem("")
        cursor.execute("SELECT nome FROM times ORDER BY nome")
        for time in cursor.fetchall(): self.combo_time.addItem(time[0])
        cursor.execute("SELECT t.nome FROM times t JOIN pilotos_times pt ON t.id = pt.time_id WHERE pt.piloto_id = ?",
                       (self.piloto_id,))
        time_piloto = cursor.fetchone()
        if time_piloto: self.combo_time.setCurrentText(time_piloto[0])
        self.categoria_checkboxes = []
        cursor.execute("SELECT id, nome FROM categorias ORDER BY nome")
        todas_categorias = cursor.fetchall()
        cursor.execute("SELECT categoria_id FROM pilotos_categorias WHERE piloto_id = ?", (self.piloto_id,))
        categorias_piloto = {row[0] for row in cursor.fetchall()}
        for cat_id, cat_nome in todas_categorias:
            checkbox = QCheckBox(cat_nome)
            if cat_id in categorias_piloto: checkbox.setChecked(True)
            self.categorias_layout.addWidget(checkbox)
            self.categoria_checkboxes.append((checkbox, cat_id))

    def accept(self):
        novo_nome = self.entry_nome.text().strip()
        time_nome = self.combo_time.currentText()
        cat_selecionadas = [cat_id for cb, cat_id in self.categoria_checkboxes if cb.isChecked()]
        if not novo_nome or not cat_selecionadas:
            QMessageBox.warning(self, "Erro", "Nome e pelo menos uma categoria são obrigatórios.")
            return
        try:
            cursor.execute("SELECT id FROM pilotos WHERE LOWER(nome) = ? AND id != ?",
                           (novo_nome.lower(), self.piloto_id))
            if cursor.fetchone():
                QMessageBox.warning(self, "Erro", "Já existe outro piloto com esse nome.")
                return
            cursor.execute("UPDATE pilotos SET nome = ? WHERE id = ?", (novo_nome, self.piloto_id))
            cursor.execute("DELETE FROM pilotos_categorias WHERE piloto_id = ?", (self.piloto_id,))
            for cat_id in cat_selecionadas: cursor.execute(
                "INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)", (self.piloto_id, cat_id))
            cursor.execute("DELETE FROM pilotos_times WHERE piloto_id = ?", (self.piloto_id,))
            if time_nome:
                cursor.execute("SELECT id FROM times WHERE nome = ?", (time_nome,))
                time_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO pilotos_times (piloto_id, time_id) VALUES (?, ?)",
                               (self.piloto_id, time_id))
            conn.commit()
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Erro ao atualizar piloto: {e}")


# ***** NOVO DIÁLOGO PARA RESOLVER CONFLITOS *****

class ResolverConflitoDialog(QDialog):
    def __init__(self, piloto1, piloto2, etapa_id, parent=None):
        super().__init__(parent)
        self.piloto1_id = piloto1['id']
        self.piloto2_id = piloto2['id']
        self.etapa_id = etapa_id

        # Busca dados do BD antes de criar a UI
        self.resultado1 = self.get_resultado(self.piloto1_id)
        self.resultado2 = self.get_resultado(self.piloto2_id)
        etapa_nome = self.get_etapa_nome()

        self.setWindowTitle("Resolver Conflito de Unificação")
        self.setMinimumWidth(600)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel(f"<b>Conflito na Etapa: {etapa_nome}</b><br>"
                                     "Ambos os pilotos têm um resultado para esta etapa. "
                                     "Para continuar a unificação, por favor, edite e/ou exclua um dos resultados abaixo."))

        # Layout para os dois resultados lado a lado
        h_layout = QHBoxLayout()
        self.group1 = self.criar_grupo_resultado(piloto1['nome'], self.resultado1, self.excluir_resultado1)
        self.group2 = self.criar_grupo_resultado(piloto2['nome'], self.resultado2, self.excluir_resultado2)
        h_layout.addWidget(self.group1)
        h_layout.addWidget(self.group2)
        main_layout.addLayout(h_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Save).setText("Resolver e Salvar")
        button_box.accepted.connect(self.salvar_resolucao)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def get_etapa_nome(self):
        cursor.execute("SELECT nome FROM etapas WHERE id = ?", (self.etapa_id,))
        return cursor.fetchone()[0]

    def get_resultado(self, piloto_id):
        cursor.execute("SELECT * FROM resultados_etapas WHERE piloto_id = ? AND etapa_id = ?",
                       (piloto_id, self.etapa_id))
        colunas = [d[0] for d in cursor.description]
        return dict(zip(colunas, cursor.fetchone()))

    def criar_grupo_resultado(self, nome_piloto, resultado_data, on_delete):
        group_box = QGroupBox(nome_piloto.title())
        layout = QVBoxLayout(group_box)

        # Guardar os widgets para ler os valores depois
        widgets = {}

        layout.addWidget(QLabel("Posição:"))
        widgets['posicao'] = QLineEdit(str(resultado_data['posicao']))
        widgets['posicao'].setValidator(QIntValidator(1, 99))
        layout.addWidget(widgets['posicao'])

        widgets['pole'] = QCheckBox("Pole Position")
        widgets['pole'].setChecked(bool(resultado_data['pole_position']))
        layout.addWidget(widgets['pole'])

        widgets['melhor_volta'] = QCheckBox("Melhor Volta")
        widgets['melhor_volta'].setChecked(bool(resultado_data['melhor_volta']))
        layout.addWidget(widgets['melhor_volta'])

        widgets['adv'] = QCheckBox("ADV")
        widgets['adv'].setChecked(bool(resultado_data['adv']))
        layout.addWidget(widgets['adv'])

        btn_excluir = QPushButton("Excluir este Resultado")
        btn_excluir.setStyleSheet("background-color: #e74c3c;")
        btn_excluir.clicked.connect(on_delete)
        layout.addWidget(btn_excluir)

        group_box.setProperty("widgets", widgets)
        return group_box

    def excluir_resultado1(self):
        self.resolver("excluir_1")

    def excluir_resultado2(self):
        self.resolver("excluir_2")

    def salvar_resolucao(self):
        self.resolver("salvar_ambos")

    def resolver(self, acao):
        try:
            # Opção 1: Excluir resultado 1
            if acao == "excluir_1":
                cursor.execute("DELETE FROM resultados_etapas WHERE id = ?", (self.resultado1['id'],))

            # Opção 2: Excluir resultado 2
            elif acao == "excluir_2":
                cursor.execute("DELETE FROM resultados_etapas WHERE id = ?", (self.resultado2['id'],))

            # Opção 3: Salvar alterações em ambos (se um não foi excluído)
            elif acao == "salvar_ambos":
                # Salva dados do piloto 1
                widgets1 = self.group1.property("widgets")
                cursor.execute("""
                    UPDATE resultados_etapas SET posicao=?, pole_position=?, melhor_volta=?, adv=? WHERE id=?
                """, (int(widgets1['posicao'].text()), widgets1['pole'].isChecked(),
                      widgets1['melhor_volta'].isChecked(), widgets1['adv'].isChecked(), self.resultado1['id']))

                # Salva dados do piloto 2
                widgets2 = self.group2.property("widgets")
                cursor.execute("""
                    UPDATE resultados_etapas SET posicao=?, pole_position=?, melhor_volta=?, adv=? WHERE id=?
                """, (int(widgets2['posicao'].text()), widgets2['pole'].isChecked(),
                      widgets2['melhor_volta'].isChecked(), widgets2['adv'].isChecked(), self.resultado2['id']))

                QMessageBox.information(self, "Sucesso",
                                        "Alterações salvas. Agora, exclua um dos resultados para prosseguir com a unificação.")
                return  # Não fecha o diálogo, força o usuário a excluir um

            conn.commit()
            QMessageBox.information(self, "Sucesso", "Conflito resolvido!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível resolver o conflito: {e}")


# --- Widget para Cadastro de Pilotos ---

class CadastroPilotosWidget(QWidget):
    # ... (init_ui, capitalizar_nome, refresh_data, salvar_piloto, editar_piloto, remover_piloto, unir_pilotos
    # e verificar_nomes_parecidos não foram alterados, mas estão incluídos para a substituição do arquivo)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.refresh_data()
        self.verificar_nomes_parecidos()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        label_titulo = QLabel("Cadastro de Pilotos")
        label_titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label_titulo)
        h_layout = QHBoxLayout()
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.addWidget(QLabel("Nome do Piloto:"))
        self.entry_nome_piloto = QLineEdit()
        form_layout.addWidget(self.entry_nome_piloto)
        form_layout.addWidget(QLabel("Time (opcional):"))
        self.combo_time_piloto = QComboBox()
        form_layout.addWidget(self.combo_time_piloto)
        group_box_cat = QGroupBox("Categorias")
        self.categorias_layout_piloto = QVBoxLayout()
        group_box_cat.setLayout(self.categorias_layout_piloto)
        scroll_area_cat = QScrollArea()
        scroll_area_cat.setWidgetResizable(True)
        scroll_area_cat.setWidget(group_box_cat)
        form_layout.addWidget(scroll_area_cat)
        btn_salvar_piloto = QPushButton("Salvar Novo Piloto")
        form_layout.addWidget(btn_salvar_piloto)
        btn_recarregar = QPushButton("Recarregar Listas")
        form_layout.addWidget(btn_recarregar)
        h_layout.addWidget(form_container, 1)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        self.table_pilotos = QTableWidget()
        self.table_pilotos.setColumnCount(3)
        self.table_pilotos.setHorizontalHeaderLabels(["Nome", "Categorias", "Time"])
        self.table_pilotos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_pilotos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_pilotos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_pilotos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_pilotos.verticalHeader().setVisible(False)
        self.table_pilotos.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table_layout.addWidget(self.table_pilotos)
        botoes_acao_layout = QHBoxLayout()
        btn_editar_piloto = QPushButton("Editar")
        btn_remover_piloto = QPushButton("Remover")
        btn_unir_pilotos = QPushButton("Unir 2 Pilotos")
        botoes_acao_layout.addStretch()
        botoes_acao_layout.addWidget(btn_editar_piloto)
        botoes_acao_layout.addWidget(btn_remover_piloto)
        botoes_acao_layout.addWidget(btn_unir_pilotos)
        table_layout.addLayout(botoes_acao_layout)
        h_layout.addWidget(table_container, 2)
        main_layout.addLayout(h_layout)
        btn_salvar_piloto.clicked.connect(self.salvar_piloto)
        btn_editar_piloto.clicked.connect(self.editar_piloto)
        btn_remover_piloto.clicked.connect(self.remover_piloto)
        btn_unir_pilotos.clicked.connect(self.unir_pilotos)
        btn_recarregar.clicked.connect(self.refresh_data)

    def capitalizar_nome(self, nome):
        return ' '.join(word.capitalize() for word in nome.split())

    def refresh_data(self):
        self.table_pilotos.setRowCount(0)
        query = """
            SELECT p.nome, GROUP_CONCAT(c.nome, ', '), t.nome
            FROM pilotos p
            LEFT JOIN pilotos_categorias pc ON p.id = pc.piloto_id
            LEFT JOIN categorias c ON pc.categoria_id = c.id
            LEFT JOIN pilotos_times pt ON p.id = pt.piloto_id
            LEFT JOIN times t ON pt.time_id = t.id
            GROUP BY p.id ORDER BY p.nome ASC
        """
        try:
            for row_num, row_data in enumerate(cursor.execute(query)):
                nome, categorias, time = row_data
                self.table_pilotos.insertRow(row_num)
                self.table_pilotos.setItem(row_num, 0, QTableWidgetItem(nome))
                self.table_pilotos.setItem(row_num, 1, QTableWidgetItem(categorias or ""))
                self.table_pilotos.setItem(row_num, 2, QTableWidgetItem(time or ""))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar pilotos: {e}")
        while self.categorias_layout_piloto.count():
            child = self.categorias_layout_piloto.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self.combo_time_piloto.clear()
        self.combo_time_piloto.addItem("")
        cursor.execute("SELECT nome FROM times ORDER BY nome")
        for time in cursor.fetchall(): self.combo_time_piloto.addItem(time[0])
        self.categoria_checkboxes_cadastro = []
        cursor.execute("SELECT id, nome FROM categorias ORDER BY nome")
        for cat_id, cat_nome in cursor.fetchall():
            cb = QCheckBox(cat_nome)
            self.categorias_layout_piloto.addWidget(cb)
            self.categoria_checkboxes_cadastro.append((cb, cat_id))

    def salvar_piloto(self):
        nome = self.entry_nome_piloto.text().strip()
        time_nome = self.combo_time_piloto.currentText()
        cat_selecionadas = [cat_id for cb, cat_id in self.categoria_checkboxes_cadastro if cb.isChecked()]
        if not nome or not cat_selecionadas:
            QMessageBox.warning(self, "Erro", "Nome e ao menos uma categoria são obrigatórios.")
            return
        nome_capitalizado = self.capitalizar_nome(nome)
        try:
            cursor.execute("SELECT id FROM pilotos WHERE LOWER(nome) = ?", (nome.lower(),))
            if cursor.fetchone():
                QMessageBox.warning(self, "Erro", "Já existe um piloto com esse nome.")
                return
            cursor.execute("INSERT INTO pilotos (nome) VALUES (?)", (nome_capitalizado,))
            piloto_id = cursor.lastrowid
            for cat_id in cat_selecionadas:
                cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                               (piloto_id, cat_id))
            if time_nome:
                cursor.execute("SELECT id FROM times WHERE nome = ?", (time_nome,))
                time_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO pilotos_times (piloto_id, time_id) VALUES (?, ?)", (piloto_id, time_id))
            conn.commit()
            QMessageBox.information(self, "Sucesso", "Piloto cadastrado com sucesso!")
            self.entry_nome_piloto.clear()
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar piloto: {e}")

    def editar_piloto(self):
        selected_rows = self.table_pilotos.selectionModel().selectedRows()
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Seleção Inválida", "Selecione exatamente um piloto para editar.")
            return
        nome_piloto = self.table_pilotos.item(selected_rows[0].row(), 0).text()
        dialog = EditarPilotoDialog(nome_piloto, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Sucesso", "Piloto atualizado com sucesso!")
            self.refresh_data()

    def remover_piloto(self):
        selected_rows = self.table_pilotos.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Seleção Inválida", "Selecione um ou mais pilotos para remover.")
            return
        nomes = [self.table_pilotos.item(row.row(), 0).text() for row in selected_rows]
        if QMessageBox.question(self, "Confirmar",
                                f"Tem certeza que quer remover os pilotos: {', '.join(nomes)}?") == QMessageBox.StandardButton.Yes:
            try:
                for nome in nomes:
                    cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome,))
                    piloto_id = cursor.fetchone()[0]
                    cursor.execute("DELETE FROM pilotos WHERE id = ?", (piloto_id,))
                conn.commit()
                QMessageBox.information(self, "Sucesso", "Pilotos removidos!")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao remover pilotos: {e}")

    def unir_pilotos(self):
        selected_rows = self.table_pilotos.selectionModel().selectedRows()
        if len(selected_rows) != 2:
            QMessageBox.warning(self, "Seleção Inválida", "Selecione exatamente dois pilotos para unir.")
            return
        nome1 = self.table_pilotos.item(selected_rows[0].row(), 0).text()
        nome2 = self.table_pilotos.item(selected_rows[1].row(), 0).text()
        novo_nome, ok = QInputDialog.getText(self, "Unir Pilotos",
                                             f"Unificando '{nome1}' e '{nome2}'.\nDigite o nome final:",
                                             text=self.capitalizar_nome(nome1))
        if ok and novo_nome.strip():
            self.unificar_pilotos_logica(nome1, nome2, novo_nome.strip())

    def verificar_nomes_parecidos(self):
        cursor.execute("SELECT nome FROM pilotos")
        nomes = [row[0] for row in cursor.fetchall()]
        if len(nomes) < 2: return
        processed_pairs = set()
        for i, nome1 in enumerate(nomes):
            matches = difflib.get_close_matches(nome1.lower(), [n.lower() for n in nomes[i + 1:]], n=5, cutoff=0.8)
            if not matches: continue
            # Find original case for matches
            original_matches = [n for n in nomes[i + 1:] if n.lower() in matches]
            for nome2 in original_matches:
                pair = tuple(sorted((nome1, nome2)))
                if pair in processed_pairs: continue
                processed_pairs.add(pair)
                if QMessageBox.question(self, "Nomes Semelhantes",
                                        f"Os pilotos '{nome1}' e '{nome2}' têm nomes semelhantes.\nDeseja unificá-los?") == QMessageBox.StandardButton.Yes:
                    novo_nome, ok = QInputDialog.getText(self, "Unir Pilotos", f"Digite o nome final:",
                                                         text=self.capitalizar_nome(nome1))
                    if ok and novo_nome.strip():
                        self.unificar_pilotos_logica(nome1, nome2, novo_nome.strip())
                        return  # Stop after one merge to avoid issues with changed list

    # ***** LÓGICA DE UNIFICAÇÃO ATUALIZADA *****
    def unificar_pilotos_logica(self, nome1, nome2, novo_nome):
        try:
            # Obter IDs dos pilotos
            cursor.execute("SELECT id FROM pilotos WHERE nome=?", (nome1,))
            piloto1_res = cursor.fetchone()
            cursor.execute("SELECT id FROM pilotos WHERE nome=?", (nome2,))
            piloto2_res = cursor.fetchone()

            if not piloto1_res or not piloto2_res:
                QMessageBox.critical(self, "Erro", "Um dos pilotos não foi encontrado. A operação foi cancelada.")
                return

            id1, id2 = piloto1_res[0], piloto2_res[0]
            piloto1 = {'id': id1, 'nome': nome1}
            piloto2 = {'id': id2, 'nome': nome2}

            # 1. Detectar conflitos antes de tentar a unificação
            cursor.execute("""
                SELECT etapa_id FROM resultados_etapas
                WHERE piloto_id IN (?, ?)
                GROUP BY etapa_id
                HAVING COUNT(DISTINCT piloto_id) > 1
            """, (id1, id2))
            conflitos = cursor.fetchall()

            # 2. Se houver conflitos, abrir o diálogo de resolução para cada um
            if conflitos:
                for etapa_conflito_id, in conflitos:
                    dialog = ResolverConflitoDialog(piloto1, piloto2, etapa_conflito_id, self)
                    if dialog.exec() != QDialog.DialogCode.Accepted:
                        QMessageBox.warning(self, "Cancelado",
                                            "A unificação foi cancelada pelo usuário durante a resolução de conflitos.")
                        return  # Aborta toda a operação de unificação

            # 3. Se todos os conflitos foram resolvidos (ou não existiam), prosseguir com a unificação
            # Mover associações de tabelas de id2 para id1
            tabelas_associacao = {
                "resultados_etapas": "piloto_id",
                "pilotos_categorias": "piloto_id",
                "pilotos_times": "piloto_id",
                "historico_sorteios": "piloto_id",
            }
            for tabela, campo in tabelas_associacao.items():
                # Usar INSERT OR IGNORE para pular duplicatas (ex: categorias) e UPDATE para o resto
                if tabela == "pilotos_categorias":
                    cursor.execute(f"SELECT categoria_id FROM pilotos_categorias WHERE piloto_id=?", (id2,))
                    cats_piloto2 = cursor.fetchall()
                    for cat_id, in cats_piloto2:
                        cursor.execute(
                            f"INSERT OR IGNORE INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?,?)",
                            (id1, cat_id))
                else:
                    cursor.execute(f"UPDATE {tabela} SET {campo} = ? WHERE {campo} = ?", (id1, id2))

            # Atualizar o nome do piloto principal
            cursor.execute("UPDATE pilotos SET nome = ? WHERE id = ?", (self.capitalizar_nome(novo_nome), id1))

            # Remover o segundo piloto (agora redundante e sem associações)
            cursor.execute("DELETE FROM pilotos_categorias WHERE piloto_id = ?", (id2,))
            cursor.execute("DELETE FROM pilotos WHERE id = ?", (id2,))

            conn.commit()
            QMessageBox.information(self, "Sucesso", f"Pilotos '{nome1}' e '{nome2}' unificados como '{novo_nome}'.")
            self.refresh_data()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erro", f"Um erro inesperado ocorreu ao unificar pilotos: {e}")