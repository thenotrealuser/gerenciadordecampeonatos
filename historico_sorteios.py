import customtkinter as ctk
from tkinter import ttk
from database import cursor, conn

class HistoricoSorteiosFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        self.label = ctk.CTkLabel(self, text="Histórico de Sorteios", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=10)

        # Treeview para Mostrar Todos os Sorteios
        self.tree = ttk.Treeview(
            self,
            columns=("Categoria", "Piloto", "Kart", "Data"),
            show='headings',
            selectmode='browse'
        )
        self.tree.heading("Categoria", text="Categoria")
        self.tree.heading("Piloto", text="Piloto")
        self.tree.heading("Kart", text="Kart")
        self.tree.heading("Data", text="Data do Sorteio")
        self.tree.column("Categoria", width=100, anchor='center')
        self.tree.column("Piloto", width=150, anchor='center')
        self.tree.column("Kart", width=80, anchor='center')
        self.tree.column("Data", width=120, anchor='center')
        self.tree.pack(fill="both", expand=True, pady=10)

        self.carregar_historico()

    def carregar_historico(self):
        cursor.execute(
            "SELECT categoria_id, piloto_id, kart, data_sorteio FROM historico_sorteios ORDER BY data_sorteio DESC")
        sorteios = cursor.fetchall()
        for sorteio in sorteios:
            categoria_id, piloto_id, kart, data = sorteio
            cursor.execute("SELECT nome FROM categorias WHERE id = ?", (categoria_id,))
            categoria = cursor.fetchone()[0]
            cursor.execute("SELECT nome FROM pilotos WHERE id = ?", (piloto_id,))
            piloto = cursor.fetchone()[0]
            self.tree.insert('', 'end', values=(categoria, piloto, kart, data))
