import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

def setup_database():
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

    # Tabela de Pontos Extras (COM A COLUNA ID CORRIGIDA)
    cursor.execute('''CREATE TABLE IF NOT EXISTS sistema_pontuacao_extras (
                        id INTEGER PRIMARY KEY DEFAULT 1,
                        pole_position INTEGER DEFAULT 0,
                        melhor_volta INTEGER DEFAULT 0
                    )''')
    # Garante que a linha de configuração sempre exista
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

    conn.commit()

# Executa a configuração ao iniciar
setup_database()