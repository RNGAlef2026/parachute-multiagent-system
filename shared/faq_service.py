import psycopg2
from sentence_transformers import SentenceTransformer


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "parachute_db",
    "user": "parachute",
    "password": "parachute123",
}

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

model = SentenceTransformer(EMBEDDING_MODEL)


def get_connection():
    """
    Crea y retorna una conexion con PostgreSQL.
    """
    return psycopg2.connect(**DB_CONFIG)


def generate_embedding(text: str) -> list:
    """
    Genera el embedding de un texto para realizar
    busquedas por similitud en la base de FAQs.
    """
    return model.encode(text).tolist()


def search_faq(query: str, limit: int = 3) -> list:
    """
    Busca las FAQs mas similares semanticamente
    a la consulta del usuario.
    """
    embedding = generate_embedding(query)
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, categoria, pregunta, respuesta,
                       embedding <=> %s::vector AS distance
                FROM faqs
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """,
                (embedding, embedding, limit),
            )

            rows = cursor.fetchall()

    finally:
        connection.close()

    return [
        {
            "id": row[0],
            "category": row[1],
            "question": row[2],
            "answer": row[3],
            "distance": float(row[4]),
        }
        for row in rows
    ]