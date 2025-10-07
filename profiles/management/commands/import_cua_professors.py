from django.core.management.base import BaseCommand
from profiles.services.serp_api import SerpAPIClient
from profiles.models import Department, Professor, Paper
from django.db import transaction
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import professors from SerpAPI for Catholic University of America by department.'

    def add_arguments(self, parser):
        parser.add_argument('--department', type=str, help='Department name to search (optional). If omitted, will ask to run for each Department in DB.', default=None)
        parser.add_argument('--limit', type=int, help='Max number of authors to fetch per department', default=20)
        parser.add_argument('--delay', type=float, help='Seconds to wait between API calls', default=1.0)
        parser.add_argument('--dry-run', action='store_true', help='Do not write to the database')

    def handle(self, *args, **options):
        dept_name = options.get('department')
        limit = options.get('limit')
        delay = options.get('delay')
        dry_run = options.get('dry_run')

        client = SerpAPIClient()

        if dept_name:
            departments = [Department.objects.get_or_create(name=dept_name)[0]]
        else:
            departments = Department.objects.all()

        for dept in departments:
            query = f"{dept.name} Catholic University of America"
            self.stdout.write(f"Searching authors for: {query} (limit={limit})")
            try:
                authors = client.search_scholar_authors(query=query, num=limit)
            except Exception as e:
                self.stderr.write(f"Search failed for {dept.name}: {e}")
                continue

            for a in authors:
                name = a.get('name') or None
                affiliation = a.get('affiliation') or None
                profile_link = a.get('profile_link') or a.get('link') or None
                snippet = a.get('snippet') or ''

                if not name:
                    continue

                # Skip obvious institutional or page results
                lowname = name.lower()
                if any(tok in lowname for tok in ('university', 'department', 'catholic', 'faculty', 'program', 'project')):
                    # likely an institution or page, skip
                    self.stdout.write(self.style.NOTICE(f"Skipping non-person result: {name}"))
                    continue

                # prefer results with profile links or with human-like names (two words)
                name_parts = [p for p in name.split() if p]
                human_like = len(name_parts) >= 2
                if not profile_link and not human_like:
                    self.stdout.write(self.style.NOTICE(f"Skipping low-confidence result: {name}"))
                    continue

                # basic dedupe by name + department
                exists = Professor.objects.filter(name__iexact=name, department=dept).exists()
                if exists:
                    self.stdout.write(self.style.NOTICE(f"Skipping existing professor: {name} (dept={dept.name})"))
                    continue

                if dry_run:
                    self.stdout.write(self.style.SUCCESS(f"Would create Professor: {name} (dept={dept.name})"))
                else:
                    with transaction.atomic():
                        prof = Professor.objects.create(
                            name=name,
                            email=None,
                            department=dept,
                            interests=snippet,
                            google_scholar_id=profile_link,
                        )

                        # Create papers if the raw field contains publications
                        raw = a.get('raw') or {}
                        pubs = []
                        # try multiple possible keys
                        for k in ('publications', 'publication_results', 'scholar_results', 'organic_results'):
                            blk = raw.get(k) or []
                            if isinstance(blk, list) and blk:
                                pubs = blk
                                break

                        for p in pubs[:5]:
                            title = p.get('title') or p.get('publication') or p.get('name')
                            year = p.get('year') or p.get('publication_year') or None
                            url = p.get('link') or p.get('url') or p.get('pub_url')
                            abstract = p.get('snippet') or p.get('description') or ''
                            if title:
                                Paper.objects.create(
                                    title=title,
                                    abstract=abstract or '',
                                    publication_year=year,
                                    professor=prof,
                                    url=url,
                                )
                        self.stdout.write(self.style.SUCCESS(f"Created Professor: {prof.name} (id={prof.id}) with up to {min(5,len(pubs))} papers"))

                time.sleep(delay)

        self.stdout.write(self.style.SUCCESS('Import finished.'))
