from django.core.management.base import BaseCommand
from profiles.models import Professor, Department, Paper
import csv

class Command(BaseCommand):
    help = 'Export all professor profiles and their publications to a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default='professors_export.csv', help='Output CSV file path')

    def handle(self, *args, **options):
        output_path = options['output']
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Professor Name', 'Email', 'Affiliation', 'Department', 'Profile Link', 'Interests',
                'Paper Title', 'Paper Year', 'Paper URL', 'Paper Snippet'
            ])
            for professor in Professor.objects.select_related('department').prefetch_related('papers').all():
                for paper in professor.papers.all():
                    writer.writerow([
                        professor.name,
                        professor.email or '',
                        professor.affiliation or '',
                        professor.department.name if professor.department else '',
                        professor.profile_link or '',
                        professor.interests or '',
                        paper.title,
                        paper.publication_year or '',
                        paper.url or '',
                        paper.snippet or ''
                    ])
                if not professor.papers.exists():
                    writer.writerow([
                        professor.name,
                        professor.email or '',
                        professor.affiliation or '',
                        professor.department.name if professor.department else '',
                        professor.profile_link or '',
                        professor.interests or '',
                        '', '', '', ''
                    ])
        self.stdout.write(self.style.SUCCESS(f'Exported professor data to {output_path}'))
