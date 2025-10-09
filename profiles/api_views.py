
from rest_framework import viewsets
from .models import Department, Professor, Paper
from .serializers import DepartmentSerializer, ProfessorSerializer, PaperSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
	queryset = Department.objects.all()
	serializer_class = DepartmentSerializer

from rest_framework import filters

class ProfessorViewSet(viewsets.ModelViewSet):
	queryset = Professor.objects.all()
	serializer_class = ProfessorSerializer
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ['name', 'affiliation', 'interests', 'department__name']
	ordering_fields = ['name', 'department__name']

	def get_queryset(self):
		queryset = super().get_queryset()
		department = self.request.query_params.get('department')
		if department:
			queryset = queryset.filter(department__name__icontains=department)
		return queryset

class PaperViewSet(viewsets.ModelViewSet):
	queryset = Paper.objects.all()
	serializer_class = PaperSerializer
