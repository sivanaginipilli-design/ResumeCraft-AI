# ResumeCraft AI

A Streamlit resume builder inspired by the supplied three-panel reference:
- Left: seven-step resume workflow
- Center: searchable template gallery with categories and grid/list views
- Right: live resume preview and PDF download

## Features
- 15 selectable resume designs across Professional, Creative and Simple categories
- Seven-step resume form
- Preview refreshes when a step is saved
- Template changes preserve entered resume information
- PDF export
- Optional Groq-powered writing assistant
- Manual resume building works without an AI key

## Run locally
```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

## Configure AI
Create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_groq_api_key"
```
Never commit your real secrets file to GitHub. The `.gitignore` excludes it.

## Deploy
Push `app.py`, `requirements.txt`, `README.md` and `.gitignore` to GitHub. Deploy the repository using Streamlit Community Cloud and add `GROQ_API_KEY` under the app's Secrets settings.

## Important
This starter version keeps data in Streamlit session state. It does not yet provide accounts or permanent database storage. Add secure authentication and persistent storage before using it as a multi-user production service. PDF output uses a clean, color-matched document layout; exact pixel-level matching between browser preview and PDF can be refined in a later iteration.
