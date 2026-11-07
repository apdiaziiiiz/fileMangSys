"""
Rich sample mock data for the Department-Based Document Management System prototype.
Contains realistic records adhering to specification rules, RBAC roles, departments,
versions, audit activity, recycle bin, and storage statistics.
"""

from datetime import datetime

MOCK_DEPARTMENTS = [
    {
        'id': 'dept-1',
        'code': 'FIN',
        'name': 'Finance',
        'manager': 'Hassan Al-Khatib',
        'users_count': 5,
        'files_count': 142,
        'storage_used_mb': 6140,
        'max_quota_mb': 10240,
        'status': 'Active',
        'folders': ['Audit Reports', 'Tax Filings', 'Annual Budgets', 'Invoices 2026']
    },
    {
        'id': 'dept-2',
        'code': 'HR',
        'name': 'Human Resources',
        'manager': 'Sara Khalid',
        'users_count': 4,
        'files_count': 98,
        'storage_used_mb': 3420,
        'max_quota_mb': 8192,
        'status': 'Active',
        'folders': ['Workplace Policies', 'Contracts', 'Recruitment', 'Performance Appraisals']
    },
    {
        'id': 'dept-3',
        'code': 'IT',
        'name': 'IT & Infrastructure',
        'manager': 'Omar Tariq',
        'users_count': 6,
        'files_count': 215,
        'storage_used_mb': 14200,
        'max_quota_mb': 25600,
        'status': 'Active',
        'folders': ['System Architecture', 'Security Audits', 'Hardware Inventory', 'Disaster Recovery']
    },
    {
        'id': 'dept-4',
        'code': 'ADM',
        'name': 'Administration',
        'manager': 'Fatima Noor',
        'users_count': 3,
        'files_count': 64,
        'storage_used_mb': 2180,
        'max_quota_mb': 5120,
        'status': 'Active',
        'folders': ['Board Resolutions', 'Procurement', 'Office Leases', 'Facility Maintenance']
    },
    {
        'id': 'dept-5',
        'code': 'PRJ',
        'name': 'Projects & Engineering',
        'manager': 'Zaid Mahmoud',
        'users_count': 7,
        'files_count': 310,
        'storage_used_mb': 18450,
        'max_quota_mb': 30720,
        'status': 'Active',
        'folders': ['Client Deliverables', 'Blueprints', 'Milestone Reports', 'Specifications']
    }
]

