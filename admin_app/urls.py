from django.urls import path
from . import views

urlpatterns = [
    path('createusers/', views.create_user, name='create_user'),
    path('updateusers/<str:username>/status/', views.update_user_status, name='update_user_status'),
    path('users/', views.users_list, name='users_list'),
    path('users/<uuid:user_id>/', views.user_detail, name='user_detail'),
    path('paperworks/', views.assign_paperwork, name='assign_paperwork'),
    path('paperworks/<uuid:id>/deadline/', views.update_paperwork_deadline, name='update_paperwork_deadline'),
    path('paperworks/<uuid:paperwork_id>/versions/<int:version_no>/<str:file_type>/view/', views.view_paperwork_file, name='view_paperwork_file'),
    path('paperworks/<uuid:paperwork_id>/versions/<int:version_no>/zip-contents/', views.view_zip_contents, name='view_zip_contents'),
    path('paperworks/<uuid:paperwork_id>/versions/<int:version_no>/zip-file/<path:file_path>/', views.view_zip_file_content, name='view_zip_file_content'),
]