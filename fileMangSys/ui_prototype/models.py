"""
Database Models for the Department-Based Document Management System (DMS).
Covers:
- Custom User & Roles (Super Admin, Admin, Manager, Employee)
- Granular Permissions & Individual User Overrides (Grant / Deny)
- Departments & Multi-Department Assignments
- Departmental Folder Hierarchy & Folder Permissions
- Permanent Documents & Physical Multi-Version Separation
- Employee Submission & Approval Workflows
- Internal Peer Document Sharing
- Comprehensive System Audit Activity Logging
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


# ==============================================================================
# 1. RBAC & PERMISSION MODELS
# ==============================================================================

class Role(models.Model):
    """
    Core organizational user roles.
    Values: Super Administrator, Administrator, Manager, Employee.
    """
    SUPER_ADMIN = 'SUPER_ADMIN'
    ADMIN = 'ADMIN'
    MANAGER = 'MANAGER'
    EMPLOYEE = 'EMPLOYEE'

    ROLE_CHOICES = [
        (SUPER_ADMIN, 'Super Administrator'),
        (ADMIN, 'Administrator'),
        (MANAGER, 'Manager'),
        (EMPLOYEE, 'Employee'),
    ]

    code = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dms_roles'
        ordering = ['id']

    def __str__(self):
        return self.name


class SystemPermission(models.Model):
    """
    Specific discrete operations (e.g. doc:upload, doc:approve, doc:delete, doc:download).
    """
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, default='Document')
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'dms_permissions'
        ordering = ['category', 'code']

    def __str__(self):
        return f"{self.category}: {self.name} ({self.code})"


class RolePermission(models.Model):
    """
    Maps baseline capabilities to system roles.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(SystemPermission, on_delete=models.CASCADE, related_name='permission_roles')

    class Meta:
        db_table = 'dms_role_permissions'
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.name} -> {self.permission.code}"


# ==============================================================================
# 2. DEPARTMENT MODELS
# ==============================================================================

class Department(models.Model):
    """
    Departments act as top-level storage directories and boundaries.
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)
    max_quota_mb = models.PositiveIntegerField(default=10240, help_text="Storage quota in Megabytes")
    is_active = models.BooleanField(default=True)
    manager = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dms_departments'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


# ==============================================================================
# 3. USER MANAGEMENT & INDIVIDUAL OVERRIDES
# ==============================================================================

class UserManager(BaseUserManager):
    """
    Custom user manager supporting corporate email authentication.
    """
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is mandatory for enterprise user accounts.')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom enterprise user model tied to a primary department and a designated role.
    """
    user_id_code = models.CharField(max_length=36, unique=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    full_name = models.CharField(max_length=180)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users', null=True, blank=True)
    primary_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_users'
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'dms_users'
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class DepartmentAssignment(models.Model):
    """
    Allows Admins and Managers to oversee/access multiple departments beyond their primary one.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='department_assignments')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='user_assignments')
    can_upload = models.BooleanField(default=True)
    can_approve = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dms_department_assignments'
        unique_together = ('user', 'department')

    def __str__(self):
        return f"{self.user.full_name} -> {self.department.name}"


class UserPermissionOverride(models.Model):
    """
    Explicit Individual Permission Grants or Denials (Spec §4).
    Individual rules override general role permissions.
    """
    OVERRIDE_CHOICES = [
        ('GRANT', 'Explicit Grant'),
        ('DENY', 'Explicit Denial'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='individual_permissions')
    permission = models.ForeignKey(SystemPermission, on_delete=models.CASCADE, related_name='user_overrides')
    override_type = models.CharField(max_length=10, choices=OVERRIDE_CHOICES, default='GRANT')
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dms_user_permissions'
        unique_together = ('user', 'permission')

    def __str__(self):
        return f"{self.user.full_name} [{self.override_type}] {self.permission.code}"


# ==============================================================================
# 4. FOLDERS & FOLDER PERMISSIONS
# ==============================================================================

class Folder(models.Model):
    """
    Folder hierarchy inside a department. Supports self-referential subfolders.
    """
    name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='folders')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders'
    )
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_folders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dms_folders'
        unique_together = ('department', 'parent', 'name')
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.department.code}/{self.parent.name}/{self.name}"
        return f"{self.department.code}/{self.name}"


class FolderPermission(models.Model):
    """
    Access rules for folders by Role or specific User.
    """
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='permissions')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True, related_name='folder_permissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='folder_permissions')
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'dms_folder_permissions'

    def __str__(self):
        target = self.user.full_name if self.user else (self.role.name if self.role else 'Public')
        return f"{self.folder.name} -> {target}"


# ==============================================================================
# 5. DOCUMENTS & MULTI-VERSION SEPARATION
# ==============================================================================

class Document(models.Model):
    """
    Permanent Document Identity and Searchable Metadata (Spec §7, §12, §20).
    Moving or revising a document preserves its permanent ID.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]

    doc_id = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=255, db_index=True)
    original_filename = models.CharField(max_length=255)
    objective = models.TextField(help_text="Why the document exists or what it achieves")
    owner = models.CharField(max_length=150, help_text="Responsible person or team")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='documents')
    folder = models.ForeignKey(Folder, on_delete=models.PROTECT, related_name='documents', null=True, blank=True)
    document_date = models.DateField(help_text="Associated date written on document")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    # 30-day Recycle bin lifecycle (Spec §13)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_documents')

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_documents')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dms_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['department', 'status', 'is_deleted']),
            models.Index(fields=['title']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.doc_id}: {self.title}"


