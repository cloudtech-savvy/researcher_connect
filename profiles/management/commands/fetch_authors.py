from django.core.management.base import BaseCommand, CommandError
from profiles.services.serp_api import SerpAPIClient
from profiles.models import Professor, Department

class Command(BaseCommand):
    help = 'Fetch authors from SerpAPI and optionally create Professor records.'

    def add_arguments(self, parser):
        parser.add_argument('--query', type=str, help='Search query for authors', required=True)
        parser.add_argument('--limit', type=int, help='Maximum number of authors to fetch', default=10)
        parser.add_argument('--department', type=str, help='Department name to assign to created Professors', default=None)
        parser.add_argument('--dry-run', action='store_true', help='Do not write changes to the database')

    def handle(self, *args, **options):
        query = options['query']
        limit = options['limit']
        dept_name = options.get('department')
        dry_run = options.get('dry_run', False)

        client = SerpAPIClient()
        authors = client.search_scholar_authors(query, num=limit)

        if not authors:
            self.stdout.write(self.style.WARNING('No authors found for query: %s' % query))
            return

        dept = None
        if dept_name:
            dept, _ = Department.objects.get_or_create(name=dept_name)

        created = 0
        for a in authors:
            name = a.get('name')
            email = None
            interests = a.get('snippet') or ''
            google_scholar_id = None

            if not name:
                continue

            exists = Professor.objects.filter(name__iexact=name).exists()
            if exists:
                self.stdout.write(self.style.NOTICE(f"Skipping existing professor: {name}"))
                continue

            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"Would create Professor: {name} (dept={dept_name})"))
            else:
                prof = Professor.objects.create(
                    name=name,
                    email=email,
                    department=dept if dept else Department.objects.first() or Department.objects.create(name='Uncategorized'),
                    interests=interests,
                    google_scholar_id=google_scholar_id,
                )
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created Professor: {prof.name} (id={prof.id})"))

        self.stdout.write(self.style.SUCCESS(f"Done. Created {created} new professors."))
