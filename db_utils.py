from database import cursor

def buscar_categorias():
    """Retorna todas as categorias ordenadas pelo nome."""
    cursor.execute("SELECT * FROM categorias ORDER BY nome")
    return cursor.fetchall()


def buscar_times():
    """Retorna todos os times ordenados pelo nome."""
    cursor.execute("SELECT * FROM times ORDER BY nome")
    return cursor.fetchall()
