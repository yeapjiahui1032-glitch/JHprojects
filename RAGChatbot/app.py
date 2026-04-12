import streamlit as st
import os
import tempfile
from pathlib import Path

# LangChain imports with fallbacks
try:
    from langchain_community.document_loaders import TextLoader
except ImportError:
    try:
        from langchain_document_loaders import TextLoader
    except ImportError:
        st.error("Could not import TextLoader. Please check your LangChain installation.")
        st.stop()

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    st.error("Could not import RecursiveCharacterTextSplitter. Please install langchain-text-splitters.")
    st.stop()

try:
    from langchain_community.vectorstores import Chroma
except ImportError:
    st.error("Could not import Chroma. Please install langchain-community.")
    st.stop()

try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
except ImportError:
    st.error("Could not import OpenAI components. Please install langchain-openai.")
    st.stop()

try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    st.error("Could not import LangChain core messages. Please install langchain-core.")
    st.stop()

# Page config
st.set_page_config(page_title="RAG Chatbot", page_icon="📚", layout="wide")

# Check for OpenAI API key from secrets or user input
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    api_key_configured = True
except KeyError:
    api_key_configured = False
    openai_api_key = None

# Title
st.title("📚 RAG Chatbot with Document Q&A")
st.markdown("Upload your documents and ask questions about them!")

# API Key status
if api_key_configured:
    st.success("✅ OpenAI API key configured via secrets")
else:
    st.warning("⚠️ OpenAI API key not found in secrets. Please enter it below.")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # API Key input (only show if not configured via secrets)
    if not api_key_configured:
        openai_api_key = st.text_input("OpenAI API Key", type="password", help="Required for embeddings and chat")
        if openai_api_key:
            st.success("✅ API key entered")
        else:
            st.error("❌ Please enter your OpenAI API key")

    # Model selection
    embedding_model = st.selectbox("Embedding Model", ["text-embedding-3-small", "text-embedding-3-large"], index=0)
    chat_model = st.selectbox("Chat Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"], index=0)

    # Chunk settings
    chunk_size = st.slider("Chunk Size", min_value=200, max_value=2000, value=500, step=100)
    chunk_overlap = st.slider("Chunk Overlap", min_value=0, max_value=200, value=50, step=10)

# File upload section
st.header("📁 Upload Documents")
uploaded_files = st.file_uploader(
    "Upload your text/markdown files",
    type=["txt", "md", "pdf"],
    accept_multiple_files=True,
    help="Upload documents to create your knowledge base"
)

# Initialize session state
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Process uploaded files
if uploaded_files and openai_api_key:
    with st.spinner("Processing documents..."):
        try:
            # Create temporary directory for files
            with tempfile.TemporaryDirectory() as temp_dir:
                documents = []

                # Save uploaded files temporarily
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    # Load document
                    if uploaded_file.name.endswith(('.txt', '.md')):
                        loader = TextLoader(file_path)
                        docs = loader.load()
                        for doc in docs:
                            doc.metadata["source"] = uploaded_file.name
                        documents.extend(docs)

                if documents:
                    # Split documents
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
                    )
                    chunks = splitter.split_documents(documents)

                    # Create embeddings and vectorstore
                    embeddings = OpenAIEmbeddings(
                        model=embedding_model,
                        openai_api_key=openai_api_key
                    )

                    st.session_state.vectorstore = Chroma.from_documents(
                        chunks,
                        embeddings,
                        collection_name="uploaded_docs"
                    )

                    st.success(f"✅ Processed {len(documents)} documents into {len(chunks)} chunks!")

        except Exception as e:
            st.error(f"Error processing documents: {str(e)}")

# Chat interface
st.header("💬 Chat with your Documents")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    if not st.session_state.vectorstore:
        st.error("Please upload documents first!")
    elif not openai_api_key:
        if api_key_configured:
            st.error("API key configuration error. Please check your secrets.")
        else:
            st.error("Please enter your OpenAI API key in the sidebar!")
    else:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get relevant documents
        with st.spinner("Searching documents..."):
            retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 4})
            results = retriever.invoke(prompt)

        if not results:
            response = "I couldn't find any relevant information in your documents for that question."
        else:
            # Show sources
            sources = list(set([doc.metadata.get("source", "unknown") for doc in results]))
            context = "\n\n---\n\n".join([doc.page_content for doc in results])

            # Create chat completion
            llm = ChatOpenAI(
                model=chat_model,
                openai_api_key=openai_api_key,
                temperature=0.1
            )

            messages = [
                SystemMessage(content=(
                    "You are a helpful assistant that answers questions using the provided context. "
                    "Only use information from the context. If you can't answer based on the context, "
                    "say so clearly. Be concise but informative."
                )),
                HumanMessage(content=f"Context:\n{context}\n\nQuestion: {prompt}")
            ]

            response = llm.invoke(messages).content

            # Show sources
            with st.expander("📄 Sources"):
                st.write(f"Found information in: {', '.join(sources)}")

        # Add assistant response to history
        st.session_state.chat_history.append({"role": "assistant", "content": response})

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response)

# Footer
st.markdown("---")
st.markdown("Built with Streamlit, LangChain, and OpenAI")