from shared.faq_service import search_faq


query = "¿Cuanto cuesta un salto en paracaidas?"

results = search_faq(query)

print(f"Consulta: {query}\n")

for i, result in enumerate(results, start=1):
    print(f"Resultado {i}:")
    print(f"Categoria: {result['category']}")
    print(f"Pregunta: {result['question']}")
    print(f"Respuesta: {result['answer']}")
    print(f"Distancia: {result['distance']:.4f}")
    print()