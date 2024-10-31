from tkinter import StringVar, ttk, messagebox, filedialog

import customtkinter as ctk
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle, SimpleDocTemplate
from database import cursor, conn


class ResultadoGeralFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Inicializar o número de descartes aplicados
        self.descartar_aplicado = 0
        self.pontuacao = {}  # Inicializar pontuação
        self.pilotos_resultados = {}  # Inicializar resultados dos pilotos

        # Título
        self.label = ctk.CTkLabel(self, text="Resultado Geral do Campeonato", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=10)

        # Seleção de Categoria
        self.label_categoria = ctk.CTkLabel(self, text="Selecione a Categoria")
        self.label_categoria.pack(pady=5)

        self.categorias = self.get_categorias()
        self.categoria_var = StringVar()
        self.dropdown_categoria = ctk.CTkComboBox(
            self,
            values=[cat[1] for cat in self.categorias],
            variable=self.categoria_var,
            command=self.atualizar_resultado
        )
        self.dropdown_categoria.pack(pady=5)

        # Botões para Aplicar Descarte
        self.btn_descartar_2 = ctk.CTkButton(self, text="Aplicar Descarte de 2 Etapas",
                                             command=lambda: self.aplicar_descarte(2))
        self.btn_descartar_2.pack(pady=5)

        # Entrada para Número de Descartes
        self.label_descartar_personalizado = ctk.CTkLabel(self, text="Quantos descartes deseja aplicar?")
        self.label_descartar_personalizado.pack(pady=5)

        self.entry_descartar = ctk.CTkEntry(self, placeholder_text="Digite o número de descartes")
        self.entry_descartar.pack(pady=5)

        self.btn_descartar_personalizado = ctk.CTkButton(self, text="Aplicar Descarte Personalizado",
                                                         command=self.aplicar_descarte_personalizado)
        self.btn_descartar_personalizado.pack(pady=5)

        # Treeview para exibir os resultados em formato de planilha
        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.pack(fill="both", expand=True, pady=10)

        columns = ('Piloto', 'Pontos', 'Posições')

        # Criação do Treeview com colunas
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show='headings', height=10)
        self.tree.heading('Piloto', text='Piloto')
        self.tree.heading('Pontos', text='Pontos')
        self.tree.heading('Posições', text='Posições')

        self.tree.column('Piloto', width=150)
        self.tree.column('Pontos', width=80)
        self.tree.column('Posições', width=250)

        # Adicionando scrollbar horizontal e vertical
        self.scrollbar_x = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.scrollbar_y = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(xscrollcommand=self.scrollbar_x.set, yscrollcommand=self.scrollbar_y.set)

        self.tree.pack(side='left', fill='both', expand=True)
        self.scrollbar_x.pack(side='bottom', fill='x')
        self.scrollbar_y.pack(side='right', fill='y')

        # Botão para reverter os descartes
        self.btn_reverter_descartes = ctk.CTkButton(self, text="Reverter Descartes", command=self.reverter_descartes)
        self.btn_reverter_descartes.pack(pady=5)

        # Botão para exportar os resultados em PDF
        self.btn_exportar_pdf = ctk.CTkButton(self, text="Exportar Resultados", command=self.exportar_resultado_campeonato)
        self.btn_exportar_pdf.pack(pady=5)

        self.atualizar_resultado()

    def get_categorias(self):
        cursor.execute("SELECT * FROM categorias ORDER BY nome")
        categorias = cursor.fetchall()
        return categorias

    def aplicar_descarte(self, numero_descartes):
        self.atualizar_resultado(descartar=numero_descartes)

    def aplicar_descarte_personalizado(self):
        try:
            numero_descartes = int(self.entry_descartar.get())
            if numero_descartes < 0:
                raise ValueError
            self.atualizar_resultado(descartar=numero_descartes)
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um número válido de descartes.")

    def atualizar_resultado(self, event=None, descartar=0):
        # Atualizar o número de descartes aplicados
        self.descartar_aplicado = descartar

        categoria_nome = self.categoria_var.get()
        if not categoria_nome:
            return

        # Buscar a categoria selecionada
        cursor.execute("SELECT id FROM categorias WHERE nome = ?", (categoria_nome,))
        categoria = cursor.fetchone()
        if not categoria:
            messagebox.showerror("Erro", "Categoria selecionada inválida.")
            return
        categoria_id = categoria[0]

        # Carregar o sistema de pontuação geral (padrão para todas as categorias)
        sistema_pontuacao = self.get_sistema_pontuacao()
        if not sistema_pontuacao:
            messagebox.showwarning("Aviso", "Sistema de pontuação não configurado.")
            return

        # Buscar resultados da categoria, ordenando as etapas corretamente
        cursor.execute('''SELECT p.nome, r.posicao, r.melhor_volta, r.pole_position, r.adv, e.nome, e.id
                          FROM resultados_etapas r
                          JOIN pilotos p ON r.piloto_id = p.id
                          JOIN etapas e ON r.etapa_id = e.id
                          WHERE r.categoria_id = ?
                          ORDER BY e.id ASC''', (categoria_id,))
        resultados = cursor.fetchall()

        self.pontuacao = {}  # Reinicializar pontuação
        self.pilotos_resultados = {}  # Reinicializar resultados dos pilotos
        self.etapas_set = set()  # Reinicializar conjunto de etapas

        # Agrupar resultados por piloto e coletar as etapas
        for res in resultados:
            nome, posicao, melhor_volta, pole_position, adv, etapa_nome, etapa_id = res
            pontos_posicao = sistema_pontuacao.get(posicao, 0)
            pontos_melhor_volta = sistema_pontuacao.get("melhor_volta", 0) if melhor_volta else 0
            pontos_pole_position = sistema_pontuacao.get("pole_position", 0) if pole_position else 0
            total_pontos = pontos_posicao + pontos_melhor_volta + pontos_pole_position

            if nome not in self.pontuacao:
                self.pontuacao[nome] = 0
                self.pilotos_resultados[nome] = []

            self.pontuacao[nome] += total_pontos
            self.pilotos_resultados[nome].append((total_pontos, etapa_nome, posicao, etapa_id, adv))

            # Adicionar as etapas ao conjunto
            self.etapas_set.add((etapa_nome, etapa_id))

        # Aplicar descarte dos piores resultados, exceto os que têm ADV
        for piloto, pontos_list in self.pilotos_resultados.items():
            # Ordena, mantendo os ADV no final (não elegíveis para descarte)
            pontos_list.sort(key=lambda x: (x[4] == 'Sim', x[0]))
            if len(pontos_list) > descartar:
                pontos_descartados = [p for p in pontos_list[:descartar] if p[4] != 'Sim']  # Pega os piores sem ADV
                self.pontuacao[piloto] -= sum(p[0] for p in pontos_descartados)  # Subtrai os piores resultados

                # Remover os pontos descartados da lista
                self.pilotos_resultados[piloto] = [p for p in pontos_list if p not in pontos_descartados]
            else:
                self.pilotos_resultados[piloto] = pontos_list

            # Ordenar os resultados restantes por ordem de etapas
            self.pilotos_resultados[piloto] = sorted(self.pilotos_resultados[piloto], key=lambda x: x[3])  # Ordena pela etapa_id

        # Limpar a Treeview
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Exibir resultados na Treeview
        classificacao = sorted(self.pontuacao.items(), key=lambda x: x[1], reverse=True)
        for piloto, pontos in classificacao:
            posicoes = ', '.join(f"{etapa_nome}: {posicao}" for _, etapa_nome, posicao, _, _ in self.pilotos_resultados[piloto])
            self.tree.insert("", "end", values=(piloto, pontos, posicoes))

    def reverter_descartes(self):
        # Atualizar resultado sem descarte
        self.atualizar_resultado(descartar=0)

    def get_sistema_pontuacao(self):
        """Busca o sistema de pontuação geral, que é aplicado a todas as categorias"""
        cursor.execute("SELECT posicao, pontos FROM sistema_pontuacao ORDER BY posicao")
        rows = cursor.fetchall()
        sistema = {pos: pontos for pos, pontos in rows}

        # Pegar pontos de pole position e melhor volta
        cursor.execute("SELECT pole_position, melhor_volta FROM sistema_pontuacao_extras")
        extras = cursor.fetchone()
        if extras:
            sistema["pole_position"] = extras[0]
            sistema["melhor_volta"] = extras[1]

        return sistema if sistema else None

    def exportar_resultado_campeonato(self):
        try:
            # Categoria selecionada
            categoria_nome = self.categoria_var.get()
            if not categoria_nome:
                messagebox.showerror("Erro", "Selecione uma categoria para exportar.")
                return

            # Buscar ID da categoria e se é de times
            cursor.execute("SELECT id, corrida_de_times FROM categorias WHERE nome = ?", (categoria_nome,))
            categoria = cursor.fetchone()
            if not categoria:
                messagebox.showerror("Erro", "Categoria inválida.")
                return
            categoria_id, corrida_de_times = categoria

            # Ordenar etapas por data
            etapas_ordenadas = sorted(self.etapas_set, key=lambda x: x[1])  # Ordena por data
            etapas_nomes = [etapa for etapa, _ in etapas_ordenadas]

            # Criar tabela para exportação
            elementos = []

            # Título
            styles = getSampleStyleSheet()
            titulo = Paragraph(f"Resultado Geral - Categoria: {categoria_nome}", styles['Title'])
            elementos.append(titulo)

            # Cabeçalho atualizado
            header = ['Pos', 'Piloto'] + [f"{etapa}" for etapa in etapas_nomes] + ['Total Piloto']
            tabela_dados = [header]

            # Usar os pontos já calculados após o descarte
            classificacao = sorted(self.pontuacao.items(), key=lambda x: x[1], reverse=True)
            for idx, (piloto, pontos_totais) in enumerate(classificacao, start=1):
                linha = [idx, piloto]
                pontos_por_etapa = {etapa: '-' for etapa in etapas_nomes}

                # Preencher pontos das etapas para o piloto
                for total_pontos, etapa_nome, posicao, _, adv in self.pilotos_resultados[piloto]:
                    if etapa_nome in pontos_por_etapa:
                        pontos_por_etapa[etapa_nome] = f"{total_pontos}"

                # Adicionar pontos das etapas e total na linha
                for etapa in etapas_nomes:
                    linha.append(pontos_por_etapa[etapa])

                # Adicionar o total do piloto (já ajustado após o descarte)
                linha.append(pontos_totais)

                tabela_dados.append(linha)

            # Adicionar a marca d'água de descarte se aplicável
            if self.descartar_aplicado > 0:
                marca_dagua = Paragraph(f"{self.descartar_aplicado} descartes foram aplicados.", styles['Normal'])
                elementos.append(marca_dagua)

            # Criar o documento PDF
            nome_default = f"resultado_campeonato_{categoria_nome.replace(' ', '_').lower()}.pdf"
            nome_arquivo = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")],
                                                        initialfile=nome_default, title="Salvar PDF")

            if not nome_arquivo:
                return

            tabela = Table(tabela_dados)
            estilo = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ])

            tabela.setStyle(estilo)
            elementos.append(tabela)

            pdf = SimpleDocTemplate(nome_arquivo, pagesize=landscape(A4))
            pdf.build(elementos)

            messagebox.showinfo("Sucesso", f"PDF exportado com sucesso para {nome_arquivo}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar PDF: {e}")
