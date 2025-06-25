from tkinter import StringVar, ttk, messagebox, filedialog
import customtkinter as ctk
from database import cursor, conn
from db_utils import buscar_categorias
import csv
import os
import PyPDF2
from bs4 import BeautifulSoup

class ResultadosEtapasFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        self.label = ctk.CTkLabel(self, text="Resultados das Etapas", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=10)

        # Dropdown para Selecionar Categoria
        self.label_categoria = ctk.CTkLabel(self, text="Selecione a Categoria")
        self.label_categoria.pack(pady=5)

        self.categorias = self.get_categorias()
        self.categoria_var = StringVar()
        self.dropdown_categoria = ctk.CTkComboBox(
            self,
            values=[categoria[1] for categoria in self.categorias],
            variable=self.categoria_var,
            command=self.atualizar_etapas
        )
        self.dropdown_categoria.pack(pady=5)

        # Dropdown para Selecionar Etapa
        self.label_etapa = ctk.CTkLabel(self, text="Selecione a Etapa")
        self.label_etapa.pack(pady=5)

        self.etapa_var = StringVar()
        self.dropdown_etapa = ctk.CTkComboBox(
            self,
            values=[],
            variable=self.etapa_var,
            command=self.carregar_resultados
        )
        self.dropdown_etapa.pack(pady=5)

        # Botões para Importar Arquivo e Desfazer
        self.btn_importar_pdf = ctk.CTkButton(self, text="Importar Arquivo", command=self.importar_arquivo)
        self.btn_importar_pdf.pack(pady=10)

        self.btn_desfazer_importacao = ctk.CTkButton(self, text="Desfazer Importação", command=self.desfazer_importacao)
        self.btn_desfazer_importacao.pack(pady=10)

        # Botão para Inserir Manualmente
        self.btn_inserir_manual = ctk.CTkButton(self, text="Inserir Resultados Manualmente", command=self.inserir_manual)
        self.btn_inserir_manual.pack(pady=10)

        # Treeview para Exibir Resultados das Etapas
        self.tree = ttk.Treeview(self, columns=("Piloto", "Posição", "Pole Position", "Melhor Volta", "ADV", "Categoria"), show="headings")
        self.tree.heading("Piloto", text="Piloto")
        self.tree.heading("Posição", text="Posição")
        self.tree.heading("Pole Position", text="Pole Position")
        self.tree.heading("Melhor Volta", text="Melhor Volta")
        self.tree.heading("ADV", text="ADV")
        self.tree.heading("Categoria", text="Categoria")
        self.tree.pack(fill="both", expand=True, pady=10)

        # Adicionar scrollbar à Treeview
        self.scrollbar_tree = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar_tree.set)
        self.scrollbar_tree.pack(side='right', fill='y')

        # Botão para Editar Resultado
        self.btn_editar = ctk.CTkButton(self, text="Editar Resultado", command=self.editar_resultado)
        self.btn_editar.pack(pady=10)

        # Botão para Mudar Categoria de Piloto
        self.btn_mudar_categoria = ctk.CTkButton(self, text="Mudar Categoria do Piloto", command=self.mudar_categoria_piloto)
        self.btn_mudar_categoria.pack(pady=10)

        # Carregar etapas e resultados
        self.atualizar_etapas()

    def get_categorias(self):
        return buscar_categorias()

    def atualizar_etapas(self, event=None):
        categoria_nome = self.categoria_var.get()
        if not categoria_nome:
            return

        cursor.execute("SELECT id FROM categorias WHERE nome = ?", (categoria_nome,))
        categoria = cursor.fetchone()
        if not categoria:
            messagebox.showerror("Erro", "Categoria selecionada inválida.")
            return

        self.categoria_id = categoria[0]

        # Buscar todas as etapas cadastradas, independentemente de terem resultados ou não
        cursor.execute("SELECT id, nome FROM etapas ORDER BY data")
        etapas = cursor.fetchall()

        # Atualizar o dropdown de etapas com todas as etapas disponíveis
        self.dropdown_etapa.configure(values=[etapa[1] for etapa in etapas])

    def carregar_resultados(self, event=None):
        etapa_nome = self.etapa_var.get()
        if not etapa_nome or not hasattr(self, 'categoria_id'):
            return

        # Buscar a etapa selecionada
        cursor.execute("SELECT id FROM etapas WHERE nome = ?", (etapa_nome,))
        etapa = cursor.fetchone()
        if not etapa:
            messagebox.showerror("Erro", "Etapa selecionada inválida.")
            return

        self.etapa_id = etapa[0]

        # Limpar a Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Atualizar as colunas da Treeview
        self.tree.config(columns=("Piloto", "Posição", "Pole Position", "Melhor Volta", "ADV", "Categoria"))
        self.tree.heading("Piloto", text="Piloto")
        self.tree.heading("Posição", text="Posição")
        self.tree.heading("Pole Position", text="Pole Position")
        self.tree.heading("Melhor Volta", text="Melhor Volta")
        self.tree.heading("ADV", text="ADV")
        self.tree.heading("Categoria", text="Categoria")

        # Consulta SQL para obter os resultados por etapa e categoria selecionada
        cursor.execute('''
            SELECT p.nome, re.posicao, re.pole_position, re.melhor_volta, re.adv, c.nome
            FROM resultados_etapas re
            JOIN pilotos p ON p.id = re.piloto_id
            JOIN categorias c ON re.categoria_id = c.id
            WHERE re.etapa_id = ? AND re.categoria_id = ?
            ORDER BY re.posicao ASC
        ''', (self.etapa_id, self.categoria_id))
        resultados = cursor.fetchall()

        # Inserir resultados na Treeview
        for resultado in resultados:
            piloto, posicao, pole_position, melhor_volta, adv, categoria = resultado
            pole_position_str = "Sim" if pole_position else "Não"
            melhor_volta_str = "Sim" if melhor_volta else "Não"
            adv_str = "Sim" if adv else "Não"
            self.tree.insert("", "end",
                             values=(piloto, posicao, pole_position_str, melhor_volta_str, adv_str, categoria))

    def mudar_categoria_piloto(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showerror("Erro", "Selecione um piloto para mudar a categoria.")
            return

        valores = self.tree.item(selecionado, 'values')
        piloto_nome, _, _, _, _, categoria_atual = valores

        # Buscar as categorias disponíveis (exceto a atual)
        categorias_nomes = [categoria[1] for categoria in self.categorias if categoria[1] != categoria_atual]

        nova_categoria = StringVar()
        categoria_selecionada = ctk.CTkComboBox(self, values=categorias_nomes, variable=nova_categoria)
        categoria_selecionada.pack(pady=5)

        def salvar_mudanca():
            nova_categoria_nome = nova_categoria.get()
            if not nova_categoria_nome:
                messagebox.showerror("Erro", "Selecione uma nova categoria.")
                return

            # Atualizar a categoria do piloto no banco de dados
            cursor.execute("SELECT id FROM categorias WHERE nome = ?", (nova_categoria_nome,))
            nova_categoria_id = cursor.fetchone()[0]

            cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (piloto_nome,))
            piloto_id = cursor.fetchone()[0]

            # Atualizar a categoria do piloto na tabela resultados_etapas
            cursor.execute('''UPDATE resultados_etapas
                              SET categoria_id = ?
                              WHERE piloto_id = ? AND etapa_id = ?''', (nova_categoria_id, piloto_id, self.etapa_id))

            # Atualizar a tabela pilotos_categorias para refletir a nova categoria do piloto
            cursor.execute('''DELETE FROM pilotos_categorias WHERE piloto_id = ?''', (piloto_id,))
            cursor.execute('''INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)''',
                           (piloto_id, nova_categoria_id))

            conn.commit()

            messagebox.showinfo("Sucesso", "Categoria do piloto atualizada com sucesso!")
            self.carregar_resultados()

        # Botão para salvar a mudança de categoria
        btn_salvar_categoria = ctk.CTkButton(self, text="Salvar Categoria", command=salvar_mudanca)
        btn_salvar_categoria.pack(pady=10)

    def importar_arquivo(self):
        try:
            categoria_nome = self.categoria_var.get()
            if not categoria_nome:
                messagebox.showerror("Erro", "Selecione uma categoria.")
                return

            etapa_nome = self.etapa_var.get()
            if not etapa_nome:
                messagebox.showerror("Erro", "Selecione uma etapa.")
                return

            # Abrir diálogo para selecionar o arquivo (PDF, HTML, ou CSV)
            arquivo = filedialog.askopenfilename(
                title="Selecionar Arquivo",
                filetypes=[("PDF Files", "*.pdf"), ("HTML Files", "*.html"), ("CSV Files", "*.csv"),
                           ("Todos os arquivos", "*.*")]
            )
            if not arquivo:
                return

            extensao = os.path.splitext(arquivo)[1].lower()
            dados = []

            if extensao == ".pdf":
                with open(arquivo, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    numero_paginas = len(reader.pages)
                    for page_num in range(numero_paginas):
                        page = reader.pages[page_num]
                        conteudo = page.extract_text()
                        dados.extend(self.extrair_dados_pdf(conteudo))  # Função para PDFs

            elif extensao == ".html":
                with open(arquivo, 'r', encoding='utf-8') as file:
                    conteudo = file.read()
                    dados = self.extrair_dados_html(conteudo)  # Função para HTML

            elif extensao == ".csv":
                with open(arquivo, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    dados = self.extrair_dados_csv(reader)  # Função para CSV

            else:
                messagebox.showerror("Erro", f"Formato de arquivo '{extensao}' não suportado.")
                return

            # Adicionar dados ao banco de dados
            for posicao, piloto_nome, melhor_volta in dados:
                # Normalizar o nome do piloto
                piloto_nome_normalizado = piloto_nome.strip().lower()

                # Buscar ou criar o piloto no banco de dados
                cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (piloto_nome_normalizado,))
                piloto = cursor.fetchone()
                if not piloto:
                    cursor.execute("INSERT INTO pilotos (nome) VALUES (?)", (piloto_nome_normalizado,))
                    piloto_id = cursor.lastrowid
                    # Associar o piloto à categoria selecionada
                    cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                                   (piloto_id, self.categoria_id))
                else:
                    piloto_id = piloto[0]
                    # Verificar se o piloto já está associado à categoria
                    cursor.execute("SELECT 1 FROM pilotos_categorias WHERE piloto_id = ? AND categoria_id = ?",
                                   (piloto_id, self.categoria_id))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO pilotos_categorias (piloto_id, categoria_id) VALUES (?, ?)",
                                       (piloto_id, self.categoria_id))

                # Verificar se já existe um resultado para este piloto na mesma etapa e categoria
                cursor.execute('''SELECT 1 FROM resultados_etapas
                                  WHERE etapa_id = ? AND piloto_id = ? AND categoria_id = ?''',
                               (self.etapa_id, piloto_id, self.categoria_id))
                if cursor.fetchone():
                    # Atualizar o resultado existente
                    cursor.execute('''UPDATE resultados_etapas
                                      SET posicao = ?, melhor_volta = ?, importado_do_pdf = 1, pole_position = ?
                                      WHERE etapa_id = ? AND piloto_id = ? AND categoria_id = ?''',
                                   (posicao, melhor_volta, 1 if 'pole_position' in dados[0] else 0,
                                    self.etapa_id, piloto_id, self.categoria_id))
                else:
                    # Inserir novo resultado
                    cursor.execute('''INSERT INTO resultados_etapas 
                                      (etapa_id, piloto_id, categoria_id, posicao, melhor_volta, pole_position, importado_do_pdf) 
                                      VALUES (?, ?, ?, ?, ?, ?, 1)''',
                                   (self.etapa_id, piloto_id, self.categoria_id, posicao,
                                    melhor_volta, 1 if 'pole_position' in dados[0] else 0))
            conn.commit()
            messagebox.showinfo("Sucesso", "Resultados importados com sucesso!")
            self.carregar_resultados()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao importar arquivo: {e}")

    def extrair_dados_html(self, conteudo):
        soup = BeautifulSoup(conteudo, 'html.parser')

        # Aqui você ajusta de acordo com a estrutura do HTML fornecido
        dados = []
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 3:
                posicao = cols[0].text.strip()
                piloto_nome = cols[2].text.strip().lower()  # Coluna de Nome do Piloto
                # Ignorar colunas após o nome do piloto, incluindo o número do kart e outras informações irrelevantes
                melhor_volta = False  # Definir valor padrão
                dados.append((posicao, piloto_nome, melhor_volta))

        return dados

    def extrair_dados_pdf(self, conteudo):
        dados = []
        melhor_volta_piloto = ''  # Inicializa como string vazia
        linhas = conteudo.splitlines()

        for linha in linhas:
            # Identificar a linha que contém "MELHOR VOLTA:"
            if "MELHOR VOLTA:" in linha:
                try:
                    melhor_volta_line = linha.split(":", 1)[1]
                    melhor_volta_piloto = melhor_volta_line.split('(')[0].strip().lower()  # Normaliza para minúsculas
                    print(f"Melhor volta piloto: {melhor_volta_piloto}")  # Depuração
                except IndexError:
                    melhor_volta_piloto = ''
                continue

            # Ignorar linhas vazias
            if not linha.strip():
                continue

            partes = linha.strip().split()

            try:
                vm = float(partes[0].replace(',', '.'))
            except (ValueError, IndexError):
                continue

            try:
                posicao = int(partes[2])
            except (ValueError, IndexError):
                continue

            nome_parts = []
            index = 4
            while index < len(partes):
                part = partes[index]
                if part.isdigit() or part == 'SP':
                    break
                nome_parts.append(part)
                index += 1
            nome = ' '.join(nome_parts).strip().lower()  # Normaliza para minúsculas
            print(f"Extraído - Posição: {posicao}, Nome: {nome}")  # Depuração

            if nome:
                melhor_volta = (nome == melhor_volta_piloto)
                dados.append((posicao, nome, melhor_volta))

        return dados

    def extrair_dados_csv(self, reader):
        dados = []
        next(reader, None)  # Pular o cabeçalho
        for row in reader:
            try:
                posicao = int(row[0])
                piloto_nome = row[1].strip().lower()
                melhor_volta = 'melhor_volta' in row[2].lower()
                dados.append((posicao, piloto_nome, melhor_volta))
            except (ValueError, IndexError):
                continue
        return dados

    def desfazer_importacao(self):
        try:
            # Remover apenas os resultados importados de qualquer formato (PDF, HTML, CSV)
            cursor.execute(
                "DELETE FROM resultados_etapas WHERE etapa_id = ? AND categoria_id = ? AND importado_do_pdf = 1",
                (self.etapa_id, self.categoria_id))
            conn.commit()
            messagebox.showinfo("Sucesso", "Importação desfeita com sucesso!")
            self.carregar_resultados()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao desfazer importação: {e}")

    def editar_resultado(self):
        print("Botão Editar Resultado foi clicado.")  # Depuração
        # Verificar se algum item foi selecionado
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showerror("Erro", "Selecione um resultado para editar.")
            return

        # Obter valores do resultado selecionado, incluindo a categoria
        valores = self.tree.item(selecionado, 'values')
        piloto_nome, posicao, pole_position, melhor_volta, adv_str, categoria = valores

        # Converter ADV de string ("Sim"/"Não") para 0 ou 1
        adv = 1 if adv_str == "Sim" else 0

        # Buscar o ID do piloto a partir do nome
        cursor.execute("SELECT id FROM pilotos WHERE nome = ?", (piloto_nome,))
        piloto = cursor.fetchone()
        if not piloto:
            messagebox.showerror("Erro", "Piloto não encontrado.")
            return
        piloto_id = piloto[0]

        # Abrir janela para edição e passar todos os argumentos necessários
        EditarResultadoWindow(self, self.etapa_id, self.categoria_id, piloto_id, piloto_nome, posicao, pole_position,
                              melhor_volta, adv)

    def get_etapas(self):
        cursor.execute("SELECT id, nome FROM etapas ORDER BY data")
        etapas = cursor.fetchall()
        return etapas

    def inserir_manual(self):
        etapa_nome = self.etapa_var.get()
        categoria_nome = self.categoria_var.get()

        if not etapa_nome or not categoria_nome:
            messagebox.showerror("Erro", "Selecione a etapa e a categoria.")
            return

        # Buscar a etapa selecionada
        etapa = next((et for et in self.get_etapas() if et[1] == etapa_nome), None)
        if not etapa:
            messagebox.showerror("Erro", "Etapa selecionada inválida.")
            return

        # Buscar a categoria selecionada
        categoria = next((cat for cat in self.get_categorias() if cat[1] == categoria_nome), None)
        if not categoria:
            messagebox.showerror("Erro", "Categoria selecionada inválida.")
            return

        # Abrir janela para inserção manual de resultados
        ManualInsertWindow(self, etapa[0])

