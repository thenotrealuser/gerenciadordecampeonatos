from tkinter import ttk, messagebox

import customtkinter as ctk
from database import cursor, conn
from tkinter import simpledialog


class CadastroTimesFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        self.label = ctk.CTkLabel(self, text="Cadastro de Times", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=10)

        # Campo para Nome do Time
        self.label_nome_time = ctk.CTkLabel(self, text="Nome do Time")
        self.label_nome_time.pack(pady=5)
        self.entry_nome_time = ctk.CTkEntry(self, placeholder_text="Digite o nome do time")
        self.entry_nome_time.pack(pady=10)

        # Botão para Salvar Time
        self.btn_salvar_time = ctk.CTkButton(self, text="Salvar Time", command=self.salvar_time)
        self.btn_salvar_time.pack(pady=10)

        # Lista de Times Cadastrados
        self.label_lista_times = ctk.CTkLabel(self, text="Times Cadastrados", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_lista_times.pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("Nome"), show="headings", selectmode="extended")
        self.tree.heading("Nome", text="Nome")
        self.tree.pack(fill="both", expand=True, pady=10)

        # Adicionar scrollbar à Treeview
        self.scrollbar_tree = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar_tree.set)
        self.scrollbar_tree.pack(side='right', fill='y')

        # Botão para Editar Time
        self.btn_editar_time = ctk.CTkButton(self, text="Editar Time", command=self.editar_time)
        self.btn_editar_time.pack(pady=10)

        # Botão para Remover Time
        self.btn_remover_time = ctk.CTkButton(self, text="Remover Time", command=self.remover_time)
        self.btn_remover_time.pack(pady=10)

        # Carregar times cadastrados
        self.carregar_times()

    def salvar_time(self):
        nome_time = self.entry_nome_time.get().strip()
        if not nome_time:
            messagebox.showerror("Erro", "O nome do time é obrigatório.")
            return

        try:
            cursor.execute("SELECT id FROM times WHERE LOWER(nome) = ?", (nome_time.lower(),))
            time_existente = cursor.fetchone()
            if time_existente:
                messagebox.showerror("Erro", "Já existe um time com esse nome.")
                return

            cursor.execute("INSERT INTO times (nome) VALUES (?)", (nome_time,))
            conn.commit()
            messagebox.showinfo("Sucesso", "Time cadastrado com sucesso!")
            self.entry_nome_time.delete(0, 'end')
            self.carregar_times()  # Atualizar a lista de times
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar time: {e}")

    def carregar_times(self):
        # Limpar a Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Buscar times cadastrados
        cursor.execute("SELECT nome FROM times ORDER BY nome")
        times = cursor.fetchall()

        # Inserir times na Treeview
        for time in times:
            self.tree.insert("", "end", values=time)

    def editar_time(self):
        # Verificar se algum time foi selecionado
        selecionados = self.tree.selection()
        if len(selecionados) != 1:
            messagebox.showerror("Erro", "Selecione exatamente um time para editar.")
            return

        # Obter o nome do time selecionado
        valores = self.tree.item(selecionados[0], 'values')
        nome_time = valores[0]

        # Perguntar ao usuário o novo nome do time
        novo_nome_time = simpledialog.askstring("Editar Time", f"Editar o time '{nome_time}'.\n\nDigite o novo nome:")
        if not novo_nome_time:
            return

        try:
            # Verificar se o novo nome já existe
            cursor.execute("SELECT id FROM times WHERE LOWER(nome) = ?", (novo_nome_time.lower(),))
            time_existente = cursor.fetchone()
            if time_existente:
                messagebox.showerror("Erro", "Já existe um time com esse nome.")
                return

            # Atualizar o nome do time
            cursor.execute("UPDATE times SET nome = ? WHERE nome = ?", (novo_nome_time, nome_time))
            conn.commit()
            messagebox.showinfo("Sucesso", "Time atualizado com sucesso!")
            self.carregar_times()  # Atualizar a lista de times
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao editar time: {e}")

    def remover_time(self):
        # Verificar se algum time foi selecionado
        selecionados = self.tree.selection()
        if not selecionados:
            messagebox.showerror("Erro", "Selecione um ou mais times para remover.")
            return

        # Obter os nomes dos times selecionados
        nomes_times = [self.tree.item(sel, 'values')[0] for sel in selecionados]

        # Confirmar a remoção
        if messagebox.askyesno("Remover Times", f"Tem certeza que deseja remover os times: {', '.join(nomes_times)}?"):
            try:
                for nome_time in nomes_times:
                    # Buscar o time pelo nome
                    cursor.execute("SELECT id FROM times WHERE nome = ?", (nome_time,))
                    time = cursor.fetchone()
                    if not time:
                        messagebox.showerror("Erro", f"Time '{nome_time}' não encontrado.")
                        continue
                    time_id = time[0]

                    # Remover o time da tabela times e das tabelas relacionadas (pilotos_times)
                    cursor.execute("DELETE FROM times WHERE id = ?", (time_id,))
                    cursor.execute("DELETE FROM pilotos_times WHERE time_id = ?", (time_id,))

                conn.commit()
                messagebox.showinfo("Sucesso", "Times removidos com sucesso!")
                self.carregar_times()  # Atualizar a lista de times
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao remover times: {e}")
