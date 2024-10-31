import customtkinter as ctk
from tkinter import Listbox
from tkinter import END
from database import cursor
import sqlite3
from tkinter import ttk, messagebox
from database import conn


class SistemaPontuacaoFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        self.label = ctk.CTkLabel(self, text="Sistema de Pontuação (Padrão para todas as categorias)",
                                  font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=10)

        # Frame para Configurar Pontos por Posição
        self.pontos_frame = ctk.CTkFrame(self)
        self.pontos_frame.pack(fill="both", expand=True, pady=10)

        # Botão para Adicionar Posição
        self.btn_adicionar_posicao = ctk.CTkButton(self, text="Adicionar Posição", command=self.adicionar_posicao)
        self.btn_adicionar_posicao.pack(pady=10)

        # Lista de Pontuação
        self.lista_pontos = Listbox(self.pontos_frame, height=10, selectmode=ctk.SINGLE)
        self.lista_pontos.pack(fill="both", expand=True, pady=5)

        # Botão para Remover Posição
        self.btn_remover_posicao = ctk.CTkButton(self, text="Remover Posição Selecionada", command=self.remover_posicao)
        self.btn_remover_posicao.pack(pady=5)

        # Pontuação extra para Pole Position e Melhor Volta
        self.label_pole = ctk.CTkLabel(self, text="Pontos por Pole Position")
        self.label_pole.pack(pady=5)
        self.entry_pontos_pole = ctk.CTkEntry(self, placeholder_text="Ex: 3")
        self.entry_pontos_pole.pack(pady=5)

        self.label_melhor_volta = ctk.CTkLabel(self, text="Pontos por Melhor Volta")
        self.label_melhor_volta.pack(pady=5)
        self.entry_pontos_melhor_volta = ctk.CTkEntry(self, placeholder_text="Ex: 5")
        self.entry_pontos_melhor_volta.pack(pady=5)

        # Botão para Salvar Pontuação
        self.btn_salvar_pontuacao = ctk.CTkButton(self, text="Salvar Pontuação", command=self.salvar_pontuacao)
        self.btn_salvar_pontuacao.pack(pady=20)

        self.carregar_pontos()

    def carregar_pontos(self):
        self.lista_pontos.delete(0, END)
        cursor.execute("SELECT posicao, pontos FROM sistema_pontuacao ORDER BY posicao")
        pontos = cursor.fetchall()
        for pos, pts in pontos:
            self.lista_pontos.insert(END, f"{pos}º Lugar: {pts} pontos")

        # Carregar pontos de pole position e melhor volta
        cursor.execute("SELECT pole_position, melhor_volta FROM sistema_pontuacao_extras")
        extras = cursor.fetchone()
        if extras:
            self.entry_pontos_pole.delete(0, END)
            self.entry_pontos_pole.insert(0, str(extras[0]))
            self.entry_pontos_melhor_volta.delete(0, END)
            self.entry_pontos_melhor_volta.insert(0, str(extras[1]))
        else:
            self.entry_pontos_pole.delete(0, END)
            self.entry_pontos_melhor_volta.delete(0, END)

    def adicionar_posicao(self):
        # Abrir uma nova janela para adicionar posição e pontos
        AdicionarPosicaoWindow(self, callback=self.carregar_pontos)

    def remover_posicao(self):
        try:
            selecionado = self.lista_pontos.get(self.lista_pontos.curselection())
        except:
            selecionado = None
        if not selecionado:
            messagebox.showerror("Erro", "Selecione uma posição para remover.")
            return
        try:
            posicao = int(selecionado.split('º')[0])
            cursor.execute("DELETE FROM sistema_pontuacao WHERE posicao = ?", (posicao,))
            conn.commit()
            self.carregar_pontos()
            messagebox.showinfo("Sucesso", "Pontos removidos com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao remover pontos: {e}")

    def salvar_pontuacao(self):
        try:
            pontos_pole = int(self.entry_pontos_pole.get())
            pontos_melhor_volta = int(self.entry_pontos_melhor_volta.get())
            if pontos_pole < 0 or pontos_melhor_volta < 0:
                raise ValueError("Pontos não podem ser negativos.")

            cursor.execute('''INSERT OR REPLACE INTO sistema_pontuacao_extras 
                              (pole_position, melhor_volta) 
                              VALUES (?, ?)''', (pontos_pole, pontos_melhor_volta))
            conn.commit()
            messagebox.showinfo("Sucesso", "Pontuação salva com sucesso!")
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira valores válidos para pontos.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar pontuação: {e}")


class AdicionarPosicaoWindow(ctk.CTkToplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.title("Adicionar Posição")
        self.geometry("300x200")
        self.transient(master)  # Sobrepõe a janela principal
        self.grab_set()  # Modal
        self.callback = callback

        # Campo para Posição
        self.label_posicao = ctk.CTkLabel(self, text="Posição (nº)")
        self.label_posicao.pack(pady=5)
        self.entry_posicao = ctk.CTkEntry(self, placeholder_text="Ex: 1")
        self.entry_posicao.pack(pady=5)

        # Campo para Pontos
        self.label_pontos = ctk.CTkLabel(self, text="Pontos")
        self.label_pontos.pack(pady=5)
        self.entry_pontos = ctk.CTkEntry(self, placeholder_text="Ex: 25")
        self.entry_pontos.pack(pady=5)

        # Botão para Salvar
        self.btn_salvar = ctk.CTkButton(self, text="Salvar", command=self.salvar_pontos)
        self.btn_salvar.pack(pady=20)

    def salvar_pontos(self):
        try:
            posicao = int(self.entry_posicao.get())
            pontos = int(self.entry_pontos.get())
            if posicao <= 0 or pontos < 0:
                messagebox.showerror("Erro", "Posição deve ser maior que 0 e os pontos não podem ser negativos.")
                return
            cursor.execute("INSERT INTO sistema_pontuacao (posicao, pontos) VALUES (?, ?)", (posicao, pontos))
            conn.commit()
            messagebox.showinfo("Sucesso", "Pontos adicionados com sucesso.")
            self.callback()  # Chama a função de callback para atualizar a lista de pontos
            self.destroy()
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira valores válidos.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Pontos para essa posição já estão configurados.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar pontos: {e}")
