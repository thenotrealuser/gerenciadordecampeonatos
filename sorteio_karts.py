import customtkinter as ctk
from database import cursor, conn
from tkinter import StringVar
from tkinter import ttk, messagebox
import random
import pandas as pd


class SorteioKartsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Criar frames principais
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.right_frame = ctk.CTkFrame(self, width=250)
        self.right_frame.pack(side="right", fill="y")

        # ----------------- Left Frame -----------------

        # Título
        self.label = ctk.CTkLabel(self.left_frame, text="Sorteio de Karts", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=10)

        # Seleção de Categoria
        self.label_categoria = ctk.CTkLabel(self.left_frame, text="Selecione a Categoria")
        self.label_categoria.pack(pady=5)

        self.categorias = self.get_categorias()
        self.categoria_var = StringVar()
        self.dropdown_categoria = ctk.CTkComboBox(
            self.left_frame,
            values=[cat[1] for cat in self.categorias],
            variable=self.categoria_var,
            command=self.atualizar_pilotos
        )
        self.dropdown_categoria.pack(pady=5)

        # Canvas para Bolinhas de Karts
        self.canvas = ctk.CTkCanvas(self.left_frame, width=600, height=300)
        self.canvas.pack(pady=10)
        self.karts = list(range(1, 101))  # Karts de 1 a 100
        self.kart_bolinhas = {}
        self.disponiveis = set()
        self.desenhar_karts()

        # Botão para Sortear Karts
        self.btn_sortear = ctk.CTkButton(self.left_frame, text="Sortear Karts", command=self.sortear_karts)
        self.btn_sortear.pack(pady=10)

        # Botão para Adicionar Piloto
        self.btn_adicionar_piloto = ctk.CTkButton(
            self.left_frame,
            text="Adicionar Piloto",
            command=self.abrir_janela_adicionar_piloto
        )
        self.btn_adicionar_piloto.pack(pady=5)

        # Botão para Recarregar Pilotos
        self.btn_recarregar_pilotos = ctk.CTkButton(
            self.left_frame,
            text="Recarregar Pilotos",
            command=self.recarregar_pilotos
        )
        self.btn_recarregar_pilotos.pack(pady=5)

        # ----------------- Right Frame -----------------

        # Lista de Pilotos Disponíveis para Sorteio
        self.label_pilotos = ctk.CTkLabel(self.right_frame, text="Pilotos para Sorteio")
        self.label_pilotos.pack(pady=5)

        # Contador de pilotos disponíveis
        self.pilotos_count_label = ctk.CTkLabel(self.right_frame, text="Total de Pilotos: 0")
        self.pilotos_count_label.pack(pady=5)

        # Usando CTkScrollableFrame para lista de pilotos com scrollbar
        self.pilotos_frame = ctk.CTkScrollableFrame(self.right_frame, width=200, height=400)
        self.pilotos_frame.pack(pady=5, fill="y", expand=True)

        # Inicializar variáveis
        self.pilotos_atual = []
        self.pilotos_disponiveis = {}

        # Inicializar o label de resultado, que estava faltando
        self.resultado_label = ctk.CTkLabel(self.left_frame, text="")
        self.resultado_label.pack(pady=5)

    def get_categorias(self):
        cursor.execute("SELECT * FROM categorias ORDER BY nome")
        categorias = cursor.fetchall()
        return categorias

    def atualizar_pilotos(self, event=None):
        categoria_nome = self.categoria_var.get()
        if not categoria_nome:
            return
        cursor.execute("SELECT id FROM categorias WHERE nome = ?", (categoria_nome,))
        categoria = cursor.fetchone()
        if not categoria:
            messagebox.showerror("Erro", "Categoria inválida.")
            return

        self.categoria_id = categoria[0]
        cursor.execute('''SELECT p.nome FROM pilotos p
                          JOIN pilotos_categorias pc ON p.id = pc.piloto_id
                          WHERE pc.categoria_id = ?''', (self.categoria_id,))
        pilotos = [piloto[0] for piloto in cursor.fetchall()]

        # Limpar a lista atual de pilotos
        for widget in self.pilotos_frame.winfo_children():
            widget.destroy()

        self.pilotos_atual = pilotos.copy()
        self.pilotos_disponiveis = {piloto: True for piloto in pilotos}

        for piloto in pilotos:
            frame = ctk.CTkFrame(self.pilotos_frame)
            frame.pack(fill="x", pady=2)

            label = ctk.CTkLabel(frame, text=piloto)
            label.pack(side="left", padx=5)

            btn_toggle = ctk.CTkButton(
                frame,
                text="V",
                width=20,
                fg_color="green",
                command=lambda p=piloto: self.toggle_piloto(p)
            )
            btn_toggle.pack(side="right", padx=5)

        # Atualizar contador de pilotos
        self.atualizar_contador_pilotos()

        # Resetar disponibilidade dos karts
        self.disponiveis = set()
        self.atualizar_bolinhas()
        self.resultado_label.configure(text="")

    def atualizar_contador_pilotos(self):
        total_pilotos = sum(self.pilotos_disponiveis.values())
        self.pilotos_count_label.configure(text=f"Total de Pilotos: {total_pilotos}")

    def desenhar_karts(self):
        self.canvas.delete("all")
        self.kart_bolinhas.clear()
        rows = 10
        cols = 10
        radius = 15
        padding = 20
        spacing_x = (600 - 2 * padding - cols * 2 * radius) / (cols - 1) if cols > 1 else 0
        spacing_y = (300 - 2 * padding - rows * 2 * radius) / (rows - 1) if rows > 1 else 0
        for i, kart in enumerate(self.karts):
            row = i // cols
            col = i % cols
            x = padding + col * (2 * radius + spacing_x)
            y = padding + row * (2 * radius + spacing_y)

            # Criar a bolinha do kart
            bolinha = self.canvas.create_oval(
                x, y, x + 2 * radius, y + 2 * radius,
                fill="red", outline="black"
            )

            # Criar o texto com o número do kart
            texto = self.canvas.create_text(
                x + radius, y + radius,
                text=str(kart), fill="white", font=("Arial", 10, "bold")
            )

            self.kart_bolinhas[kart] = bolinha

            # Vincular o clique tanto na bolinha quanto no texto
            self.canvas.tag_bind(bolinha, "<Button-1>", lambda event, k=kart: self.toggle_kart(k))
            self.canvas.tag_bind(texto, "<Button-1>", lambda event, k=kart: self.toggle_kart(k))

    def atualizar_bolinhas(self):
        for kart in self.karts:
            if kart in self.disponiveis:
                self.canvas.itemconfig(self.kart_bolinhas[kart], fill="green")
            else:
                self.canvas.itemconfig(self.kart_bolinhas[kart], fill="red")

    def toggle_kart(self, kart):
        if kart in self.disponiveis:
            self.disponiveis.remove(kart)
            self.canvas.itemconfig(self.kart_bolinhas[kart], fill="red")
        else:
            self.disponiveis.add(kart)
            self.canvas.itemconfig(self.kart_bolinhas[kart], fill="green")

    def toggle_piloto(self, piloto):
        if self.pilotos_disponiveis.get(piloto, False):
            self.pilotos_disponiveis[piloto] = False
            self.update_piloto_button(piloto, "X", "red")
        else:
            self.pilotos_disponiveis[piloto] = True
            self.update_piloto_button(piloto, "V", "green")
        # Atualizar contador de pilotos
        self.atualizar_contador_pilotos()

    def update_piloto_button(self, piloto, text, color):
        for widget in self.pilotos_frame.winfo_children():
            label = widget.winfo_children()[0]
            if label.cget("text") == piloto:
                btn_toggle = widget.winfo_children()[1]
                btn_toggle.configure(text=text, fg_color=color)
                break

    def abrir_janela_adicionar_piloto(self):
        adicionar = AdicionarPilotoSorteioWindow(self)
        self.wait_window(adicionar)
        self.recarregar_pilotos()

    def recarregar_pilotos(self):
        categoria_nome = self.categoria_var.get()
        if not categoria_nome:
            messagebox.showerror("Erro", "Selecione uma categoria.")
            return
        cursor.execute("SELECT id FROM categorias WHERE nome = ?", (categoria_nome,))
        categoria = cursor.fetchone()
        if not categoria:
            messagebox.showerror("Erro", "Categoria inválida.")
            return
        categoria_id = categoria[0]
        cursor.execute('''SELECT p.nome FROM pilotos p
                          JOIN pilotos_categorias pc ON p.id = pc.piloto_id
                          WHERE pc.categoria_id = ?''', (categoria_id,))
        pilotos = [piloto[0] for piloto in cursor.fetchall()]

        # Limpar a lista atual de pilotos
        for widget in self.pilotos_frame.winfo_children():
            widget.destroy()

        self.pilotos_atual = pilotos.copy()
        self.pilotos_disponiveis = {piloto: True for piloto in pilotos}

        for piloto in pilotos:
            frame = ctk.CTkFrame(self.pilotos_frame)
            frame.pack(fill="x", pady=2)

            label = ctk.CTkLabel(frame, text=piloto)
            label.pack(side="left", padx=5)

            btn_toggle = ctk.CTkButton(
                frame,
                text="V",
                width=20,
                fg_color="green",
                command=lambda p=piloto: self.toggle_piloto(p)
            )
            btn_toggle.pack(side="right", padx=5)

        # Atualizar contador de pilotos
        self.atualizar_contador_pilotos()

        # Resetar disponibilidade dos karts
        self.disponiveis = set()
        self.atualizar_bolinhas()
        self.resultado_label.configure(text="")

    def sortear_karts(self):
        categoria_nome = self.categoria_var.get()
        if not categoria_nome:
            messagebox.showerror("Erro", "Selecione uma categoria.")
            return
        cursor.execute("SELECT id FROM categorias WHERE nome = ?", (categoria_nome,))
        categoria = cursor.fetchone()
        if not categoria:
            messagebox.showerror("Erro", "Categoria inválida.")
            return

        categoria_id = categoria[0]
        # Obter pilotos disponíveis para sorteio
        pilotos = [piloto for piloto, disponivel in self.pilotos_disponiveis.items() if disponivel]
        if not pilotos:
            messagebox.showwarning("Aviso", "Nenhum piloto disponível para sorteio.")
            return

        karts_disponiveis = list(self.disponiveis)
        if len(pilotos) > len(karts_disponiveis):
            messagebox.showerror("Erro", "Número de pilotos excede o número de karts disponíveis.")
            return

        random.shuffle(karts_disponiveis)  # Garantir aleatoriedade
        sorteios = {piloto: karts_disponiveis[i] for i, piloto in enumerate(pilotos)}

        # Registrar sorteios no banco de dados
        data_sorteio = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        for piloto, kart in sorteios.items():
            cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (piloto,))
            piloto_id = cursor.fetchone()[0]
            cursor.execute('''INSERT INTO historico_sorteios 
                              (categoria_id, piloto_id, kart, data_sorteio) 
                              VALUES (?, ?, ?, ?)''',
                           (categoria_id, piloto_id, kart, data_sorteio))
        conn.commit()

        # Exibir resultado em uma janela pop-up
        resultado = "\n".join([f"{piloto}: Kart {kart}" for piloto, kart in sorteios.items()])
        self.abrir_janela_resultado(resultado, sorteios)

    def abrir_janela_resultado(self, resultado, sorteios):
        resultado_popup = ResultadoPopup(self, resultado, sorteios)
        resultado_popup.grab_set()  # Torna a janela modal


