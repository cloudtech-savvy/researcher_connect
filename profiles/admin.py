
from django.contrib import admin
from .models import Department, Professor, Paper

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
	list_display = ('name',)

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'department', 'interests')
	search_fields = ('name', 'interests')
	list_filter = ('department',)

@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
	list_display = ('title', 'professor', 'publication_year')
	search_fields = ('title',)
	list_filter = ('publication_year', 'professor')
