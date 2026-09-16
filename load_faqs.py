from pathlib import Path

import psycopg2
from sentence_transformers import SentenceTransformer


CORPUS_FILE = Path("Corpus_FAQs_Parachute_SA_2026.txt")

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "parachute_db",
    "user": "parachute",
    "password": "parachute123",
}

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_corpus() -> list:
    """
    Lee el corpus y extrae las FAQs.
    """
    content = CORPUS_FILE.read_text(encoding="utf-8")

    records = []

    current_record = {}

    for line in content.splitlines():
        line = line.strip()

        if line.startswith("ID:"):
            current_record["id"] = line.removeprefix("ID:").strip()

        elif line.startswith("CATEGORÍA:"):
            current_record["categoria"] = line.removeprefix(
                "CATEGORÍA:"
            ).strip()

        elif line.startswith("PREGUNTA:"):
            current_record["pregunta"] = line.removeprefix(
                "PREGUNTA:"
            ).strip()

        elif line.startswith("RESPUESTA:"):
            current_record["respuesta"] = line.removeprefix(
                "RESPUESTA:"
            ).strip()

        elif line.startswith("METADATA:"):
            if all(
                key in current_record
                for key in ["id", "categoria", "pregunta", "respuesta"]
            ):
                records.append(current_record)

            current_record = {}

    return records


def initialize_database(connection):
    """
    Crea la extension vector y la tabla de FAQs si no existen.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE EXTENSION IF NOT EXISTS vector;
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS faqs (
                id TEXT PRIMARY KEY,
                categoria TEXT NOT NULL,
                pregunta TEXT NOT NULL,
                respuesta TEXT NOT NULL,
                embedding VECTOR(384) NOT NULL
            );
            """
        )

    connection.commit()


def insert_faqs(connection, records: list):
    """
    Genera embeddings e inserta las FAQs en PostgreSQL.
    """
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Generando embeddings para {len(records)} FAQs...")

    for index, record in enumerate(records, start=1):
        text = (
            f"{record['pregunta']} "
            f"{record['respuesta']}"
        )

        embedding = model.encode(text).tolist()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO faqs (
                    id,
                    categoria,
                    pregunta,
                    respuesta,
                    embedding
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id)
                DO UPDATE SET
                    categoria = EXCLUDED.categoria,
                    pregunta = EXCLUDED.pregunta,
                    respuesta = EXCLUDED.respuesta,
                    embedding = EXCLUDED.embedding;
                """,
                (
                    record["id"],
                    record["categoria"],
                    record["pregunta"],
                    record["respuesta"],
                    embedding,
                ),
            )

        print(
            f"[{index}/{len(records)}] "
            f"{record['id']} cargada"
        )

    connection.commit()


def main():
    print("Parachute S.A. - Carga de FAQs")
    print("--------------------------------")

    records = load_corpus()

    print(f"FAQs encontradas en el corpus: {len(records)}")

    if not records:
        print("No se encontraron FAQs.")
        return

    connection = psycopg2.connect(**DB_CONFIG)

    try:
        initialize_database(connection)
        insert_faqs(connection, records)

    finally:
        connection.close()

    print("\nCarga completada correctamente.")


if __name__ == "__main__":
    main()