from fda.providers import registry


def _provider(db):
    return registry.first(db, "embeddings")


def embedding_model(db):
    return _provider(db).model_name


def embed_texts(db, texts):
    p = _provider(db)
    out = []
    for i in range(0, len(texts), 64):
        out += p.embed(texts[i:i + 64])
    return out
