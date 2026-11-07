"""
Data schemas and default baseline structures for the Department-Based Document Management System.
All demonstration / sample records have been removed. Data is populated dynamically from the database.
"""

# Dynamic default baseline dictionaries (empty by default)
MOCK_DEPARTMENTS = []
MOCK_DOCUMENTS = []
MOCK_RECYCLE_BIN = []
MOCK_USERS = []
MOCK_ACTIVITY_LOGS = []

MOCK_STORAGE_STATS = {
    'total_capacity_gb': 500,
    'used_storage_gb': 0.0,
    'free_storage_gb': 500.0,
    'usage_percentage': 0,
    'db_backup_status': 'Configured (MySQL dms_db)',
    'nas_connection': 'Local Central Repository (C:\\fileMngSys)',
    'breakdown': []
}

# Standard Role Capabilities Reference Matrix (RBAC structure defined in system specs)
MOCK_ROLES_PERMISSIONS = [
    {
        'role': 'Super Administrator',
        'code': 'SUPER_ADMIN',
        'user_count': 0,
        'scope': 'System-wide (All Departments)',
        'can_upload': True,
        'can_approve': True,
        'can_delete': True,
        'can_manage_users': True,
        'can_view_audit': True,
        'can_restore_bin': True
    },
    {
        'role': 'Administrator',
        'code': 'ADMIN',
        'user_count': 0,
        'scope': 'Assigned Departments',
        'can_upload': True,
        'can_approve': True,
        'can_delete': True,
        'can_manage_users': True,
        'can_view_audit': True,
        'can_restore_bin': True
    },
    {
        'role': 'Manager',
        'code': 'MANAGER',
        'user_count': 0,
        'scope': 'Primary Department Only',
        'can_upload': True,
        'can_approve': True,
        'can_delete': True,
        'can_manage_users': False,
        'can_view_audit': False,
        'can_restore_bin': False
    },
    {
        'role': 'Employee',
        'code': 'EMPLOYEE',
        'user_count': 0,
        'scope': 'Permitted Folders Only',
        'can_upload': False, # Must submit for approval
        'can_approve': False,
        'can_delete': False,
        'can_manage_users': False,
        'can_view_audit': False,
        'can_restore_bin': False
    }
]
