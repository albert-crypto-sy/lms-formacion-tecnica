# LMS Tecnico Industrial para Streamlit

## Local
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

## Streamlit Community Cloud
1. Crea un repositorio GitHub y sube esta carpeta.
2. No subas `.streamlit/secrets.toml`.
3. En Community Cloud pulsa Create app, elige repositorio, rama y `app.py`.
4. En Advanced settings > Secrets pega las claves del ejemplo, usando la URL final en APP_URL.
5. Pulsa Deploy.

## Nota de persistencia
SQLite y los uploads locales pueden perderse en un reinicio o redespliegue de Community Cloud. Para produccion migra a PostgreSQL/Supabase y almacenamiento de objetos. La app permite descargar la base SQLite desde Configuracion.
