# Fibra Tech — Bot de Atención al Cliente

Chatbot de atención al cliente para Fibra Tech (ISP de fibra óptica):
consulta de saldo, reporte de pagos, información de planes y soporte
técnico con respuestas generadas por RAG (búsqueda híbrida + Gemini).

## Estructura

```
bot/
  main.py            CLI de entrada (loop de chat por consola)
  engine.py           Intérprete de flujos: lee flows.json y decide qué
                       nodo mostrar / qué handler llamar en cada turno
  flows.json           Árbol de conversación (menús, mensajes, inputs)
  handlers.py           Lógica de negocio de cada nodo (consulta de saldo,
                        registro de pagos, chat de soporte técnico...)
  db.py                 Persistencia en SQLite (clientes, pagos, escalamientos)
  bot.db                 Base SQLite (se genera sola, no se versiona)

  knowledge/
    soporte_tecnico_fibra.json   FAQ de soporte técnico (base de conocimiento del RAG)

  rag/
    config.py            Variables de entorno y parámetros (chunking, umbrales)
    ingest.py             Chunking + índice vectorial (Chroma) + índice BM25
    llm.py                 Cliente de Gemini (vía Vertex AI, google-genai)
    chat.py                 Orquesta retrieval híbrido + LLM + detección de
                            "no resuelto"
    chroma_store/            Base vectorial persistente (se genera sola, no se versiona)

Project/                Notebooks y scripts de un proyecto de aprendizaje
                        de RAG (KFF/ACA) — ver Project/README.md. Sirvió
                        como referencia de patrones (retrieval híbrido,
                        cliente Gemini) para bot/rag/, pero es un proyecto
                        independiente.

requirements.txt        Dependencias de bot/
.env                     Credenciales (no versionado, ver abajo)
```

## Configuración

Crea un `.env` en la raíz del proyecto con:

```
VERTEX_CREDENTIALS_JSON=<ruta al JSON de credenciales de servicio de GCP>
VERTEX_PROJECT_ID=<project id de GCP>
VERTEX_LOCATION=<región, ej. us-central1>
```

Instala dependencias:

```
pip install -r requirements.txt
```

## Uso

```
cd bot
python main.py
```

Escribe `salir` para terminar la sesión.

## Soporte técnico (RAG)

Desde el menú principal: **Fibra Tech → Soporte Técnico**. El bot
responde preguntas sobre señal/conexión usando únicamente el contenido de
`bot/knowledge/soporte_tecnico_fibra.json`, recuperado con un retriever
híbrido (búsqueda vectorial + BM25) y respondido con Gemini restringido a
ese contexto.

Si la consulta no se puede resolver con la base de conocimiento (dos
intentos fallidos seguidos, o el usuario escribe `agente`), el caso se
escala y queda registrado en la tabla `escalamientos_soporte` de
`bot.db`.

Para agregar o editar preguntas, basta con editar
`bot/knowledge/soporte_tecnico_fibra.json` — el índice vectorial se
reconstruye automáticamente la próxima vez que arranca el bot si el
contenido cambió (se detecta por hash).