class DocumentVersion(models.Model):
    """
    Physical Stored Versions of a Document (Spec §12, §20).
    Separates file storage paths and metadata from permanent document entity.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField(default=1)
    storage_path = models.CharField(max_length=500, help_text="Path on central LAN storage or NAS")
    file_type = models.CharField(max_length=20, help_text="Extension / detected format e.g. pdf, docx")
    file_size_bytes = models.BigIntegerField()
    file_hash_sha256 = models.CharField(max_length=64, blank=True, null=True, help_text="Integrity checksum")
    is_current = models.BooleanField(default=True, db_index=True)
    revision_note = models.TextField(blank=True, null=True)

    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='uploaded_versions')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dms_document_versions'
        unique_together = ('document', 'version_number')
        ordering = ['-version_number']

    def __str__(self):
        return f"{self.document.doc_id} - V{self.version_number}"


# ==============================================================================
# 6. UPLOAD REQUESTS & APPROVAL WORKFLOWS
# ==============================================================================

class UploadRequest(models.Model):
    """
    Submission and Approval Workflow for Employee uploads (Spec §8.1 & §9).
    """
    REQUEST_STATUS = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='upload_requests')
    version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, null=True, blank=True)
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='submitted_requests')
    submitted_at = models.DateTimeField(auto_now_add=True)

    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='PENDING', db_index=True)
    rejection_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'dms_upload_requests'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Request #{self.id} for {self.document.title} ({self.status})"


# ==============================================================================
# 7. DOCUMENT SHARING PERMISSIONS
# ==============================================================================

class DocumentShare(models.Model):
    """
    Secure Internal Document-Level Sharing with colleagues (Spec §14).
    """
    PERMISSION_LEVELS = [
        ('VIEW', 'View Only'),
        ('DOWNLOAD', 'View & Download'),
        ('EDIT', 'Edit & Submit Revision'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='internal_shares')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_shares')
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_shares')
    permission_level = models.CharField(max_length=20, choices=PERMISSION_LEVELS, default='VIEW')
    expires_at = models.DateField(null=True, blank=True)
    is_revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dms_document_shares'
        unique_together = ('document', 'shared_with')

    def __str__(self):
        return f"{self.document.doc_id} shared with {self.shared_with.full_name} [{self.permission_level}]"


# ==============================================================================
# 8. ACTIVITY & AUDIT LOGS
# ==============================================================================

class ActivityLog(models.Model):
    """
    Immutable System-Wide Audit Activity Log (Spec §16).
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    user_name_snapshot = models.CharField(max_length=180, blank=True, null=True)
    role_snapshot = models.CharField(max_length=100, blank=True, null=True)
    action = models.CharField(max_length=100, db_index=True)
    target_resource = models.CharField(max_length=255)
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_records')
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    result = models.CharField(max_length=50, default='Success')
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'dms_activity_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.user_name_snapshot or 'System'} - {self.action}"
