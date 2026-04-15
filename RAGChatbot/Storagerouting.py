import streamlit as st

from rag_app.services.qa import answer_question, build_context, collect_sources
from rag_app.services.resources import load_embeddings, load_llm, load_splitter
from rag_app.services.retrieval import find_relevant_notes, retrieve_chunks
from rag_app.services.vault import fetch_vault_from_github


def build_note_tree_lines(notes):
    tree = {}
    for note in notes:
        parts = note["path"].split("/")
        node = tree
        for folder in parts[:-1]:
            node = node.setdefault(folder, {})
        node.setdefault("__files__", []).append(parts[-1])

    lines = []

    def walk(node, depth=0):
        for folder in sorted([key for key in node.keys() if key != "__files__"]):
            lines.append(f'{"  " * depth}- {folder}/')
            walk(node[folder], depth + 1)
        for filename in sorted(node.get("__files__", [])):
            lines.append(f'{"  " * depth}- {filename}')

    walk(tree)
    return lines


def group_notes_by_folder(notes):
    folders = {}
    for note in notes:
        path = note["path"]
        if "/" in path:
            folder, filename = path.rsplit("/", 1)
        else:
            folder, filename = "(root)", path
        folders.setdefault(folder, []).append(filename)

    for folder in folders:
        folders[folder] = sorted(folders[folder])
    return dict(sorted(folders.items(), key=lambda item: item[0].lower()))


def render_sidebar():
    with st.sidebar:
        st.title("Obsidian RAG")
        st.markdown("---")

        if st.button("Refresh vault from GitHub"):
            st.cache_data.clear()
            st.rerun()

        notes, error = fetch_vault_from_github()

        if error:
            st.error(error)
            st.stop()
        if not notes:
            st.warning("No `.md` files found in repo")
            st.stop()

        st.success(f"{len(notes)} notes loaded")
        with st.expander("View loaded notes (folder structure)"):
            tree_lines = build_note_tree_lines(notes)
            st.code("\n".join(tree_lines), language="text")

        with st.expander("Browse notes by folder"):
            folders = group_notes_by_folder(notes)
            selected_folder = st.selectbox("Folder", list(folders.keys()))
            st.caption(f"{len(folders[selected_folder])} files")
            for filename in folders[selected_folder]:
                st.text(f"- {filename}")

        st.markdown("---")
        st.caption("Notes refresh every 5 minutes automatically.")
        st.caption("Push to your vault repo to update notes.")

        return notes


def render_chat(notes, embeddings, llm, splitter):
    st.title("Chat with your Obsidian Vault")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.button("Clear chat history"):
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                st.caption(f"Sources: {message['sources']}")

    prompt = st.chat_input("Ask anything about your notes...")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching your vault..."):
            matched_notes = find_relevant_notes(prompt, notes)
            results = retrieve_chunks(matched_notes, prompt, embeddings, splitter)

        if not results:
            no_results_message = "No relevant content found in your notes for this question."
            st.warning(no_results_message)
            st.session_state.messages.append(
                {"role": "assistant", "content": no_results_message}
            )
            return

        context = build_context(results)
        sources = collect_sources(results)
        answer = answer_question(llm, prompt, context)

        st.markdown(answer)
        st.caption(f"Sources: {', '.join(sources)}")

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "sources": ", ".join(sources),
            }
        )


def main():
    st.set_page_config(page_title="Obsidian RAG", page_icon=":books:", layout="wide")

    embeddings = load_embeddings()
    llm = load_llm()
    splitter = load_splitter()

    notes = render_sidebar()
    render_chat(notes, embeddings, llm, splitter)


if __name__ == "__main__":
    main()
