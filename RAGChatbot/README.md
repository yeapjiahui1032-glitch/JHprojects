Obsidian RAG Chatbot
A Streamlit chatbot that answers questions from your Obsidian vault using Claude AI.

Project Structure
text
your-app-repo/
├── app.py
├── requirements.txt
└── README.md
Streamlit Secrets
In Streamlit Cloud dashboard → App settings → Secrets, add:

text
ANTHROPIC_API_KEY = "sk-ant-xxxxxxxxxxxxxxxxxxxx"
GITHUB_TOKEN      = "ghp_xxxxxxxxxxxxxxxxxxxx"
GITHUB_REPO       = "your-username/your-obsidian-vault-repo"
Deploy Steps
Push app.py + requirements.txt to a GitHub repo (your APP repo)

Go to https://share.streamlit.io → New app

Select your app repo, set main file as app.py

Add the secrets above in Advanced settings

Click Deploy

Obsidian Git Setup (auto-sync vault to GitHub)
Install Obsidian Git plugin in Obsidian

Create a separate private GitHub repo for your vault

Connect Obsidian Git to that vault repo

Set auto-commit interval (e.g. every 10 minutes)

Use "Refresh vault" button in the sidebar after pushing new notes

How It Works
Fetches all .md files from your GitHub vault repo (cached 5 min)

Keyword-matches filenames to find relevant notes for your question

Chunks and embeds matched notes using sentence-transformers/all-MiniLM-L6-v2

Retrieves top-4 most relevant chunks via Chroma vector search

Sends chunks as context to Claude Haiku to generate a grounded answer

Temp vector store deleted after each question to save RAM