import os
import base64
import requests
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.schema import Document

# ================================================================
#  CACHED RESOURCES — loaded ONCE per session, never re-downloaded
# ================================================================

@st.cache_resource
def load_embeddings():
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

@st.cache_resource
def load_llm():
    return ChatGroq(
        api_key=st.secrets["GROQ_API_KEY"],
        model="llama-3.3-70b-versatile"
    )

@st.cache_resource
def load_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )

# ================================================================
#  FETCH VAULT — cached for 5 minutes, re-fetches on manual refresh
# ================================================================

@st.cache_data(ttl=300)
def fetch_vault_from_github():
    token   = st.secrets["GITHUB_TOKEN"]
    repo    = st.secrets["GITHUB_REPO"]
    headers = {"Authorization": f"token {token}"}
    url     = f"https://api.github.com/repos/{repo}/git/trees/main?recursive=1"
    resp    = requests.get(url, headers=headers)

    if resp.status_code != 200:
        return [], f"GitHub error {resp.status_code}: {resp.json().get('message', 'Unknown error')}"

    tree     = resp.json().get("tree", [])
    md_files = [f for f in tree if f["path"].endswith(".md")]
    notes    = []

    for f in md_files:
        try:
            blob    = requests.get(f["url"], headers=headers).json()
            content = base64.b64decode(blob["content"]).decode("utf-8", errors="ignore")
            notes.append({
                "name":    os.path.basename(f["path"]),
                "path":    f["path"],
                "content": content
            })
        except Exception:
            continue

    return notes, None

# ================================================================
#  RETRIEVAL HELPERS
# ================================================================

def find_relevant_notes(question, notes, top_n=5):
    keywords = [w.lower() for w in question.split() if len(w) > 3]
    scored = []
    for note in notes:
        # Score on filename AND first 500 chars of content
        search_text = note["name"].lower() + " " + note["content"][:500].lower()
        score = sum(1 for kw in keywords if kw in search_text)
        scored.append((score, note))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [n for s, n in scored if s > 0][:top_n]
    return top if top else [n for _, n in scored[:top_n]]

def retrieve_chunks(matched_notes, question, embeddings, splitter):
    """Load matched notes, chunk, embed, retrieve top-k relevant chunks"""
    docs = [
        Document(page_content=n["content"], metadata={"source": n["name"]})
        for n in matched_notes
    ]
    chunks  = splitter.split_documents(docs)
    store = FAISS.from_documents(chunks, embeddings)
    results = store.as_retriever(search_kwargs={"k": 8}).invoke(question)
    return results

# ================================================================
#  STREAMLIT UI
# ================================================================

st.set_page_config(page_title="Obsidian RAG", page_icon="📓", layout="wide")

# Load heavy resources once (cached across reruns)
embeddings = load_embeddings()
llm        = load_llm()
splitter   = load_splitter()

# ── SIDEBAR ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("📓 Obsidian RAG")
    st.markdown("---")

    if st.button("🔄 Refresh vault from GitHub"):
        st.cache_data.clear()
        st.rerun()

    notes, error = fetch_vault_from_github()

    if error:
        st.error(f"❌ {error}")
        st.stop()
    elif notes:
        st.success(f"✅ {len(notes)} notes loaded")
        with st.expander("📂 View loaded notes"):
            for n in notes:
                st.text(f"• {n['name']}")
    else:
        st.warning("⚠️ No `.md` files found in repo")
        st.stop()

    st.markdown("---")
    st.caption("Notes refresh every 5 minutes automatically.")
    st.caption("Push to your vault repo to update notes.")

# ── MAIN CHAT AREA ────────────────────────────────────────────────
st.title("💬 Chat with your Obsidian Vault")

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.button("🗑️ Clear chat history"):
    st.session_state.messages = []
    st.rerun()

# Render existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg:
            st.caption(f"📓 Sources: {msg['sources']}")

# Handle new question
if prompt := st.chat_input("Ask anything about your notes..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching your vault..."):
            matched = find_relevant_notes(prompt, notes)
            results = retrieve_chunks(matched, prompt, embeddings, splitter)

        if not results:
            msg = "⚠️ No relevant content found in your notes for this question."
            st.warning(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})
        else:
            context = "\n\n---\n\n".join([d.page_content for d in results])
            sources = list(set([d.metadata.get("source", "") for d in results]))

            messages = [
                SystemMessage(content=(
                    "You are a precise assistant that answers questions ONLY using the notes provided below. "
                    "Rules you must follow:\n"
                    "1. Base your answer STRICTLY on the provided notes. Do not use outside knowledge.\n"
                    "2. If the notes do not contain enough information to answer, say exactly: "
                    "'I could not find this in your notes.' Do not guess or fill in gaps.\n"
                    "3. Always cite the note name (e.g. 'According to RAG-Chatbot.md...') for every claim.\n"
                    "4. Be concise and direct. Do not add commentary not found in the notes.\n"
                    "5. If the question is ambiguous, answer what the notes most closely support.\n"
                )),
                HumanMessage(content=f"My notes:\n\n{context}\n\nQuestion: {prompt}")
            ]

            answer = llm.invoke(messages).content
            st.markdown(answer)
            st.caption(f"📓 Sources: {', '.join(sources)}")

            st.session_state.messages.append({
                "role":    "assistant",
                "content": answer,
                "sources": ", ".join(sources)
            })