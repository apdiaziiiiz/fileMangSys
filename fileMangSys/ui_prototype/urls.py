"""
URL patterns for the Department-Based Document Management System.
"""

from django.urls import path
from . import views

urlpatterns = [
    # 1. Login & Logout
    path('', views.login_view, name='login_page'),
    path('login/', views.login_view, name='login_direct'),
    path('logout/', views.logout_view, name='logout_user'),

    # Dashboard dispatcher
    path('dashboard/', views.dashboard_dispatcher, name='dashboard_dispatcher'),

    # 2-5. Role-Specific Dashboards
    path('dashboard/super-admin/', views.dashboard_super_admin, name='dashboard_super_admin'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/manager/', views.dashboard_manager, name='dashboard_manager'),
    path('dashboard/employee/', views.dashboard_employee, name='dashboard_employee'),
    path('dashboard/<str:role>/', views.dashboard_switcher, name='dashboard_switcher'),

    # 6. Department Navigation & API
    path('departments/', views.department_list, name='department_list'),
    path('api/departments/<int:dept_id>/folders/', views.api_department_folders, name='api_department_folders'),

    # 7. File manager (also handles uploads via POST)
    path('files/', views.file_manager, name='file_manager'),

    # 8. Document listing, details, view in browser & download
    path('documents/', views.document_list, name='document_list'),
    path('documents/<str:doc_id>/', views.document_detail, name='document_detail'),
    path('documents/<str:doc_id>/view/', views.view_document_file, name='view_document_file'),
    path('documents/<str:doc_id>/download/', views.download_document_file, name='download_document_file'),
    path('documents/<str:doc_id>/versions/<int:version_number>/download/', views.download_document_file, name='download_version_file'),

    # 9. Quick search and advanced search
    path('search/', views.search_page, name='search_page'),

    # 11. Approval and rejection interface
    path('approvals/', views.approvals_list, name='approvals_list'),

    # 12. Document version history
    path('documents/<str:doc_id>/versions/', views.version_history, name='version_history'),

    # 13. Recycle bin
    path('recycle-bin/', views.recycle_bin, name='recycle_bin'),

    # 14. Internal sharing interface
    path('documents/<str:doc_id>/share/', views.share_interface, name='share_interface'),

    # 15. User management
    path('admin/users/', views.user_management, name='user_management'),

    # 16. Department management (CRUD + folders)
    path('admin/departments/', views.department_management, name='department_management'),

    # 17. Permission management
    path('admin/permissions/', views.permission_management, name='permission_management'),

    # 18. Activity logs
    path('admin/activity-logs/', views.activity_logs, name='activity_logs'),

    # 19. Storage monitoring
    path('admin/storage/', views.storage_monitoring, name='storage_monitoring'),

    # 20. System settings
    path('admin/settings/', views.system_settings, name='system_settings'),
]