MOCK_DOCUMENTS = [
    {
        'id': 'DOC-2026-001',
        'title': 'Q3_Financial_Audit_Report.pdf',
        'original_filename': 'Q3_Financial_Audit_Report.pdf',
        'objective': 'Third quarter internal financial verification, reconciliation and variance analysis report.',
        'owner': 'Finance Department',
        'department': 'Finance',
        'document_date': '2026-09-30',
        'uploaded_by': 'Hassan Al-Khatib',
        'uploaded_date': '2026-10-02 09:30',
        'file_type': 'pdf',
        'file_size': '4.2 MB',
        'status': 'Published',
        'current_version': 'V3',
        'folder': 'Audit Reports',
        'versions': [
            {'version': 'V3', 'uploaded_by': 'Hassan Al-Khatib', 'date': '2026-10-02 09:30', 'size': '4.2 MB', 'is_current': True, 'note': 'Incorporated committee tax revisions'},
            {'version': 'V2', 'uploaded_by': 'Ahmed Al-Mansoor', 'date': '2026-09-28 14:15', 'size': '3.9 MB', 'is_current': False, 'note': 'Draft with initial balance sheets'},
            {'version': 'V1', 'uploaded_by': 'Hassan Al-Khatib', 'date': '2026-09-15 11:00', 'size': '3.5 MB', 'is_current': False, 'note': 'Initial submission draft'}
        ],
        'shares': [
            {'user_name': 'Sara Khalid', 'department': 'Human Resources', 'permission': 'View', 'expires': '2026-12-31'},
            {'user_name': 'Omar Tariq', 'department': 'IT & Infrastructure', 'permission': 'Download', 'expires': 'Never'}
        ]
    },
    {
        'id': 'DOC-2026-002',
        'title': 'Employee_Code_of_Conduct_2026.docx',
        'original_filename': 'Employee_Code_of_Conduct_2026.docx',
        'objective': 'Comprehensive workplace ethics, security policies and remote work governance guidelines.',
        'owner': 'Human Resources',
        'department': 'Human Resources',
        'document_date': '2026-01-10',
        'uploaded_by': 'Sara Khalid',
        'uploaded_date': '2026-01-12 14:20',
        'file_type': 'docx',
        'file_size': '1.8 MB',
        'status': 'Published',
        'current_version': 'V2',
        'folder': 'Workplace Policies',
        'versions': [
            {'version': 'V2', 'uploaded_by': 'Sara Khalid', 'date': '2026-01-12 14:20', 'size': '1.8 MB', 'is_current': True, 'note': 'Approved annual standard release'},
            {'version': 'V1', 'uploaded_by': 'Sara Khalid', 'date': '2025-12-20 10:00', 'size': '1.6 MB', 'is_current': False, 'note': 'Pre-board review draft'}
        ],
        'shares': []
    },
    {
        'id': 'DOC-2026-003',
        'title': 'LAN_Server_Architecture_Diagram.png',
        'original_filename': 'LAN_Server_Architecture_Diagram.png',
        'objective': 'Physical and logical topology diagram of central file servers, NAS backup array and 20 client subnet nodes.',
        'owner': 'IT & Infrastructure',
        'department': 'IT & Infrastructure',
        'document_date': '2026-10-15',
        'uploaded_by': 'Bilal Nabil',
        'uploaded_date': '2026-10-18 16:45',
        'file_type': 'png',
        'file_size': '3.1 MB',
        'status': 'Pending',
        'current_version': 'V1',
        'folder': 'System Architecture',
        'versions': [
            {'version': 'V1', 'uploaded_by': 'Bilal Nabil', 'date': '2026-10-18 16:45', 'size': '3.1 MB', 'is_current': True, 'note': 'Awaiting Admin network security sign-off'}
        ],
        'shares': []
    },
    {
        'id': 'DOC-2026-004',
        'title': 'Q4_Capital_Expenditure_Budget.xlsx',
        'original_filename': 'Q4_Capital_Expenditure_Budget.xlsx',
        'objective': 'Hardware replacement and departmental software licensing projections for Q4 operations.',
        'owner': 'Finance Department',
        'department': 'Finance',
        'document_date': '2026-11-01',
        'uploaded_by': 'Youssef Karim',
        'uploaded_date': '2026-11-03 11:10',
        'file_type': 'xlsx',
        'file_size': '820 KB',
        'status': 'Pending',
        'current_version': 'V1',
        'folder': 'Annual Budgets',
        'versions': [
            {'version': 'V1', 'uploaded_by': 'Youssef Karim', 'date': '2026-11-03 11:10', 'size': '820 KB', 'is_current': True, 'note': 'Initial department submission'}
        ],
        'shares': []
    },
    {
        'id': 'DOC-2026-005',
        'title': 'Vendor_Procurement_Contract_Template.docx',
        'original_filename': 'Vendor_Procurement_Contract_Template.docx',
        'objective': 'Standard legal procurement contract boilerplate for SLA agreements with equipment vendors.',
        'owner': 'Administration',
        'department': 'Administration',
        'document_date': '2026-08-14',
        'uploaded_by': 'Fatima Noor',
        'uploaded_date': '2026-08-15 08:30',
        'file_type': 'docx',
        'file_size': '640 KB',
        'status': 'Published',
        'current_version': 'V1',
        'folder': 'Procurement',
        'versions': [
            {'version': 'V1', 'uploaded_by': 'Fatima Noor', 'date': '2026-08-15 08:30', 'size': '640 KB', 'is_current': True, 'note': 'Legal team ratified release'}
        ],
        'shares': []
    },
    {
        'id': 'DOC-2026-006',
        'title': 'ERP_Migration_Plan_Proposal.pdf',
        'original_filename': 'ERP_Migration_Plan_Proposal.pdf',
        'objective': 'Proposal for database migration schedule with temporary offline windows across clients.',
        'owner': 'IT & Infrastructure',
        'department': 'IT & Infrastructure',
        'document_date': '2026-10-05',
        'uploaded_by': 'Bilal Nabil',
        'uploaded_date': '2026-10-06 13:00',
        'file_type': 'pdf',
        'file_size': '2.4 MB',
        'status': 'Rejected',
        'current_version': 'V1',
        'folder': 'System Architecture',
        'rejection_reason': 'Downtime window conflicts with fiscal month-end reconciliation. Reschedule to weekend maintenance.',
        'reviewed_by': 'Ahmed Al-Mansoor',
        'review_date': '2026-10-07 10:15',
        'versions': [
            {'version': 'V1', 'uploaded_by': 'Bilal Nabil', 'date': '2026-10-06 13:00', 'size': '2.4 MB', 'is_current': True, 'note': 'Submission declined'}
        ],
        'shares': []
    },
    {
        'id': 'DOC-2026-007',
        'title': 'Data_Center_Facility_Lease.pdf',
        'original_filename': 'Data_Center_Facility_Lease.pdf',
        'objective': 'Multi-year server colocation and backup power utility contract binding terms.',
        'owner': 'Administration',
        'department': 'Administration',
        'document_date': '2026-05-12',
        'uploaded_by': 'Fatima Noor',
        'uploaded_date': '2026-05-14 11:20',
        'file_type': 'pdf',
        'file_size': '3.8 MB',
        'status': 'Published',
        'current_version': 'V1',
        'folder': 'Office Leases',
        'versions': [
            {'version': 'V1', 'uploaded_by': 'Fatima Noor', 'date': '2026-05-14 11:20', 'size': '3.8 MB', 'is_current': True, 'note': 'Signed lease agreement'}
        ],
        'shares': []
    },
    {
        'id': 'DOC-2026-008',
        'title': 'Client_Portal_Milestone_2_Deliverable.pdf',
        'original_filename': 'Client_Portal_Milestone_2_Deliverable.pdf',
        'objective': 'Signed customer acceptance certificate and completed feature checklist for Milestone 2.',
        'owner': 'Projects & Engineering',
        'department': 'Projects & Engineering',
        'document_date': '2026-10-29',
        'uploaded_by': 'Zaid Mahmoud',
        'uploaded_date': '2026-11-01 15:40',
        'file_type': 'pdf',
        'file_size': '5.6 MB',
        'status': 'Published',
        'current_version': 'V2',
        'folder': 'Client Deliverables',
        'versions': [
            {'version': 'V2', 'uploaded_by': 'Zaid Mahmoud', 'date': '2026-11-01 15:40', 'size': '5.6 MB', 'is_current': True, 'note': 'Final sign-off attached'},
            {'version': 'V1', 'uploaded_by': 'Zaid Mahmoud', 'date': '2026-10-25 10:10', 'size': '5.1 MB', 'is_current': False, 'note': 'Preliminary delivery'}
        ],
        'shares': []
    }
]

