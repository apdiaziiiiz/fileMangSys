"""
Views for the Department-Based Document Management System.
Full backend implementation: auth, upload, approvals, departments, folders,
sharing, recycle bin, user management, activity logging, file download/view,
permission management, and deletion controls.
"""

import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponseForbidden, FileResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from .models import (
    Role, SystemPermission, RolePermission, Department, User,
    DepartmentAssignment, UserPermissionOverride, Folder,
    FolderPermission, Document, DocumentVersion, UploadRequest,
    DocumentShare, ActivityLog
)


# ==============================================================================
# HELPERS
# ==============================================================================

def get_user_role_code(user):
    """Returns canonical role code for user (SUPER_ADMIN, ADMIN, MANAGER, EMPLOYEE)."""
    if not user or not user.is_authenticated:
        return 'ANONYMOUS'
    if user.is_superuser or (user.role and user.role.code == 'SUPER_ADMIN'):
        return 'SUPER_ADMIN'
    if user.role:
        return user.role.code
    return 'EMPLOYEE'


def _log(user, action, target, doc=None, request=None, result='Success', details=''):
    """Create an ActivityLog entry."""
    ip = None
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
    ActivityLog.objects.create(
        user=user if user and user.is_authenticated else None,
        user_name_snapshot=user.full_name if user and user.is_authenticated else 'System',
        role_snapshot=user.role.code if user and user.is_authenticated and user.role else (
            'SUPER_ADMIN' if user and user.is_superuser else 'UNKNOWN'),
        action=action,
        target_resource=target,
        document=doc,
        client_ip=ip,
        result=result,
        details=details,
    )


def _get_base_context(request, active_page='', active_role=None):
    real_user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    role_code = get_user_role_code(real_user)

    role_code_to_template_role = {
        'SUPER_ADMIN': 'super_admin',
        'ADMIN': 'admin',
        'MANAGER': 'manager',
        'EMPLOYEE': 'employee',
    }
    computed_role = role_code_to_template_role.get(role_code, 'employee')

    if real_user:
        current_user = {
            'id': real_user.user_id_code,
            'name': real_user.full_name or real_user.email,
            'email': real_user.email,
            'role': real_user.role.name if real_user.role else ('Super Administrator' if real_user.is_superuser else 'Employee'),
            'department': real_user.primary_department.name if real_user.primary_department else 'System-Wide',
        }
    else:
        current_user = {'id': '-', 'name': 'Guest', 'email': '', 'role': 'Guest', 'department': 'None'}

    # Department scope
    depts_qs = Department.objects.filter(is_active=True)
    if role_code in ('EMPLOYEE', 'MANAGER') and real_user and real_user.primary_department:
        depts_qs = depts_qs.filter(id=real_user.primary_department_id)

    depts = list(depts_qs.values('id', 'code', 'name', 'max_quota_mb'))

    # Pending approvals count
    approvals_qs = UploadRequest.objects.filter(status='PENDING')
    if role_code == 'MANAGER' and real_user and real_user.primary_department:
        approvals_qs = approvals_qs.filter(document__department=real_user.primary_department)
    elif role_code == 'EMPLOYEE':
        approvals_qs = approvals_qs.none()

    return {
        'current_user': current_user,
        'active_page': active_page,
        'active_role': active_role or computed_role,
        'departments': depts,
        'pending_approvals_count': approvals_qs.count(),
        'user_role_code': role_code,
    }


def _save_uploaded_file(file_obj, doc_id, version_number):
    """Save file to STORAGE_ROOT/doc_id/vN_filename. Returns (storage_path, file_type, size, sha256)."""
    storage_root = getattr(settings, 'STORAGE_ROOT', Path('C:/fileMngSys'))
    doc_dir = Path(storage_root) / str(doc_id)
    doc_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file_obj.name).suffix.lower().lstrip('.')
    safe_name = f"v{version_number}_{file_obj.name}"
    dest_path = doc_dir / safe_name

    sha = hashlib.sha256()
    with open(dest_path, 'wb') as f:
        for chunk in file_obj.chunks():
            sha.update(chunk)
            f.write(chunk)

    return str(dest_path), ext, file_obj.size, sha.hexdigest()


def _generate_doc_id():
    """Generate a short unique document ID like DOC-XXXX."""
    while True:
        candidate = 'DOC-' + uuid.uuid4().hex[:8].upper()
        if not Document.objects.filter(doc_id=candidate).exists():
            return candidate


