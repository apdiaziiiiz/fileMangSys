"""
Views for the Department-Based Document Management System.
Connects with real database models while supporting clean empty states when no records exist.
"""

from django.shortcuts import render, redirect
from django.http import Http404
from .models import (
    Role, SystemPermission, RolePermission, Department, User,
    DepartmentAssignment, UserPermissionOverride, Folder,
    FolderPermission, Document, DocumentVersion, UploadRequest,
    DocumentShare, ActivityLog
)
from .mock_data import MOCK_STORAGE_STATS, MOCK_ROLES_PERMISSIONS


def _get_base_context(request, active_page='', active_role='super_admin'):
    # Check if a real authenticated user exists, otherwise display a clean system profile
    real_user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    
    if real_user:
        current_user = {
            'id': real_user.user_id_code,
            'name': real_user.full_name or real_user.email,
            'email': real_user.email,
            'role': real_user.role.name if real_user.role else 'Authorized User',
            'department': real_user.primary_department.name if real_user.primary_department else 'None'
        }
    else:
        role_titles = {
            'super_admin': ('Super Administrator', 'System-Wide'),
            'admin': ('Administrator', 'Assigned Scope'),
            'manager': ('Manager', 'Department Scope'),
            'employee': ('Employee', 'Staff Member')
        }
        title, dept_label = role_titles.get(active_role, ('Authorized User', 'Standard'))
        current_user = {
            'id': '-',
            'name': title,
            'email': 'admin@enterprise.local' if active_role == 'super_admin' else '',
            'role': title,
            'department': dept_label
        }

    # Query real departments from database
    depts = list(Department.objects.filter(is_active=True).values('id', 'code', 'name', 'max_quota_mb'))
    pending_approvals_count = UploadRequest.objects.filter(status='PENDING').count()

    return {
        'current_user': current_user,
        'active_page': active_page,
        'active_role': active_role,
        'departments': depts,
        'pending_approvals_count': pending_approvals_count,
    }


# 1. Login Page
def login_view(request):
    return render(request, 'prototype/login.html')


# 2. Super Administrator Dashboard
def dashboard_super_admin(request):
    ctx = _get_base_context(request, active_page='dash_super_admin', active_role='super_admin')
    
    total_docs = Document.objects.filter(is_deleted=False).count()
    total_users = User.objects.filter(is_active=True).count()
    total_depts = Department.objects.filter(is_active=True).count()
    pending_approvals = UploadRequest.objects.filter(status='PENDING').count()
    recent_uploads = list(Document.objects.filter(is_deleted=False).select_related('department', 'created_by').order_by('-created_at')[:6])
    recycle_bin_count = Document.objects.filter(is_deleted=True).count()
    recent_activity = list(ActivityLog.objects.select_related('user').order_by('-timestamp')[:6])

    # Dynamic storage stats
    storage_stats = {
        'total_capacity_gb': 500,
        'used_storage_gb': 0.0,
        'free_storage_gb': 500.0,
        'usage_percentage': 0,
        'db_backup_status': 'Configured (MySQL dms_db)',
        'nas_connection': 'Local Central Repository (C:\\fileMngSys)',
        'breakdown': []
    }

    ctx.update({
        'total_documents': total_docs,
        'total_users': total_users,
        'total_departments': total_depts,
        'pending_approvals': pending_approvals,
        'recent_uploads': recent_uploads,
        'storage_stats': storage_stats,
        'recycle_bin_count': recycle_bin_count,
        'recent_activity': recent_activity,
    })
    return render(request, 'prototype/dashboards/super_admin.html', ctx)


# 3. Administrator Dashboard
def dashboard_admin(request):
    ctx = _get_base_context(request, active_page='dash_admin', active_role='admin')
    pending_docs = list(UploadRequest.objects.filter(status='PENDING').select_related('document', 'submitted_by'))
    recent_docs = list(Document.objects.filter(is_deleted=False).select_related('department', 'created_by').order_by('-created_at')[:6])
    
    ctx.update({
        'pending_documents': pending_docs,
        'recent_uploads': recent_docs,
        'total_scope_documents': Document.objects.filter(is_deleted=False).count(),
        'managed_users_count': User.objects.filter(is_active=True).count(),
    })
    return render(request, 'prototype/dashboards/admin.html', ctx)