class ResultadoPopup(ctk.CTkToplevel):
    def __init__(self, master, resultado_text, sorteios):
        super().__init__(master)
        self.title("Resultado do Sorteio")
        self.geometry("400x400")
        self.transient(master)  # Sobrepõe a janela principal
        self.grab_set()  # Modal

        # Texto do Resultado
        self.text = ctk.CTkTextbox(self, state='normal')
        self.text.insert("0.0", resultado_text)
        self.text.configure(state='disabled')
        self.text.pack(fill="both", expand=True, pady=10, padx=10)

        # Botão para Sortear Novamente
        self.btn_sortear_novamente = ctk.CTkButton(
            self,
            text="Sortear Novamente",
            command=lambda: self.sortear_novamente(sorteios)
        )
        self.btn_sortear_novamente.pack(pady=10)

        # Botão para Fechar
        self.btn_fechar = ctk.CTkButton(self, text="Fechar", command=self.destroy)
        self.btn_fechar.pack(pady=5)

    def sortear_novamente(self, sorteios):
        # Reutilizar a função de sortear do frame principal
        self.destroy()
        self.master.sortear_karts()


class AdicionarPilotoSorteioWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Adicionar Piloto ao Sorteio")
        self.geometry("400x400")
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
        self.categoria_var = StringVar()
        self.dropdown_categoria = ctk.CTkComboBox(
            self,
            values=[cat[1] for cat in self.categorias],
            variable=self.categoria_var
        )
        self.dropdown_categoria.pack(pady=5)
        self.dropdown_categoria.set(master.categoria_var.get())

        # Inicializar categoria_vars para corrigir o erro
        self.categoria_vars = []

        # Botão para Salvar Piloto
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Piloto", command=self.salvar_piloto)
        self.btn_salvar.pack(pady=20)

    def get_categorias(self):
        cursor.execute("SELECT * FROM categorias ORDER BY nome")
        categorias = cursor.fetchall()
        return categorias

    def salvar_piloto(self):
        nome = self.entry_nome.get().strip().lower()  # Normaliza o nome para minúsculas
        if not nome:
            messagebox.showerror("Erro", "O nome do piloto é obrigatório.")
            return

        # Simulação de seleção de categoria (como foi pedido o uso de categoria_vars)
        categoria_nome = self.categoria_var.get()
        cursor.execute("SELECT id FROM categorias WHERE nome = ?", (categoria_nome,))
        categoria = cursor.fetchone()
        if not categoria:
            messagebox.showerror("Erro", "Categoria inválida.")
            return
        categorias_selecionadas = [categoria[0]]  # Adiciona a categoria selecionada

        try:
            cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (nome,))
            piloto = cursor.fetchone()
            if piloto:
                messagebox.showerror("Erro", "Já existe um piloto com esse nome.")
                return
            cursor.execute("INSERT INTO pilotos (nome) VALUES (?)", (nome,))
            piloto_id = cursor.lastrowid
            for cat_id in categorias_selecionadas:
                cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                               (piloto_id, cat_id))
            conn.commit()
            messagebox.showinfo("Sucesso", "Piloto cadastrado com sucesso!")
            self.entry_nome.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar piloto: {e}")