class ManualInsertWindow(ctk.CTkToplevel):
    def __init__(self, master, etapa_id):
        super().__init__(master)
        self.title("Inserir Resultados Manualmente")
        self.geometry("400x400")
        self.transient(master)  # Sobrepõe a janela principal
        self.grab_set()  # Torna a janela modal
        self.etapa_id = etapa_id
        self.master = master

        # Campo para Nome do Piloto
        self.label_piloto = ctk.CTkLabel(self, text="Nome do Piloto")
        self.label_piloto.pack(pady=10)
        self.entry_piloto = ctk.CTkEntry(self)
        self.entry_piloto.pack(pady=5)

        # Campo para Posição
        self.label_posicao = ctk.CTkLabel(self, text="Posição")
        self.label_posicao.pack(pady=10)
        self.entry_posicao = ctk.CTkEntry(self)
        self.entry_posicao.pack(pady=5)

        # Checkbox para Pole Position
        self.var_pole_position = ctk.BooleanVar()
        self.checkbox_pole_position = ctk.CTkCheckBox(self, text="Pole Position", variable=self.var_pole_position)
        self.checkbox_pole_position.pack(pady=5)

        # Checkbox para Melhor Volta
        self.var_melhor_volta = ctk.BooleanVar()
        self.checkbox_melhor_volta = ctk.CTkCheckBox(self, text="Melhor Volta", variable=self.var_melhor_volta)
        self.checkbox_melhor_volta.pack(pady=5)

        # Botão para Inserir Resultado
        self.btn_inserir = ctk.CTkButton(self, text="Inserir Resultado", command=self.inserir_resultado)
        self.btn_inserir.pack(pady=20)

    def inserir_resultado(self):
        piloto_nome = self.entry_piloto.get().strip().lower()  # Normalizar para minúsculas e remover espaços extras
        posicao = self.entry_posicao.get().strip()

        try:
            posicao = int(posicao)
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um número válido para a posição.")
            return

        pole_position = 1 if self.var_pole_position.get() else 0
        melhor_volta = 1 if self.var_melhor_volta.get() else 0

        # Buscar o piloto pelo nome
        cursor.execute("SELECT id FROM pilotos WHERE LOWER(nome) = ?", (piloto_nome,))
        piloto = cursor.fetchone()
        if not piloto:
            messagebox.showerror("Erro", "Piloto não encontrado.")
            return
        piloto_id = piloto[0]

        # Verificar se já existe uma pole position atribuída nesta etapa e categoria
        if pole_position:
            cursor.execute('''SELECT COUNT(*) FROM resultados_etapas
                              WHERE etapa_id = ? AND categoria_id = ? AND pole_position = 1''',
                           (self.etapa_id, self.master.categoria_id))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Erro",
                                     "Já existe um piloto com a Pole Position nesta etapa. Por favor, edite o resultado existente.")
                return

        # Verificar se já existe uma melhor volta atribuída nesta etapa e categoria
        if melhor_volta:
            cursor.execute('''SELECT COUNT(*) FROM resultados_etapas
                              WHERE etapa_id = ? AND categoria_id = ? AND melhor_volta = 1''',
                           (self.etapa_id, self.master.categoria_id))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Erro",
                                     "Já existe um piloto com a Melhor Volta nesta etapa. Por favor, edite o resultado existente.")
                return

        # Inserir o resultado no banco de dados
        try:
            cursor.execute('''INSERT INTO resultados_etapas (etapa_id, piloto_id, categoria_id, posicao, pole_position, melhor_volta)
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (self.etapa_id, piloto_id, self.master.categoria_id, posicao, pole_position, melhor_volta))
            conn.commit()
            messagebox.showinfo("Sucesso", "Resultado inserido com sucesso!")
            self.master.carregar_resultados()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao inserir resultado: {e}")

class EditarResultadoWindow(ctk.CTkToplevel):
    def __init__(self, master, etapa_id, categoria_id, piloto_id, piloto_nome, posicao, pole_position, melhor_volta, adv):
        super().__init__(master)
        self.etapa_id = etapa_id
        self.categoria_id = categoria_id
        self.piloto_id = piloto_id
        self.master = master

        self.title("Editar Resultado")

        # Campo de entrada para o nome do piloto
        self.label_piloto = ctk.CTkLabel(self, text="Nome do Piloto")
        self.label_piloto.pack(pady=5)
        self.entry_piloto = ctk.CTkEntry(self)
        self.entry_piloto.insert(0, piloto_nome)
        self.entry_piloto.pack(pady=5)

        # Campo de entrada para a posição
        self.label_posicao = ctk.CTkLabel(self, text="Posição")
        self.label_posicao.pack(pady=5)
        self.entry_posicao = ctk.CTkEntry(self)
        self.entry_posicao.insert(0, posicao)
        self.entry_posicao.pack(pady=5)

        # Checkbox para Pole Position
        self.var_pole_position = ctk.BooleanVar(value=(pole_position == "Sim"))
        self.checkbox_pole_position = ctk.CTkCheckBox(self, text="Pole Position", variable=self.var_pole_position)
        self.checkbox_pole_position.pack(pady=5)

        # Checkbox para Melhor Volta
        self.var_melhor_volta = ctk.BooleanVar(value=(melhor_volta == "Sim"))
        self.checkbox_melhor_volta = ctk.CTkCheckBox(self, text="Melhor Volta", variable=self.var_melhor_volta)
        self.checkbox_melhor_volta.pack(pady=5)

        # Checkbox para ADV
        self.var_adv = ctk.BooleanVar(value=(adv == 1))
        self.checkbox_adv = ctk.CTkCheckBox(self, text="ADV", variable=self.var_adv)
        self.checkbox_adv.pack(pady=5)

        # Botão de salvar
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Alterações", command=self.salvar_alteracoes)
        self.btn_salvar.pack(pady=10)

    def salvar_alteracoes(self):
        try:
            # Capturar os novos valores do formulário
            novo_piloto_nome = self.entry_piloto.get().strip().lower()  # Normalizar o nome do piloto
            posicao = self.entry_posicao.get().strip()
            pole_position = 1 if self.var_pole_position.get() else 0
            melhor_volta = 1 if self.var_melhor_volta.get() else 0
            adv = 1 if self.var_adv.get() else 0

            # Atualizar o nome do piloto no banco de dados
            cursor.execute('''UPDATE pilotos
                              SET nome = ?
                              WHERE id = ?''',
                           (novo_piloto_nome, self.piloto_id))

            # Atualizar o resultado no banco de dados
            cursor.execute('''UPDATE resultados_etapas
                              SET posicao = ?, pole_position = ?, melhor_volta = ?, adv = ?
                              WHERE etapa_id = ? AND piloto_id = ? AND categoria_id = ?''',
                           (posicao, pole_position, melhor_volta, adv, self.etapa_id, self.piloto_id, self.categoria_id))
            conn.commit()

            # Atualizar a lista de resultados e fechar a janela
            self.master.carregar_resultados()
            self.destroy()

        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um número válido para a posição.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar alterações: {e}")
