from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('thread/<slug:category_slug>/<int:pk>/', views.thread_view, name='thread-view'),
    path('create_thread/', views.create_thread, name='create-thread'),
    path('thread/<slug:category_slug>/<int:pk>/reply/', views.create_reply, name='reply-thread'),
    path('thread/<slug:category_slug>/<int:pk>/reply/<int:parent_id>/', views.create_reply, name='reply-reply'),
    path('delete/thread/<int:pk>/', views.delete_thread, name='delete-thread'),
    path('delete/reply/<int:pk>/', views.delete_reply, name='delete-reply'),
    path('categories/', views.category_list, name='category-list'),
    path('categories/<slug:category_slug>/', views.home, name='category-detail'),
    path('thread/<int:pk>/toggle-lock/', views.toggle_thread_lock, name='toggle-thread-lock'),
    path('report/thread/<int:pk>/', views.report_thread, name='report-thread'),
    path('report/reply/<int:pk>/', views.report_reply, name='report-reply'),
    path('reports/', views.reports_view, name='reports-list'),
    path('reports/<int:pk>/resolve/', views.resolve_report, name='resolve-report'),
    path('ajax/resources/', views.load_resources_for_course, name='ajax_resources'),
]
