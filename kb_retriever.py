from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def search_knowledge_base(query, documents):
    corpus = [doc["content"] for doc in documents]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english"
    )

    document_vectors = vectorizer.fit_transform(corpus)
    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(
        query_vector,
        document_vectors
    )[0]

    results = []

    query_lower = query.lower()

    for doc, score in zip(documents, scores):
        final_score = float(score)

        path_lower = doc["path"].lower()

        # Boost the product document when the ticket
        # explicitly mentions that product.
        if (
            "databridge-pro" in path_lower
            and "databridge pro" in query_lower
        ):
            final_score += 0.20

        results.append({
            "path": doc["path"],
            "score": final_score,
            "content": doc["content"]
        })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results