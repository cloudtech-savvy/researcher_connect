from rest_framework import serializers
from .models import Department, Professor, Paper

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class ProfessorSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    class Meta:
        model = Professor
        fields = '__all__'

class PaperSerializer(serializers.ModelSerializer):
    professor = ProfessorSerializer(read_only=True)
    class Meta:
        model = Paper
        fields = '__all__'
