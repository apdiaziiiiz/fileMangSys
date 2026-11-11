# Project Architecture & File Relationship Map

This document provides a tree map of the codebase and explains how files, templates, styles, scripts, routing, and data structures connect to each other.

---

## 1. Directory Structure Tree

```text
fileMS/
│
├── department_document_management_system_specification.md  # Core approved requirements and technical spec
├── PROJECT_MAP.md                                          # This architectural roadmap & file relationship guide
├── venv/                                                   # Python 3.12 virtual environment (Django, libraries)
│
└── fileMangSys/                                            # Main Django Project Root Directory
    │
    ├── manage.py                                           # Django command-line runner (starts server, check commands)
    ├── db.sqlite3                                          # Local SQLite placeholder (PostgreSQL in Phase 2)
    │
    ├── fileMangSys/                                        # Global Project Configuration Package
    │   ├── __init__.py                                     # Python package marker
    │   ├── asgi.py                                         # ASGI entry point for async server deployment
    │   ├── wsgi.py                                         # WSGI entry point for web servers
    │   ├── settings.py                                     # Global Django settings (INSTALLED_APPS, static, templates)
    │   └── urls.py                                         # Root routing hub (routes requests to ui_prototype.urls)
    │
    ├── static/                                             # Static Assets (Styling and Interactivity)
    │   ├── css/
    │   │   └── main.css                                    # Design system stylesheet (colors, layout, tables, modals)
    │   └── js/
    │       └── app.js                                      # Frontend logic (search, filter, modals, approval toggle)
    │
    ├── templates/                                          # Django HTML Templates Directory
    │   └── prototype/
    │       ├── base.html                                   # Master layout (sidebar, topbar, role switcher, upload modal)
    │       ├── login.html                                  # Interface 1: User login & quick role-switch preview
    │       │
    │       ├── dashboards/                                 # Role-Specific Dashboard Views
    │       │   ├── super_admin.html                        # Interface 2: System-wide metrics, storage & audit feeds
    │       │   ├── admin.html                              # Interface 3: Assigned departments & pending submissions
    │       │   ├── manager.html                            # Interface 4: Department folders & quota monitoring
    │       │   └── employee.html                           # Interface 5: Employee submissions, status & permitted files
    │       │
    │       ├── documents/                                  # Document & File Workflow Interfaces
    │       │   ├── department_list.html                    # Interface 6: Department directories & folder structures
    │       │   ├── file_manager.html                       # Interface 7: Interactive folder browser & file explorer
    │       │   ├── document_list.html                      # Interface 8: All documents list with category filters
    │       │   ├── document_detail.html                    # Interface 8b: Detailed metadata & download view
    │       │   ├── search_page.html                        # Interface 9: Live quick search & advanced multi-filters
    │       │   ├── approvals_list.html                     # Interface 11: Document approval & rejection queue
    │       │   ├── version_history.html                    # Interface 12: Stored revisions log (V1, V2, V3)
    │       │   ├── recycle_bin.html                        # Interface 13: 30-day recoverable deleted items
    │       │   └── share_interface.html                    # Interface 14: Internal user sharing & permissions
    │       │
    │       └── admin/                                      # System Administration Interfaces
    │           ├── user_management.html                    # Interface 15: User accounts & department assignments
    │           ├── department_management.html              # Interface 16: Department quotas & manager settings
    │           ├── permission_management.html              # Interface 17: RBAC capability matrix & custom overrides
    │           ├── activity_logs.html                      # Interface 18: Audit trail of user actions & IP addresses
    │           ├── storage_monitoring.html                 # Interface 19: LAN server storage capacity & backups
    │           └── system_settings.html                    # Interface 20: Retention policy & global constraints
    │
    └── ui_prototype/                                       # Django Application Module
        ├── __init__.py                                     # Python package marker
        ├── apps.py                                         # App configuration ('ui_prototype')
        ├── mock_data.py                                    # Realistic sample data (departments, files, users, logs)
        ├── views.py                                        # View controllers connecting mock data with templates
        └── urls.py                                         # URL mapping for all 20 prototype routes
```

---

## 2. How the Files and Components are Connected

