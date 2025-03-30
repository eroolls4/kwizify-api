# kwizify-api

### Kwizify API

A FastAPI-based application for extracting keywords from files and generating quizzes, with database storage and NLP capabilities.

### Prerequisites

- ***Please make sure to have Python 3.12.X installed
- A PostgreSQL database (or adjust for your DB choice)
- Google API keys (if applicable, e.g., for AI services)
- Git (to clone the repository)


2. Set Up Virtual Environment
Create and activate a virtual environment:

```bash
"python -m venv .venv"
".\venv\Scripts\activate"  # On Windows
# source .venv/bin/activate  # On macOS/Linux
3. Install Dependencies
Install the required Python packages:

"pip install -r requirements.txt"
4. Initialize Alembic Migrations
Apply the database migrations from the alembic/ directory:

"alembic upgrade head"
5. Configure Environment
Set your Google API keys and database URL in core/config.py:

python
Copy
# core/config.py
class Settings:
    DATABASE_URL = "postgresql://your_user:your_password@localhost:5432/your_db"
    GOOGLE_API_KEY = "your-google-api-key"
    APP_TITLE = "Kwizify API"
    APP_DESCRIPTION = "NLP Keyword Extractor and Quiz Generator"
    APP_VERSION = "1.0.0"

settings = Settings()
Replace your_user, your_password, your_db, and your-google-api-key with your actual values.
Ensure your database is running and accessible.

6. Download spaCy Model
Install the English spaCy model required for NLP:

"python -m spacy download en_core_web_sm"
7. Run the Project
Start the FastAPI server:

"python .\main.py"

