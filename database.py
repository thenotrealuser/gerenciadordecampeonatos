import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()


def verificar_estrutura_banco():
    # Verificar se a coluna 'adv' existe na tabela 'resultados_etapas'
    cursor.execute("PRAGMA table_info(resultados_etapas)")
    colunas = [info[1] for info in cursor.fetchall()]

    # Se a coluna 'adv' não existir, adicioná-la
    if 'adv' not in colunas:
        cursor.execute("ALTER TABLE resultados_etapas ADD COLUMN adv INTEGER DEFAULT 0")
        conn.commit()
        print("Coluna 'adv' adicionada com sucesso à tabela 'resultados_etapas'.")


def setup_database():
    cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pilotos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pilotos_categorias (
                        piloto_id INTEGER,
                        categoria_id INTEGER,
                        FOREIGN KEY(piloto_id) REFERENCES pilotos(id),
                        FOREIGN KEY(categoria_id) REFERENCES categorias(id),
                        UNIQUE(piloto_id, categoria_id)
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS etapas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        data TEXT NOT NULL
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS resultados_etapas (
                        etapa_id INTEGER,
                        piloto_id INTEGER,
                        categoria_id INTEGER,
                        posicao INTEGER,
                        melhor_volta INTEGER,
                        pole_position INTEGER,
                        importado_do_pdf INTEGER DEFAULT 0,
                        FOREIGN KEY(etapa_id) REFERENCES etapas(id),
                        FOREIGN KEY(piloto_id) REFERENCES pilotos(id),
                        FOREIGN KEY(categoria_id) REFERENCES categorias(id),
                        UNIQUE(etapa_id, piloto_id, categoria_id)
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sistema_pontuacao (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        posicao INTEGER,
                        pontos INTEGER
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sistema_pontuacao_extras (
                        pole_position INTEGER DEFAULT 0,
                        melhor_volta INTEGER DEFAULT 0
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS historico_sorteios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        categoria_id INTEGER,
                        piloto_id INTEGER,
                        kart INTEGER,
                        data_sorteio TEXT,
                        FOREIGN KEY(categoria_id) REFERENCES categorias(id),
                        FOREIGN KEY(piloto_id) REFERENCES pilotos(id)
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS times (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pilotos_times (
                        piloto_id INTEGER,
                        time_id INTEGER,
                        FOREIGN KEY(piloto_id) REFERENCES pilotos(id),
                        FOREIGN KEY(time_id) REFERENCES times(id),
                        UNIQUE(piloto_id, time_id)
                    )''')

    # Verificar e adicionar a coluna corrida_de_times, se não existir
    verificar_ou_adicionar_coluna_corrida_de_times()

    # **ADICIONAR ESTA LINHA**: Verificar se a coluna 'adv' existe e, se não, adicioná-la.
    verificar_estrutura_banco()

    conn.commit()

def verificar_ou_adicionar_coluna_corrida_de_times():
    try:
        cursor.execute("PRAGMA table_info(categorias)")
        colunas = cursor.fetchall()

        # Verificar se a coluna corrida_de_times já existe
        colunas_existentes = [coluna[1] for coluna in colunas]  # [1] é o nome da coluna no resultado do PRAGMA
        if 'corrida_de_times' not in colunas_existentes:
            # Adicionar a coluna corrida_de_times
            cursor.execute("ALTER TABLE categorias ADD COLUMN corrida_de_times BOOLEAN DEFAULT 0")
            conn.commit()
            print("Coluna corrida_de_times adicionada com sucesso.")
        else:
            print("Coluna corrida_de_times já existe.")
    except Exception as e:
        print(f"Erro ao verificar ou adicionar a coluna corrida_de_times: {e}")
