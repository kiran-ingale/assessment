# Sample Notes: Personalized AI Research Agent

This sample document exists so the app has something to retrieve before the user uploads files.

The research agent has five required parts:

- System prompt: Defines the assistant's role, source-use rules, citation expectations, and refusal behavior.
- Memory: Preserves the conversation history for the current Streamlit session so follow-up questions have context.
- RAG: Uses ChromaDB as a vector database over uploaded documents and this sample knowledge base.
- Tool calling: Exposes document retrieval and optional web search as tools that the language model can call.
- Guardrails: Requires the assistant to say "I don't know based on the available sources." when evidence is missing.

For safe sharing, API keys should be stored in a local `.env` file or entered in the Streamlit sidebar. The real `.env` file, uploaded documents, and Chroma database should not be uploaded publicly.

