import logging

from django.db import transaction

from .. import models
from ..functions import ModelUnavailableError
from . import chunking, embeddings

logger = logging.getLogger(__name__)


def ingest_document(document_id: int, text: str) -> None:
    """Chunks, embeds, and saves a document's content. Runs in a background
    thread (see views.Documents.post) — real embedding calls are too slow to
    do inline in the upload request. Only the id and already-extracted text
    cross the thread boundary; extraction itself happens synchronously in
    the view, since it needs the request's in-memory uploaded file, which
    Django tears down once the response is sent. A brand-new thread lazily
    gets its own fresh connection on first use, so there's no stale
    connection to clean up here the way a long-lived worker might need to.
    """
    try:
        document = models.Document.objects.select_related(
            "collection", "collection__embedding_model"
        ).get(id=document_id)
    except models.Document.DoesNotExist:
        logger.warning("Document %s vanished before ingest started", document_id)
        return

    document.status = models.Document.STATUS_PROCESSING
    document.save(update_fields=["status"])

    try:
        chunks = chunking.chunk_text(text)
        if not chunks:
            raise ValueError("No extractable text found in this file.")

        client = embeddings.get_embeddings_client(
            document.collection.embedding_model.model, document.collection.embedding_parameters
        )
        vectors = client.embed_documents([c.content for c in chunks])

        with transaction.atomic():
            models.DocumentChunk.objects.bulk_create(
                [
                    models.DocumentChunk(
                        document=document,
                        chunk_index=i,
                        content=chunk.content,
                        char_start=chunk.char_start,
                        embedding=vector,
                    )
                    for i, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
                ]
            )
            document.status = models.Document.STATUS_READY
            document.chunk_count = len(chunks)
            document.save(update_fields=["status", "chunk_count"])

    except ModelUnavailableError as e:
        logger.warning("Ingest failed for document %s: %s", document_id, e)
        document.status = models.Document.STATUS_FAILED
        document.error_message = str(e)
        document.save(update_fields=["status", "error_message"])
    except Exception as e:
        logger.exception("Ingest crashed for document %s", document_id)
        document.status = models.Document.STATUS_FAILED
        document.error_message = str(e)
        document.save(update_fields=["status", "error_message"])
