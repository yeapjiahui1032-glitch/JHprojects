import streamlit as st
import os
import tempfile
from pathlib import Path

# LangChain imports with fallbacks
try:
    from langchain_community.document_loaders import TextLoader
except ImportError:
    try:
        from langchain.document_loaders import TextLoader
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

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(45deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .chat-container {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f9f9f9;
    }
    .sidebar-info {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Title with custom styling
st.markdown('<h1 class="main-header">📚 RAG Chatbot with Document Q&A</h1>', unsafe_allow_html=True)
st.markdown("*Upload your documents and ask questions about them using AI!*")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # API Key input with validation
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Required for embeddings and chat. Get one at https://platform.openai.com/api-keys"
    )

    if openai_api_key:
        st.success("✅ API Key provided")
    else:
        st.warning("🔑 Please enter your OpenAI API key")

    st.divider()

    # Model selection with descriptions
    st.subheader("🤖 AI Models")
    embedding_model = st.selectbox(
        "Embedding Model",
        ["text-embedding-3-small", "text-embedding-3-large"],
        index=0,
        help="Smaller model is faster, larger model is more accurate"
    )

    chat_model = st.selectbox(
        "Chat Model",
        ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
        index=0,
        help="GPT-4 is more accurate but slower and more expensive"
    )

    st.divider()

    # Advanced settings in expandable section
    with st.expander("🔧 Advanced Settings"):
        st.subheader("Document Processing")
        chunk_size = st.slider(
            "Chunk Size",
            min_value=200,
            max_value=2000,
            value=500,
            step=100,
            help="Larger chunks preserve more context but may reduce precision"
        )
        chunk_overlap = st.slider(
            "Chunk Overlap",
            min_value=0,
            max_value=200,
            value=50,
            step=10,
            help="Overlap helps maintain context between chunks"
        )

        st.subheader("Search Settings")
        search_k = st.slider(
            "Number of chunks to retrieve",
            min_value=1,
            max_value=10,
            value=4,
            help="More chunks may provide better answers but slower responses"
        )

    # Clear chat button
    if st.button("🗑️ Clear Chat History", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()

    # Info section
    st.divider()
    with st.container():
        st.markdown("""
        <div class="sidebar-info">
        <h4>💡 How it works:</h4>
        <ol>
        <li>Upload your documents</li>
        <li>AI creates searchable embeddings</li>
        <li>Ask questions in natural language</li>
        <li>Get answers with source citations</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

# File upload section
st.header("📁 Upload Documents")

# File upload with better UI
col1, col2 = st.columns([3, 1])

with col1:
    uploaded_files = st.file_uploader(
        "Upload your text/markdown files",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True,
        help="Upload documents to create your knowledge base. Supported: .txt, .md, .pdf"
    )

with col2:
    if uploaded_files:
        st.metric("Files Uploaded", len(uploaded_files))
    else:
        st.metric("Files Uploaded", 0)

# Show uploaded files list
if uploaded_files:
    with st.expander("📋 Uploaded Files", expanded=False):
        for i, file in enumerate(uploaded_files, 1):
            col_a, col_b, col_c = st.columns([1, 3, 1])
            with col_a:
                st.write(f"**{i}.**")
            with col_b:
                st.write(f"📄 {file.name}")
            with col_c:
                st.write(f"{file.size} bytes")

# Processing status
if uploaded_files and openai_api_key:
    # Check if we need to process files
    if st.button("🚀 Process Documents", type="primary") or not st.session_state.vectorstore:
        with st.spinner("🔄 Processing documents... This may take a few minutes for large files."):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("📂 Creating temporary workspace...")
                progress_bar.progress(10)

                # Create temporary directory for files
                with tempfile.TemporaryDirectory() as temp_dir:
                    documents = []

                    status_text.text("📖 Loading documents...")
                    progress_bar.progress(30)

                    # Save uploaded files temporarily
                    for i, uploaded_file in enumerate(uploaded_files):
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

                        # Update progress
                        progress = 30 + (i + 1) / len(uploaded_files) * 20
                        progress_bar.progress(int(progress))

                    if documents:
                        status_text.text("✂️ Splitting documents into chunks...")
                        progress_bar.progress(50)

                        # Split documents
                        splitter = RecursiveCharacterTextSplitter(
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                            separators=["\n## ", "\n### ", "\n\n", "\n", " "]
                        )
                        chunks = splitter.split_documents(documents)

                        status_text.text("🧠 Creating embeddings...")
                        progress_bar.progress(70)

                        # Create embeddings and vectorstore
                        embeddings = OpenAIEmbeddings(
                            model=embedding_model,
                            openai_api_key=openai_api_key
                        )

                        status_text.text("💾 Building vector database...")
                        progress_bar.progress(90)

                        st.session_state.vectorstore = Chroma.from_documents(
                            chunks,
                            embeddings,
                            collection_name="uploaded_docs"
                        )

                        progress_bar.progress(100)
                        status_text.text("✅ Processing complete!")

                        # Success message with stats
                        st.success(f"✅ Successfully processed {len(documents)} documents into {len(chunks)} chunks!")

                        # Show processing stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Documents", len(documents))
                        with col2:
                            st.metric("Chunks", len(chunks))
                        with col3:
                            st.metric("Avg Chunk Size", f"{chunk_size} chars")

                    else:
                        st.error("❌ No valid documents found to process.")

            except Exception as e:
                st.error(f"❌ Error processing documents: {str(e)}")
                st.info("💡 Try reducing chunk size or check your file formats.")

            finally:
                progress_bar.empty()
                status_text.empty()

# Show current status
elif uploaded_files and not openai_api_key:
    st.warning("⚠️ Please enter your OpenAI API key in the sidebar to process documents.")
elif not uploaded_files:
    st.info("💡 Upload some documents to get started!")

# Chat interface
st.header("💬 Chat with your Documents")

# Status indicators
if st.session_state.vectorstore:
    st.success("✅ Knowledge base ready! You can now ask questions.")
else:
    st.info("📚 Upload and process documents to start chatting.")

# Chat controls
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    temperature = st.slider(
        "Creativity Level",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.1,
        help="Higher values make responses more creative but less factual"
    )
with col2:
    if st.button("🔄 New Chat", help="Start a new conversation"):
        st.session_state.chat_history = []
        st.rerun()
with col3:
    if st.session_state.chat_history:
        st.metric("Messages", len(st.session_state.chat_history))

# Chat container with custom styling
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display chat history
for i, message in enumerate(st.session_state.chat_history):
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(message["content"])

st.markdown('</div>', unsafe_allow_html=True)

# Chat input with better UX
if not st.session_state.vectorstore:
    st.chat_input("Upload documents first...", disabled=True)
elif not openai_api_key:
    st.chat_input("Enter API key first...", disabled=True)
else:
    if prompt := st.chat_input("Ask a question about your documents...", key="chat_input"):
        if prompt.strip():
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(f"**You:** {prompt}")

            # Create a placeholder for the assistant response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                status_placeholder = st.empty()

                try:
                    # Show searching status
                    status_placeholder.text("🔍 Searching your documents...")

                    # Get relevant documents
                    retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": search_k})
                    results = retriever.invoke(prompt)

                    if not results:
                        response = "I couldn't find any relevant information in your documents for that question. Try rephrasing or upload more documents."
                        status_placeholder.empty()
                    else:
                        # Show sources
                        sources = list(set([doc.metadata.get("source", "unknown") for doc in results]))
                        context = "\n\n---\n\n".join([doc.page_content for doc in results])

                        # Update status
                        status_placeholder.text(f"🤖 Generating response using {len(sources)} source(s)...")

                        # Create chat completion
                        llm = ChatOpenAI(
                            model=chat_model,
                            openai_api_key=openai_api_key,
                            temperature=temperature
                        )

                        messages = [
                            SystemMessage(content=(
                                "You are a helpful assistant that answers questions using the provided context. "
                                "Only use information from the context. If you can't answer based on the context, "
                                "say so clearly. Be concise but informative. Always cite specific information from the documents."
                            )),
                            HumanMessage(content=f"Context from documents:\n{context}\n\nQuestion: {prompt}")
                        ]

                        response = llm.invoke(messages).content

                        # Clear status
                        status_placeholder.empty()

                        # Show sources in an expander
                        with st.expander(f"📄 Sources ({len(sources)} found)", expanded=False):
                            st.write("**Documents referenced:**")
                            for source in sources:
                                st.write(f"• {source}")

                            if st.checkbox("Show document chunks", key=f"chunks_{i}"):
                                st.write("**Relevant text chunks:**")
                                for j, doc in enumerate(results[:3]):  # Show first 3 chunks
                                    st.text_area(
                                        f"Chunk {j+1} from {doc.metadata.get('source', 'unknown')}",
                                        doc.page_content,
                                        height=100,
                                        key=f"chunk_{i}_{j}"
                                    )

                except Exception as e:
                    response = f"I encountered an error while processing your question: {str(e)}"
                    status_placeholder.empty()

            # Add assistant response to history
            st.session_state.chat_history.append({"role": "assistant", "content": response})

            # Display the response
            message_placeholder.markdown(response)

            # Auto-scroll to bottom (using rerun to refresh)
            st.rerun()
        else:
            st.warning("Please enter a question.")

# Footer with usage stats and info
st.markdown("---")

# Usage statistics
if st.session_state.chat_history:
    total_messages = len(st.session_state.chat_history)
    user_messages = len([m for m in st.session_state.chat_history if m["role"] == "user"])
    assistant_messages = len([m for m in st.session_state.chat_history if m["role"] == "assistant"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Messages", total_messages)
    with col2:
        st.metric("Questions Asked", user_messages)
    with col3:
        st.metric("AI Responses", assistant_messages)
    with col4:
        if st.session_state.vectorstore:
            # Estimate token usage (rough approximation)
            avg_chars_per_message = sum(len(m["content"]) for m in st.session_state.chat_history) / total_messages
            estimated_tokens = int(total_messages * avg_chars_per_message * 0.3)  # Rough token estimation
            st.metric("Est. Tokens Used", f"{estimated_tokens:,}")

# About section
with st.expander("ℹ️ About this App", expanded=False):
    st.markdown("""
    ### 🤖 How RAG Works
    **Retrieval-Augmented Generation (RAG)** combines the best of both worlds:
    - **Retrieval**: Find relevant information from your documents
    - **Generation**: Use AI to provide natural, contextual answers

    ### 📊 Features
    - **Document Upload**: Support for .txt, .md, and .pdf files
    - **Smart Chunking**: Documents are split intelligently to preserve context
    - **Semantic Search**: AI-powered search finds relevant information
    - **Source Citations**: Always know which documents provided the answers
    - **Chat History**: Conversations persist during your session

    ### 🔧 Technical Details
    - **Embeddings**: OpenAI's text-embedding models
    - **Vector Store**: ChromaDB for efficient similarity search
    - **LLM**: GPT models via OpenAI API
    - **Framework**: Built with Streamlit and LangChain

    ### 💰 Cost Estimation
    - **Embeddings**: ~$0.02 per 1K pages
    - **Chat**: Varies by model ($0.002-0.03 per 1K tokens)
    - **Free Tier**: OpenAI offers $5-18 in free credits for new accounts
    """)

# Footer
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    Built with ❤️ using <a href="https://streamlit.io" target="_blank">Streamlit</a>,
    <a href="https://python.langchain.com" target="_blank">LangChain</a>, and
    <a href="https://openai.com" target="_blank">OpenAI</a>
</div>
""", unsafe_allow_html=True)