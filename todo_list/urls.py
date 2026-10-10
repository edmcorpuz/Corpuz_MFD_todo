from django.urls import path

from . import views

app_name = 'todo_list'

urlpatterns = [
    path('', views.task_list, name='list'),
    path('tasks/new/', views.task_create, name='create'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='edit'),
    path('tasks/<int:pk>/toggle/', views.task_toggle, name='toggle'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='delete'),
]
