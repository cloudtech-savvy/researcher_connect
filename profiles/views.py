
from django.shortcuts import render
from .models import Professor, Department, Paper

from django.http import HttpResponse

def scholar_search(request):
	import scholarly
	department = request.GET.get('department', '')
	keyword = request.GET.get('keyword', '')
	results = []
	error = None
	if department or keyword:
		query = f"{department} Catholic University of America {keyword}".strip()
		try:
			search = scholarly.search_author(query)
			for author in search:
				author_filled = scholarly.fill(author)
				author_data = {
					'name': author_filled.get('name'),
					'affiliation': author_filled.get('affiliation'),
					'interests': author_filled.get('interests'),
					'citedby': author_filled.get('citedby'),
					'publications': []
				}
				for pub in author_filled.get('publications', [])[:3]:
					pub_filled = scholarly.fill(pub)
					author_data['publications'].append({
						'title': pub_filled.get('bib', {}).get('title', ''),
						'year': pub_filled.get('bib', {}).get('pub_year', ''),
						'abstract': pub_filled.get('bib', {}).get('abstract', ''),
						'url': pub_filled.get('pub_url', '')
					})
				results.append(author_data)
		except Exception as e:
			error = str(e)
	departments = Department.objects.all()
	return render(request, 'profiles/scholar_search.html', {
		'results': results,
		'departments': departments,
		'selected_department': department,
		'keyword': keyword,
		'error': error
	})

def professor_list(request):
	department_id = request.GET.get('department')
	if department_id:
		professors = Professor.objects.filter(department_id=department_id)
	else:
		professors = Professor.objects.all()
	departments = Department.objects.all()
	return render(request, 'profiles/professor_list.html', {
		'professors': professors,
		'departments': departments,
		'selected_department': department_id
	})

def professor_detail(request, pk):
	import scholarly

	professor = Professor.objects.get(pk=pk)
	papers = professor.papers.all()

	# Fetch live data from Google Scholar if scholar_id is present
	scholar_data = None
	scholar_papers = []
	if professor.google_scholar_id:
		try:
			author = scholarly.search_author_id(professor.google_scholar_id)
			author_filled = scholarly.fill(author)
			scholar_data = {
				'name': author_filled.get('name'),
				'affiliation': author_filled.get('affiliation'),
				'interests': author_filled.get('interests'),
				'citedby': author_filled.get('citedby'),
			}
			for pub in author_filled.get('publications', [])[:5]:  # Limit to 5 for speed
				pub_filled = scholarly.fill(pub)
				scholar_papers.append({
					'title': pub_filled.get('bib', {}).get('title', ''),
					'year': pub_filled.get('bib', {}).get('pub_year', ''),
					'abstract': pub_filled.get('bib', {}).get('abstract', ''),
					'url': pub_filled.get('pub_url', '')
				})
		except Exception as e:
			scholar_data = {'error': str(e)}

	return render(request, 'profiles/professor_detail.html', {
		'professor': professor,
		'papers': papers,
		'scholar_data': scholar_data,
		'scholar_papers': scholar_papers
	})
