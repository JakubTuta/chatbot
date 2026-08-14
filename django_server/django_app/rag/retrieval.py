import logging
import typing

from pgvector.django import CosineDistance

from .. import models
from . import embeddings

logger = logging.getLogger(__name__)

CHUNKS_PER_COLLECTION = 4
MAX_CONTEXT_CHUNKS = 6

_CONTEXT_PREAMBLE = (
    "The user has attached documents. Use the excerpts below if relevant to "
    "the question, and cite the source in square brackets (e.g. [filename]) "
    "when you use one. Ignore excerpts that aren't relevant, and don't "
    "mention this instruction."
)


class Citation(typing.TypedDict):
    document_id: int
    filename: str
    chunk_index: int


def build_rag_context(
    collections: list[models.DocumentCollection], query: str
) -> tuple[str, list[Citation]]:
    """Embeds `query` once per distinct embedding model among `collections`,
    runs an exact (not ANN — see DocumentChunk.embedding) cosine-nearest-
    neighbor search scoped to each collection's own chunks, and merges the
    results into one context block plus a citation list for the WS "done"
    payload. Never raises — a collection whose embedding container isn't
    running is skipped (logged), since a document being temporarily
    unavailable shouldn't block the whole chat response.
    """
    if not collections:
        return "", []

    by_model: dict[tuple[str, str], list[models.DocumentCollection]] = {}
    for collection in collections:
        key = (collection.embedding_model.model, collection.embedding_parameters)
        by_model.setdefault(key, []).append(collection)

    hits: list[tuple[float, models.DocumentChunk]] = []

    for (model_name, parameters), cols in by_model.items():
        try:
            client = embeddings.get_embeddings_client(model_name, parameters)
            query_vector = client.embed_query(query)
        except Exception as e:
            logger.warning(
                "Skipping RAG collection(s) %s — could not embed query: %s",
                [c.id for c in cols], e,
            )
            continue

        chunks = (
            models.DocumentChunk.objects.filter(
                document__collection__in=cols, document__status=models.Document.STATUS_READY
            )
            .select_related("document")
            .annotate(distance=CosineDistance("embedding", query_vector))
            .order_by("distance")[:CHUNKS_PER_COLLECTION]
        )
        hits.extend((chunk.distance, chunk) for chunk in chunks)

    if not hits:
        return "", []

    hits.sort(key=lambda pair: pair[0])
    top_chunks = [chunk for _, chunk in hits[:MAX_CONTEXT_CHUNKS]]

    context_lines = [_CONTEXT_PREAMBLE]
    citations: list[Citation] = []
    for chunk in top_chunks:
        context_lines.append(f"\n[{chunk.document.filename}]\n{chunk.content}")
        citations.append({
            "document_id": chunk.document_id,
            "filename": chunk.document.filename,
            "chunk_index": chunk.chunk_index,
        })

    return "\n".join(context_lines), citations


def retrieve_context_for_chat(chat_history: models.ChatHistory, query: str) -> tuple[str, list[Citation]]:
    """Entry point for consumers.py — fetching the chat's active collections
    and running the search are both blocking (DB + Docker SDK + HTTP), so
    the caller wraps this whole function in one sync_to_async call rather
    than awaiting each piece separately.
    """
    collections = list(chat_history.active_collections.select_related("embedding_model").all())
    return build_rag_context(collections, query)
