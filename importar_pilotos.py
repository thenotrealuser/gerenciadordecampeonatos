import sqlite3

import customtkinter as ctk
from database import cursor, conn
from tkinter import StringVar, messagebox, filedialog


class ImportarPilotosFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        self.label = ctk.CTkLabel(self, text="Importar Lista de Pilotos", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=10)

        # Seleção de Arquivo
        self.btn_selecionar_arquivo = ctk.CTkButton(self, text="Selecionar Arquivo TXT/CSV",
                                                    command=self.selecionar_arquivo)
        self.btn_selecionar_arquivo.pack(pady=10)

        # Seleção de Categoria
        self.label_categoria = ctk.CTkLabel(self, text="Selecione a Categoria")
        self.label_categoria.pack(pady=5)

        self.categorias = self.get_categorias()
        self.categoria_var = StringVar()
        self.dropdown_categoria = ctk.CTkComboBox(
            self,
            values=[cat[1] for cat in self.categorias],
            variable=self.categoria_var
        )
        self.dropdown_categoria.pack(pady=5)

    def get_categorias(self):
        cursor.execute("SELECT * FROM categorias ORDER BY nome")
        categorias = cursor.fetchall()
        return categorias

    def selecionar_arquivo(self):
        arquivo = filedialog.askopenfilename(title="Selecionar Arquivo",
                                             filetypes=[("TXT Files", "*.txt"), ("CSV Files", "*.csv")])
        if not arquivo:
            return
        categoria_nome = self.categoria_var.get()
        if not categoria_nome:
            messagebox.showerror("Erro", "Selecione uma categoria.")
            return
        categoria = next((cat for cat in self.categorias if cat[1] == categoria_nome), None)
        if not categoria:
            messagebox.showerror("Erro", "Categoria inválida.")
            return
        importar_pilotos(arquivo, categoria[0])


def importar_pilotos(arquivo, categoria_id):
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            linhas = f.readlines()

        # Remover quebras de linha e linhas vazias
        pilotos = [linha.strip() for linha in linhas if linha.strip()]

        # Processar os pilotos como necessário
        for nome in pilotos:
            if not nome:
                continue
            nome = nome.strip().lower()  # Normaliza o nome para minúsculas
            cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome,))
            piloto = cursor.fetchone()
            if piloto:
                piloto_id = piloto[0]
            else:
                cursor.execute("INSERT INTO pilotos (nome) VALUES (?)", (nome,))
                piloto_id = cursor.lastrowid
            try:
                cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                               (piloto_id, categoria_id))
            except sqlite3.IntegrityError:
                continue

        conn.commit()
        messagebox.showinfo("Sucesso", "Pilotos importados com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao importar pilotos: {e}")


def selecionar_arquivo():
    arquivo = filedialog.askopenfilename(title="Selecionar Arquivo",
                                         filetypes=[("TXT Files", "*.txt"), ("CSV Files", "*.csv")])
    if not arquivo:
        return
    categoria_nome = dropdown_categoria.get()
    if not categoria_nome:
        messagebox.showerror("Erro", "Selecione uma categoria.")
        return
    categoria = next((cat for cat in categorias if cat[1] == categoria_nome), None)
    if not categoria:
        messagebox.showerror("Erro", "Categoria inválida.")
        return
    importar_pilotos(arquivo, categoria[0])
