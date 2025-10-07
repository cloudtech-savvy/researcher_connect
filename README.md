# Research Connect Platform

A Django-based platform that connects young researchers (students) with senior researchers (professors), specifically focusing on professors from the specifica unversity who have published papers on Google Scholar.

## Features

- **Scrape/Fetch Professor Data:** Uses the `scholarly` package to fetch CUA professors' profiles and papers from Google Scholar.
- **Rich Metadata:** Stores and displays department, interests, papers, and more.
- **Department-Based Filtering:** Search and filter professors by department and research interests.
- **API Endpoints:** RESTful API for accessing professors, papers, and departments.
- **Browser Views:** User-friendly web interface for students to discover and connect with professors.
- **Live Google Scholar Data:** Fetches and displays live data from Google Scholar on professor detail pages.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd research_connect
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv base
   source base/Scripts/activate  # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # If needed, install scholarly specifically:
   pip install scholarly==1.7.11
   pip install djangorestframework
   ```

4. **Apply migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser (for admin access):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the platform:**
   - Professors list: [http://127.0.0.1:8000/professors/](http://127.0.0.1:8000/professors/)
   - Professor detail: [http://127.0.0.1:8000/professors/<id>/](http://127.0.0.1:8000/professors/1/)

## Usage

- **Add Departments and Professors:** Use the Django admin interface to add departments, professors, and papers.
- **Fetch Live Data:** On a professor's detail page, live data from Google Scholar will be displayed if a Google Scholar ID is provided.
- **Search:** Use the browser or API endpoints to search and filter professors by department or research interests.


## Optional: Use SerpAPI for Google results

You can use SerpAPI to fetch Google Scholar-like search results instead of (or alongside) `scholarly`.

1. Get an API key at https://serpapi.com/ and add it to your environment or the project's `.env` file:

```properties
SERPAPI_API_KEY="your_serpapi_api_key_here"
```

2. The project includes a small wrapper at `profiles/services/serp_api.py`. Example usage from Django code:

```python
from profiles.services.serp_api import SerpAPIClient

client = SerpAPIClient()
authors = client.search_scholar_authors("Computer Science Catholic University of America", num=10)
for a in authors:
   print(a['name'], a.get('affiliation'))
```

3. You can call this from views or a management command and persist results into the local models. Consider caching and respecting SerpAPI rate limits.


## License

This project is for academic and research purposes only.



