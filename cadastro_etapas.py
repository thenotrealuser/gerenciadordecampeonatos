from tkinter import ttk, messagebox

import customtkinter as ctk
from database import cursor, conn


class CadastroEtapasFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        self.label = ctk.CTkLabel(self, text="Cadastro de Etapas", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=10)

        # Campo para Nome da Etapa
        self.entry_nome = ctk.CTkEntry(self, placeholder_text="Nome da Etapa")
        self.entry_nome.pack(pady=10)

        # Campo para Data da Etapa
        self.entry_data = ctk.CTkEntry(self, placeholder_text="Data (DD/MM/AAAA)")
        self.entry_data.pack(pady=10)

        # Botão para Salvar Etapa
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Etapa", command=self.salvar_etapa)
        self.btn_salvar.pack(pady=20)

        # Treeview para listar as etapas já cadastradas
        self.tree = ttk.Treeview(self, columns=("Nome", "Data"), show="headings")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Data", text="Data")
        self.tree.pack(fill="both", expand=True, pady=10)

        # Botões para Editar e Remover Etapas
        self.btn_editar = ctk.CTkButton(self, text="Editar Etapa", command=self.editar_etapa)
        self.btn_editar.pack(pady=10)

        self.btn_remover = ctk.CTkButton(self, text="Remover Etapa", command=self.remover_etapa)
        self.btn_remover.pack(pady=10)

        # Carregar etapas existentes
        self.carregar_etapas()

    def carregar_etapas(self):
        # Limpa a Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Carrega todas as etapas do banco de dados
        cursor.execute("SELECT nome, data FROM etapas ORDER BY data")
        etapas = cursor.fetchall()

        # Insere as etapas na Treeview
        for etapa in etapas:
            self.tree.insert("", "end", values=etapa)

    def salvar_etapa(self):
        nome = self.entry_nome.get().strip()
        data = self.entry_data.get().strip()
        if not nome or not data:
            messagebox.showerror("Erro", "Nome e Data da etapa são obrigatórios.")
            return

        try:
            cursor.execute("INSERT INTO etapas (nome, data) VALUES (?, ?)", (nome, data))
            conn.commit()
            messagebox.showinfo("Sucesso", "Etapa cadastrada com sucesso!")
            self.entry_nome.delete(0, 'end')
            self.entry_data.delete(0, 'end')
            self.carregar_etapas()  # Atualiza a lista de etapas
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar etapa: {e}")

    def editar_etapa(self):
        # Verifica se uma etapa foi selecionada
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showerror("Erro", "Selecione uma etapa para editar.")
            return

        # Obtém os valores da etapa selecionada
        valores = self.tree.item(selecionado, 'values')
        nome_etapa, data_etapa = valores

        # Janela para editar a etapa selecionada
        EditarEtapaWindow(self, nome_etapa, data_etapa)

    def remover_etapa(self):
        # Verifica se uma etapa foi selecionada
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showerror("Erro", "Selecione uma etapa para remover.")
            return

        # Obtém o nome da etapa selecionada
        valores = self.tree.item(selecionado, 'values')
        nome_etapa = valores[0]

        # Confirmar remoção
        if messagebox.askyesno("Remover Etapa", f"Tem certeza que deseja remover a etapa '{nome_etapa}'?"):
            try:
                cursor.execute("DELETE FROM etapas WHERE nome = ?", (nome_etapa,))
                conn.commit()
                self.carregar_etapas()  # Atualiza a lista de etapas
                messagebox.showinfo("Sucesso", "Etapa removida com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao remover etapa: {e}")


class EditarEtapaWindow(ctk.CTkToplevel):
    def __init__(self, master, nome_etapa, data_etapa):
        super().__init__(master)
        self.title("Editar Etapa")
        self.geometry("400x300")
        self.transient(master)  # Sobrepõe a janela principal
        self.grab_set()  # Modal

        self.nome_etapa_antigo = nome_etapa

        # Campo para Nome da Etapa
        self.label_nome = ctk.CTkLabel(self, text="Nome da Etapa")
        self.label_nome.pack(pady=10)
        self.entry_nome = ctk.CTkEntry(self, placeholder_text="Nome da Etapa")
        self.entry_nome.insert(0, nome_etapa)
        self.entry_nome.pack(pady=5)

        # Campo para Data da Etapa
        self.label_data = ctk.CTkLabel(self, text="Data da Etapa (DD/MM/AAAA)")
        self.label_data.pack(pady=10)
        self.entry_data = ctk.CTkEntry(self, placeholder_text="Data da Etapa")
        self.entry_data.insert(0, data_etapa)
        self.entry_data.pack(pady=5)

        # Botão para Salvar Alterações
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Alterações", command=self.salvar_alteracoes)
        self.btn_salvar.pack(pady=20)

    def salvar_alteracoes(self):
        novo_nome = self.entry_nome.get().strip()
        nova_data = self.entry_data.get().strip()

        if not novo_nome or not nova_data:
            messagebox.showerror("Erro", "Nome e Data da etapa são obrigatórios.")
            return

        try:
            cursor.execute("UPDATE etapas SET nome = ?, data = ? WHERE nome = ?", (novo_nome, nova_data, self.nome_etapa_antigo))
            conn.commit()
            messagebox.showinfo("Sucesso", "Etapa atualizada com sucesso!")
            self.master.carregar_etapas()  # Atualiza a lista de etapas na janela principal
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar alterações: {e}")
