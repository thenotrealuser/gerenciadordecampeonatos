import sqlite3
import sys
from tkinter import messagebox, Tk, Entry, Button
import customtkinter as ctk
import requests


def verificar_acesso(login_usuario):
    # URL para o documento do Google Docs
    url = 'https://docs.google.com/document/d/1D_Jr8SJhW2Z0mcMlzjvYB8OO7KjWfOaL-PQb92stbwY/export?format=txt'

    try:
        # Fazer a solicitação GET para obter o conteúdo do documento como texto
        response = requests.get(url)
        response.raise_for_status()  # Levanta um erro se houver problemas na requisição

        # Processar o conteúdo do documento em memória
        conteudo = response.text.splitlines()

        # Analisar as linhas do arquivo para encontrar o login e status
        logins_autorizados = {}

        for linha in conteudo:
            # Cada linha deve estar no formato: "login: <login>, status: <status>"
            if "login:" in linha and "status:" in linha:
                # Separar login e status
                partes = linha.split(',')
                login_part = partes[0].split(":")[1].strip()
                status_part = partes[1].split(":")[1].strip()
                logins_autorizados[login_part] = status_part

        # Verificar se o login do usuário está na lista e se o status é 'liberado'
        if login_usuario in logins_autorizados and logins_autorizados[login_usuario] == "liberado":
            return True  # Permitir o acesso
        else:
            messagebox.showerror("Acesso Negado", "O acesso ao programa foi bloqueado. Entre em contato com o suporte.")
            return False  # Bloquear o acesso
    except requests.RequestException as e:
        # Tratar erros de conexão
        messagebox.showerror("Erro de Conexão", f"Não foi possível verificar o acesso online: {e}")
        return False


def tentar_login():
    login_usuario = entry_login.get().strip()
    if verificar_acesso(login_usuario):
        messagebox.showinfo("Acesso Liberado", "Acesso liberado. Carregando o programa...")
        root.destroy()  # Fecha a janela de login
        iniciar_aplicativo()  # Chama a função que inicializa o aplicativo principal
    else:
        # Acesso negado
        entry_login.delete(0, 'end')


def iniciar_aplicativo():
    from main import App  # Agora só importa o App quando necessário, para evitar importação circular
    app = App()
    app.mainloop()


def iniciar_login():
    global root, entry_login
    root = Tk()
    root.title("Login do Sistema")
    root.geometry("300x200")

    # Label para o campo de login
    label_login = ctk.CTkLabel(root, text="Digite o Login:")
    label_login.pack(pady=10)

    # Entry para o login
    entry_login = Entry(root)
    entry_login.pack(pady=10)

    # Botão de login
    btn_login = Button(root, text="Entrar", command=tentar_login)
    btn_login.pack(pady=10)

    root.mainloop()


def ao_fechar_login():
    root.destroy()
    sys.exit()  # Encerra o programa completamente
