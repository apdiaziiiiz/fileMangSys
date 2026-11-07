"""
Part 2A CRUD Verification Test
Exercises all 13 models end-to-end to confirm relationships work correctly.
Run with: python manage.py shell < crud_test.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fileMangSys.settings')
django.setup()

from django.utils import timezone
from ui_prototype.models import (
    Role, SystemPermission, RolePermission,
    Department, User, DepartmentAssignment, UserPermissionOverride,
    Folder, FolderPermission,
    Document, DocumentVersion,
    UploadRequest, DocumentShare, ActivityLog,
)

print("=" * 60)
print("DMS Part 2A - CRUD Verification Test")
print("=" * 60)

errors = []

def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    print(f"  {status} - {label}")
    if not condition:
        errors.append(label)

# ------------------------------------------------------------------
# 1. CLEAN UP previous test data
# ------------------------------------------------------------------
print("\n[0] Cleaning previous test data...")
ActivityLog.objects.filter(action__startswith='CRUD_TEST').delete()
DocumentShare.objects.filter(document__doc_id='CRUD-001').delete()
UploadRequest.objects.filter(document__doc_id='CRUD-001').delete()
DocumentVersion.objects.filter(document__doc_id='CRUD-001').delete()
Document.objects.filter(doc_id='CRUD-001').delete()
FolderPermission.objects.filter(folder__name='CRUD Test Folder').delete()
Folder.objects.filter(name='CRUD Test Folder').delete()
UserPermissionOverride.objects.filter(reason='crud_test').delete()
DepartmentAssignment.objects.filter(user__email='crud_manager@test.com').delete()
User.objects.filter(email__in=['crud_emp@test.com', 'crud_manager@test.com']).delete()
Department.objects.filter(code='CRUD').delete()
RolePermission.objects.filter(permission__code='crud:test').delete()
SystemPermission.objects.filter(code='crud:test').delete()
Role.objects.filter(code__in=['MANAGER', 'EMPLOYEE']).delete()
print("  Done.")

# ------------------------------------------------------------------
# 2. ROLES & PERMISSIONS
# ------------------------------------------------------------------
print("\n[1] Roles & Permissions...")
manager_role, _ = Role.objects.get_or_create(code='MANAGER', defaults={'name': 'Manager'})
employee_role, _ = Role.objects.get_or_create(code='EMPLOYEE', defaults={'name': 'Employee'})
perm = SystemPermission.objects.create(code='crud:test', name='CRUD Test Permission', category='Test')
rp = RolePermission.objects.create(role=manager_role, permission=perm)

check("manager_role created", manager_role.pk is not None)
check("employee_role created", employee_role.pk is not None)
check("SystemPermission created", perm.pk is not None)
check("RolePermission links role→permission", rp.role == manager_role and rp.permission == perm)

# ------------------------------------------------------------------
# 3. DEPARTMENTS
# ------------------------------------------------------------------
print("\n[2] Departments...")
dept = Department.objects.create(code='CRUD', name='CRUD Test Department', max_quota_mb=512)
check("Department created", dept.pk is not None)
check("Department code correct", dept.code == 'CRUD')

# ------------------------------------------------------------------
# 4. USERS
# ------------------------------------------------------------------
print("\n[3] Users...")
manager = User.objects.create_user(
    email='crud_manager@test.com',
    full_name='CRUD Manager',
    password='TestPass123!',
    role=manager_role,
    primary_department=dept,
    is_staff=True,
)
employee = User.objects.create_user(
    email='crud_emp@test.com',
    full_name='CRUD Employee',
    password='TestPass456!',
    role=employee_role,
    primary_department=dept,
)
check("Manager user created", manager.pk is not None)
check("Manager user_id_code length ok", len(str(manager.user_id_code)) == 36)
check("Employee user created", employee.pk is not None)
check("Password hashed (not plain text)", manager.password != 'TestPass123!')

# ------------------------------------------------------------------
# 5. DEPARTMENT ASSIGNMENT & USER PERMISSION OVERRIDE
# ------------------------------------------------------------------
print("\n[4] Department Assignment & User Permission Override...")
assignment = DepartmentAssignment.objects.create(
    user=manager, department=dept, can_upload=True, can_approve=True
)
override = UserPermissionOverride.objects.create(
    user=employee, permission=perm, override_type='DENY', reason='crud_test'
)
check("DepartmentAssignment created", assignment.pk is not None)
check("Assignment links user→dept", assignment.user == manager and assignment.department == dept)
check("UserPermissionOverride created", override.pk is not None)
check("Override is DENY type", override.override_type == 'DENY')

# ------------------------------------------------------------------
# 6. FOLDERS & FOLDER PERMISSIONS
# ------------------------------------------------------------------
print("\n[5] Folders & Folder Permissions...")
folder = Folder.objects.create(name='CRUD Test Folder', department=dept, created_by=manager)
subfolder = Folder.objects.create(name='CRUD Subfolder', department=dept, parent=folder, created_by=manager)
fp = FolderPermission.objects.create(folder=folder, role=manager_role, can_read=True, can_write=True)
check("Root folder created", folder.pk is not None)
check("Subfolder with parent created", subfolder.parent == folder)
check("FolderPermission created", fp.pk is not None)
check("FolderPermission links to role", fp.role == manager_role)

# ------------------------------------------------------------------
# 7. DOCUMENTS & VERSIONS
# ------------------------------------------------------------------
print("\n[6] Documents & Document Versions...")
doc = Document.objects.create(
    doc_id='CRUD-001',
    title='CRUD Test Document',
    original_filename='crud_test.pdf',
    objective='Verify CRUD operations for Part 2A',
    owner='CRUD Manager',
    department=dept,
    folder=folder,
    document_date=timezone.now().date(),
    status='PENDING',
    created_by=manager,
)
version = DocumentVersion.objects.create(
    document=doc,
    version_number=1,
    storage_path='/nas/dms/crud/crud_test_v1.pdf',
    file_type='pdf',
    file_size_bytes=102400,
    file_hash_sha256='a' * 64,
    is_current=True,
    revision_note='Initial version for CRUD test',
    uploaded_by=manager,
)
check("Document created", doc.pk is not None)
check("Document status is PENDING", doc.status == 'PENDING')
check("DocumentVersion created", version.pk is not None)
check("Version links to document", version.document == doc)
check("Version number is 1", version.version_number == 1)

# ------------------------------------------------------------------
# 8. UPLOAD REQUEST & APPROVAL WORKFLOW
# ------------------------------------------------------------------
print("\n[7] Upload Request...")
upload_req = UploadRequest.objects.create(
    document=doc,
    version=version,
    submitted_by=employee,
    status='PENDING',
)
check("UploadRequest created", upload_req.pk is not None)
check("UploadRequest is PENDING", upload_req.status == 'PENDING')

# Simulate approval
upload_req.status = 'APPROVED'
upload_req.reviewed_by = manager
upload_req.reviewed_at = timezone.now()
upload_req.save()
upload_req.refresh_from_db()
check("UploadRequest approved and saved", upload_req.status == 'APPROVED')
check("UploadRequest reviewed_by is manager", upload_req.reviewed_by == manager)

# ------------------------------------------------------------------
# 9. DOCUMENT SHARE
# ------------------------------------------------------------------
print("\n[8] Document Share...")
share = DocumentShare.objects.create(
    document=doc,
    shared_with=employee,
    granted_by=manager,
    permission_level='DOWNLOAD',
)
check("DocumentShare created", share.pk is not None)
check("Share permission level is DOWNLOAD", share.permission_level == 'DOWNLOAD')

# ------------------------------------------------------------------
# 10. ACTIVITY LOG
# ------------------------------------------------------------------
print("\n[9] Activity Log...")
log = ActivityLog.objects.create(
    user=manager,
    user_name_snapshot=manager.full_name,
    role_snapshot='MANAGER',
    action='CRUD_TEST_UPLOAD',
    target_resource=f'Document:{doc.doc_id}',
    document=doc,
    client_ip='127.0.0.1',
    result='Success',
    details='Automated CRUD verification test for Part 2A',
)
check("ActivityLog created", log.pk is not None)
check("Log links to user and document", log.user == manager and log.document == doc)

# ------------------------------------------------------------------
# 11. RELATIONSHIP QUERIES
# ------------------------------------------------------------------
print("\n[10] Relationship queries...")
dept_docs = dept.documents.count()
doc_versions = doc.versions.count()
user_logs = manager.activity_logs.count()
user_shares = employee.received_shares.count()
folder_subs = folder.subfolders.count()
role_users = manager_role.users.count()

check("Department has 1 document", dept_docs == 1)
check("Document has 1 version", doc_versions == 1)
check("Manager has activity logs", user_logs >= 1)
check("Employee received share", user_shares >= 1)
check("Folder has 1 subfolder", folder_subs == 1)
check("Manager role has users", role_users >= 1)

# ------------------------------------------------------------------
# 12. UPDATE & DELETE (non-destructive)
# ------------------------------------------------------------------
print("\n[11] Update & soft-delete...")
doc.status = 'APPROVED'
doc.save()
doc.refresh_from_db()
check("Document status updated to APPROVED", doc.status == 'APPROVED')

doc.is_deleted = True
doc.deleted_at = timezone.now()
doc.deleted_by = manager
doc.save()
doc.refresh_from_db()
check("Document soft-deleted (is_deleted=True)", doc.is_deleted is True)
check("deleted_by set to manager", doc.deleted_by == manager)

# Restore
doc.is_deleted = False
doc.deleted_at = None
doc.deleted_by = None
doc.save()
check("Document restored from soft-delete", doc.is_deleted is False)

# ------------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------------
print("\n" + "=" * 60)
total = 30  # expected number of checks
passed = total - len(errors)
print(f"RESULT: {passed}/{total} checks passed.")
if errors:
    print("\nFailed checks:")
    for e in errors:
        print(f"  ✗ {e}")
else:
    print("\n✓ ALL CHECKS PASSED — Part 2A CRUD verification complete!")
print("=" * 60)
