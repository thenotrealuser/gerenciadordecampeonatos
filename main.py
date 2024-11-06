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

setup_database()


class App(ctk.CTk):
    def __init__(self):
        # Configuração inicial do tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        super().__init__()

        self.title("Sistema de gerenciamento de campeonato de karts by :::Kimi Morgam:::")
        self.minsize(1024, 720)  # Tamanho mínimo da janela

        # Permitir redimensionamento
        self.resizable(True, True)
        self.state('zoomed')

        # Layout Principal com peso para permitir redimensionamento
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Menu Container (Lado Esquerdo)
        self.menu_container = ctk.CTkFrame(
            self,
            width=250,
            corner_radius=0
        )
        self.menu_container.grid(row=0, column=0, sticky="nswe", padx=(10, 5), pady=10)
        self.menu_container.grid_rowconfigure(1, weight=1)
        self.menu_container.grid_propagate(False)  # Impede o encolhimento

        # Título do Menu
        self.title_label = ctk.CTkLabel(
            self.menu_container,
            text="MENU PRINCIPAL",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Frame scrollável para o menu
        self.menu_scroll = ctk.CTkScrollableFrame(
            self.menu_container,
            corner_radius=0
        )
        self.menu_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.menu_scroll.grid_columnconfigure(0, weight=1)

        # Dark Mode Switch
        self.theme_switch = ctk.CTkSwitch(
            self.menu_scroll,
            text="Dark Mode",
            command=self.toggle_theme
        )
        self.theme_switch.grid(row=0, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.theme_switch.select()

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

        for i, button in enumerate(buttons, start=1):
            text, command = button[:2]
            fg_color = button[2] if len(button) > 2 else None
            hover_color = button[3] if len(button) > 3 else None

            btn = ctk.CTkButton(
                self.menu_scroll,
                text=text,
                command=command,
                fg_color=fg_color,
                hover_color=hover_color,
                height=40
            )
            btn.grid(row=i, column=0, padx=20, pady=8, sticky="ew")

        # Content Container (Lado Direito)
        self.content_container = ctk.CTkFrame(
            self,
            corner_radius=0
        )
        self.content_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Frame scrollável para conteúdo
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.content_container,
            corner_radius=0
        )
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Bind do evento de redimensionamento
        self.bind('<Configure>', self.on_resize)

        # Mostrar tela inicial
        self.show_cadastro_categorias()

    def on_resize(self, event=None):
        """Ajusta os elementos quando a janela é redimensionada"""
        if event and event.widget == self:
            # Atualiza o conteúdo para preencher o espaço disponível
            for widget in self.scrollable_frame.winfo_children():
                if hasattr(widget, 'configure'):
                    widget.configure(width=self.content_container.winfo_width() - 30)

    def toggle_theme(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_switch.deselect()
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_switch.select()

    def clear_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def show_frame(self, frame_class):
        """Método genérico para mostrar frames"""
        self.clear_content()
        frame = frame_class(self.scrollable_frame)
        frame.pack(fill="both", expand=True)
        self.on_resize()  # Ajusta o tamanho do frame

    def show_cadastro_categorias(self):
        self.show_frame(CadastroCategoriasFrame)

    def show_cadastro_pilotos(self):
        self.show_frame(CadastroPilotosFrame)

    def show_cadastro_times(self):
        self.show_frame(CadastroTimesFrame)

    def show_cadastro_etapas(self):
        self.show_frame(CadastroEtapasFrame)

    def show_resultados_etapas(self):
        self.show_frame(ResultadosEtapasFrame)

    def show_resultado_geral(self):
        self.show_frame(ResultadoGeralFrame)

    def show_sorteio_karts(self):
        self.show_frame(SorteioKartsFrame)

    def show_importar_pilotos(self):
        self.show_frame(ImportarPilotosFrame)

    def show_sistema_pontuacao(self):
        self.show_frame(SistemaPontuacaoFrame)

    def show_historico_sorteios(self):
        self.show_frame(HistoricoSorteiosFrame)

    def resetar_campeonato(self):
        ResetarCampeonatoWindow(self)


class ResetarCampeonatoWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Resetar Campeonato")
        self.geometry("400x250")

        # Centralizar a janela
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.label = ctk.CTkLabel(
            self,
            text="Tem certeza que deseja resetar o campeonato?",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.label.pack(pady=30)

        self.btn_confirmar = ctk.CTkButton(
            self,
            text="Confirmar",
            command=self.resetar_campeonato,
            fg_color="red",
            hover_color="darkred"
        )
        self.btn_confirmar.pack(pady=10)

        self.btn_cancelar = ctk.CTkButton(
            self,
            text="Cancelar",
            command=self.destroy
        )
        self.btn_cancelar.pack(pady=10)

    def resetar_campeonato(self):
        try:
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

    iniciar_login()