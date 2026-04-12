import os
import glob
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# ── CONFIG ──────────────────────────────────────────────────────
VAULT_PATH   = r"C:\Users\yeapj\OneDrive\Documents\Obsidian\claude-repo"  # ← change this
OLLAMA_MODEL = "llama3"
TOP_N_FILES  = 5

splitter   = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n## ", "\n### ", "\n\n", "\n", " "]
)
embeddings = OllamaEmbeddings(model=OLLAMA_MODEL)
llm        = ChatOllama(model=OLLAMA_MODEL)

# ── STEP 1: Scan vault filenames only (zero RAM cost) ────────────
def get_all_note_paths(vault_path):
    return glob.glob(os.path.join(vault_path, "**", "*.md"), recursive=True)

# ── STEP 2: Keyword match filenames to find relevant notes ───────
def find_relevant_files(question, all_paths, top_n=TOP_N_FILES):
    keywords = [w.lower() for w in question.split() if len(w) > 3]
    scored = []
    for path in all_paths:
        name   = os.path.basename(path).lower().replace(".md", "")
        folder = os.path.dirname(path).lower()
        score  = sum(1 for kw in keywords if kw in name or kw in folder)
        scored.append((score, path))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [p for s, p in scored if s > 0][:top_n]

    if not top:
        # fallback: most recently modified notes
        top = sorted(all_paths, key=os.path.getmtime, reverse=True)[:top_n]
        print(f"   No filename match — using {top_n} most recent notes")

    return top

# ── STEP 3: Read files → chunk → embed → retrieve ───────────────
def read_and_retrieve(file_paths, question):
    all_docs = []

    for path in file_paths:
        try:
            # Actually reads the file content here
            loader = TextLoader(path, encoding="utf-8")
            docs   = loader.load()
            all_docs.extend(docs)
            print(f"    Read: {os.path.basename(path)} ({len(docs[0].page_content)} chars)")
        except Exception as e:
            print(f"     Skipped {os.path.basename(path)}: {e}")

    if not all_docs:
        return []

    # Split content into chunks
    chunks = splitter.split_documents(all_docs)
    print(f"    {len(chunks)} chunks ready for retrieval")

    # Embed chunks into a temporary in-memory store
    temp_store = Chroma.from_documents(
        chunks,
        embeddings,
        collection_name="temp_session"
    )

    # Retrieve the most relevant chunks for the question
    retriever = temp_store.as_retriever(search_kwargs={"k": 4})
    results   = retriever.invoke(question)

    # Clean up temp store from memory
    temp_store.delete_collection()

    return results

# ── STEP 4: Build context and generate answer ────────────────────
def ask(question, all_paths):
    print(f"\n Scanning {len(all_paths)} filenames for: '{question}'")
    matched = find_relevant_files(question, all_paths)

    print(f"\n Loading {len(matched)} matched note(s):")
    for f in matched:
        print(f"   - {os.path.basename(f)}")

    # Read files and retrieve relevant chunks
    results = read_and_retrieve(matched, question)

    if not results:
        print("\n  Could not extract useful content from matched notes.\n")
        return

    # Build context string from retrieved chunks
    context = "\n\n---\n\n".join([doc.page_content for doc in results])

    # Show which notes the answer is drawn from
    sources = list(set([
        os.path.basename(doc.metadata.get("source", "unknown"))
        for doc in results
    ]))

    print(f"\n Generating answer from: {', '.join(sources)}\n")

    # Send to LLM
    messages = [
        SystemMessage(content=(
            "You are a helpful assistant. Answer the question using ONLY "
            "the Obsidian notes provided below as context. "
            "Quote the relevant note name when possible. "
            "If the notes don't contain enough info, say so clearly."
        )),
        HumanMessage(content=(
            f"My notes:\n\n{context}\n\n"
            f"Question: {question}"
        ))
    ]

    answer = llm.invoke(messages)

    print(f"📓 Sources used: {', '.join(sources)}")
    print(f"\n Answer:\n{answer.content}\n")
    print("─" * 60)

# ── STEP 5: Chat loop ────────────────────────────────────────────
all_paths = get_all_note_paths(VAULT_PATH)
print(f" Vault indexed: {len(all_paths)} notes found (filenames only)")
print(" Ask anything about your notes. Type 'exit' to quit.\n")

while True:
    q = input("You: ").strip()
    if q.lower() in ("exit", "quit", "q"):
        break
    if q:
        ask(q, all_paths)