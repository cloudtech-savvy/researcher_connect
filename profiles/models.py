
from django.db import models

class Department(models.Model):
	name = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)

	def __str__(self):
		return self.name

class Professor(models.Model):
	name = models.CharField(max_length=100)
	email = models.EmailField(blank=True, null=True)
	department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='professors')
	interests = models.TextField(blank=True)
	google_scholar_id = models.CharField(max_length=100, blank=True, null=True)

	def __str__(self):
		return self.name

class Paper(models.Model):
	title = models.CharField(max_length=300)
	abstract = models.TextField(blank=True)
	publication_year = models.IntegerField(blank=True, null=True)
	professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='papers')
	url = models.URLField(blank=True, null=True)

	def __str__(self):
		return self.title
