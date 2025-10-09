from django.core.management.base import BaseCommand
from profiles.services.serp_api import SerpAPIClient
from profiles.models import Professor, Department, Paper
from django.db import transaction
import pprint

class Command(BaseCommand):
    help = 'Fetch professor profiles from Google Scholar using SerpAPI and store them in the database.'

    def add_arguments(self, parser):
        parser.add_argument('--query', type=str, default='Catholic University of America', help='Search query for professors')
        parser.add_argument('--num', type=int, default=50, help='Number of professors to fetch')

    def handle(self, *args, **options):
        query = options['query']
        num = options['num']
        client = SerpAPIClient()
        self.stdout.write(self.style.NOTICE(f"Searching for professors with query: {query}"))
        authors = client.search_scholar_authors(query=query, num=num)
        pprint.pprint(authors)  # Print the raw author data to your terminal
        for author in authors:
            # Try to get the real full name from the author profile if available
            profile_link = author.get('profile_link')
            name = None
            university_names = [
                'The Catholic University of America',
                'THE CATHOLIC UNIVERSITY OF AMERICA',
                'Catholic University of America',
            ]
            def is_real_person(name):
                if not name:
                    return False
                n = name.strip()
                # Must not be a university name
                if n in university_names:
                    return False
                # Must not contain 'university', 'college', 'school', etc.
                lowered = n.lower()
                if any(word in lowered for word in ['university', 'college', 'school', 'institute', 'department', 'faculty', 'center', 'laboratory']):
                    return False
                # Must have at least two words (first and last name)
                if len(n.split()) < 2:
                    return False
                # Must not be all uppercase (likely not a real name)
                if n.isupper():
                    return False
                # Must not look like a publication title (long, with punctuation)
                if len(n) > 50 or any(p in n for p in [':', ',', ';', '(', ')', '–', '—', '"']):
                    return False
                return True

            if profile_link:
                author_profile = client.get_author_profile(profile_link)
                profile_info = author_profile.get('author', {})
                candidate_name = profile_info.get('name') or profile_info.get('author') or author.get('name') or author.get('author') or author.get('title')
                if is_real_person(candidate_name):
                    name = candidate_name.strip()
            if not name:
                candidate_name = author.get('name') or author.get('author') or author.get('title')
                if is_real_person(candidate_name):
                    name = candidate_name.strip()
            if not name:
                continue  # skip this entry, as it is not a real person
            # ...existing code...
            # Always fetch full author profile if profile_link is available
            if profile_link:
                # author_profile already fetched above
                profile_info = author_profile.get('author', {})
                affiliation = profile_info.get('affiliations') or author.get('affiliation')
                interests = ', '.join(profile_info.get('interests', [])) if profile_info.get('interests') else ''
                profile_photo = profile_info.get('thumbnail') or profile_info.get('profile_picture') or None
                citations = profile_info.get('cited_by', {}).get('value') if profile_info.get('cited_by') else None
                h_index = profile_info.get('h_index') if 'h_index' in profile_info else None
                i10_index = profile_info.get('i10_index') if 'i10_index' in profile_info else None
                snippet = author.get('snippet')
            else:
                affiliation = author.get('affiliation')
                interests = ''
                profile_photo = author.get('raw', {}).get('thumbnail') or author.get('raw', {}).get('profile_photo')
                citations = author.get('raw', {}).get('cited_by', {}).get('value') if author.get('raw', {}).get('cited_by') else None
                h_index = author.get('raw', {}).get('h_index') if 'h_index' in author.get('raw', {}) else None
                i10_index = author.get('raw', {}).get('i10_index') if 'i10_index' in author.get('raw', {}) else None
                snippet = author.get('snippet')
            # Try to extract department from affiliation or snippet
            department_name = None
            if affiliation:
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
                        'profile_photo': profile_photo,
                        'citations': citations,
                        'h_index': h_index,
                        'i10_index': i10_index,
                        'interests': interests,
                    }
                )
                if not created:
                    professor.affiliation = affiliation
                    professor.profile_link = profile_link
                    professor.snippet = snippet
                    professor.department = department
                    professor.profile_photo = profile_photo
                    professor.citations = citations
                    professor.h_index = h_index
                    professor.i10_index = i10_index
                    professor.interests = interests
                    professor.save()
                # Fetch and save all publications from author profile if available
                publications = []
                if profile_link and author_profile:
                    # Try to get publications from author profile response
                    pubs_block = author_profile.get('articles') or author_profile.get('publications') or []
                    for pub in pubs_block:
                        title = pub.get('title')
                        year = pub.get('year')
                        link = pub.get('link')
                        snippet = pub.get('snippet') or pub.get('description')
                        citation_count = pub.get('cited_by', {}).get('value') if pub.get('cited_by') else None
                        authors = pub.get('authors') if 'authors' in pub else None
                        journal = pub.get('publication') or pub.get('journal') or None
                        Paper.objects.get_or_create(
                            title=title or 'Untitled',
                            professor=professor,
                            defaults={
                                'abstract': snippet or '',
                                'publication_year': year,
                                'url': link,
                                'snippet': snippet,
                                'citation_count': citation_count,
                                'authors': authors,
                                'journal': journal,
                            }
                        )
                else:
                    # fallback: use publications from search_author_publications
                    publications = client.search_author_publications(name, profile_link=profile_link, num=20)
                    for pub in publications:
                        raw_pub = pub.get('raw', {})
                        Paper.objects.get_or_create(
                            title=pub.get('title', 'Untitled'),
                            professor=professor,
                            defaults={
                                'abstract': pub.get('snippet') or '',
                                'publication_year': pub.get('year'),
                                'url': pub.get('link'),
                                'snippet': pub.get('snippet'),
                                'citation_count': raw_pub.get('cited_by', {}).get('value') if raw_pub.get('cited_by') else None,
                                'authors': raw_pub.get('authors') if 'authors' in raw_pub else None,
                                'journal': raw_pub.get('publication') or raw_pub.get('journal') or None,
                            }
                        )
        self.stdout.write(self.style.SUCCESS('Finished importing professor profiles and publications.'))
