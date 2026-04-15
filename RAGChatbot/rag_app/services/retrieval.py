from langchain.schema import Document
from langchain_community.vectorstores import FAISS


TAG_KEYWORD_MAP = {
    "who am i": ["profile", "about", "personal", "identity"],
    "my name": ["profile", "about"],
    "my skills": ["skills", "expertise"],
    "my projects": ["projects", "portfolio"],
}

# Lowered threshold to allow more candidate chunks through.
MIN_RELEVANCE_SCORE = 0.15

PRIORITY_SOURCE_RULES = [
    {
        "keywords": ["projects", "project"],
        "source": "Master-Project-List.md",
    },
    {
        "keywords": [" i","Jia Hui", "my name", "who am i", "about me", "profile"],
        "source": "About J.md",
    },
]


def infer_tags(note):
    haystack = f"{note['path']} {note['name']} {note['content'][:1000]}".lower()
    tags = set()

    if any(token in haystack for token in ["profile", "about", "personal", "identity", "bio", "me"]):
        tags.update(["profile", "about", "personal", "identity"])
    if any(token in haystack for token in ["skill", "skills", "expertise", "technology", "stack"]):
        tags.update(["skills", "expertise"])
    if any(token in haystack for token in ["project", "projects", "portfolio", "build", "built"]):
        tags.update(["projects", "portfolio"])

    return sorted(tags)


def search_with_debug_scores(query, vectorstore, k=5, filter_fn=None):
    docs_with_scores = vectorstore.similarity_search_with_relevance_scores(
        query,
        k=k,
        filter=filter_fn,
    )

    for doc, score in docs_with_scores:
        preview = doc.page_content[:80].replace("\n", " ")
        print(f"Score: {score:.4f} | {preview}")

    return [
        doc
        for doc, score in docs_with_scores
        if score >= MIN_RELEVANCE_SCORE
    ]


def get_priority_sources(query: str):
    q_lower = query.lower()
    sources = []

    for rule in PRIORITY_SOURCE_RULES:
        if any(keyword in q_lower for keyword in rule["keywords"]):
            sources.append(rule["source"])

    # Keep order stable while removing duplicates.
    return list(dict.fromkeys(sources))


def priority_source_search(query: str, vectorstore, k=5):
    sources = get_priority_sources(query)
    if not sources:
        return []

    results = []
    seen = set()

    for source in sources:
        def source_filter(metadata):
            return metadata.get("source") == source

        docs = search_with_debug_scores(
            query=query,
            vectorstore=vectorstore,
            k=k,
            filter_fn=source_filter,
        )

        for doc in docs:
            doc_key = (doc.metadata.get("source", ""), doc.page_content)
            if doc_key in seen:
                continue
            seen.add(doc_key)
            results.append(doc)
            if len(results) >= k:
                return results

    return results


def smart_search(query: str, vectorstore, k=5):
    priority_docs = priority_source_search(query=query, vectorstore=vectorstore, k=k)
    if priority_docs:
        return priority_docs

    q_lower = query.lower()

    for keyword, tags in TAG_KEYWORD_MAP.items():
        if keyword in q_lower:
            def tag_filter(metadata):
                metadata_tags = metadata.get("tags", [])
                return any(tag in metadata_tags for tag in tags)

            docs = search_with_debug_scores(
                query=query,
                vectorstore=vectorstore,
                k=k,
                filter_fn=tag_filter,
            )
            if docs:
                return docs

    docs = search_with_debug_scores(query=query, vectorstore=vectorstore, k=k)
    if docs:
        return docs

    # Final fallback if threshold filtering removed everything.
    return vectorstore.similarity_search(query, k=k)


def rewrite_query(query: str) -> list[str]:
    """Expand a query into multiple semantic variations."""
    rewrites = [query]
    q_lower = query.lower()

    phrase_map = {
        "who am i": ["about me", "my profile", "personal identity", "my name"],
        "my name": ["who am i", "about me", "profile"],
        "my skills": ["skills", "expertise", "tech stack", "what am i good at"],
        "my projects": ["projects", "portfolio", "things i built", "my work"],
    }

    name_map = {
        "jia hui": ["I am", "my name is", "about me", "profile"],
    }

    for phrase, aliases in phrase_map.items():
        if phrase in q_lower:
            rewrites.extend(aliases)

    for name, aliases in name_map.items():
        if name in q_lower:
            rewrites.extend(aliases)

    # Keep order stable while removing duplicates.
    return list(dict.fromkeys(rewrites))


def smart_retrieve(query, vectorstore, k=5):
    queries = rewrite_query(query)
    seen = set()
    results = []

    for rewritten_query in queries:
        docs = smart_search(rewritten_query, vectorstore, k=k)
        for doc in docs:
            source = doc.metadata.get("source", "")
            doc_key = (source, doc.page_content)
            if doc_key in seen:
                continue
            seen.add(doc_key)
            results.append(doc)
            if len(results) >= k:
                return results

    return results[:k]


def find_relevant_notes(question, notes, top_n=5):
    keywords = [word.lower() for word in question.split() if len(word) > 3]
    scored = []

    for note in notes:
        search_text = (
            note["name"].lower()
            + " "
            + note["path"].lower()
            + " "
            + note["content"][:500].lower()
        )
        score = sum(1 for keyword in keywords if keyword in search_text)
        scored.append((score, note))

    scored.sort(key=lambda item: item[0], reverse=True)
    top_matches = [note for score, note in scored if score > 0][:top_n]

    if top_matches:
        return top_matches

    return [note for _, note in scored[:top_n]]


def retrieve_chunks(matched_notes, question, embeddings, splitter, k=8):
    documents = [
        Document(
            page_content=note["content"],
            metadata={"source": note["path"], "tags": infer_tags(note)},
        )
        for note in matched_notes
    ]
    chunks = splitter.split_documents(documents)
    store = FAISS.from_documents(chunks, embeddings)
    return smart_retrieve(question, store, k=k)
