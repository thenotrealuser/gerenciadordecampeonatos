import difflib
from tkinter import messagebox, StringVar, ttk, simpledialog, END
from tkinter import Listbox
import customtkinter as ctk
from database import cursor, conn
from db_utils import buscar_categorias, buscar_times
import sqlite3

# Certifique-se de que as tabelas 'times' e 'pilotos_times' existam no banco de dados.
# Exemplo de criação das tabelas:
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS times (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     nome TEXT UNIQUE NOT NULL
# )
# ''')
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS pilotos_times (
#     piloto_id INTEGER UNIQUE,
#     time_id INTEGER,
#     FOREIGN KEY (piloto_id) REFERENCES pilotos(id),
#     FOREIGN KEY (time_id) REFERENCES times(id)
# )
# ''')
# conn.commit()

class CadastroCategoriasFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        self.label = ctk.CTkLabel(self, text="Cadastro de Categorias", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=10)

        # Campo para Nome da Categoria
        self.entry_nome = ctk.CTkEntry(self, placeholder_text="Nome da Categoria")
        self.entry_nome.pack(pady=10)

        # Campo para Selecionar se é uma Corrida de Times
        self.label_time = ctk.CTkLabel(self, text="Categoria de Times?")
        self.label_time.pack(pady=5)

        self.var_corrida_de_times = ctk.BooleanVar()
        self.checkbox_corrida_de_times = ctk.CTkCheckBox(self, text="Sim", variable=self.var_corrida_de_times)
        self.checkbox_corrida_de_times.pack(pady=5)

        # Botão para Salvar Categoria
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Categoria", command=self.salvar_categoria)
        self.btn_salvar.pack(pady=20)

        # Lista de Categorias Cadastradas
        self.label_lista = ctk.CTkLabel(self, text="Categorias Cadastradas", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_lista.pack(pady=10)

        # Utilizando tkinter.Listbox dentro do customtkinter Frame
        self.categorias_listbox = Listbox(self, height=10, selectmode=ctk.SINGLE)
        self.categorias_listbox.pack(fill="both", expand=True, pady=5)
        self.atualizar_lista()

        # Botão para Remover Categoria
        self.btn_remover = ctk.CTkButton(self, text="Remover Categoria Selecionada", command=self.remover_categoria)
        self.btn_remover.pack(pady=10)

    def salvar_categoria(self):
        nome_categoria = self.entry_nome.get().strip()
        corrida_de_times = self.var_corrida_de_times.get()

        if not nome_categoria:
            messagebox.showerror("Erro", "O nome da categoria não pode estar vazio.")
            return

        # Salvar a nova categoria no banco de dados
        try:
            cursor.execute("INSERT INTO categorias (nome, corrida_de_times) VALUES (?, ?)", (nome_categoria, corrida_de_times))
            conn.commit()
            messagebox.showinfo("Sucesso", "Categoria cadastrada com sucesso!")
            self.entry_nome.delete(0, END)
            self.var_corrida_de_times.set(False)
            self.atualizar_lista()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Já existe uma categoria com esse nome.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar categoria: {e}")

    def atualizar_lista(self):
        self.categorias_listbox.delete(0, END)
        cursor.execute("SELECT nome FROM categorias ORDER BY nome")
        categorias = cursor.fetchall()
        for cat in categorias:
            self.categorias_listbox.insert(END, cat[0])

    def remover_categoria(self):
        try:
            selecionado = self.categorias_listbox.get(self.categorias_listbox.curselection())
        except:
            selecionado = None
        if not selecionado:
            messagebox.showerror("Erro", "Selecione uma categoria para remover.")
            return
        try:
            cursor.execute("SELECT id FROM categorias WHERE nome = ?", (selecionado,))
            categoria = cursor.fetchone()
            if not categoria:
                messagebox.showerror("Erro", "Categoria selecionada inválida.")
                return
            categoria_id = categoria[0]

            # Remover pilotos associados à categoria
            cursor.execute("DELETE FROM pilotos_categorias WHERE categoria_id = ?", (categoria_id,))

            # Remover resultados associados à categoria
            cursor.execute("DELETE FROM resultados_etapas WHERE categoria_id = ?", (categoria_id,))

            # Remover sorteios associados à categoria
            cursor.execute("DELETE FROM historico_sorteios WHERE categoria_id = ?", (categoria_id,))

            # Remover a categoria
            cursor.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))

            conn.commit()

            messagebox.showinfo("Sucesso", "Categoria e todas as informações relacionadas foram removidas com sucesso!")
            self.atualizar_lista()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao remover categoria: {e}")


class CadastroPilotosFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        self.label = ctk.CTkLabel(self, text="Cadastro de Pilotos", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=10)

        # Campo para Nome do Piloto
        self.entry_nome = ctk.CTkEntry(self, placeholder_text="Nome do Piloto")
        self.entry_nome.pack(pady=10)

        # Seleção de Times
        self.label_time = ctk.CTkLabel(self, text="Selecione Time (opcional)")
        self.label_time.pack(pady=5)

        self.times = self.get_times()
        self.time_var = StringVar()
        time_values = [""] + [time[1] for time in self.times]  # Adiciona uma opção vazia
        self.dropdown_time = ctk.CTkComboBox(self, values=time_values, variable=self.time_var)
        self.dropdown_time.pack(pady=5)
        self.dropdown_time.set("")  # Define como vazio por padrão

        # Seleção de Categorias
        self.label_categoria = ctk.CTkLabel(self, text="Selecione Categorias")
        self.label_categoria.pack(pady=5)

        self.categorias = self.get_categorias()
        if not self.categorias:
            messagebox.showwarning("Aviso", "Nenhuma categoria cadastrada. Por favor, cadastre uma categoria primeiro.")

        self.categoria_vars = []
        self.categoria_checkboxes = []
        for categoria in self.categorias:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(self, text=categoria[1], variable=var)
            cb.pack(anchor='w')
            self.categoria_vars.append((var, categoria[0]))
            self.categoria_checkboxes.append(cb)

        # Botão para Salvar Piloto
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Piloto", command=self.salvar_piloto)
        self.btn_salvar.pack(pady=20)

        # Exibir Pilotos Cadastrados
        self.label_lista_pilotos = ctk.CTkLabel(self, text="Pilotos Cadastrados",
                                                font=ctk.CTkFont(size=16, weight="bold"))
        self.label_lista_pilotos.pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("Nome", "Categorias", "Time"), show="headings", selectmode="extended")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Categorias", text="Categorias")
        self.tree.heading("Time", text="Time")
        self.tree.pack(fill="both", expand=True, pady=10)

        # Adicionar scrollbar à Treeview
        self.scrollbar_tree = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar_tree.set)
        self.scrollbar_tree.pack(side='right', fill='y')

        # Carregar lista de pilotos cadastrados
        self.carregar_pilotos()

        # Verificar nomes semelhantes após carregar pilotos
        self.verificar_nomes_parecidos()

        # Botão para Editar Piloto
        self.btn_editar_piloto = ctk.CTkButton(self, text="Editar Piloto", command=self.editar_piloto)
        self.btn_editar_piloto.pack(pady=10)

        # Botão para Remover Piloto
        self.btn_remover_piloto = ctk.CTkButton(self, text="Remover Piloto", command=self.remover_piloto)
        self.btn_remover_piloto.pack(pady=10)

        # Botão para Unir Pilotos
        self.btn_unir_pilotos = ctk.CTkButton(self, text="Unir Pilotos", command=self.unir_pilotos)
        self.btn_unir_pilotos.pack(pady=10)

    def get_categorias(self):
        return buscar_categorias()

    def get_times(self):
        return buscar_times()

    def carregar_pilotos(self):
        # Limpar a Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Atualizar as colunas da Treeview para incluir a coluna de Times
        self.tree.config(columns=("Nome", "Categorias", "Time"))
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Categorias", text="Categorias")
        self.tree.heading("Time", text="Time")

        # Buscar pilotos cadastrados e incluir o time
        cursor.execute('''
            SELECT p.nome, GROUP_CONCAT(c.nome, ', '), t.nome
            FROM pilotos p
            LEFT JOIN pilotos_categorias pc ON p.id = pc.piloto_id
            LEFT JOIN categorias c ON pc.categoria_id = c.id
            LEFT JOIN pilotos_times pt ON p.id = pt.piloto_id
            LEFT JOIN times t ON pt.time_id = t.id
            GROUP BY p.nome, t.nome
            ORDER BY p.nome ASC
        ''')
        pilotos = cursor.fetchall()

        # Inserir pilotos na Treeview
        for piloto in pilotos:
            nome, categorias, time = piloto
            # Se time é None, deixar a coluna em branco
            time_display = time if time else ""
            self.tree.insert("", "end", values=(nome, categorias, time_display))

    def salvar_piloto(self):
        nome = self.entry_nome.get().strip()
        time_nome = self.time_var.get()  # Time selecionado
        if not nome:
            messagebox.showerror("Erro", "O nome do piloto é obrigatório.")
            return

        # Capitalizar o nome corretamente
        nome_capitalizado = self.capitalizar_nome(nome)

        categorias_selecionadas = [cat_id for var, cat_id in self.categoria_vars if var.get()]
        if not categorias_selecionadas:
            messagebox.showerror("Erro", "Selecione pelo menos uma categoria.")
            return

        try:
            # Verificar se o piloto já existe
            cursor.execute("SELECT id FROM pilotos WHERE LOWER(nome) = ?", (nome.lower(),))
            piloto = cursor.fetchone()

            if piloto:
                piloto_id = piloto[0]
                messagebox.showerror("Erro", "Já existe um piloto com esse nome.")
                return
            else:
                # Inserir novo piloto
                cursor.execute("INSERT INTO pilotos (nome) VALUES (?)", (nome_capitalizado,))
                piloto_id = cursor.lastrowid

                # Inserir categorias do piloto
                for cat_id in categorias_selecionadas:
                    cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                                   (piloto_id, cat_id))

                # Se um time foi selecionado, associá-lo ao piloto
                if time_nome:
                    cursor.execute("SELECT id FROM times WHERE nome = ?", (time_nome,))
                    time = cursor.fetchone()
                    if time:
                        time_id = time[0]
                        # Verificar se o piloto já tem time
                        cursor.execute("SELECT * FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))
                        piloto_time_existente = cursor.fetchone()

                        if piloto_time_existente:
                            # Atualizar time existente
                            cursor.execute("UPDATE pilotos_times SET time_id = ? WHERE piloto_id = ?",
                                           (time_id, piloto_id))
                        else:
                            # Associar o novo time
                            cursor.execute("INSERT INTO pilotos_times (piloto_id, time_id) VALUES (?, ?)",
                                           (piloto_id, time_id))
                # Se nenhum time for selecionado, garantir que não haja associação
                else:
                    # Se nenhum time for selecionado e o piloto já tem time, remover o time
                    cursor.execute("DELETE FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))

            conn.commit()
            messagebox.showinfo("Sucesso", "Piloto cadastrado com sucesso!")
            self.entry_nome.delete(0, 'end')
            for var, _ in self.categoria_vars:
                var.set(False)
            self.dropdown_time.set("")  # Resetar para vazio
            self.carregar_pilotos()  # Recarregar a lista de pilotos
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Piloto já está associado a esta categoria.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar piloto: {e}")

    def editar_piloto(self):
        # Verificar se algum item foi selecionado
        selecionados = self.tree.selection()
        if len(selecionados) != 1:
            messagebox.showerror("Erro", "Selecione exatamente um piloto para editar.")
            return

        # Obter valores do piloto selecionado
        valores = self.tree.item(selecionados[0], 'values')
        nome_piloto = valores[0]

        # Abrir janela para editar o piloto
        EditarPilotoWindow(self, nome_piloto)

    def capitalizar_nome(self, nome):
        # Capitaliza corretamente o nome (primeira letra maiúscula de cada palavra)
        return ' '.join(word.capitalize() for word in nome.split())

    def verificar_nomes_parecidos(self):
        # Obter lista de nomes de pilotos
        cursor.execute("SELECT nome FROM pilotos")
        nomes = [row[0] for row in cursor.fetchall()]

        nomes_lower = [nome.lower() for nome in nomes]
        nomes_dict = {nome.lower(): nome for nome in nomes}  # Map lowercased to original

        # Usar difflib para encontrar nomes semelhantes
        similar_pairs = []
        for i in range(len(nomes_lower)):
            nome1 = nomes_lower[i]
            nome_original1 = nomes_dict[nome1]
            matches = difflib.get_close_matches(nome1, nomes_lower, n=5, cutoff=0.8)
            for nome2 in matches:
                if nome1 == nome2:
                    continue
                # Ordenar os nomes para evitar duplicatas
                pair = tuple(sorted([nome_original1, nomes_dict[nome2]]))
                if pair not in similar_pairs:
                    similar_pairs.append(pair)

        # Remover duplicatas
        unique_pairs = []
        seen = set()
        for pair in similar_pairs:
            if pair not in seen:
                unique_pairs.append(pair)
                seen.add(pair)

        # Para cada par semelhante, perguntar ao usuário se deseja unificar
        for pair in unique_pairs:
            piloto1, piloto2 = pair
            response = messagebox.askyesno("Nomes Semelhantes Detectados",
                                           f"Os pilotos '{piloto1}' e '{piloto2}' têm nomes semelhantes.\n\nDeseja unificá-los?")
            if response:
                # Perguntar pelo novo nome unificado
                novo_nome = simpledialog.askstring("Unificar Pilotos",
                                                   f"Unificar '{piloto1}' e '{piloto2}'.\n\nDigite o novo nome para o piloto unificado:")
                if novo_nome:
                    # Unificar os pilotos
                    self.unificar_pilotos(piloto1, piloto2, novo_nome)
            # Se não, continuar

    def unir_pilotos(self):
        # Obter pilotos selecionados na Treeview
        selecionados = self.tree.selection()
        if len(selecionados) != 2:
            messagebox.showerror("Erro", "Selecione exatamente dois pilotos para unir.")
            return

        # Coletar os IDs e nomes dos pilotos selecionados
        pilotos_selecionados = []
        for sel in selecionados:
            nome_piloto = self.tree.item(sel, 'values')[0]
            cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome_piloto,))
            piloto = cursor.fetchone()
            if piloto:
                pilotos_selecionados.append((piloto[0], nome_piloto))

        # Verificar se encontrou os dois pilotos
        if len(pilotos_selecionados) != 2:
            messagebox.showerror("Erro", "Ocorreu um erro ao obter os pilotos selecionados.")
            return

        # Perguntar ao usuário para confirmar o novo nome unificado
        nomes = [p[1] for p in pilotos_selecionados]
        novo_nome = simpledialog.askstring("Unir Pilotos",
                                           f"Os pilotos selecionados serão unificados.\nNomes: {', '.join(nomes)}\n\nDigite o novo nome para o piloto unificado:")
        if not novo_nome:
            return

        # Unificar pilotos
        self.unificar_pilotos(pilotos_selecionados[0][1], pilotos_selecionados[1][1], novo_nome)

    def unificar_pilotos(self, piloto1_nome, piloto2_nome, novo_nome):
        try:
            # Buscar IDs dos pilotos
            cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (piloto1_nome,))
            piloto1 = cursor.fetchone()
            cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (piloto2_nome,))
            piloto2 = cursor.fetchone()

            if not piloto1 or not piloto2:
                messagebox.showerror("Erro", "Um ou ambos os pilotos não foram encontrados.")
                return

            piloto1_id, piloto2_id = piloto1[0], piloto2[0]

            # Transferir resultados do segundo piloto para o primeiro piloto, verificando duplicatas
            cursor.execute("SELECT * FROM resultados_etapas WHERE piloto_id = ?", (piloto2_id,))
            resultados_piloto2 = cursor.fetchall()
            for resultado in resultados_piloto2:
                etapa_id = resultado[1]  # etapa_id
                categoria_id = resultado[3]  # categoria_id

                # Verificar se já existe um resultado para o piloto1 na mesma etapa e categoria
                cursor.execute('''SELECT * FROM resultados_etapas
                                  WHERE etapa_id = ? AND piloto_id = ? AND categoria_id = ?''',
                               (etapa_id, piloto1_id, categoria_id))
                resultado_existente = cursor.fetchone()

                if not resultado_existente:
                    # Se não houver conflito, transferir o resultado
                    cursor.execute('''UPDATE resultados_etapas
                                      SET piloto_id = ?
                                      WHERE piloto_id = ? AND etapa_id = ? AND categoria_id = ?''',
                                   (piloto1_id, piloto2_id, etapa_id, categoria_id))
                else:
                    # Se já houver um resultado, decidir como proceder (manter ou descartar duplicado)
                    # Neste caso, vamos ignorar o resultado duplicado do piloto2
                    continue

            # Transferir categorias do segundo piloto para o primeiro piloto
            cursor.execute("SELECT categoria_id FROM pilotos_categorias WHERE piloto_id = ?", (piloto2_id,))
            categorias_piloto2 = cursor.fetchall()
            for categoria in categorias_piloto2:
                categoria_id = categoria[0]
                # Verificar se o piloto1 já está nessa categoria para evitar duplicatas
                cursor.execute("SELECT 1 FROM pilotos_categorias WHERE piloto_id = ? AND categoria_id = ?",
                               (piloto1_id, categoria_id))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                                   (piloto1_id, categoria_id))

            # Transferir time do segundo piloto para o primeiro piloto, se existir
            cursor.execute("SELECT time_id FROM pilotos_times WHERE piloto_id = ?", (piloto2_id,))
            time_piloto2 = cursor.fetchone()
            if time_piloto2:
                time_id = time_piloto2[0]
                # Verificar se o piloto1 já tem um time
                cursor.execute("SELECT time_id FROM pilotos_times WHERE piloto_id = ?", (piloto1_id,))
                time_piloto1 = cursor.fetchone()
                if time_piloto1:
                    # Atualizar time do piloto1 para o time do piloto2
                    cursor.execute("UPDATE pilotos_times SET time_id = ? WHERE piloto_id = ?",
                                   (time_id, piloto1_id))
                else:
                    # Associar o time do piloto2 ao piloto1
                    cursor.execute("INSERT INTO pilotos_times (piloto_id, time_id) VALUES (?, ?)",
                                   (piloto1_id, time_id))

            # Atualizar o nome do piloto principal para o novo nome unificado
            novo_nome_capitalizado = self.capitalizar_nome(novo_nome)
            cursor.execute("UPDATE pilotos SET nome = ? WHERE id = ?", (novo_nome_capitalizado, piloto1_id))

            # Remover o segundo piloto
            cursor.execute("DELETE FROM pilotos WHERE id = ?", (piloto2_id,))

            conn.commit()
            messagebox.showinfo("Sucesso",
                                f"Pilotos '{piloto1_nome}' e '{piloto2_nome}' unificados como '{novo_nome_capitalizado}'.")
            self.carregar_pilotos()  # Atualizar a lista de pilotos
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao unificar pilotos: {e}")

    def remover_piloto(self):
        # Verificar se algum piloto foi selecionado
        selecionados = self.tree.selection()
        if not selecionados:
            messagebox.showerror("Erro", "Selecione um ou mais pilotos para remover.")
            return

        # Obter os nomes dos pilotos selecionados
        nomes_pilotos = [self.tree.item(sel, 'values')[0] for sel in selecionados]

        # Confirmar a remoção
        if messagebox.askyesno("Remover Pilotos", f"Tem certeza que deseja remover os pilotos: {', '.join(nomes_pilotos)}?"):
            try:
                for nome_piloto in nomes_pilotos:
                    # Buscar o piloto pelo nome
                    cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome_piloto,))
                    piloto = cursor.fetchone()
                    if not piloto:
                        messagebox.showerror("Erro", f"Piloto '{nome_piloto}' não encontrado.")
                        continue
                    piloto_id = piloto[0]

                    # Remover o piloto da tabela pilotos e das tabelas relacionadas (pilotos_categorias, pilotos_times)
                    cursor.execute("DELETE FROM pilotos WHERE id = ?", (piloto_id,))
                    cursor.execute("DELETE FROM pilotos_categorias WHERE piloto_id = ?", (piloto_id,))
                    cursor.execute("DELETE FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))
                    # Opcional: Remover também resultados nas etapas, se necessário
                    cursor.execute("DELETE FROM resultados_etapas WHERE piloto_id = ?", (piloto_id,))

                conn.commit()
                messagebox.showinfo("Sucesso", "Pilotos removidos com sucesso!")
                self.carregar_pilotos()  # Atualizar a lista de pilotos
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao remover pilotos: {e}")


class EditarPilotoWindow(ctk.CTkToplevel):
    def __init__(self, parent, nome_piloto):
        super().__init__(parent)
        self.title(f"Editar Piloto - {nome_piloto}")
        self.geometry("500x600")
        self.parent = parent
        self.nome_piloto = nome_piloto

        # Campo para Nome do Piloto
        self.label_nome = ctk.CTkLabel(self, text="Nome do Piloto")
        self.label_nome.pack(pady=10)
        self.entry_nome = ctk.CTkEntry(self, placeholder_text="Nome do Piloto")
        self.entry_nome.pack(pady=10)
        self.entry_nome.insert(0, nome_piloto)

        # Seleção de Categorias
        self.label_categoria = ctk.CTkLabel(self, text="Selecione Categorias")
        self.label_categoria.pack(pady=5)

        self.categorias = parent.get_categorias()
        self.categoria_vars = []
        self.categoria_checkboxes = []
        # Buscar categorias atuais do piloto
        cursor.execute("""
            SELECT categoria_id FROM pilotos_categorias 
            WHERE piloto_id = (SELECT id FROM pilotos WHERE nome = ?)
            """, (nome_piloto,))
        categorias_piloto = cursor.fetchall()
        categorias_piloto_ids = [cat[0] for cat in categorias_piloto]

        for categoria in self.categorias:
            var = ctk.BooleanVar()
            if categoria[0] in categorias_piloto_ids:
                var.set(True)
            cb = ctk.CTkCheckBox(self, text=categoria[1], variable=var)
            cb.pack(anchor='w')
            self.categoria_vars.append((var, categoria[0]))
            self.categoria_checkboxes.append(cb)

        # Seleção de Time
        self.label_time = ctk.CTkLabel(self, text="Selecione Time (opcional)")
        self.label_time.pack(pady=10)

        self.times = parent.get_times()
        self.time_var = StringVar()
        time_values = [""] + [time[1] for time in self.times]  # Adiciona uma opção vazia
        self.dropdown_time = ctk.CTkComboBox(self, values=time_values, variable=self.time_var)
        self.dropdown_time.pack(pady=5)
        self.dropdown_time.set("")  # Define como vazio por padrão

        # Carregar o time atual do piloto
        cursor.execute("SELECT time_id FROM pilotos_times WHERE piloto_id = (SELECT id FROM pilotos WHERE nome = ?)", (nome_piloto,))
        time_piloto = cursor.fetchone()
        if time_piloto:
            time_id = time_piloto[0]
            cursor.execute("SELECT nome FROM times WHERE id = ?", (time_id,))
            time_nome = cursor.fetchone()
            if time_nome:
                self.dropdown_time.set(time_nome[0])
        else:
            self.dropdown_time.set("")  # Deixar vazio se não tiver time

        # Botão para Salvar Alterações
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Alterações", command=self.salvar_alteracoes)
        self.btn_salvar.pack(pady=20)

    def salvar_alteracoes(self):
        novo_nome = self.entry_nome.get().strip()
        if not novo_nome:
            messagebox.showerror("Erro", "O nome do piloto é obrigatório.")
            return

        # Capitalizar o nome corretamente
        novo_nome_capitalizado = self.parent.capitalizar_nome(novo_nome)

        categorias_selecionadas = [cat_id for var, cat_id in self.categoria_vars if var.get()]
        if not categorias_selecionadas:
            messagebox.showerror("Erro", "Selecione pelo menos uma categoria.")
            return

        time_nome = self.time_var.get()

        try:
            # Verificar se o novo nome já existe (exceto o piloto atual)
            cursor.execute("SELECT id FROM pilotos WHERE LOWER(nome) = ? AND nome != ?", (novo_nome.lower(), self.nome_piloto))
            piloto_existente = cursor.fetchone()
            if piloto_existente:
                messagebox.showerror("Erro", "Já existe um piloto com esse nome.")
                return

            # Atualizar o nome do piloto
            cursor.execute("UPDATE pilotos SET nome = ? WHERE nome = ?", (novo_nome_capitalizado, self.nome_piloto))

            # Atualizar as categorias do piloto
            piloto_id = self.get_piloto_id(self.nome_piloto)
            if piloto_id:
                # Remover todas as categorias atuais
                cursor.execute("DELETE FROM pilotos_categorias WHERE piloto_id = ?", (piloto_id,))
                # Adicionar as categorias selecionadas
                for cat_id in categorias_selecionadas:
                    cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                                   (piloto_id, cat_id))

            # Atualizar a associação com o time
            if time_nome:
                cursor.execute("SELECT id FROM times WHERE nome = ?", (time_nome,))
                time = cursor.fetchone()
                if time:
                    time_id = time[0]
                    # Verificar se o piloto já tem time
                    cursor.execute("SELECT * FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))
                    piloto_time_existente = cursor.fetchone()

                    if piloto_time_existente:
                        # Atualizar time existente
                        cursor.execute("UPDATE pilotos_times SET time_id = ? WHERE piloto_id = ?",
                                       (time_id, piloto_id))
                    else:
                        # Associar o novo time
                        cursor.execute("INSERT INTO pilotos_times (piloto_id, time_id) VALUES (?, ?)",
                                       (piloto_id, time_id))
            else:
                # Se nenhum time for selecionado e o piloto já tem time, remover o time
                cursor.execute("DELETE FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))

            conn.commit()
            messagebox.showinfo("Sucesso", "Piloto atualizado com sucesso!")
            self.parent.carregar_pilotos()  # Atualizar a lista de pilotos na janela principal
            self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Já existe um piloto com esse nome.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar piloto: {e}")

    def get_piloto_id(self, nome_piloto):
        cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome_piloto,))
        piloto = cursor.fetchone()
        return piloto[0] if piloto else None


class AdicionarPilotoManualWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Adicionar Piloto Manualmente")
        self.geometry("400x500")
        self.transient(master)  # Sobrepõe a janela principal
        self.grab_set()  # Modal

        # Campo para Nome do Piloto
        self.label_nome = ctk.CTkLabel(self, text="Nome do Piloto")
        self.label_nome.pack(pady=10)

        self.entry_nome = ctk.CTkEntry(self, placeholder_text="Nome do Piloto")
        self.entry_nome.pack(pady=5)

        # Campo para Selecionar Categoria
        self.label_categoria = ctk.CTkLabel(self, text="Selecione a Categoria")
        self.label_categoria.pack(pady=10)

        self.categorias = self.get_categorias()
        if not self.categorias:
            messagebox.showerror("Erro", "Nenhuma categoria cadastrada. Por favor, cadastre uma categoria primeiro.")
            self.destroy()
            return

        self.categoria_var = StringVar()
        self.dropdown_categoria = ctk.CTkComboBox(
            self,
            values=[cat[1] for cat in self.categorias],
            variable=self.categoria_var
        )
        self.dropdown_categoria.pack(pady=5)

        # Seleção de Time (opcional)
        self.label_time = ctk.CTkLabel(self, text="Selecione Time (opcional)")
        self.label_time.pack(pady=10)

        self.times = self.get_times()
        self.time_var = StringVar()
        time_values = [""] + [time[1] for time in self.times]  # Adiciona uma opção vazia
        self.dropdown_time = ctk.CTkComboBox(self, values=time_values, variable=self.time_var)
        self.dropdown_time.pack(pady=5)
        self.dropdown_time.set("")  # Define como vazio por padrão

        # Botão para Salvar Piloto
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Piloto", command=self.salvar_piloto)
        self.btn_salvar.pack(pady=20)

    def get_categorias(self):
        return buscar_categorias()

    def get_times(self):
        return buscar_times()

    def salvar_piloto(self):
        nome = self.entry_nome.get().strip()
        categoria_nome = self.categoria_var.get()
        time_nome = self.time_var.get()

        if not nome or not categoria_nome:
            messagebox.showerror("Erro", "Todos os campos obrigatórios devem ser preenchidos.")
            return

        try:
            cursor.execute("SELECT id FROM categorias WHERE nome = ?", (categoria_nome,))
            categoria = cursor.fetchone()
            if not categoria:
                messagebox.showerror("Erro", "Categoria inválida.")
                return
            categoria_id = categoria[0]

            cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome,))
            piloto = cursor.fetchone()
            if piloto:
                piloto_id = piloto[0]
            else:
                cursor.execute("INSERT INTO pilotos (nome) VALUES (?)", (nome,))
                piloto_id = cursor.lastrowid

            cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                           (piloto_id, categoria_id))

            # Se um time foi selecionado, associá-lo ao piloto
            if time_nome:
                cursor.execute("SELECT id FROM times WHERE nome = ?", (time_nome,))
                time = cursor.fetchone()
                if time:
                    time_id = time[0]
                    # Verificar se o piloto já tem time
                    cursor.execute("SELECT * FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))
                    piloto_time_existente = cursor.fetchone()

                    if piloto_time_existente:
                        # Atualizar time existente
                        cursor.execute("UPDATE pilotos_times SET time_id = ? WHERE piloto_id = ?",
                                       (time_id, piloto_id))
                    else:
                        # Associar o novo time
                        cursor.execute("INSERT INTO pilotos_times (piloto_id, time_id) VALUES (?, ?)",
                                       (piloto_id, time_id))
            # Se nenhum time for selecionado, garantir que não haja associação
            else:
                # Se nenhum time for selecionado e o piloto já tem time, remover o time
                cursor.execute("DELETE FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))

            conn.commit()
            messagebox.showinfo("Sucesso", "Piloto cadastrado com sucesso!")
            self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Piloto já está associado a esta categoria.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar piloto: {e}")


class EditarPilotoWindow(ctk.CTkToplevel):
    def __init__(self, parent, nome_piloto):
        super().__init__(parent)
        self.title(f"Editar Piloto - {nome_piloto}")
        self.geometry("500x600")
        self.parent = parent
        self.nome_piloto = nome_piloto

        # Campo para Nome do Piloto
        self.label_nome = ctk.CTkLabel(self, text="Nome do Piloto")
        self.label_nome.pack(pady=10)
        self.entry_nome = ctk.CTkEntry(self, placeholder_text="Nome do Piloto")
        self.entry_nome.pack(pady=10)
        self.entry_nome.insert(0, nome_piloto)

        # Seleção de Categorias
        self.label_categoria = ctk.CTkLabel(self, text="Selecione Categorias")
        self.label_categoria.pack(pady=5)

        self.categorias = parent.get_categorias()
        self.categoria_vars = []
        self.categoria_checkboxes = []
        # Buscar categorias atuais do piloto
        cursor.execute("""
            SELECT categoria_id FROM pilotos_categorias 
            WHERE piloto_id = (SELECT id FROM pilotos WHERE nome = ?)
            """, (nome_piloto,))
        categorias_piloto = cursor.fetchall()
        categorias_piloto_ids = [cat[0] for cat in categorias_piloto]

        for categoria in self.categorias:
            var = ctk.BooleanVar()
            if categoria[0] in categorias_piloto_ids:
                var.set(True)
            cb = ctk.CTkCheckBox(self, text=categoria[1], variable=var)
            cb.pack(anchor='w')
            self.categoria_vars.append((var, categoria[0]))
            self.categoria_checkboxes.append(cb)

        # Seleção de Time
        self.label_time = ctk.CTkLabel(self, text="Selecione Time (opcional)")
        self.label_time.pack(pady=10)

        self.times = parent.get_times()
        self.time_var = StringVar()
        time_values = [""] + [time[1] for time in self.times]  # Adiciona uma opção vazia
        self.dropdown_time = ctk.CTkComboBox(self, values=time_values, variable=self.time_var)
        self.dropdown_time.pack(pady=5)
        self.dropdown_time.set("")  # Define como vazio por padrão

        # Carregar o time atual do piloto
        cursor.execute("SELECT time_id FROM pilotos_times WHERE piloto_id = (SELECT id FROM pilotos WHERE nome = ?)", (nome_piloto,))
        time_piloto = cursor.fetchone()
        if time_piloto:
            time_id = time_piloto[0]
            cursor.execute("SELECT nome FROM times WHERE id = ?", (time_id,))
            time_nome = cursor.fetchone()
            if time_nome:
                self.dropdown_time.set(time_nome[0])
        else:
            self.dropdown_time.set("")  # Deixar vazio se não tiver time

        # Botão para Salvar Alterações
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Alterações", command=self.salvar_alteracoes)
        self.btn_salvar.pack(pady=20)

    def salvar_alteracoes(self):
        novo_nome = self.entry_nome.get().strip()
        if not novo_nome:
            messagebox.showerror("Erro", "O nome do piloto é obrigatório.")
            return

        # Capitalizar o nome corretamente
        novo_nome_capitalizado = self.parent.capitalizar_nome(novo_nome)

        categorias_selecionadas = [cat_id for var, cat_id in self.categoria_vars if var.get()]
        if not categorias_selecionadas:
            messagebox.showerror("Erro", "Selecione pelo menos uma categoria.")
            return

        time_nome = self.time_var.get()

        try:
            # Verificar se o novo nome já existe (exceto o piloto atual)
            cursor.execute("SELECT id FROM pilotos WHERE LOWER(nome) = ? AND nome != ?", (novo_nome.lower(), self.nome_piloto))
            piloto_existente = cursor.fetchone()
            if piloto_existente:
                messagebox.showerror("Erro", "Já existe um piloto com esse nome.")
                return

            # Atualizar o nome do piloto
            cursor.execute("UPDATE pilotos SET nome = ? WHERE nome = ?", (novo_nome_capitalizado, self.nome_piloto))

            # Atualizar as categorias do piloto
            piloto_id = self.get_piloto_id(self.nome_piloto)
            if piloto_id:
                # Remover todas as categorias atuais
                cursor.execute("DELETE FROM pilotos_categorias WHERE piloto_id = ?", (piloto_id,))
                # Adicionar as categorias selecionadas
                for cat_id in categorias_selecionadas:
                    cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                                   (piloto_id, cat_id))

            # Atualizar a associação com o time
            if time_nome:
                cursor.execute("SELECT id FROM times WHERE nome = ?", (time_nome,))
                time = cursor.fetchone()
                if time:
                    time_id = time[0]
                    # Verificar se o piloto já tem time
                    cursor.execute("SELECT * FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))
                    piloto_time_existente = cursor.fetchone()

                    if piloto_time_existente:
                        # Atualizar time existente
                        cursor.execute("UPDATE pilotos_times SET time_id = ? WHERE piloto_id = ?",
                                       (time_id, piloto_id))
                    else:
                        # Associar o novo time
                        cursor.execute("INSERT INTO pilotos_times (piloto_id, time_id) VALUES (?, ?)",
                                       (piloto_id, time_id))
            else:
                # Se nenhum time for selecionado e o piloto já tem time, remover o time
                cursor.execute("DELETE FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))

            conn.commit()
            messagebox.showinfo("Sucesso", "Piloto atualizado com sucesso!")
            self.parent.carregar_pilotos()  # Atualizar a lista de pilotos na janela principal
            self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Já existe um piloto com esse nome.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar piloto: {e}")

    def get_piloto_id(self, nome_piloto):
        cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome_piloto,))
        piloto = cursor.fetchone()
        return piloto[0] if piloto else None


class AdicionarPilotoManualWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Adicionar Piloto Manualmente")
        self.geometry("400x500")
        self.transient(master)  # Sobrepõe a janela principal
        self.grab_set()  # Modal

        # Campo para Nome do Piloto
        self.label_nome = ctk.CTkLabel(self, text="Nome do Piloto")
        self.label_nome.pack(pady=10)

        self.entry_nome = ctk.CTkEntry(self, placeholder_text="Nome do Piloto")
        self.entry_nome.pack(pady=5)

        # Campo para Selecionar Categoria
        self.label_categoria = ctk.CTkLabel(self, text="Selecione a Categoria")
        self.label_categoria.pack(pady=10)

        self.categorias = self.get_categorias()
        if not self.categorias:
            messagebox.showerror("Erro", "Nenhuma categoria cadastrada. Por favor, cadastre uma categoria primeiro.")
            self.destroy()
            return

        self.categoria_var = StringVar()
        self.dropdown_categoria = ctk.CTkComboBox(
            self,
            values=[cat[1] for cat in self.categorias],
            variable=self.categoria_var
        )
        self.dropdown_categoria.pack(pady=5)

        # Seleção de Time (opcional)
        self.label_time = ctk.CTkLabel(self, text="Selecione Time (opcional)")
        self.label_time.pack(pady=10)

        self.times = self.get_times()
        self.time_var = StringVar()
        time_values = [""] + [time[1] for time in self.times]  # Adiciona uma opção vazia
        self.dropdown_time = ctk.CTkComboBox(self, values=time_values, variable=self.time_var)
        self.dropdown_time.pack(pady=5)
        self.dropdown_time.set("")  # Define como vazio por padrão

        # Botão para Salvar Piloto
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Piloto", command=self.salvar_piloto)
        self.btn_salvar.pack(pady=20)

    def get_categorias(self):
        return buscar_categorias()

    def get_times(self):
        return buscar_times()

    def salvar_piloto(self):
        nome = self.entry_nome.get().strip()
        categoria_nome = self.categoria_var.get()
        time_nome = self.time_var.get()

        if not nome or not categoria_nome:
            messagebox.showerror("Erro", "Todos os campos obrigatórios devem ser preenchidos.")
            return

        try:
            cursor.execute("SELECT id FROM categorias WHERE nome = ?", (categoria_nome,))
            categoria = cursor.fetchone()
            if not categoria:
                messagebox.showerror("Erro", "Categoria inválida.")
                return
            categoria_id = categoria[0]

            cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome,))
            piloto = cursor.fetchone()
            if piloto:
                piloto_id = piloto[0]
            else:
                cursor.execute("INSERT INTO pilotos (nome) VALUES (?)", (nome,))
                piloto_id = cursor.lastrowid

            cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                           (piloto_id, categoria_id))

            # Se um time foi selecionado, associá-lo ao piloto
            if time_nome:
                cursor.execute("SELECT id FROM times WHERE nome = ?", (time_nome,))
                time = cursor.fetchone()
                if time:
                    time_id = time[0]
                    # Verificar se o piloto já tem time
                    cursor.execute("SELECT * FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))
                    piloto_time_existente = cursor.fetchone()

                    if piloto_time_existente:
                        # Atualizar time existente
                        cursor.execute("UPDATE pilotos_times SET time_id = ? WHERE piloto_id = ?",
                                       (time_id, piloto_id))
                    else:
                        # Associar o novo time
                        cursor.execute("INSERT INTO pilotos_times (piloto_id, time_id) VALUES (?, ?)",
                                       (piloto_id, time_id))
            # Se nenhum time for selecionado, garantir que não haja associação
            else:
                # Se nenhum time for selecionado e o piloto já tem time, remover o time
                cursor.execute("DELETE FROM pilotos_times WHERE piloto_id = ?", (piloto_id,))

            conn.commit()
            messagebox.showinfo("Sucesso", "Piloto cadastrado com sucesso!")
            self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Piloto já está associado a esta categoria.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar piloto: {e}")


# Exemplo de como integrar as frames em uma janela principal
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestão de Pilotos e Categorias")
        self.geometry("800x600")

        # Criar abas para Categorias e Pilotos
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(expand=True, fill="both")

        self.tabview.add("Categorias")
        self.tabview.add("Pilotos")

        self.categorias_frame = CadastroCategoriasFrame(self.tabview.tab("Categorias"))
        self.pilotos_frame = CadastroPilotosFrame(self.tabview.tab("Pilotos"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
