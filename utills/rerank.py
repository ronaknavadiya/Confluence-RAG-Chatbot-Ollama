try:
    from sentence_transformers import CrossEncoder
    _HAS_CROSS = True
except Exception:
    _HAS_CROSS = False


def re_rank(query: str, docs: list, top_k: int = 5) -> list:
    if not _HAS_CROSS or not docs:
        return docs[:top_k]
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    pairs = [[query, d.page_content] for d in docs]
    scores = model.predict(pairs)
    ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
    return [d for _, d in ranked[:top_k]]