# 4. Manager Dashboard
def dashboard_manager(request):
    ctx = _get_base_context(request, active_page='dash_manager', active_role='manager')
    dept_docs = list(Document.objects.filter(is_deleted=False).select_related('department', 'folder').order_by('-created_at')[:8])
    pending_count = UploadRequest.objects.filter(status='PENDING').count()

    ctx.update({
        'department_docs': dept_docs,
        'dept_folders': list(Folder.objects.filter(is_archived=False).values('id', 'name')),
        'dept_documents_count': Document.objects.filter(is_deleted=False).count(),
        'team_members_count': User.objects.filter(is_active=True).count(),
        'pending_count': pending_count,
    })
    return render(request, 'prototype/dashboards/manager.html', ctx)


# 5. Employee Dashboard
def dashboard_employee(request):
    ctx = _get_base_context(request, active_page='dash_employee', active_role='employee')
    accessible_docs = list(Document.objects.filter(is_deleted=False, status='PUBLISHED').select_related('department').order_by('-created_at')[:6])
    my_submissions = list(UploadRequest.objects.select_related('document').order_by('-submitted_at')[:6])
    
    ctx.update({
        'accessible_docs': accessible_docs,
        'my_submissions': my_submissions,
        'accessible_count': Document.objects.filter(is_deleted=False, status='PUBLISHED').count(),
        'my_submissions_count': len(my_submissions),
        'pending_count': UploadRequest.objects.filter(status='PENDING').count(),
        'approved_count': UploadRequest.objects.filter(status='APPROVED').count(),
    })
    return render(request, 'prototype/dashboards/employee.html', ctx)


# Role switcher redirection helper
def dashboard_switcher(request, role):
    role_redirects = {
        'super-admin': 'dashboard_super_admin',
        'admin': 'dashboard_admin',
        'manager': 'dashboard_manager',
        'employee': 'dashboard_employee',
    }
    target = role_redirects.get(role, 'dashboard_super_admin')
    return redirect(target)


# 6. Department Navigation
def department_list(request):
    ctx = _get_base_context(request, active_page='departments', active_role='super_admin')
    departments = list(Department.objects.filter(is_active=True).select_related('manager'))
    ctx.update({
        'departments': departments,
    })
    return render(request, 'prototype/documents/department_list.html', ctx)


# 7. File Manager & Documents
def file_manager(request):
    dept_query = request.GET.get('dept', 'all')
    folder_query = request.GET.get('folder', '')

    docs_qs = Document.objects.filter(is_deleted=False).select_related('department', 'folder', 'created_by')
    folders_qs = Folder.objects.filter(is_archived=False)

    if dept_query and dept_query != 'all':
        docs_qs = docs_qs.filter(department__name__iexact=dept_query)
        folders_qs = folders_qs.filter(department__name__iexact=dept_query)

    if folder_query:
        docs_qs = docs_qs.filter(folder__name__iexact=folder_query)

    folders = list(folders_qs.values_list('name', flat=True).distinct())

    ctx = _get_base_context(request, active_page='file_manager', active_role='super_admin')
    ctx.update({
        'active_dept': dept_query,
        'current_folders': folders,
        'documents': list(docs_qs.order_by('-created_at')),
        'selected_folder': folder_query,
    })
    return render(request, 'prototype/documents/file_manager.html', ctx)


def document_list(request):
    return redirect('file_manager')


# 8. Document Details
def document_detail(request, doc_id):
    ctx = _get_base_context(request, active_page='file_manager', active_role='super_admin')
    try:
        doc = Document.objects.select_related('department', 'folder', 'created_by').prefetch_related('versions', 'internal_shares').get(doc_id=doc_id, is_deleted=False)
    except Document.DoesNotExist:
        raise Http404("Document not found.")

    ctx.update({
        'doc': doc,
        'versions': list(doc.versions.all().order_by('-version_number')),
        'shares': list(doc.internal_shares.all().select_related('shared_with')),
    })
    return render(request, 'prototype/documents/document_detail.html', ctx)


# 9. Quick & Advanced Search
def search_page(request):
    ctx = _get_base_context(request, active_page='search_page', active_role='super_admin')
    docs = list(Document.objects.filter(is_deleted=False).select_related('department', 'folder').order_by('-created_at'))
    ctx.update({
        'documents': docs,
    })
    return render(request, 'prototype/documents/search_page.html', ctx)


# 11. Approval and Rejection Interface
def approvals_list(request):
    ctx = _get_base_context(request, active_page='approvals_list', active_role='super_admin')
    pending_requests = list(UploadRequest.objects.filter(status='PENDING').select_related('document', 'submitted_by', 'version'))
    ctx.update({
        'pending_documents': pending_requests,
    })
    return render(request, 'prototype/documents/approvals_list.html', ctx)


