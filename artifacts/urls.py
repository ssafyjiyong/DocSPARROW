from django.urls import path
from . import views, manage_views

app_name = 'artifacts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('history/<int:product_id>/<int:category_id>/', views.artifact_history, name='history'),
    path('upload/<int:product_id>/<int:category_id>/', views.artifact_upload, name='upload'),
    path('download/<int:artifact_id>/', views.artifact_download, name='download'),
    path('download-product-bulk/<int:product_id>/', views.product_bulk_download, name='product_bulk_download'),
    path('delete/<int:artifact_id>/', views.artifact_delete, name='delete'),

    
    # Admin Management URLs
    path('manage/', manage_views.admin_management, name='admin_manage'),
    path('manage/category/create/', manage_views.category_create, name='category_create'),
    path('manage/category/<int:category_id>/update/', manage_views.category_update, name='category_update'),
    path('manage/category/<int:category_id>/delete/', manage_views.category_delete, name='category_delete'),
    path('manage/product/create/', manage_views.product_create, name='product_create'),
    path('manage/product/<int:product_id>/update/', manage_views.product_update, name='product_update'),
    path('manage/product/<int:product_id>/delete/', manage_views.product_delete, name='product_delete'),
    path('manage/disabled-cells/', manage_views.get_disabled_cells, name='get_disabled_cells'),
    path('manage/toggle-disabled-cell/', manage_views.toggle_disabled_cell, name='toggle_disabled_cell'),
    
    # Login Logs URLs (Superuser only)
    path('manage/login-logs/', manage_views.login_logs_view, name='login_logs'),
    path('manage/api/login-logs/', manage_views.get_login_logs_api, name='get_login_logs_api'),
]
