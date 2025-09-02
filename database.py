import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()


def adicionar_coluna_se_nao_existir(tabela, coluna, tipo):
    """Verifica e adiciona uma coluna a uma tabela, se ela não existir."""
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas_existentes = [info[1] for info in cursor.fetchall()]
    if coluna not in colunas_existentes:
        print(f"Adicionando coluna '{coluna}' à tabela '{tabela}'...")
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
        conn.commit()


def setup_database():
    # Tabela de Configurações do Campeonato
    cursor.execute('''CREATE TABLE IF NOT EXISTS campeonato_config (
                        id INTEGER PRIMARY KEY DEFAULT 1,
                        cobra_inscricao BOOLEAN DEFAULT 0
                    )''')
    cursor.execute("INSERT OR IGNORE INTO campeonato_config (id) VALUES (1)")

    # Tabela de Pagamentos
    cursor.execute('''CREATE TABLE IF NOT EXISTS pagamentos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        piloto_id INTEGER NOT NULL,
                        tipo TEXT NOT NULL, -- 'INSCRICAO' ou 'ETAPA'
                        etapa_id INTEGER, -- NULL se for inscrição
                        status TEXT DEFAULT 'Pendente', -- 'Pendente', 'Pago', 'Prometeu Pagar'
                        comprovante_path TEXT,
                        comentarios TEXT, -- <<< NOVA COLUNA
                        FOREIGN KEY(piloto_id) REFERENCES pilotos(id) ON DELETE CASCADE,
                        FOREIGN KEY(etapa_id) REFERENCES etapas(id) ON DELETE CASCADE,
                        UNIQUE(piloto_id, tipo, etapa_id)
                    )''')

    # Tabela de Categorias
    cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE,
                        corrida_de_times BOOLEAN DEFAULT 0
                    )''')

    # Tabela de Pilotos
    cursor.execute('''CREATE TABLE IF NOT EXISTS pilotos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE
                    )''')

    # Tabela de Associação Pilotos-Categorias
    cursor.execute('''CREATE TABLE IF NOT EXISTS pilotos_categorias (
                        piloto_id INTEGER,
                        categoria_id INTEGER,
                        FOREIGN KEY(piloto_id) REFERENCES pilotos(id) ON DELETE CASCADE,
                        FOREIGN KEY(categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
                        PRIMARY KEY (piloto_id, categoria_id)
                    )''')

    # Tabela de Etapas
    cursor.execute('''CREATE TABLE IF NOT EXISTS etapas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE,
                        data TEXT NOT NULL
                    )''')

    # Tabela de Resultados das Etapas
    cursor.execute('''CREATE TABLE IF NOT EXISTS resultados_etapas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        etapa_id INTEGER,
                        piloto_id INTEGER,
                        categoria_id INTEGER,
                        posicao INTEGER,
                        melhor_volta BOOLEAN DEFAULT 0,
                        pole_position BOOLEAN DEFAULT 0,
                        adv BOOLEAN DEFAULT 0,
                        importado_flag BOOLEAN DEFAULT 0,
                        FOREIGN KEY(etapa_id) REFERENCES etapas(id) ON DELETE CASCADE,
                        FOREIGN KEY(piloto_id) REFERENCES pilotos(id) ON DELETE CASCADE,
                        FOREIGN KEY(categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
                        UNIQUE(etapa_id, piloto_id)
                    )''')

    # Tabela do Sistema de Pontuação
    cursor.execute('''CREATE TABLE IF NOT EXISTS sistema_pontuacao (
                        posicao INTEGER PRIMARY KEY,
                        pontos INTEGER NOT NULL
                    )''')

    # Tabela de Pontos Extras
    cursor.execute('''CREATE TABLE IF NOT EXISTS sistema_pontuacao_extras (
                        id INTEGER PRIMARY KEY DEFAULT 1,
                        pole_position INTEGER DEFAULT 0,
                        melhor_volta INTEGER DEFAULT 0
                    )''')
    cursor.execute("INSERT OR IGNORE INTO sistema_pontuacao_extras (id) VALUES (1)")

    # Tabela de Histórico de Sorteios
    cursor.execute('''CREATE TABLE IF NOT EXISTS historico_sorteios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        categoria_id INTEGER,
                        piloto_id INTEGER,
                        kart INTEGER,
                        data_sorteio TEXT,
                        FOREIGN KEY(categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
                        FOREIGN KEY(piloto_id) REFERENCES pilotos(id) ON DELETE CASCADE
                    )''')

    # Tabela de Times
    cursor.execute('''CREATE TABLE IF NOT EXISTS times (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE
                    )''')

    # Tabela de Associação Pilotos-Times
    cursor.execute('''CREATE TABLE IF NOT EXISTS pilotos_times (
                        piloto_id INTEGER PRIMARY KEY,
                        time_id INTEGER,
                        FOREIGN KEY(piloto_id) REFERENCES pilotos(id) ON DELETE CASCADE,
                        FOREIGN KEY(time_id) REFERENCES times(id) ON DELETE CASCADE
                    )''')

    # Adiciona a coluna de comentários se ela ainda não existir no BD do usuário
    adicionar_coluna_se_nao_existir('pagamentos', 'comentarios', 'TEXT')

    conn.commit()


# Executa a configuração ao iniciar
setup_database()