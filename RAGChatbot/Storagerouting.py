import os
import base64
import requests
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_anthropic import ChatAnthropic
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
    return ChatAnthropic(
        api_key=st.secrets["ANTHROPIC_API_KEY"],
        model="claude-3-5-haiku-20241022"
    )

@st.cache_resource
def load_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
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
    """Cheap keyword match on filenames — no embedding cost"""
    keywords = [w.lower() for w in question.split() if len(w) > 3]
    scored   = []
    for note in notes:
        score = sum(1 for kw in keywords if kw in note["name"].lower() or kw in note["path"].lower())
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
    store   = Chroma.from_documents(chunks, embeddings, collection_name="temp_vault")
    results = store.as_retriever(search_kwargs={"k": 4}).invoke(question)
    store.delete_collection()
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
                    "You are a helpful assistant that answers questions using "
                    "the user's personal Obsidian notes. "
                    "Answer ONLY from the notes provided. "
                    "Mention the note name where relevant. "
                    "If the notes don't cover the question, say so clearly — "
                    "do not make up information."
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