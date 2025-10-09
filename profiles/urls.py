from django.urls import path
from . import views

urlpatterns = [
    path('professors/search/', views.professor_search, name='professor_search'),
    path('professors/<int:pk>/', views.professor_detail, name='professor_detail'),
    path('tools/import-cua/', views.import_cua_view, name='import_cua_view'),
    path('scholar-search/', views.scholar_search, name='scholar_search'),
]