# 12. Document Version History
def version_history(request, doc_id):
    ctx = _get_base_context(request, active_page='file_manager', active_role='super_admin')
    try:
        doc = Document.objects.prefetch_related('versions').get(doc_id=doc_id, is_deleted=False)
    except Document.DoesNotExist:
        raise Http404("Document not found.")

    ctx.update({
        'doc': doc,
        'versions': list(doc.versions.all().order_by('-version_number')),
    })
    return render(request, 'prototype/documents/version_history.html', ctx)


# 13. Recycle Bin
def recycle_bin(request):
    ctx = _get_base_context(request, active_page='recycle_bin', active_role='super_admin')
    deleted_docs = list(Document.objects.filter(is_deleted=True).select_related('department', 'folder', 'deleted_by').order_by('-deleted_at'))
    ctx.update({
        'deleted_items': deleted_docs,
    })
    return render(request, 'prototype/documents/recycle_bin.html', ctx)


# 14. Internal Sharing Interface
def share_interface(request, doc_id):
    ctx = _get_base_context(request, active_page='file_manager', active_role='super_admin')
    try:
        doc = Document.objects.prefetch_related('internal_shares').get(doc_id=doc_id, is_deleted=False)
    except Document.DoesNotExist:
        raise Http404("Document not found.")

    ctx.update({
        'doc': doc,
        'shares': list(doc.internal_shares.filter(is_revoked=False).select_related('shared_with')),
        'users': list(User.objects.filter(is_active=True).values('id', 'full_name', 'email')),
    })
    return render(request, 'prototype/documents/share_interface.html', ctx)


# 15. User Management
def user_management(request):
    ctx = _get_base_context(request, active_page='users', active_role='super_admin')
    users = list(User.objects.all().select_related('role', 'primary_department').order_by('full_name'))
    ctx.update({
        'users': users,
    })
    return render(request, 'prototype/admin/user_management.html', ctx)


# 16. Department Management
def department_management(request):
    ctx = _get_base_context(request, active_page='departments', active_role='super_admin')
    depts = list(Department.objects.all().select_related('manager').order_by('name'))
    ctx.update({
        'departments': depts,
    })
    return render(request, 'prototype/admin/department_management.html', ctx)


# 17. Permission Management
def permission_management(request):
    ctx = _get_base_context(request, active_page='permissions', active_role='super_admin')
    roles = Role.objects.all().order_by('id')
    role_list = []
    for r in roles:
        role_list.append({
            'role': r.name,
            'code': r.code,
            'user_count': r.users.count(),
            'scope': 'System-wide' if r.code == 'SUPER_ADMIN' else ('Assigned Scope' if r.code == 'ADMIN' else ('Department' if r.code == 'MANAGER' else 'Permitted Folders')),
            'can_upload': r.code in ['SUPER_ADMIN', 'ADMIN', 'MANAGER'],
            'can_approve': r.code in ['SUPER_ADMIN', 'ADMIN', 'MANAGER'],
            'can_delete': r.code in ['SUPER_ADMIN', 'ADMIN', 'MANAGER'],
            'can_manage_users': r.code in ['SUPER_ADMIN', 'ADMIN'],
            'can_view_audit': r.code in ['SUPER_ADMIN', 'ADMIN'],
            'can_restore_bin': r.code in ['SUPER_ADMIN', 'ADMIN'],
        })

    ctx.update({
        'roles_permissions': role_list,
    })
    return render(request, 'prototype/admin/permission_management.html', ctx)


# 18. Activity Logs
def activity_logs(request):
    ctx = _get_base_context(request, active_page='activity_logs', active_role='super_admin')
    logs = list(ActivityLog.objects.all().select_related('user', 'document').order_by('-timestamp')[:50])
    ctx.update({
        'logs': logs,
    })
    return render(request, 'prototype/admin/activity_logs.html', ctx)


# 19. Storage Monitoring
def storage_monitoring(request):
    ctx = _get_base_context(request, active_page='storage', active_role='super_admin')
    storage_stats = {
        'total_capacity_gb': 500,
        'used_storage_gb': 0.0,
        'free_storage_gb': 500.0,
        'usage_percentage': 0,
        'db_backup_status': 'Configured (MySQL dms_db)',
        'nas_connection': 'Local Central Repository (C:\\fileMngSys)',
        'breakdown': []
    }
    ctx.update({
        'storage_stats': storage_stats,
    })
    return render(request, 'prototype/admin/storage_monitoring.html', ctx)


# 20. System Settings
def system_settings(request):
    ctx = _get_base_context(request, active_page='settings', active_role='super_admin')
    return render(request, 'prototype/admin/system_settings.html', ctx)
