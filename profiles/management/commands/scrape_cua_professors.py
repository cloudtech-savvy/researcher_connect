from django.core.management.base import BaseCommand
from django.conf import settings
from profiles.services.serp_api import SerpAPIClient
from profiles.models import Department, Professor, Paper
import os
import csv
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Scrape Google Scholar authors affiliated with Catholic University of America via SerpAPI"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50, help="Max number of author results to fetch")
        parser.add_argument("--csv", type=str, default="", help="Optional path to write CSV output")
        parser.add_argument("--department", type=str, default="Computer Science", help="Department name to assign")

    def handle(self, *args, **options):
        limit = options.get("limit")
        csv_path = options.get("csv")
        dept_name = options.get("department")

        api_key = os.environ.get("SERPAPI_API_KEY") or getattr(settings, "SERPAPI_API_KEY", None)
        client = SerpAPIClient(api_key=api_key)

        # Ensure department exists
        dept, _ = Department.objects.get_or_create(name=dept_name)

        query = 'Catholic University of America "Google Scholar" author'
        self.stdout.write(f"Searching SerpAPI for authors matching: {query}")

        authors = client.search_scholar_authors(query=query, num=limit)
        self.stdout.write(f"Found {len(authors)} potential authors (raw entries may include non-academics)")

        rows = []
        created = 0
        for a in authors:
            name = a.get("name") or ""
            profile_link = a.get("profile_link") or a.get("raw", {}).get("link")
            snippet = a.get("snippet") or ""

            if not name:
                continue

            prof_obj, was_created = Professor.objects.get_or_create(
                name=name, department=dept, defaults={"interests": snippet}
            )
            if was_created:
                created += 1

            # attempt to get publications
            pubs = []
            if profile_link:
                try:
                    prof_resp = client.get_author_profile(profile_link)
                    pubs = client.extract_publications(prof_resp)
                except Exception:
                    logger.exception("Failed to fetch/parse author profile: %s", profile_link)

            # persist publications
            for pub in pubs:
                title = (pub.get("title") or "").strip()
                if not title:
                    continue
                Paper.objects.get_or_create(
                    title=title,
                    professor=prof_obj,
                    defaults={
                        "abstract": pub.get("snippet") or "",
                        "publication_year": pub.get("year"),
                        "url": pub.get("link") or "",
                    },
                )

            rows.append({
                "name": name,
                "department": dept.name,
                "profile_link": profile_link or "",
                "snippet": snippet,
                "num_publications": len(pubs),
            })

        self.stdout.write(f"Created {created} new Professor records (department: {dept.name})")

        if csv_path:
            fieldnames = ["name", "department", "profile_link", "snippet", "num_publications"]
            try:
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for r in rows:
                        writer.writerow(r)
                self.stdout.write(f"Wrote CSV to {csv_path}")
            except Exception:
                logger.exception("Failed to write CSV %s", csv_path)

        self.stdout.write(self.style.SUCCESS("Scrape complete."))
