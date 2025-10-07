from django.core.management.base import BaseCommand
from profiles.services.serp_api import SerpAPIClient
from profiles.models import Professor, Department, Paper
from django.db import transaction

class Command(BaseCommand):
    help = 'Fetch professor profiles from Google Scholar using SerpAPI and store them in the database.'

    def add_arguments(self, parser):
        parser.add_argument('--query', type=str, default='Catholic University of America', help='Search query for professors')
        parser.add_argument('--num', type=int, default=10, help='Number of professors to fetch')

    def handle(self, *args, **options):
        query = options['query']
        num = options['num']
        client = SerpAPIClient()
        self.stdout.write(self.style.NOTICE(f"Searching for professors with query: {query}"))
        authors = client.search_scholar_authors(query=query, num=num)
        for author in authors:
            name = author.get('name')
            affiliation = author.get('affiliation')
            profile_link = author.get('profile_link')
            snippet = author.get('snippet')
            # Try to extract department from affiliation or snippet
            department_name = None
            if affiliation:
                # crude guess: department is first part before comma
                department_name = affiliation.split(',')[0].strip()
            elif snippet:
                department_name = snippet.split(',')[0].strip()
            if not department_name:
                department_name = 'Unknown'
            department, _ = Department.objects.get_or_create(name=department_name)
            with transaction.atomic():
                professor, created = Professor.objects.get_or_create(
                    name=name,
                    defaults={
                        'affiliation': affiliation,
                        'profile_link': profile_link,
                        'snippet': snippet,
                        'department': department,
                    }
                )
                if not created:
                    professor.affiliation = affiliation
                    professor.profile_link = profile_link
                    professor.snippet = snippet
                    professor.department = department
                    professor.save()
                # Fetch and save publications
                publications = client.search_author_publications(name, profile_link=profile_link, num=20)
                for pub in publications:
                    Paper.objects.get_or_create(
                        title=pub.get('title', 'Untitled'),
                        professor=professor,
                        defaults={
                            'abstract': pub.get('snippet'),
                            'publication_year': pub.get('year'),
                            'url': pub.get('link'),
                            'snippet': pub.get('snippet'),
                        }
                    )
        self.stdout.write(self.style.SUCCESS('Finished importing professor profiles and publications.'))