MOCK_RECYCLE_BIN = [
    {
        'id': 'DOC-2026-DEL-01',
        'title': 'Old_Office_Floorplan_2024.pdf',
        'department': 'Administration',
        'deleted_by': 'Fatima Noor',
        'deleted_date': '2026-10-24 14:10',
        'days_remaining': 18,
        'size': '5.1 MB',
        'original_folder': 'Facility Maintenance'
    },
    {
        'id': 'DOC-2026-DEL-02',
        'title': 'Draft_Quarterly_Bonus_Calculation.xlsx',
        'department': 'Finance',
        'deleted_by': 'Hassan Al-Khatib',
        'deleted_date': '2026-11-01 09:20',
        'days_remaining': 26,
        'size': '1.2 MB',
        'original_folder': 'Annual Budgets'
    },
    {
        'id': 'DOC-2026-DEL-03',
        'title': 'Legacy_Switch_Configuration_Backup.docx',
        'department': 'IT & Infrastructure',
        'deleted_by': 'Omar Tariq',
        'deleted_date': '2026-10-12 18:00',
        'days_remaining': 6,
        'size': '890 KB',
        'original_folder': 'Hardware Inventory'
    }
]

MOCK_USERS = [
    {
        'id': 'USR-01',
        'name': 'Ahmed Al-Mansoor',
        'email': 'ahmed.mansoor@enterprise.local',
        'role': 'Super Administrator',
        'department': 'Executive / All',
        'status': 'Active',
        'last_login': 'Just now',
        'direct_permissions': ['ALL_SYSTEM_ACCESS', 'USER_MANAGEMENT', 'STORAGE_MONITORING', 'AUDIT_LOG_FULL']
    },
    {
        'id': 'USR-02',
        'name': 'Tariq Jamil',
        'email': 'tariq.jamil@enterprise.local',
        'role': 'Administrator',
        'department': 'Finance, IT & Infrastructure',
        'status': 'Active',
        'last_login': '2 hours ago',
        'direct_permissions': ['DIRECT_UPLOAD', 'REVIEW_SUBMISSIONS', 'MANAGE_USERS_SCOPE', 'MANAGE_FOLDERS']
    },
    {
        'id': 'USR-03',
        'name': 'Sara Khalid',
        'email': 'sara.khalid@enterprise.local',
        'role': 'Manager',
        'department': 'Human Resources',
        'status': 'Active',
        'last_login': 'Today 15:30',
        'direct_permissions': ['DEPT_MANAGE', 'DIRECT_UPLOAD', 'APPROVE_DEPARTMENT', 'DOWNLOAD']
    },
    {
        'id': 'USR-04',
        'name': 'Hassan Al-Khatib',
        'email': 'hassan.khatib@enterprise.local',
        'role': 'Manager',
        'department': 'Finance',
        'status': 'Active',
        'last_login': 'Today 13:40',
        'direct_permissions': ['DEPT_MANAGE', 'DIRECT_UPLOAD', 'APPROVE_DEPARTMENT', 'DOWNLOAD']
    },
    {
        'id': 'USR-05',
        'name': 'Omar Tariq',
        'email': 'omar.tariq@enterprise.local',
        'role': 'Manager',
        'department': 'IT & Infrastructure',
        'status': 'Active',
        'last_login': 'Yesterday',
        'direct_permissions': ['DEPT_MANAGE', 'DIRECT_UPLOAD', 'APPROVE_DEPARTMENT', 'DOWNLOAD']
    },
    {
        'id': 'USR-06',
        'name': 'Bilal Nabil',
        'email': 'bilal.nabil@enterprise.local',
        'role': 'Employee',
        'department': 'IT & Infrastructure',
        'status': 'Active',
        'last_login': 'Today 11:25',
        'direct_permissions': ['SUBMIT_FOR_REVIEW', 'DOWNLOAD_PERMITTED', 'VIEW_PERMITTED']
    },
    {
        'id': 'USR-07',
        'name': 'Youssef Karim',
        'email': 'youssef.karim@enterprise.local',
        'role': 'Employee',
        'department': 'Finance',
        'status': 'Active',
        'last_login': 'Today 17:05',
        'direct_permissions': ['SUBMIT_FOR_REVIEW', 'DOWNLOAD_PERMITTED', 'VIEW_PERMITTED']
    },
    {
        'id': 'USR-08',
        'name': 'Fatima Noor',
        'email': 'fatima.noor@enterprise.local',
        'role': 'Manager',
        'department': 'Administration',
        'status': 'Active',
        'last_login': '3 days ago',
        'direct_permissions': ['DEPT_MANAGE', 'DIRECT_UPLOAD', 'DOWNLOAD']
    }
]