# ==============================================================================
# 1. AUTH
# ==============================================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_dispatcher')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return render(request, 'prototype/login.html')

        user = authenticate(request, username=email, password=password)
        if user is None:
            user = authenticate(request, email=email, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated. Contact your administrator.')
                return render(request, 'prototype/login.html')
            login(request, user)
            _log(user, 'USER_LOGIN', f'Login: {email}', request=request)
            messages.success(request, f'Welcome back, {user.full_name or user.email}!')
            return redirect('dashboard_dispatcher')
        else:
            messages.error(request, 'Invalid email or password. Access denied.')

    return render(request, 'prototype/login.html')


def logout_view(request):
    if request.user.is_authenticated:
        _log(request.user, 'USER_LOGOUT', f'Logout: {request.user.email}', request=request)
    logout(request)
    messages.info(request, 'You have been safely signed out.')
    return redirect('login_page')


# ==============================================================================
# 2. DASHBOARD DISPATCHER + ROLE DASHBOARDS
# ==============================================================================

@login_required
def dashboard_dispatcher(request):
    role = get_user_role_code(request.user)
    if role == 'SUPER_ADMIN':
        return redirect('dashboard_super_admin')
    elif role == 'ADMIN':
        return redirect('dashboard_admin')
    elif role == 'MANAGER':
        return redirect('dashboard_manager')
    else:
        return redirect('dashboard_employee')


@login_required
def dashboard_super_admin(request):
    if get_user_role_code(request.user) != 'SUPER_ADMIN':
        return redirect('dashboard_dispatcher')

    ctx = _get_base_context(request, active_page='dash_super_admin', active_role='super_admin')
    total_docs = Document.objects.filter(is_deleted=False).count()
    total_users = User.objects.filter(is_active=True).count()
    total_depts = Department.objects.filter(is_active=True).count()
    pending_approvals = UploadRequest.objects.filter(status='PENDING').count()
    recent_uploads = list(Document.objects.filter(is_deleted=False).select_related('department', 'created_by').order_by('-created_at')[:6])
    recycle_bin_count = Document.objects.filter(is_deleted=True).count()
    recent_activity = list(ActivityLog.objects.select_related('user').order_by('-timestamp')[:8])

    total_size_bytes = sum(
        v.file_size_bytes for v in DocumentVersion.objects.filter(is_current=True)
    )
    used_gb = round(total_size_bytes / (1024 ** 3), 3)

    storage_stats = {
        'total_capacity_gb': 500,
        'used_storage_gb': used_gb,
        'free_storage_gb': round(500 - used_gb, 3),
        'usage_percentage': round((used_gb / 500) * 100, 1),
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


@login_required
def dashboard_admin(request):
    role = get_user_role_code(request.user)
    if role not in ['SUPER_ADMIN', 'ADMIN']:
        return redirect('dashboard_dispatcher')

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


@login_required
def dashboard_manager(request):
    role = get_user_role_code(request.user)
    if role not in ['SUPER_ADMIN', 'ADMIN', 'MANAGER']:
        return redirect('dashboard_dispatcher')

    user = request.user
    dept = user.primary_department

    docs_qs = Document.objects.filter(is_deleted=False)
    folders_qs = Folder.objects.filter(is_archived=False)
    users_qs = User.objects.filter(is_active=True)
    pending_qs = UploadRequest.objects.filter(status='PENDING')

    if dept and role == 'MANAGER':
        docs_qs = docs_qs.filter(department=dept)
        folders_qs = folders_qs.filter(department=dept)
        users_qs = users_qs.filter(primary_department=dept)
        pending_qs = pending_qs.filter(document__department=dept)

    ctx = _get_base_context(request, active_page='dash_manager', active_role='manager')
    ctx.update({
        'department_docs': list(docs_qs.select_related('department', 'folder').order_by('-created_at')[:8]),
        'dept_folders': list(folders_qs.values('id', 'name')),
        'dept_documents_count': docs_qs.count(),
        'team_members_count': users_qs.count(),
        'pending_count': pending_qs.count(),
    })
    return render(request, 'prototype/dashboards/manager.html', ctx)


@login_required
def dashboard_employee(request):
    user = request.user
    dept = user.primary_department

    accessible_docs_qs = Document.objects.filter(is_deleted=False, status='PUBLISHED')
    if dept:
        accessible_docs_qs = accessible_docs_qs.filter(department=dept)

    # Also include documents shared directly with this user
    shared_doc_ids = DocumentShare.objects.filter(
        shared_with=user, is_revoked=False
    ).values_list('document_id', flat=True)
    all_accessible_ids = set(accessible_docs_qs.values_list('id', flat=True)) | set(shared_doc_ids)

    my_submissions = list(UploadRequest.objects.filter(submitted_by=user).select_related('document').order_by('-submitted_at')[:6])
    pending_submissions = UploadRequest.objects.filter(submitted_by=user, status='PENDING').count()
    approved_submissions = UploadRequest.objects.filter(submitted_by=user, status='APPROVED').count()

    ctx = _get_base_context(request, active_page='dash_employee', active_role='employee')
    ctx.update({
        'accessible_docs': list(accessible_docs_qs.select_related('department').order_by('-created_at')[:6]),
        'my_submissions': my_submissions,
        'accessible_count': len(all_accessible_ids),
        'my_submissions_count': len(my_submissions),
        'pending_count': pending_submissions,
        'approved_count': approved_submissions,
    })
    return render(request, 'prototype/dashboards/employee.html', ctx)


@login_required
def dashboard_switcher(request, role):
    if get_user_role_code(request.user) != 'SUPER_ADMIN':
        return redirect('dashboard_dispatcher')
    role_redirects = {
        'super-admin': 'dashboard_super_admin',
        'admin': 'dashboard_admin',
        'manager': 'dashboard_manager',
        'employee': 'dashboard_employee',
    }
    return redirect(role_redirects.get(role, 'dashboard_super_admin'))


# ==============================================================================
# 6. DEPARTMENT NAVIGATION LIST & FOLDERS API
# ==============================================================================

@login_required
def department_list(request):
    role = get_user_role_code(request.user)
    if role not in ['SUPER_ADMIN', 'ADMIN']:
        return redirect('dashboard_dispatcher')
    ctx = _get_base_context(request, active_page='departments')
    departments = list(Department.objects.filter(is_active=True).select_related('manager'))
    ctx['departments'] = departments
    return render(request, 'prototype/documents/department_list.html', ctx)


@login_required
def api_department_folders(request, dept_id):
    """Return JSON list of active folders for a selected department."""
    from django.http import JsonResponse
    try:
        dept = Department.objects.get(id=dept_id)
        # Ensure 'General' folder exists for this department
        Folder.objects.get_or_create(
            department=dept,
            name='General',
            defaults={'created_by': request.user, 'is_archived': False}
        )
        folders = list(dept.folders.filter(is_archived=False).order_by('name').values('id', 'name'))
        return JsonResponse({'folders': folders})
    except Department.DoesNotExist:
        return JsonResponse({'folders': []}, status=404)


# ==============================================================================
# 7. FILE MANAGER + UPLOAD
# ==============================================================================

@login_required
def file_manager(request):
    user = request.user
    role = get_user_role_code(user)

    # --- UPLOAD (POST) ---
    if request.method == 'POST' and request.POST.get('action') == 'upload':
        uploaded_file = request.FILES.get('document_file')
        title = request.POST.get('title', '').strip()
        if not title and uploaded_file:
            # Directly use the filename as title (without path)
            title = Path(uploaded_file.name).stem.replace('_', ' ').replace('-', ' ').title()
            if not title:
                title = uploaded_file.name

        objective = request.POST.get('objective', '').strip()
        owner_name = request.POST.get('owner', '').strip() or user.full_name
        department_id = request.POST.get('department_id')
        folder_id = request.POST.get('folder_id') or None
        doc_date_str = request.POST.get('document_date') or str(date.today())

        if not objective or not department_id or not uploaded_file:
            messages.error(request, 'Objective, department, and a file are all required.')
        else:
            try:
                dept = Department.objects.get(id=department_id, is_active=True)
            except Department.DoesNotExist:
                messages.error(request, 'Selected department does not exist.')
                return redirect('file_manager')

            # Employees must upload to their own department
            if role == 'EMPLOYEE' and user.primary_department and dept != user.primary_department:
                messages.error(request, 'You can only upload documents to your assigned department.')
                return redirect('file_manager')

            folder = None
            if folder_id:
                try:
                    folder = Folder.objects.get(id=folder_id, department=dept)
                except Folder.DoesNotExist:
                    folder = None

            # Fallback to default 'General' folder if no folder specified
            if not folder:
                folder, _ = Folder.objects.get_or_create(
                    department=dept,
                    name='General',
                    defaults={'created_by': user, 'is_archived': False}
                )

            doc_id = _generate_doc_id()
            try:
                storage_path, file_type, file_size, sha = _save_uploaded_file(uploaded_file, doc_id, 1)
            except Exception as e:
                messages.error(request, f'File storage error: {e}')
                return redirect('file_manager')

            # Determine initial status
            if role in ('SUPER_ADMIN', 'ADMIN'):
                initial_status = 'PUBLISHED'
            elif role == 'MANAGER':
                initial_status = 'PUBLISHED'
            else:
                initial_status = 'PENDING'

            try:
                doc_date = date.fromisoformat(doc_date_str)
            except ValueError:
                doc_date = date.today()

            doc = Document.objects.create(
                doc_id=doc_id,
                title=title,
                original_filename=uploaded_file.name,
                objective=objective,
                owner=owner_name,
                department=dept,
                folder=folder,
                document_date=doc_date,
                status=initial_status,
                created_by=user,
            )

            version = DocumentVersion.objects.create(
                document=doc,
                version_number=1,
                storage_path=storage_path,
                file_type=file_type,
                file_size_bytes=file_size,
                file_hash_sha256=sha,
                is_current=True,
                uploaded_by=user,
            )

            # For employees: create approval request
            if role == 'EMPLOYEE':
                UploadRequest.objects.create(
                    document=doc,
                    version=version,
                    submitted_by=user,
                    status='PENDING',
                )
                messages.success(request, f'Document "{title}" submitted for approval.')
            else:
                messages.success(request, f'Document "{title}" uploaded and published successfully.')

            _log(user, 'DOCUMENT_UPLOAD', f'{doc_id}: {title}', doc=doc, request=request,
                 details=f'File: {uploaded_file.name}, Dept: {dept.name}, Status: {initial_status}')
            return redirect('file_manager')

    # --- GET / filter ---
    dept_query = request.GET.get('dept', 'all')
    folder_query = request.GET.get('folder', '')

    docs_qs = Document.objects.filter(is_deleted=False).select_related('department', 'folder', 'created_by')
    folders_qs = Folder.objects.filter(is_archived=False)

    if role == 'EMPLOYEE' and user.primary_department:
        docs_qs = docs_qs.filter(department=user.primary_department, status='PUBLISHED')
        folders_qs = folders_qs.filter(department=user.primary_department)
        dept_query = str(user.primary_department.id)
    elif role == 'MANAGER' and user.primary_department:
        docs_qs = docs_qs.filter(department=user.primary_department)
        folders_qs = folders_qs.filter(department=user.primary_department)
        dept_query = str(user.primary_department.id)
    elif dept_query and dept_query != 'all':
        try:
            dept_id = int(dept_query)
            docs_qs = docs_qs.filter(department_id=dept_id)
            folders_qs = folders_qs.filter(department_id=dept_id)
        except ValueError:
            docs_qs = docs_qs.filter(department__name__iexact=dept_query)
            folders_qs = folders_qs.filter(department__name__iexact=dept_query)

    if folder_query:
        try:
            docs_qs = docs_qs.filter(folder_id=int(folder_query))
        except ValueError:
            docs_qs = docs_qs.filter(folder__name__iexact=folder_query)

    folders = list(folders_qs.select_related('department').order_by('name'))
    all_folders = list(Folder.objects.filter(is_archived=False).select_related('department').order_by('department__name', 'name'))

    ctx = _get_base_context(request, active_page='file_manager')
    ctx.update({
        'active_dept': dept_query,
        'current_folders': folders,
        'all_folders': all_folders,
        'documents': list(docs_qs.order_by('-created_at')),
        'selected_folder': folder_query,
    })
    return render(request, 'prototype/documents/file_manager.html', ctx)


@login_required
def document_list(request):
    return redirect('file_manager')


# ==============================================================================
# 8. DOCUMENT DETAIL + VIEW IN BROWSER + DOWNLOAD + DELETE
# ==============================================================================

@login_required
def document_detail(request, doc_id):
    user = request.user
    role = get_user_role_code(user)

    ctx = _get_base_context(request, active_page='file_manager')
    try:
        doc = Document.objects.select_related(
            'department', 'folder', 'created_by'
        ).prefetch_related('versions', 'internal_shares').get(doc_id=doc_id, is_deleted=False)
    except Document.DoesNotExist:
        raise Http404("Document not found.")

    # POST: soft delete
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete' and (role in ('SUPER_ADMIN', 'ADMIN', 'MANAGER') or doc.created_by == user):
            doc.is_deleted = True
            doc.deleted_at = timezone.now()
            doc.deleted_by = user
            doc.save()
            _log(user, 'DOCUMENT_DELETE', f'{doc.doc_id}: {doc.title}', doc=doc, request=request)
            messages.success(request, f'"{doc.title}" moved to recycle bin.')
            return redirect('file_manager')

    current_version = doc.versions.filter(is_current=True).first() or doc.versions.order_by('-version_number').first()

    ctx.update({
        'doc': doc,
        'current_version': current_version,
        'versions': list(doc.versions.all().order_by('-version_number')),
        'shares': list(doc.internal_shares.all().select_related('shared_with')),
    })
    return render(request, 'prototype/documents/document_detail.html', ctx)


@login_required
def view_document_file(request, doc_id):
    """Open/view the current version of the document directly in browser tab."""
    user = request.user
    try:
        doc = Document.objects.get(doc_id=doc_id, is_deleted=False)
    except Document.DoesNotExist:
        raise Http404("Document not found.")

    version = doc.versions.filter(is_current=True).first() or doc.versions.order_by('-version_number').first()
    if not version or not os.path.exists(version.storage_path):
        raise Http404("Document file not found on disk.")

    _log(user, 'DOCUMENT_VIEW', f'{doc.doc_id} (V{version.version_number})', doc=doc, request=request)

    mime_type, _ = mimetypes.guess_type(version.storage_path)
    if not mime_type:
        mime_type = 'application/octet-stream'

    response = FileResponse(open(version.storage_path, 'rb'), content_type=mime_type)
    response['Content-Disposition'] = f'inline; filename="{doc.original_filename}"'
    return response


@login_required
def download_document_file(request, doc_id, version_number=None):
    """Download the document or a specific version to local drive."""
    user = request.user
    try:
        doc = Document.objects.get(doc_id=doc_id, is_deleted=False)
    except Document.DoesNotExist:
        raise Http404("Document not found.")

    if version_number:
        version = get_object_or_404(doc.versions, version_number=version_number)
    else:
        version = doc.versions.filter(is_current=True).first() or doc.versions.order_by('-version_number').first()

    if not version or not os.path.exists(version.storage_path):
        raise Http404("Document file not found on disk.")

    _log(user, 'DOCUMENT_DOWNLOAD', f'{doc.doc_id} (V{version.version_number})', doc=doc, request=request)

    mime_type, _ = mimetypes.guess_type(version.storage_path)
    if not mime_type:
        mime_type = 'application/octet-stream'

    response = FileResponse(open(version.storage_path, 'rb'), content_type=mime_type, as_attachment=True, filename=doc.original_filename)
    return response


# ==============================================================================
# 9. SEARCH & LIVE API
# ==============================================================================

@login_required
def search_page(request):
    user = request.user
    role = get_user_role_code(user)

    q = request.GET.get('q', '').strip()
    dept_val = request.GET.get('dept', '').strip()
    file_type = request.GET.get('type', '').strip().lower()
    owner_val = request.GET.get('owner', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    docs_qs = Document.objects.filter(is_deleted=False).select_related('department', 'folder')
    if role == 'EMPLOYEE' and user.primary_department:
        docs_qs = docs_qs.filter(department=user.primary_department, status='PUBLISHED')
    elif role == 'MANAGER' and user.primary_department:
        docs_qs = docs_qs.filter(department=user.primary_department)

    if q:
        docs_qs = docs_qs.filter(
            Q(title__icontains=q) | Q(objective__icontains=q) |
            Q(owner__icontains=q) | Q(doc_id__icontains=q) |
            Q(original_filename__icontains=q)
        )

    if dept_val:
        docs_qs = docs_qs.filter(department__name__iexact=dept_val)

    if file_type:
        docs_qs = docs_qs.filter(original_filename__iendswith=f'.{file_type}')

    if owner_val:
        docs_qs = docs_qs.filter(owner__icontains=owner_val)

    if date_from:
        try:
            docs_qs = docs_qs.filter(document_date__gte=date.fromisoformat(date_from))
        except ValueError:
            pass

    if date_to:
        try:
            docs_qs = docs_qs.filter(document_date__lte=date.fromisoformat(date_to))
        except ValueError:
            pass

    # If AJAX requested live JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        from django.http import JsonResponse
        results = []
        for doc in docs_qs.order_by('-created_at')[:100]:
            ext = Path(doc.original_filename).suffix.lower().lstrip('.') or 'file'
            results.append({
                'doc_id': doc.doc_id,
                'title': doc.title,
                'original_filename': doc.original_filename,
                'objective': doc.objective,
                'department_name': doc.department.name if doc.department else '-',
                'folder_name': doc.folder.name if doc.folder else 'General',
                'owner': doc.owner,
                'document_date': str(doc.document_date) if doc.document_date else '',
                'created_at': doc.created_at.strftime('%Y-%m-%d %H:%M'),
                'status': doc.status,
                'ext': ext,
            })
        return JsonResponse({'count': len(results), 'documents': results})

    ctx = _get_base_context(request, active_page='search_page')
    ctx.update({
        'documents': list(docs_qs.order_by('-created_at')),
        'search_query': q,
        'search_dept': dept_val,
        'search_type': file_type,
        'search_owner': owner_val,
        'search_from': date_from,
        'search_to': date_to,
    })
    return render(request, 'prototype/documents/search_page.html', ctx)


# ==============================================================================
# 11. APPROVALS
# ==============================================================================

@login_required
def approvals_list(request):
    user = request.user
    role = get_user_role_code(user)
    if role == 'EMPLOYEE':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_dispatcher')

    # POST: approve or reject
    if request.method == 'POST':
        action = request.POST.get('action')
        req_id = request.POST.get('request_id')
        if req_id:
            try:
                upload_req = UploadRequest.objects.select_related('document', 'submitted_by').get(id=req_id)
            except UploadRequest.DoesNotExist:
                messages.error(request, 'Request not found.')
                return redirect('approvals_list')

            # Managers only approve within their department
            if role == 'MANAGER' and user.primary_department:
                if upload_req.document.department != user.primary_department:
                    messages.error(request, 'Permission denied.')
                    return redirect('approvals_list')

            if action == 'approve':
                upload_req.status = 'APPROVED'
                upload_req.reviewed_by = user
                upload_req.reviewed_at = timezone.now()
                upload_req.save()
                upload_req.document.status = 'PUBLISHED'
                upload_req.document.save()
                _log(user, 'DOCUMENT_APPROVE', upload_req.document.doc_id,
                     doc=upload_req.document, request=request,
                     details=f'Approved submission by {upload_req.submitted_by.full_name}')
                messages.success(request, f'"{upload_req.document.title}" approved and published.')
            elif action == 'reject':
                reason = request.POST.get('rejection_reason', '').strip()
                upload_req.status = 'REJECTED'
                upload_req.reviewed_by = user
                upload_req.reviewed_at = timezone.now()
                upload_req.rejection_reason = reason
                upload_req.save()
                upload_req.document.status = 'REJECTED'
                upload_req.document.save()
                _log(user, 'DOCUMENT_REJECT', upload_req.document.doc_id,
                     doc=upload_req.document, request=request,
                     details=f'Rejected. Reason: {reason}')
                messages.success(request, f'"{upload_req.document.title}" rejected.')

        return redirect('approvals_list')

    pending_qs = UploadRequest.objects.filter(status='PENDING').select_related('document', 'submitted_by', 'version')
    if role == 'MANAGER' and user.primary_department:
        pending_qs = pending_qs.filter(document__department=user.primary_department)

    ctx = _get_base_context(request, active_page='approvals_list')
    ctx['pending_documents'] = list(pending_qs.order_by('-submitted_at'))
    return render(request, 'prototype/documents/approvals_list.html', ctx)


# ==============================================================================
# 12. VERSION HISTORY + NEW VERSION UPLOAD
# ==============================================================================

@login_required
def version_history(request, doc_id):
    user = request.user
    ctx = _get_base_context(request, active_page='file_manager')
    try:
        doc = Document.objects.prefetch_related('versions').get(doc_id=doc_id, is_deleted=False)
    except Document.DoesNotExist:
        raise Http404("Document not found.")

    if request.method == 'POST' and request.POST.get('action') == 'upload_version':
        revision_note = request.POST.get('revision_note', '').strip()
        uploaded_file = request.FILES.get('version_file')
        if not uploaded_file:
            messages.error(request, 'Please select a file to upload.')
        else:
            # Mark previous versions as not current
            doc.versions.filter(is_current=True).update(is_current=False)
            new_version_number = (doc.versions.order_by('-version_number').first().version_number if doc.versions.exists() else 0) + 1
            storage_path, file_type, file_size, sha = _save_uploaded_file(uploaded_file, doc_id, new_version_number)
            DocumentVersion.objects.create(
                document=doc,
                version_number=new_version_number,
                storage_path=storage_path,
                file_type=file_type,
                file_size_bytes=file_size,
                file_hash_sha256=sha,
                is_current=True,
                revision_note=revision_note,
                uploaded_by=user,
            )
            _log(user, 'DOCUMENT_NEW_VERSION', f'{doc_id} V{new_version_number}', doc=doc, request=request)
            messages.success(request, f'Version {new_version_number} uploaded successfully.')
            return redirect('version_history', doc_id=doc_id)

    ctx.update({
        'doc': doc,
        'versions': list(doc.versions.all().order_by('-version_number')),
    })
    return render(request, 'prototype/documents/version_history.html', ctx)


# ==============================================================================
# 13. RECYCLE BIN
# ==============================================================================

@login_required
def recycle_bin(request):
    role = get_user_role_code(request.user)
    if role not in ['SUPER_ADMIN', 'ADMIN']:
        return redirect('dashboard_dispatcher')

    if request.method == 'POST':
        action = request.POST.get('action')
        doc_id = request.POST.get('doc_id')
        if doc_id:
            try:
                doc = Document.objects.get(doc_id=doc_id, is_deleted=True)
            except Document.DoesNotExist:
                messages.error(request, 'Document not found in recycle bin.')
                return redirect('recycle_bin')

            if action == 'restore':
                doc.is_deleted = False
                doc.deleted_at = None
                doc.deleted_by = None
                doc.save()
                _log(request.user, 'DOCUMENT_RESTORE', doc_id, doc=doc, request=request)
                messages.success(request, f'"{doc.title}" restored successfully.')
            elif action == 'permanent_delete':
                title = doc.title
                # Remove physical files
                storage_root = getattr(settings, 'STORAGE_ROOT', Path('C:/fileMngSys'))
                doc_dir = Path(storage_root) / str(doc_id)
                if doc_dir.exists():
                    import shutil
                    shutil.rmtree(doc_dir, ignore_errors=True)
                doc.delete()
                _log(request.user, 'DOCUMENT_PERMANENT_DELETE', doc_id, request=request,
                     details=f'Permanently deleted: {title}')
                messages.success(request, f'"{title}" permanently deleted.')

        return redirect('recycle_bin')

    ctx = _get_base_context(request, active_page='recycle_bin')
    deleted_docs = list(Document.objects.filter(is_deleted=True).select_related('department', 'folder', 'deleted_by').order_by('-deleted_at'))
    ctx['deleted_items'] = deleted_docs
    return render(request, 'prototype/documents/recycle_bin.html', ctx)


# ==============================================================================
# 14. DOCUMENT SHARING
# ==============================================================================

@login_required
def share_interface(request, doc_id):
    user = request.user
    ctx = _get_base_context(request, active_page='file_manager')
    try:
        doc = Document.objects.prefetch_related('internal_shares').get(doc_id=doc_id, is_deleted=False)
    except Document.DoesNotExist:
        raise Http404("Document not found.")

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'share':
            share_user_id = request.POST.get('user_id')
            permission_level = request.POST.get('permission_level', 'VIEW')
            expires_at_str = request.POST.get('expires_at', '')
            expires_at = None
            if expires_at_str:
                try:
                    expires_at = date.fromisoformat(expires_at_str)
                except ValueError:
                    expires_at = None
            try:
                target_user = User.objects.get(id=share_user_id)
                share, created = DocumentShare.objects.update_or_create(
                    document=doc,
                    shared_with=target_user,
                    defaults={
                        'granted_by': user,
                        'permission_level': permission_level,
                        'expires_at': expires_at,
                        'is_revoked': False,
                    }
                )
                _log(user, 'DOCUMENT_SHARE', f'{doc_id} -> {target_user.email}', doc=doc, request=request)
                messages.success(request, f'Access granted to {target_user.full_name}.')
            except User.DoesNotExist:
                messages.error(request, 'Selected user not found.')

        elif action == 'revoke':
            share_id = request.POST.get('share_id')
            try:
                share = DocumentShare.objects.get(id=share_id, document=doc)
                share.is_revoked = True
                share.save()
                _log(user, 'DOCUMENT_SHARE_REVOKE', f'{doc_id} -> {share.shared_with.email}', doc=doc, request=request)
                messages.success(request, f'Access revoked for {share.shared_with.full_name}.')
            except DocumentShare.DoesNotExist:
                messages.error(request, 'Share record not found.')

        return redirect('share_interface', doc_id=doc_id)

    ctx.update({
        'doc': doc,
        'shares': list(doc.internal_shares.filter(is_revoked=False).select_related('shared_with')),
        'users': list(User.objects.filter(is_active=True).exclude(id=user.id).values('id', 'full_name', 'email')),
    })
    return render(request, 'prototype/documents/share_interface.html', ctx)


# ==============================================================================
# 15. USER MANAGEMENT (Create / Edit / Deactivate / Delete)
# ==============================================================================

@login_required
def user_management(request):
    user = request.user
    role = get_user_role_code(user)
    if role not in ['SUPER_ADMIN', 'ADMIN']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard_dispatcher')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_user':
            email = request.POST.get('email', '').strip()
            full_name = request.POST.get('full_name', '').strip()
            password = request.POST.get('password', '')
            role_id = request.POST.get('role_id')
            department_id = request.POST.get('department_id')

            if not email or not password or not full_name:
                messages.error(request, 'Full name, email, and password are all required.')
            elif User.objects.filter(email__iexact=email).exists():
                messages.error(request, f'An account with email "{email}" already exists.')
            else:
                selected_role = None
                if role_id:
                    try:
                        selected_role = Role.objects.get(id=role_id)
                    except Role.DoesNotExist:
                        pass

                selected_dept = None
                if department_id:
                    try:
                        selected_dept = Department.objects.get(id=department_id)
                    except Department.DoesNotExist:
                        pass

                is_staff_val = selected_role and selected_role.code in ['SUPER_ADMIN', 'ADMIN']
                is_super_val = selected_role and selected_role.code == 'SUPER_ADMIN'

                new_user = User.objects.create_user(
                    email=email,
                    full_name=full_name,
                    password=password,
                    role=selected_role,
                    primary_department=selected_dept,
                    is_staff=bool(is_staff_val),
                    is_superuser=bool(is_super_val),
                    is_active=True,
                )
                _log(user, 'USER_CREATE', f'{new_user.email}', request=request,
                     details=f'Role: {selected_role.name if selected_role else "none"}, Dept: {selected_dept.name if selected_dept else "none"}')
                messages.success(request, f'Account for {new_user.full_name} ({new_user.email}) created.')

        elif action == 'edit_user':
            target_user_id = request.POST.get('user_id')
            try:
                target_user = User.objects.get(id=target_user_id)
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
                return redirect('user_management')

            if get_user_role_code(target_user) == 'SUPER_ADMIN' and role != 'SUPER_ADMIN':
                messages.error(request, 'Permission denied.')
                return redirect('user_management')

            full_name = request.POST.get('full_name', '').strip()
            role_id = request.POST.get('role_id')
            department_id = request.POST.get('department_id')
            new_password = request.POST.get('new_password', '').strip()

            if full_name:
                target_user.full_name = full_name
            if role_id:
                try:
                    sel_role = Role.objects.get(id=role_id)
                    target_user.role = sel_role
                    target_user.is_staff = sel_role.code in ['SUPER_ADMIN', 'ADMIN']
                    target_user.is_superuser = sel_role.code == 'SUPER_ADMIN'
                except Role.DoesNotExist:
                    pass
            if department_id:
                try:
                    target_user.primary_department = Department.objects.get(id=department_id)
                except Department.DoesNotExist:
                    target_user.primary_department = None
            elif department_id == '':
                target_user.primary_department = None
            if new_password:
                target_user.set_password(new_password)
            target_user.save()
            _log(user, 'USER_EDIT', target_user.email, request=request)
            messages.success(request, f'Account for {target_user.full_name} updated.')

        elif action == 'toggle_active':
            target_user_id = request.POST.get('user_id')
            try:
                target_user = User.objects.get(id=target_user_id)
                if target_user == user:
                    messages.error(request, 'You cannot deactivate your own account.')
                else:
                    target_user.is_active = not target_user.is_active
                    target_user.save()
                    status_str = 'activated' if target_user.is_active else 'deactivated'
                    _log(user, 'USER_TOGGLE_ACTIVE', target_user.email, request=request,
                         details=f'Account {status_str}')
                    messages.success(request, f'Account {target_user.full_name} {status_str}.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')

        elif action == 'delete_user':
            target_user_id = request.POST.get('user_id')
            if role != 'SUPER_ADMIN':
                messages.error(request, 'Only Super Administrators can delete user accounts.')
                return redirect('user_management')

            try:
                target_user = User.objects.get(id=target_user_id)
                if target_user == user:
                    messages.error(request, 'You cannot delete your own account.')
                else:
                    user_email = target_user.email
                    user_name = target_user.full_name
                    target_user.delete()
                    _log(user, 'USER_DELETE', user_email, request=request,
                         details=f'Permanently deleted user: {user_name} ({user_email})')
                    messages.success(request, f'User account {user_name} ({user_email}) deleted permanently.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')

        return redirect('user_management')

    ctx = _get_base_context(request, active_page='users',
                             active_role='super_admin' if role == 'SUPER_ADMIN' else 'admin')
    ctx.update({
        'users': list(User.objects.all().select_related('role', 'primary_department').order_by('full_name')),
        'all_roles': list(Role.objects.all().order_by('id')),
        'all_departments': list(Department.objects.filter(is_active=True).order_by('name')),
    })
    return render(request, 'prototype/admin/user_management.html', ctx)


# ==============================================================================
# 16. DEPARTMENT MANAGEMENT (Create / Edit / Deactivate / Delete / Folders)
# ==============================================================================

@login_required
def department_management(request):
    user = request.user
    role = get_user_role_code(user)
    if role != 'SUPER_ADMIN':
        messages.error(request, 'Only Super Administrators can manage departments.')
        return redirect('dashboard_dispatcher')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_department':
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip().upper()
            description = request.POST.get('description', '').strip()
            quota_mb = int(request.POST.get('quota_mb', 10240) or 10240)
            manager_id = request.POST.get('manager_id') or None

            if not name or not code:
                messages.error(request, 'Department name and code are required.')
            elif Department.objects.filter(code=code).exists():
                messages.error(request, f'A department with code "{code}" already exists.')
            elif Department.objects.filter(name=name).exists():
                messages.error(request, f'A department named "{name}" already exists.')
            else:
                manager = None
                if manager_id:
                    try:
                        manager = User.objects.get(id=manager_id)
                    except User.DoesNotExist:
                        pass
                dept = Department.objects.create(
                    name=name, code=code, description=description,
                    max_quota_mb=quota_mb, manager=manager, is_active=True,
                )
                # Automatically create default 'General' folder for the new department
                Folder.objects.create(
                    name='General',
                    department=dept,
                    created_by=user,
                    is_archived=False
                )
                _log(user, 'DEPT_CREATE', f'{code}: {name}', request=request)
                messages.success(request, f'Department "{name}" created with default "General" folder.')

        elif action == 'edit_department':
            dept_id = request.POST.get('dept_id')
            try:
                dept = Department.objects.get(id=dept_id)
            except Department.DoesNotExist:
                messages.error(request, 'Department not found.')
                return redirect('department_management')
            dept.name = request.POST.get('name', dept.name).strip() or dept.name
            dept.description = request.POST.get('description', dept.description)
            quota_mb = request.POST.get('quota_mb')
            if quota_mb:
                dept.max_quota_mb = int(quota_mb)
            manager_id = request.POST.get('manager_id')
            if manager_id:
                try:
                    dept.manager = User.objects.get(id=manager_id)
                except User.DoesNotExist:
                    dept.manager = None
            else:
                dept.manager = None
            dept.save()
            _log(user, 'DEPT_EDIT', dept.code, request=request)
            messages.success(request, f'Department "{dept.name}" updated.')

        elif action == 'toggle_department':
            dept_id = request.POST.get('dept_id')
            try:
                dept = Department.objects.get(id=dept_id)
                dept.is_active = not dept.is_active
                dept.save()
                status_str = 'activated' if dept.is_active else 'deactivated'
                _log(user, 'DEPT_TOGGLE', dept.code, request=request, details=status_str)
                messages.success(request, f'Department "{dept.name}" {status_str}.')
            except Department.DoesNotExist:
                messages.error(request, 'Department not found.')

        elif action == 'delete_department':
            dept_id = request.POST.get('dept_id')
            try:
                dept = Department.objects.get(id=dept_id)
                # Check for active non-deleted documents
                if dept.documents.filter(is_deleted=False).exists():
                    messages.error(request, f'Cannot delete department "{dept.name}": active documents exist inside it. Please delete or move them first.')
                else:
                    dept_name = dept.name
                    dept_code = dept.code
                    # Remove any folders inside this department
                    dept.folders.all().delete()
                    dept.delete()
                    _log(user, 'DEPT_DELETE', f'{dept_code}: {dept_name}', request=request)
                    messages.success(request, f'Department "{dept_name}" deleted.')
            except Department.DoesNotExist:
                messages.error(request, 'Department not found.')

        elif action == 'create_folder':
            dept_id = request.POST.get('dept_id')
            folder_name = request.POST.get('folder_name', '').strip()
            parent_id = request.POST.get('parent_id') or None
            if not folder_name or not dept_id:
                messages.error(request, 'Folder name and department are required.')
            else:
                try:
                    dept = Department.objects.get(id=dept_id)
                    parent = None
                    if parent_id:
                        try:
                            parent = Folder.objects.get(id=parent_id, department=dept)
                        except Folder.DoesNotExist:
                            pass
                    Folder.objects.get_or_create(
                        name=folder_name, department=dept, parent=parent,
                        defaults={'created_by': user, 'is_archived': False}
                    )
                    _log(user, 'FOLDER_CREATE', f'{dept.code}/{folder_name}', request=request)
                    messages.success(request, f'Folder "{folder_name}" created in {dept.name}.')
                except Department.DoesNotExist:
                    messages.error(request, 'Department not found.')

        elif action == 'delete_folder':
            folder_id = request.POST.get('folder_id')
            try:
                folder = Folder.objects.get(id=folder_id)
                if folder.documents.filter(is_deleted=False).exists():
                    messages.error(request, f'Cannot delete folder "{folder.name}": it contains documents. Move or delete them first.')
                else:
                    fname = folder.name
                    folder.delete()
                    _log(user, 'FOLDER_DELETE', fname, request=request)
                    messages.success(request, f'Folder "{fname}" deleted.')
            except Folder.DoesNotExist:
                messages.error(request, 'Folder not found.')

        return redirect('department_management')

    depts = list(Department.objects.all().select_related('manager').order_by('name'))
    folders_by_dept = {}
    for f in Folder.objects.filter(is_archived=False).select_related('department').order_by('name'):
        folders_by_dept.setdefault(f.department_id, []).append(f)

    managers = list(User.objects.filter(is_active=True, role__code__in=['MANAGER', 'ADMIN', 'SUPER_ADMIN']).order_by('full_name'))

    ctx = _get_base_context(request, active_page='departments', active_role='super_admin')
    ctx.update({
        'departments': depts,
        'folders_by_dept': folders_by_dept,
        'managers': managers,
    })
    return render(request, 'prototype/admin/department_management.html', ctx)


# ==============================================================================
# 17. PERMISSION MANAGEMENT (Editable overrides & role mapping)
# ==============================================================================

@login_required
def permission_management(request):
    user = request.user
    role = get_user_role_code(user)
    if role != 'SUPER_ADMIN':
        messages.error(request, 'Only Super Administrators can manage permissions.')
        return redirect('dashboard_dispatcher')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_override':
            target_user_id = request.POST.get('user_id')
            reason = request.POST.get('reason', '').strip()

            try:
                target_user = User.objects.get(id=target_user_id)
                # Clear existing individual overrides for this user
                UserPermissionOverride.objects.filter(user=target_user).delete()

                # Process all capabilities submitted via checkboxes
                for perm in SystemPermission.objects.all():
                    val = request.POST.get(f'perm_state_{perm.code.replace(":", "_")}')
                    if val in ('GRANT', 'DENY'):
                        UserPermissionOverride.objects.create(
                            user=target_user,
                            permission=perm,
                            override_type=val,
                            reason=reason
                        )

                _log(user, 'PERMISSION_OVERRIDE', f'{target_user.email} overrides updated', request=request)
                messages.success(request, f'Permission overrides updated for {target_user.full_name}.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')

        elif action == 'save_role_permissions':
            # Matrix mapping: role_code -> list of perm codes
            for r in Role.objects.exclude(code='SUPER_ADMIN'):
                RolePermission.objects.filter(role=r).delete()
                for perm_code in ['doc:upload', 'doc:approve', 'doc:delete', 'user:manage', 'audit:view', 'bin:manage']:
                    field_name = f'perm_{r.code}_{perm_code.replace(":", "_")}'
                    if request.POST.get(field_name):
                        try:
                            p = SystemPermission.objects.get(code=perm_code)
                            RolePermission.objects.create(role=r, permission=p)
                        except SystemPermission.DoesNotExist:
                            pass
            _log(user, 'ROLE_PERMISSIONS_UPDATE', 'Default Role Capabilities Matrix', request=request)
            messages.success(request, 'Role capabilities matrix updated successfully.')

        elif action == 'reset_role_permissions':
            # Reset roles to default capabilities
            defaults = {
                'SUPER_ADMIN': ['doc:upload', 'doc:approve', 'doc:delete', 'user:manage', 'audit:view', 'bin:manage'],
                'ADMIN': ['doc:upload', 'doc:approve', 'doc:delete', 'user:manage', 'audit:view', 'bin:manage'],
                'MANAGER': ['doc:upload', 'doc:approve', 'doc:delete'],
                'EMPLOYEE': ['doc:upload'],
            }
            RolePermission.objects.all().delete()
            for role_code, perm_codes in defaults.items():
                try:
                    r = Role.objects.get(code=role_code)
                    for pc in perm_codes:
                        p = SystemPermission.objects.get(code=pc)
                        RolePermission.objects.create(role=r, permission=p)
                except Exception:
                    pass
            _log(user, 'ROLE_PERMISSIONS_RESET', 'Default Role Capabilities Matrix', request=request)
            messages.success(request, 'Role capabilities have been reset to default policies.')
        elif action == 'delete_override':
            override_id = request.POST.get('override_id')
            try:
                override = UserPermissionOverride.objects.get(id=override_id)
                target_name = override.user.full_name
                override.delete()
                _log(user, 'PERMISSION_OVERRIDE_DELETE', f'Override #{override_id}', request=request)
                messages.success(request, f'Permission override removed for {target_name}.')
            except UserPermissionOverride.DoesNotExist:
                messages.error(request, 'Override not found.')

        return redirect('permission_management')

    roles = Role.objects.all().order_by('id')
    role_list = []
    for r in roles:
        assigned_perm_codes = set(r.role_permissions.values_list('permission__code', flat=True)) if r.code != 'SUPER_ADMIN' else {
            'doc:upload', 'doc:approve', 'doc:delete', 'user:manage', 'audit:view', 'bin:manage'
        }
        role_list.append({
            'role': r.name,
            'code': r.code,
            'user_count': r.users.count(),
            'scope': 'System-wide' if r.code == 'SUPER_ADMIN' else (
                'All Departments' if r.code == 'ADMIN' else (
                    'Own Department' if r.code == 'MANAGER' else 'Permitted Folders')),
            'is_super': r.code == 'SUPER_ADMIN',
            'can_upload': 'doc:upload' in assigned_perm_codes,
            'can_approve': 'doc:approve' in assigned_perm_codes,
            'can_delete': 'doc:delete' in assigned_perm_codes,
            'can_manage_users': 'user:manage' in assigned_perm_codes,
            'can_view_audit': 'audit:view' in assigned_perm_codes,
            'can_restore_bin': 'bin:manage' in assigned_perm_codes,
        })

    # Fetch real users and their permission overrides
    users_with_overrides = []
    real_users = User.objects.all().select_related('role', 'primary_department').prefetch_related('individual_permissions__permission').order_by('full_name')

    for u in real_users:
        overrides = list(u.individual_permissions.all())
        grants = [o for o in overrides if o.override_type == 'GRANT']
        denials = [o for o in overrides if o.override_type == 'DENY']
        users_with_overrides.append({
            'user': u,
            'is_super': u.is_superuser or (u.role and u.role.code == 'SUPER_ADMIN'),
            'grants': grants,
            'denials': denials,
            'overrides': overrides,
        })

    all_permissions = list(SystemPermission.objects.all().order_by('category', 'name'))

    ctx = _get_base_context(request, active_page='permissions', active_role='super_admin')
    ctx.update({
        'roles_permissions': role_list,
        'users_with_overrides': users_with_overrides,
        'all_users': real_users,
        'all_permissions': all_permissions,
    })
    return render(request, 'prototype/admin/permission_management.html', ctx)


# ==============================================================================
# 18. ACTIVITY LOGS
# ==============================================================================

@login_required
def activity_logs(request):
    if get_user_role_code(request.user) not in ['SUPER_ADMIN', 'ADMIN']:
        return redirect('dashboard_dispatcher')
    ctx = _get_base_context(request, active_page='activity_logs', active_role='super_admin')
    logs = list(ActivityLog.objects.all().select_related('user', 'document').order_by('-timestamp')[:100])
    ctx['logs'] = logs
    return render(request, 'prototype/admin/activity_logs.html', ctx)


# ==============================================================================
# 19. STORAGE MONITORING
# ==============================================================================

@login_required
def storage_monitoring(request):
    if get_user_role_code(request.user) != 'SUPER_ADMIN':
        return redirect('dashboard_dispatcher')
    ctx = _get_base_context(request, active_page='storage', active_role='super_admin')

    total_bytes = sum(v.file_size_bytes for v in DocumentVersion.objects.filter(is_current=True))
    used_gb = round(total_bytes / (1024 ** 3), 4)

    dept_breakdown = []
    for dept in Department.objects.filter(is_active=True):
        dept_bytes = sum(
            v.file_size_bytes for v in DocumentVersion.objects.filter(
                is_current=True, document__department=dept
            )
        )
        dept_gb = round(dept_bytes / (1024 ** 3), 4)
        quota_gb = dept.max_quota_mb / 1024
        pct = round((dept_gb / quota_gb) * 100, 1) if quota_gb else 0
        dept_breakdown.append({
            'name': dept.name,
            'used_gb': dept_gb,
            'quota_gb': quota_gb,
            'percentage': min(pct, 100),
            'color': '#EF4444' if pct > 90 else ('#F59E0B' if pct > 70 else '#3B82F6'),
        })

    storage_stats = {
        'total_capacity_gb': 500,
        'used_storage_gb': used_gb,
        'free_storage_gb': round(500 - used_gb, 4),
        'usage_percentage': round((used_gb / 500) * 100, 2),
        'breakdown': dept_breakdown,
    }
    ctx['storage_stats'] = storage_stats
    return render(request, 'prototype/admin/storage_monitoring.html', ctx)


# ==============================================================================
# 20. SYSTEM SETTINGS
# ==============================================================================

@login_required
def system_settings(request):
    if get_user_role_code(request.user) != 'SUPER_ADMIN':
        return redirect('dashboard_dispatcher')
    ctx = _get_base_context(request, active_page='settings', active_role='super_admin')
    return render(request, 'prototype/admin/system_settings.html', ctx)
