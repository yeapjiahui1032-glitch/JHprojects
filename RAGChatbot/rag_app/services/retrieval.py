from langchain.schema import Document
from langchain_community.vectorstores import FAISS


TAG_KEYWORD_MAP = {
    "who am i": ["profile", "about", "personal", "identity"],
    "my name": ["profile", "about"],
    "my skills": ["skills", "expertise"],
    "my projects": ["projects", "portfolio"],
}


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


def smart_search(query: str, vectorstore, k=5):
    q_lower = query.lower()

    for keyword, tags in TAG_KEYWORD_MAP.items():
        if keyword in q_lower:
            def tag_filter(metadata):
                metadata_tags = metadata.get("tags", [])
                return any(tag in metadata_tags for tag in tags)

            docs = vectorstore.similarity_search(query, k=k, filter=tag_filter)
            if docs:
                return docs

    return vectorstore.similarity_search(query, k=k)


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
    return smart_search(question, store, k=k)