MOCK_ACTIVITY_LOGS = [
    {
        'id': 'LOG-901',
        'user': 'Ahmed Al-Mansoor',
        'role': 'Super Administrator',
        'action': 'Approved Document',
        'target': 'Q3_Financial_Audit_Report.pdf (V3)',
        'timestamp': '2026-11-07 14:22',
        'result': 'Success',
        'ip': '192.168.123.35'
    },
    {
        'id': 'LOG-902',
        'user': 'Youssef Karim',
        'role': 'Employee',
        'action': 'Submitted For Approval',
        'target': 'Q4_Capital_Expenditure_Budget.xlsx',
        'timestamp': '2026-11-07 11:10',
        'result': 'Success',
        'ip': '192.168.123.42'
    },
    {
        'id': 'LOG-903',
        'user': 'Sara Khalid',
        'role': 'Manager',
        'action': 'Shared Document Internally',
        'target': 'Employee_Code_of_Conduct_2026.docx',
        'timestamp': '2026-11-06 15:45',
        'result': 'Success',
        'ip': '192.168.123.39'
    },
    {
        'id': 'LOG-904',
        'user': 'Hassan Al-Khatib',
        'role': 'Manager',
        'action': 'Restored From Recycle Bin',
        'target': 'Draft_Quarterly_Bonus_Calculation.xlsx',
        'timestamp': '2026-11-06 14:02',
        'result': 'Success',
        'ip': '192.168.123.36'
    },
    {
        'id': 'LOG-905',
        'user': 'Bilal Nabil',
        'role': 'Employee',
        'action': 'Document Downloaded',
        'target': 'Employee_Code_of_Conduct_2026.docx',
        'timestamp': '2026-11-06 11:30',
        'result': 'Success',
        'ip': '192.168.123.50'
    },
    {
        'id': 'LOG-906',
        'user': 'Ahmed Al-Mansoor',
        'role': 'Super Administrator',
        'action': 'Updated Role Permission Matrix',
        'target': 'Manager Role (Finance Department)',
        'timestamp': '2026-11-05 16:15',
        'result': 'Success',
        'ip': '192.168.123.35'
    },
    {
        'id': 'LOG-907',
        'user': 'Tariq Jamil',
        'role': 'Administrator',
        'action': 'Created User Account',
        'target': 'Youssef Karim (Finance)',
        'timestamp': '2026-11-05 09:12',
        'result': 'Success',
        'ip': '192.168.123.38'
    },
    {
        'id': 'LOG-908',
        'user': 'Ahmed Al-Mansoor',
        'role': 'Super Administrator',
        'action': 'Rejected Document Submission',
        'target': 'ERP_Migration_Plan_Proposal.pdf',
        'timestamp': '2026-10-07 10:15',
        'result': 'Success',
        'ip': '192.168.123.35'
    }
]