### A. The Request & Routing Flow
```text
Browser Request (e.g. http://127.0.0.1:8000/dashboard/super-admin/)
       │
       ▼
fileMangSys/urls.py (Root URLconf)
       │  (delegates route to ui_prototype)
       ▼
ui_prototype/urls.py (App URLconf)
       │  (maps path to view function)
       ▼
ui_prototype/views.py (e.g. `dashboard_super_admin` function)
       │  (pulls data from ui_prototype/mock_data.py)
       ▼
templates/prototype/dashboards/super_admin.html
       │  (extends base.html)
       ▼
templates/prototype/base.html
       │  (loads stylesheet: static/css/main.css)
       │  (loads client script: static/js/app.js)
       ▼
Rendered HTML & CSS response sent to the browser
```

---

### B. Detailed File Connection Breakdown

#### 1. Configuration & Core Settings
- [fileMangSys/settings.py](file:///d:/myProjects/fileMS/fileMangSys/fileMangSys/settings.py)
  - Configures `INSTALLED_APPS` to include `'ui_prototype'`.
  - Configures `TEMPLATES` to look in `fileMangSys/templates/`.
  - Configures `STATICFILES_DIRS` to serve files from `fileMangSys/static/`.
- [fileMangSys/urls.py](file:///d:/myProjects/fileMS/fileMangSys/fileMangSys/urls.py)
  - Delegates the root path `''` to [ui_prototype/urls.py](file:///d:/myProjects/fileMS/fileMangSys/ui_prototype/urls.py) via `include('ui_prototype.urls')`.

#### 2. App Routing & Views
- [ui_prototype/urls.py](file:///d:/myProjects/fileMS/fileMangSys/ui_prototype/urls.py)
  - Connects URL patterns (such as `/`, `/dashboard/<role>/`, `/files/`, `/search/`, `/admin/users/`) to python functions in [ui_prototype/views.py](file:///d:/myProjects/fileMS/fileMangSys/ui_prototype/views.py).
- [ui_prototype/views.py](file:///d:/myProjects/fileMS/fileMangSys/ui_prototype/views.py)
  - Imports mock records from [ui_prototype/mock_data.py](file:///d:/myProjects/fileMS/fileMangSys/ui_prototype/mock_data.py).
  - Prepares the active user context, department scopes, and filtered documents.
  - Passes the data to the appropriate HTML template in `templates/prototype/`.

#### 3. Styling & Presentation Layer
- [static/css/main.css](file:///d:/myProjects/fileMS/fileMangSys/static/css/main.css)
  - Contains CSS variables (`--primary: #F36B32`, `--bg-page: #F1F1F1`, `--border-color: #E8E8E8`).
  - Defines shared styles for the sidebar, top header search bar, stat cards, responsive data tables, status badges (`Published`, `Pending`, `Rejected`), and modal overlays.
  - Linked directly in the `<head>` of [templates/prototype/base.html](file:///d:/myProjects/fileMS/fileMangSys/templates/prototype/base.html) and [templates/prototype/login.html](file:///d:/myProjects/fileMS/fileMangSys/templates/prototype/login.html).

#### 4. Frontend Interactivity
- [static/js/app.js](file:///d:/myProjects/fileMS/fileMangSys/static/js/app.js)
  - Included at the bottom of [templates/prototype/base.html](file:///d:/myProjects/fileMS/fileMangSys/templates/prototype/base.html).
  - Manages interactive modal popups (Upload Modal).
  - Handles real-time client search filtering on table rows.
  - Handles table header sorting (`data-sort`).
  - Simulates document approvals and rejections.
  - Powers the top navbar role switcher.

#### 5. Template Inheritance Hierarchy
- [templates/prototype/base.html](file:///d:/myProjects/fileMS/fileMangSys/templates/prototype/base.html)
  - Master skeleton containing the persistent Left Sidebar, Top Navigation Bar, User Avatar, Global Quick Search, and Reusable Upload Modal.
  - All 19 inner pages inherit from this file via `{% extends 'prototype/base.html' %}` and place their content inside `{% block content %}`.
- [templates/prototype/login.html](file:///d:/myProjects/fileMS/fileMangSys/templates/prototype/login.html)
  - Standalone login window styled with [static/css/main.css](file:///d:/myProjects/fileMS/fileMangSys/static/css/main.css), providing quick-access role cards to launch the 4 dashboards.

---

## 3. Running the Server

To launch the local web server:

```powershell
cd d:\myProjects\fileMS\fileMangSys
& ..\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Access in your browser at:
- **`http://127.0.0.1:8000/`** (Login)
- **`http://127.0.0.1:8000/dashboard/super-admin/`** (Super Admin Dashboard)
