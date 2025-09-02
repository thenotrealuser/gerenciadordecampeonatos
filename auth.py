import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit,
    QMessageBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt


def verificar_acesso(login_usuario):
    """Verifica o acesso consultando um documento online."""
    url = 'https://docs.google.com/document/d/1D_Jr8SJhW2Z0mcMlzjvYB8OO7KjWfOaL-PQb92stbwY/export?format=txt'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        conteudo = response.text.splitlines()
        logins_autorizados = {}

        for linha in conteudo:
            if "login:" in linha and "status:" in linha:
                partes = linha.split(',')
                login_part = partes[0].split(":")[1].strip()
                status_part = partes[1].split(":")[1].strip()
                logins_autorizados[login_part] = status_part

        if login_usuario in logins_autorizados and logins_autorizados[login_part] == "liberado":
            return True, "Acesso liberado."
        else:
            return False, "Acesso negado. Verifique seu login ou contate o suporte."

    except requests.RequestException as e:
        return False, f"Não foi possível verificar o acesso online: {e}"


class LoginDialog(QDialog):
    """Janela de login criada com PyQt6."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login do Sistema")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Digite o Login:"))

        self.login_input = QLineEdit()
        self.login_input.returnPressed.connect(self.tentar_login)
        layout.addWidget(self.login_input)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        button_box = QDialogButtonBox()
        btn_entrar = button_box.addButton("Entrar", QDialogButtonBox.ButtonRole.ActionRole)
        btn_entrar.clicked.connect(self.tentar_login)
        layout.addWidget(button_box)

        self.login_input.setFocus()

    def tentar_login(self):
        login = self.login_input.text().strip()
        if not login:
            self.status_label.setText("Por favor, digite um login.")
            return

        self.status_label.setText("Verificando...")
        QApplication.processEvents()

        sucesso, mensagem = verificar_acesso(login)

        if sucesso:
            self.accept()
        else:
            self.status_label.setText("")
            QMessageBox.critical(self, "Acesso Negado", mensagem)
            self.login_input.clear()