# Security Notes

This project is designed so it can be shared on Google Drive without exposing secrets.

## Secrets

- Real API keys belong only in a local `.env` file or the Streamlit password field.
- `.env` and `.streamlit/secrets.toml` are ignored by `.gitignore`.
- The app never prints the API key; it only shows a masked environment status in the sidebar placeholder.

## Uploaded Documents

- Uploaded files are stored in `data/uploads/`.
- `data/uploads/` is ignored because uploaded documents may contain private data.
- Remove private documents before zipping or uploading the project.

## Vector Database

- ChromaDB data is stored in `chroma_db/`.
- `chroma_db/` is ignored because embeddings and metadata can reveal information from uploaded documents.
- Rebuild the index locally after downloading the project.

## Guardrails

The system prompt requires the agent to:

- answer only from retrieved document or web evidence,
- cite sources,
- avoid invented citations or claims,
- say `I don't know based on the available sources.` when evidence is missing,
- refuse credential-exfiltration or unsafe requests.

