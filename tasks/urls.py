"""
URL routing for tasks app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # CRUD endpoints
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/bulk/', views.bulk_create_tasks, name='bulk_create_tasks'),
    path('tasks/all/', views.delete_all_tasks, name='delete_all_tasks'),
    
    # Analysis endpoints
    path('tasks/analyze/', views.analyze_tasks, name='analyze_tasks'),
    path('tasks/suggest/', views.suggest_tasks, name='suggest_tasks'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
]