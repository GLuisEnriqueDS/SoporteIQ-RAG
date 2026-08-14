from dataclasses import dataclass

from . import config
from .ingest import get_hybrid_retriever, get_vectorstore
from .llm import generate

NO_RESUELTO = "NO_RESUELTO"

_SYSTEM_PROMPT = """Eres la asistente virtual de soporte técnico de \
Fibra Tech (proveedor de internet por fibra óptica). Respondes dudas sobre \
señal, conexión, wifi y equipos, usando ÚNICAMENTE la información del \
CONTEXTO de abajo, que proviene de la base de conocimiento oficial.

Reglas:
- Responde en español, tono cercano, claro y breve, con algún emoji moderado.
- Usa SOLO datos del CONTEXTO. No inventes pasos, IPs, ni datos que no estén ahí.
- Si el CONTEXTO no tiene información suficiente para responder la pregunta \
del usuario con confianza, responde EXACTAMENTE y solo con el texto: {sentinel}
- No agregues explicaciones ni disculpas alrededor de {sentinel}; si lo usas, \
debe ser la única palabra de tu respuesta.

CONTEXTO:
{context}

PREGUNTA DEL USUARIO:
{query}
""".format(sentinel=NO_RESUELTO, context="{context}", query="{query}")


@dataclass
class RagResult:
    respuesta: str
    resuelto: bool
    fuente_ids: list[str]


def _format_context(docs) -> str:
    bloques = []
    for doc in docs:
        bloques.append(
            f"- [{doc.metadata['categoria']}] {doc.metadata['pregunta']}\n  {doc.metadata['respuesta']}"
        )
    return "\n".join(bloques)


def answer_query(query: str) -> RagResult:
    vectorstore = get_vectorstore()
    top = vectorstore.similarity_search_with_relevance_scores(query, k=1)

    if not top or top[0][1] < config.MIN_RELEVANCE_SCORE:
        return RagResult(respuesta="", resuelto=False, fuente_ids=[])

    retriever = get_hybrid_retriever()
    docs = retriever.invoke(query)
    if not docs:
        return RagResult(respuesta="", resuelto=False, fuente_ids=[])

    prompt = _SYSTEM_PROMPT.format(context=_format_context(docs), query=query)
    respuesta = generate(prompt)

    if not respuesta or NO_RESUELTO in respuesta:
        return RagResult(respuesta="", resuelto=False, fuente_ids=[])

    fuente_ids = sorted({doc.metadata["id"] for doc in docs})
    return RagResult(respuesta=respuesta, resuelto=True, fuente_ids=fuente_ids)
