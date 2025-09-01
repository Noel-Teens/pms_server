from django.urls import path
from . import views

urlpatterns = [
    path('paperworks/', views.paperworks_list, name='paperworks_list'),
    path('paperworks/<uuid:id>/', views.paperwork_detail, name='paperwork_detail'),
    path('paperworks/<uuid:id>/versions/', views.versions_list, name='versions_list'),
    path('paperworks/<uuid:id>/versions/<int:ver>/', views.version_detail, name='version_detail'),
    path('paperworks/<uuid:id>/review/', views.review_paperwork, name='review_paperwork'),
    path('paperworks/<uuid:id>/reviews/', views.paperwork_reviews, name='paperwork_reviews'),
    path('paperworks/<uuid:id>/delete/', views.delete_paperwork, name='delete_paperwork'),
    path('reports/summary/', views.reports_summary, name='reports_summary'),
    path('reports/export.csv/', views.reports_export, name='reports_export'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('stats/researcher/', views.researcher_stats, name='researcher_stats'),
    path('stats/admin/', views.admin_stats, name='admin_stats'),
]