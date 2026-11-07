"""
UI Prototype Views for the Department-Based Document Management System.
Renders all 20 required interfaces with clean mock data without any database/backend logic.
"""

from django.shortcuts import render, redirect
from django.http import Http404
from .mock_data import (
    MOCK_DEPARTMENTS,
    MOCK_DOCUMENTS,
    MOCK_RECYCLE_BIN,
    MOCK_USERS,
    MOCK_ACTIVITY_LOGS,
    MOCK_STORAGE_STATS,
    MOCK_ROLES_PERMISSIONS
)

def _get_base_context(active_page='', active_role='super_admin'):
    user_map = {
        'super_admin': MOCK_USERS[0],
        'admin': MOCK_USERS[1],
        'manager': MOCK_USERS[3], # Hassan Al-Khatib (Finance)
        'employee': MOCK_USERS[5], # Bilal Nabil (IT)
    }
    return {
        'current_user': user_map.get(active_role, MOCK_USERS[0]),
        'active_page': active_page,
        'active_role': active_role,
        'departments': MOCK_DEPARTMENTS,
        'pending_approvals_count': len([d for d in MOCK_DOCUMENTS if d['status'] == 'Pending']),
    }

# 1. Login Page
def login_view(request):
    return render(request, 'prototype/login.html')

# 2. Super Administrator Dashboard
def dashboard_super_admin(request):
    ctx = _get_base_context(active_page='dash_super_admin', active_role='super_admin')
    ctx.update({
        'total_documents': len(MOCK_DOCUMENTS),
        'total_users': len(MOCK_USERS),
        'total_departments': len(MOCK_DEPARTMENTS),
        'pending_approvals': len([d for d in MOCK_DOCUMENTS if d['status'] == 'Pending']),
        'recent_uploads': MOCK_DOCUMENTS[:6],
        'storage_stats': MOCK_STORAGE_STATS,
        'recycle_bin_count': len(MOCK_RECYCLE_BIN),
        'recent_activity': MOCK_ACTIVITY_LOGS[:6],
    })
    return render(request, 'prototype/dashboards/super_admin.html', ctx)

# 3. Administrator Dashboard
def dashboard_admin(request):
    ctx = _get_base_context(active_page='dash_admin', active_role='admin')
    pending_docs = [d for d in MOCK_DOCUMENTS if d['status'] == 'Pending']
    ctx.update({
        'pending_documents': pending_docs,
        'recent_uploads': [d for d in MOCK_DOCUMENTS if d['department'] in ['Finance', 'IT & Infrastructure']],
    })
    return render(request, 'prototype/dashboards/admin.html', ctx)

# 4. Manager Dashboard
def dashboard_manager(request):
    ctx = _get_base_context(active_page='dash_manager', active_role='manager')
    finance_docs = [d for d in MOCK_DOCUMENTS if d['department'] == 'Finance']
    ctx.update({
        'department_docs': finance_docs,
    })
    return render(request, 'prototype/dashboards/manager.html', ctx)

# 5. Employee Dashboard
def dashboard_employee(request):
    ctx = _get_base_context(active_page='dash_employee', active_role='employee')
    it_docs = [d for d in MOCK_DOCUMENTS if d['department'] == 'IT & Infrastructure' and d['status'] == 'Published']
    ctx.update({
        'accessible_docs': it_docs,
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
    ctx = _get_base_context(active_page='departments')
    return render(request, 'prototype/documents/department_list.html', ctx)

# 7. File Manager and Folder Navigation
def file_manager(request):
    dept = request.GET.get('dept', 'Finance')
    ctx = _get_base_context(active_page='file_manager')
    ctx.update({
        'active_dept': dept,
        'documents': MOCK_DOCUMENTS,
    })
    return render(request, 'prototype/documents/file_manager.html', ctx)

# 8. Document Listing
def document_list(request):
    ctx = _get_base_context(active_page='document_list')
    ctx.update({
        'documents': MOCK_DOCUMENTS,
    })
    return render(request, 'prototype/documents/document_list.html', ctx)

# 8. Document Details
def document_detail(request, doc_id):
    ctx = _get_base_context(active_page='document_list')
    doc = next((d for d in MOCK_DOCUMENTS if d['id'] == doc_id), None)
    if not doc:
        raise Http404("Document not found in prototype mock records.")
    ctx.update({'doc': doc})
    return render(request, 'prototype/documents/document_detail.html', ctx)

# 9. Quick & Advanced Search
def search_page(request):
    ctx = _get_base_context(active_page='search_page')
    ctx.update({
        'documents': MOCK_DOCUMENTS,
    })
    return render(request, 'prototype/documents/search_page.html', ctx)

# 11. Approval and Rejection Interface
def approvals_list(request):
    ctx = _get_base_context(active_page='approvals_list')
    pending_docs = [d for d in MOCK_DOCUMENTS if d['status'] == 'Pending']
    ctx.update({
        'pending_documents': pending_docs,
    })
    return render(request, 'prototype/documents/approvals_list.html', ctx)

# 12. Document Version History
def version_history(request, doc_id):
    ctx = _get_base_context(active_page='document_list')
    doc = next((d for d in MOCK_DOCUMENTS if d['id'] == doc_id), None)
    if not doc:
        raise Http404("Document not found.")
    ctx.update({'doc': doc})
    return render(request, 'prototype/documents/version_history.html', ctx)

# 13. Recycle Bin
def recycle_bin(request):
    ctx = _get_base_context(active_page='recycle_bin')
    ctx.update({
        'deleted_items': MOCK_RECYCLE_BIN,
    })
    return render(request, 'prototype/documents/recycle_bin.html', ctx)

# 14. Internal Sharing Interface
def share_interface(request, doc_id):
    ctx = _get_base_context(active_page='document_list')
    doc = next((d for d in MOCK_DOCUMENTS if d['id'] == doc_id), None)
    if not doc:
        raise Http404("Document not found.")
    ctx.update({'doc': doc})
    return render(request, 'prototype/documents/share_interface.html', ctx)

# 15. User Management
def user_management(request):
    ctx = _get_base_context(active_page='users')
    ctx.update({
        'users': MOCK_USERS,
    })
    return render(request, 'prototype/admin/user_management.html', ctx)

# 16. Department Management
def department_management(request):
    ctx = _get_base_context(active_page='departments')
    return render(request, 'prototype/admin/department_management.html', ctx)

# 17. Permission Management
def permission_management(request):
    ctx = _get_base_context(active_page='permissions')
    ctx.update({
        'roles_permissions': MOCK_ROLES_PERMISSIONS,
    })
    return render(request, 'prototype/admin/permission_management.html', ctx)

# 18. Activity Logs
def activity_logs(request):
    ctx = _get_base_context(active_page='activity_logs')
    ctx.update({
        'logs': MOCK_ACTIVITY_LOGS,
    })
    return render(request, 'prototype/admin/activity_logs.html', ctx)

# 19. Storage Monitoring
def storage_monitoring(request):
    ctx = _get_base_context(active_page='storage')
    ctx.update({
        'storage_stats': MOCK_STORAGE_STATS,
    })
    return render(request, 'prototype/admin/storage_monitoring.html', ctx)

# 20. System Settings
def system_settings(request):
    ctx = _get_base_context(active_page='settings')
    return render(request, 'prototype/admin/system_settings.html', ctx)
