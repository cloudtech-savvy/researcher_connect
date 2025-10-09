import os
import csv
from django.core.management.base import BaseCommand
from profiles.models import Professor, Paper

class Command(BaseCommand):
    help = 'Export all professor profiles and their publications to a CSV file in the data/ folder.'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default='data/professors_export.csv', help='Output CSV file path')

    def handle(self, *args, **options):
        output_path = options['output']
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as csv_out:
            writer = csv.writer(csv_out)
            writer.writerow([
                'Professor Name', 'University Name', 'Email', 'Affiliation', 'Department', 'Profile Link', 'Profile Photo', 'Interests', 'Citations', 'h-index', 'i10-index',
                'Paper Title', 'Paper Year', 'Paper URL', 'Paper Snippet', 'Paper Citation Count', 'Paper Authors', 'Paper Journal'
            ])
            for professor in Professor.objects.select_related('department').prefetch_related('papers').all():
                for paper in professor.papers.all():
                    writer.writerow([
                        professor.name,
                        'Catholic University of America',
                        professor.email or '',
                        professor.affiliation or '',
                        professor.department.name if professor.department else '',
                        professor.profile_link or '',
                        professor.profile_photo or '',
                        professor.interests or '',
                        professor.citations or '',
                        professor.h_index or '',
                        professor.i10_index or '',
                        paper.title,
                        paper.publication_year or '',
                        paper.url or '',
                        paper.snippet or '',
                        paper.citation_count or '',
                        paper.authors or '',
                        paper.journal or ''
                    ])
                if not professor.papers.exists():
                    writer.writerow([
                        professor.name,
                        'Catholic University of America',
                        professor.email or '',
                        professor.affiliation or '',
                        professor.department.name if professor.department else '',
                        professor.profile_link or '',
                        professor.profile_photo or '',
                        professor.interests or '',
                        professor.citations or '',
                        professor.h_index or '',
                        professor.i10_index or '',
                        '', '', '', '', '', '', ''
                    ])
        self.stdout.write(self.style.SUCCESS(f'Exported professor data to {output_path}'))
