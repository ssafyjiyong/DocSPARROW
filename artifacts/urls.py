from django.urls import path
from . import views

app_name = 'artifacts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('history/<int:product_id>/<int:category_id>/', views.artifact_history, name='history'),
    path('upload/<int:product_id>/<int:category_id>/', views.artifact_upload, name='upload'),
    path('download/<int:artifact_id>/', views.artifact_download, name='download'),
    path('delete/<int:artifact_id>/', views.artifact_delete, name='delete'),
]
