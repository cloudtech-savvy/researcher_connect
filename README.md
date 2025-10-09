# Research Connect Platform

A Django-based platform that connects young researchers (students) with senior researchers (professors), who have published papers on Google Scholar.

**Now supports Google Scholar data import via SerpAPI, including author ID extraction and robust CSV export.**

## Features

- **Fetch Professor Data:** Uses SerpAPI to fetch university professors' profiles and papers from Google Scholar.
- **Author ID Extraction:** Management command to extract Google Scholar author IDs for accurate data import.
- **Rich Metadata:** Stores and displays department, interests, papers, and more.
- **Department-Based Filtering:** Search and filter professors by department and research interests.
- **API Endpoints:** RESTful API for accessing professors, papers, and departments.
- **Browser Views:** User-friendly web interface for students to discover and connect with professors.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cloudtech-savvy/researcher_connect.git
   cd researcher_connect
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv base
   source base/bin/activate  # On Linux/Mac
   # or
   base\Scripts\activate  # On Windows
   ```
## Importing Google Scholar Data with SerpAPI

1. **Set your SerpAPI API key:**
   - Get an API key at https://serpapi.com/
   - Add it to your environment or `.env` file:
     ```properties
     SERPAPI_API_KEY="your_serpapi_api_key_here"
     ```

2. **Extract Google Scholar author IDs:**
   
   - Use specific professor names or departments for best results.

3. **Import full author profiles by ID:**
   - Update your import script or use the provided method to fetch by author ID for accurate data.

4. **Export data to CSV:**
   - Export all professor and publication data:
     ```bash
     python manage.py export_professors
     ```

## GitHub Authentication for Push

GitHub now requires a personal access token (PAT) for git push:
1. Generate a token at https://github.com/settings/tokens (classic), with repo permissions.
2. Use your GitHub username and paste the token when prompted for a password.

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
## License

This project is for academic and research purposes only.



