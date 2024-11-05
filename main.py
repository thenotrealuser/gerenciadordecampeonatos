from tkinter import messagebox
import customtkinter as ctk
from cadastro_pilotos_categorias import CadastroCategoriasFrame, CadastroPilotosFrame
from cadastro_equipes import CadastroTimesFrame
from cadastro_etapas import CadastroEtapasFrame
from frame_resultado_etapas import ResultadosEtapasFrame
from resultado_geral_frame import ResultadoGeralFrame
from sorteio_karts import SorteioKartsFrame
from importar_pilotos import ImportarPilotosFrame
from sistema_pontuacao import SistemaPontuacaoFrame
from historico_sorteios import HistoricoSorteiosFrame
from database import cursor, conn, verificar_estrutura_banco, setup_database

# Garantir que o banco de dados esteja configurado
setup_database()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de gerenciamento de campeonato de karts by :::Kimi Morgam::: Tela principal")
        self.state('zoomed')  # Maximiza a janela no Windows

        # Layout Principal: Frame da Esquerda (Menu) e Frame da Direita (Conteúdo)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Frame do Menu Lateral
        self.menu_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, sticky="nswe")
        self.menu_frame.grid_rowconfigure(11, weight=1)

        # Botões do Menu
        buttons = [
            ("Cadastro de Categorias", self.show_cadastro_categorias),
            ("Cadastro de Pilotos", self.show_cadastro_pilotos),
            ("Cadastro de Times", self.show_cadastro_times),
            ("Cadastro de Etapas", self.show_cadastro_etapas),
            ("Resultados das Etapas", self.show_resultados_etapas),
            ("Resultado Geral", self.show_resultado_geral),
            ("Sorteio de Karts", self.show_sorteio_karts),
            ("Importar Pilotos", self.show_importar_pilotos),
            ("Sistema de Pontuação", self.show_sistema_pontuacao),
            ("Histórico de Sorteios", self.show_historico_sorteios),
            ("Resetar Campeonato", self.resetar_campeonato, "red", "darkred")
        ]

        for i, button in enumerate(buttons):
            text, command = button[:2]
            fg_color = button[2] if len(button) > 2 else None
            hover_color = button[3] if len(button) > 3 else None
            btn = ctk.CTkButton(self.menu_frame, text=text, command=command, fg_color=fg_color, hover_color=hover_color)
            btn.grid(row=i, column=0, padx=20, pady=10, sticky="ew")

        # Frame de Conteúdo
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Create a scrollable frame within content_frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self.content_frame)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")

        # Inicialmente, mostrar o cadastro de categorias
        self.show_cadastro_categorias()

    def clear_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def show_cadastro_categorias(self):
        self.clear_content()
        frame = CadastroCategoriasFrame(self.scrollable_frame)
        frame.pack(fill="both", expand=True)

    def show_cadastro_pilotos(self):
        self.clear_content()
        frame = CadastroPilotosFrame(self.scrollable_frame)
        frame.pack(fill="both", expand=True)

    def show_cadastro_times(self):
        self.clear_content()
        frame = CadastroTimesFrame(self.scrollable_frame)
        frame.pack(fill="both", expand=True)

    def show_cadastro_etapas(self):
        self.clear_content()
        frame = CadastroEtapasFrame(self.scrollable_frame)
        frame.pack(fill="both", expand=True)

    def show_resultados_etapas(self):
        self.clear_content()
        frame = ResultadosEtapasFrame(self.scrollable_frame)
        frame.pack(fill="both", expand=True)

    def show_resultado_geral(self):
        self.clear_content()
        frame = ResultadoGeralFrame(self.scrollable_frame)
        frame.pack(fill="both", expand=True)

    def show_sorteio_karts(self):
        self.clear_content()
        frame = SorteioKartsFrame(self.scrollable_frame)
        frame.pack(fill="both", expand=True)

    def show_importar_pilotos(self):
        self.clear_content()
        frame = ImportarPilotosFrame(self.scrollable_frame)
        frame.pack(fill="both", expand=True)

    def show_sistema_pontuacao(self):
        self.clear_content()
        frame = SistemaPontuacaoFrame(self.scrollable_frame)
        frame.pack(fill="both", expand=True)

    def show_historico_sorteios(self):
        self.clear_content()
        frame = HistoricoSorteiosFrame(self.scrollable_frame)
        frame.pack(fill="both", expand=True)

    def resetar_campeonato(self):
        ResetarCampeonatoWindow(self)

class ResetarCampeonatoWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Resetar Campeonato")
        self.geometry("300x200")

        self.label = ctk.CTkLabel(self, text="Tem certeza que deseja resetar o campeonato?")
        self.label.pack(pady=20)

        self.btn_confirmar = ctk.CTkButton(self, text="Confirmar", command=self.resetar_campeonato)
        self.btn_confirmar.pack(pady=10)

        self.btn_cancelar = ctk.CTkButton(self, text="Cancelar", command=self.destroy)
        self.btn_cancelar.pack(pady=10)

    def resetar_campeonato(self):
        try:
            # Deletar todas as informações das tabelas relacionadas ao campeonato
            cursor.execute("DELETE FROM resultados_etapas")
            cursor.execute("DELETE FROM pilotos_categorias")
            cursor.execute("DELETE FROM etapas")
            cursor.execute("DELETE FROM pilotos")
            cursor.execute("DELETE FROM categorias")
            cursor.execute("DELETE FROM times")
            cursor.execute("DELETE FROM pilotos_times")
            cursor.execute("DELETE FROM sistema_pontuacao")
            cursor.execute("DELETE FROM sistema_pontuacao_extras")
            cursor.execute("DELETE FROM historico_sorteios")
            conn.commit()

            self.destroy()
            messagebox.showinfo("Campeonato Resetado", "O campeonato foi resetado com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao resetar o campeonato: {e}")
            self.destroy()

if __name__ == "__main__":
    from auth import iniciar_login
    iniciar_login()  # Inicia o processo de login