MOCK_STORAGE_STATS = {
    'total_capacity_gb': 500,
    'used_storage_gb': 184.2,
    'free_storage_gb': 315.8,
    'usage_percentage': 36.8,
    'db_backup_status': 'Healthy (Last at 03:00 AM)',
    'nas_connection': 'Connected (192.168.123.10)',
    'breakdown': [
        {'name': 'Projects & Engineering', 'used_gb': 72.4, 'percentage': 39.3, 'color': '#F36B32'},
        {'name': 'IT & Infrastructure', 'used_gb': 48.6, 'percentage': 26.4, 'color': '#2563EB'},
        {'name': 'Finance', 'used_gb': 32.1, 'percentage': 17.4, 'color': '#10B981'},
        {'name': 'Human Resources', 'used_gb': 18.2, 'percentage': 9.9, 'color': '#F59E0B'},
        {'name': 'Administration', 'used_gb': 12.9, 'percentage': 7.0, 'color': '#8B5CF6'},
    ]
}

MOCK_ROLES_PERMISSIONS = [
    {
        'role': 'Super Administrator',
        'user_count': 1,
        'scope': 'All Departments & System Config',
        'can_upload': True,
        'can_approve': True,
        'can_delete': True,
        'can_manage_users': True,
        'can_manage_depts': True,
        'can_view_audit': True,
        'can_restore_bin': True
    },
    {
        'role': 'Administrator',
        'user_count': 2,
        'scope': 'Assigned Departments (Finance, IT)',
        'can_upload': True,
        'can_approve': True,
        'can_delete': True,
        'can_manage_users': True,
        'can_manage_depts': False,
        'can_view_audit': True,
        'can_restore_bin': True
    },
    {
        'role': 'Manager',
        'user_count': 5,
        'scope': 'Primary Department Only',
        'can_upload': True,
        'can_approve': True,
        'can_delete': True,
        'can_manage_users': False,
        'can_manage_depts': False,
        'can_view_audit': False,
        'can_restore_bin': False
    },
    {
        'role': 'Employee',
        'user_count': 12,
        'scope': 'Assigned Folders (Submission Mode)',
        'can_upload': False,
        'can_approve': False,
        'can_delete': False,
        'can_manage_users': False,
        'can_manage_depts': False,
        'can_view_audit': False,
        'can_restore_bin': False
    }
]
