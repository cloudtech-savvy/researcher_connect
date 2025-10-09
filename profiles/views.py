from django.core.paginator import Paginator

def professor_search(request):
	department = request.GET.get('department', '')
	professors = Professor.objects.all()
	if department:
		professors = professors.filter(department__name__icontains=department)
	professors = professors.select_related('department')
	paginator = Paginator(professors, 20)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	return render(request, 'profiles/professor_search.html', {
		'professors': page_obj,
	})

def professor_detail(request, pk):
	professor = get_object_or_404(Professor.objects.select_related('department').prefetch_related('papers'), pk=pk)
	return render(request, 'profiles/professor_detail.html', {
		'professor': professor,
	})
from django.shortcuts import render, get_object_or_404
from .models import Professor, Department, Paper
from profiles.services.serp_api import SerpAPIClient
import logging
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.utils.html import escape

logger = logging.getLogger(__name__)


def scholar_search(request):
	"""Search for authors using SerpAPI and render results.

	Query params:
	  - department: department name (optional)
	  - keyword: additional keywords (optional)
	"""
	department = request.GET.get('department', '')
	keyword = request.GET.get('keyword', '')
	results = []
	error = None

	if department or keyword:
		query = f"{department} Catholic University of America {keyword}".strip()
		client = SerpAPIClient()
		try:
			results = client.search_scholar_authors(query=query, num=10)
		except Exception as e:
			logger.exception("SerpAPI scholar search failed")
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
	"""Show stored professor and enrich with SerpAPI author data when available."""
	professor = get_object_or_404(Professor, pk=pk)
	papers = professor.papers.all()

	scholar_data = None
	scholar_papers = []

	# If professor has a google_scholar_id or we can build a query from name, use SerpAPI
	client = SerpAPIClient()
	try:
		if professor.google_scholar_id:
			# Search by the scholar id/profile link if the ID looks like a profile identifier
			query = professor.google_scholar_id
		else:
			# Fallback: search by name + affiliation keywords
			query = f"{professor.name} {professor.department.name if professor.department else ''}"

			if query:
				# Request the raw SerpAPI JSON so we can flexibly parse authors or publication results
				raw_resp = None
				try:
					raw_resp = client.search_scholar(query=query, num=5)
				except Exception:
					raise

				# Try to extract author blocks first (author_results / scholar_results)
				author_block = None
				for k in ('author_results', 'scholar_results', 'author_profiles'):
					if raw_resp.get(k):
						author_block = raw_resp.get(k)
						break

				if author_block and isinstance(author_block, list) and len(author_block) > 0:
					# Use the first author match
					item = author_block[0]
					scholar_data = {
						'name': item.get('name') or item.get('author') or item.get('title'),
						'affiliation': item.get('affiliation') or item.get('publication'),
						'snippet': item.get('snippet') or item.get('description'),
						'profile_link': item.get('profile_link') or item.get('link'),
						'raw': item,
					}

					# If the author block contains nested publications, extract them
					pubs = []
					for key in ('publications', 'publication_results', 'scholar_publications'):
						block = item.get(key)
						if block and isinstance(block, list):
							for p in block[:5]:
								pubs.append({
									'title': p.get('title') or p.get('bib', {}).get('title') if isinstance(p, dict) else None,
									'year': p.get('year') or p.get('bib', {}).get('pub_year') if isinstance(p, dict) else None,
									'url': p.get('link') or p.get('pub_url') or None,
									'snippet': p.get('snippet') or p.get('description') or None,
								})
						if pubs:
							break

					scholar_papers = pubs
				else:
					# No author block: fall back to treating 'organic_results' as publication hits
					organic = raw_resp.get('organic_results') or []
					pubs = []
					for p in organic[:5]:
						pubs.append({
							'title': p.get('title') or p.get('publication') or p.get('name'),
							'year': p.get('year') or p.get('publication_year') or None,
							'url': p.get('link') or p.get('url') or None,
							'abstract': p.get('snippet') or p.get('description') or None,
						})
					scholar_papers = pubs
					# Provide minimal scholar_data so the template will render the Live section
					scholar_data = {
						'name': professor.name,
						'affiliation': professor.department.name if professor.department else None,
						'interests': [],
						'citedby': None,
					}
	except Exception as e:
		logger.exception("SerpAPI fetch for professor failed")
		scholar_data = {'error': str(e)}

	return render(request, 'profiles/professor_detail.html', {
		'professor': professor,
		'papers': papers,
		'scholar_data': scholar_data,
		'scholar_papers': scholar_papers
	})


@staff_member_required
@require_http_methods(["GET", "POST"])
def import_cua_view(request):
	"""Admin view to preview and optionally persist SerpAPI import results for a department.

	GET: show form to enter department and limit and preview dry-run results.
	POST: if 'persist' present, create Professor and Paper records for the previewed candidates.
	"""
	context = {}
	department_name = request.GET.get('department') or request.POST.get('department') or ''
	limit = int(request.GET.get('limit') or request.POST.get('limit') or 10)
	client = SerpAPIClient()
	candidates = []

	if department_name:
		query = f"{department_name} Catholic University of America"
		try:
			candidates = client.search_scholar_authors(query=query, num=limit)
			# apply same filtering heuristics as the management command
			filtered = []
			for a in candidates:
				name = a.get('name')
				if not name:
					continue
				lowname = name.lower()
				if any(tok in lowname for tok in ('university', 'department', 'catholic', 'faculty', 'program', 'project')):
					continue
				name_parts = [p for p in name.split() if p]
				profile_link = a.get('profile_link') or a.get('link')
				human_like = len(name_parts) >= 2
				if not profile_link and not human_like:
					continue
				filtered.append(a)
			candidates = filtered
		except Exception as e:
			context['error'] = str(e)

	# Persist if requested
	if request.method == 'POST' and request.POST.get('action') == 'persist' and candidates:
		dept, _ = Department.objects.get_or_create(name=department_name or 'Uncategorized')
		created = []
		for a in candidates:
			name = a.get('name')
			snippet = a.get('snippet') or ''
			profile_link = a.get('profile_link') or a.get('link')
			# Basic dedupe
			if Professor.objects.filter(name__iexact=name, department=dept).exists():
				continue
			prof = Professor.objects.create(
				name=name,
				email=None,
				department=dept,
				interests=snippet,
				google_scholar_id=profile_link,
			)
			# create papers from raw if present
			raw = a.get('raw') or {}
			pubs = []
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
			created.append(prof)
		context['created'] = created

	context.update({
		'department': department_name,
		'limit': limit,
		'candidates': candidates,
	})
	return render(request, 'profiles/import_cua_view.html', context)
