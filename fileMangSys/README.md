# File Management System (FileMangSys)

A department-based document management system built with **Django**. FileMangSys provides a centralized platform for managing departments, folders, users, permissions, and organizational documents.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
- [System Features](#system-features)
  - [Authentication and Dashboard](#1-authentication-and-dashboard)
  - [Department and Folder Management](#2-department-and-folder-management)
  - [Document Upload](#3-document-upload)
  - [File Manager](#4-file-manager)
  - [Permissions Management](#5-permissions-management)
  - [Live Search](#6-live-search)
- [Project Structure](#project-structure)
- [Development Commands](#development-commands)
- [Troubleshooting](#troubleshooting)

---

## Overview

FileMangSys is designed to simplify document organization and sharing within an organization.

The system allows a **Super Admin** to manage departments, folders, users, and system-wide permissions. Regular users can access documents according to their assigned roles and permissions.

The application provides a centralized document management environment where users can upload, view, download, search, and inspect documents.

### Main System Principles

- Department-based document organization.
- Role-based access control.
- Centralized document storage.
- Folder-based document classification.
- Individual user permission overrides.
- AJAX-powered interactions for a smoother user experience.

---

## Key Features

| Feature | Description |
|---|---|
| User Authentication | Secure login with role-based dashboard redirection. |
| Department Management | Create and manage organizational departments. |
| Folder Management | Organize documents into department-specific folders. |
| Document Management | Upload, view, download, and inspect documents. |
| Role-Based Permissions | Control access according to user roles. |
| Individual Permissions | Grant, deny, or inherit default permissions for individual users. |
| Live Search | Search documents using debounced AJAX requests. |
| Dynamic Folder Selection | Automatically load folders when a department is selected. |
| Default General Folder | Automatically create a `General` folder for every new department. |

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Backend programming language |
| Django | Web application framework |
| MySQL | Relational database management system |
| HTML5 | Application structure |
| CSS3 | User interface styling |
| JavaScript | Client-side interactions |
| AJAX | Asynchronous communication |
| Git | Version control |

---

## Prerequisites

Before installing the application, ensure the following tools are available:

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Backend development |
| pip | Latest | Python package management |
| MySQL | Compatible version | Database management |
| Git | Latest (optional) | Version control |
| Node.js | 18+ (optional) | Frontend tooling, if required |

---

## Installation and Setup

Follow these steps to configure and run FileMangSys on your local machine.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fileMangSys
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
venv\Scripts\activate.bat
```

### 3. Upgrade pip and Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure the Database

Create a MySQL database for the application.

For example:

```sql
CREATE DATABASE filemangsys;
```

Configure the database connection using the project's environment variables or Django database settings.

Make sure the database name, username, password, host, and port match your MySQL configuration.

### 5. Apply Database Migrations

```bash
python manage.py migrate
```

### 6. Create the Super Admin Account

```bash
python manage.py createsuperuser
```

Follow the prompts to configure the Super Admin username, email, and password.

**Security Note:** Never store actual passwords or sensitive credentials in this README or commit them to version control.

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

This collects the application's static assets, including CSS, JavaScript, and images.

### 8. Start the Development Server

```bash
python manage.py runserver
```

Open your browser and navigate to:

```text
http://127.0.0.1:8000/
```

The login page will be displayed. Sign in using your Super Admin credentials.

---

## System Features

### 1. Authentication and Dashboard

The system provides role-based authentication and dashboard redirection.

After successful authentication, users are redirected to the dashboard associated with their assigned role.

Supported roles:

- Super Admin
- Admin
- Manager
- Employee

The login page provides a centralized authentication interface without exposing user information.

### 2. Department and Folder Management

The Super Admin manages the organizational structure of the system.

**Department Management**

- Create and manage departments.
- Each newly created department automatically receives a default `General` folder.
- Delete departments through the administration interface.

**Folder Management**

- Create and manage department-specific folders.
- Delete folders through the administration interface.
- Each folder belongs to its respective department.

**Dynamic Folder Selection**

When a department is selected, the folder dropdown automatically refreshes using AJAX.

Only folders associated with the selected department are displayed.

### 3. Document Upload

Users can upload documents to their assigned departments and folders, subject to their permissions.

Upload behavior:

- The document title is automatically generated from the uploaded filename.
- The title field is hidden from the upload form.
- If no folder is selected, the document is automatically stored in the department's `General` folder.
- Uploaded documents become available in the dashboard and File Manager, according to access permissions.

### 4. File Manager

The File Manager provides a centralized interface for accessing organizational documents.

Each document provides three primary actions:

| Action | Description |
|---|---|
| Open | View the document in the browser. |
| Download | Download a local copy of the document. |
| Inspect | View detailed document information, including Open and Download actions. |

The interface has been simplified to focus on essential document operations.

### 5. Permissions Management

The Super Admin controls system permissions through a centralized permissions interface.

**Role-Based Permissions**

- Permissions are managed through a checkbox-based matrix.
- Permissions can be configured for different user roles.
- The Super Admin permission row is locked and cannot be modified through the matrix.

**Individual User Permissions**

Individual user permissions can override the default role permissions.

Available options:

- **Grant:** Explicitly allow an action.
- **Deny:** Explicitly restrict an action.
- **Default:** Inherit the permission assigned to the user's role.

**Permission Controls**

- Save: Persist permission changes.
- Reset: Revert unsaved changes.

### 6. Live Search

The search interface supports live document searching through AJAX.

Key characteristics:

- Search requests are triggered automatically while typing.
- Requests are debounced to reduce unnecessary server requests.
- Results update dynamically without reloading the page.

---

## Project Structure

The following is a high-level representation of the project structure:

```text
fileMangSys/
│
├── ui_prototype/
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── templates/
│   └── prototype/
│       └── HTML templates
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── manage.py
├── requirements.txt
└── README.md
```

| Directory / File | Responsibility |
|---|---|
| `ui_prototype/` | Django application containing models, views, URLs, and business logic. |
| `models.py` | Database models and relationships. |
| `views.py` | Application logic, dashboards, authentication, and API endpoints. |
| `urls.py` | URL routing and endpoint configuration. |
| `templates/` | HTML templates for the application's interface. |
| `static/` | CSS, JavaScript, and image assets. |
| `manage.py` | Django command-line utility. |
| `requirements.txt` | Python dependencies. |
| `README.md` | Project documentation. |

---

## Development Commands

Common Django commands used during development:

| Action | Command |
|---|---|
| Start development server | `python manage.py runserver` |
| Apply migrations | `python manage.py migrate` |
| Create migrations | `python manage.py makemigrations` |
| Create Super Admin | `python manage.py createsuperuser` |
| Open Django shell | `python manage.py shell` |
| Collect static files | `python manage.py collectstatic` |
| Run tests | `python manage.py test` |
| Create a new Django app | `python manage.py startapp app_name` |

### Adding New Functionality

- **Create a Django app:** Use `python manage.py startapp app_name`.
- **Add URL routes:** Update the appropriate Django `urls.py` file.
- **Add database models:** Define models in `models.py`, then generate and apply migrations.
- **Add frontend assets:** Place custom CSS, JavaScript, and images in the `static/` directory.
- **Update templates:** Add or modify HTML files in the appropriate templates directory.

---

## Troubleshooting

| Problem | Possible Solution |
|---|---|
| Module not found | Activate the virtual environment and run `pip install -r requirements.txt`. |
| Database connection error | Verify MySQL is running and check the database connection settings. |
| Login fails | Verify that the user exists in the database and that the credentials are correct. |
| Folder list does not update | Check browser developer tools for JavaScript errors and verify the `/api/department_folders/` endpoint. |
| Permissions are not saving | Ensure the Save action is triggered and the request includes a valid CSRF token. |
| Static files are missing | Run `python manage.py collectstatic --noinput` and verify static file configuration. |

To check whether a user exists, open the Django shell:

```bash
python manage.py shell
```

Then execute:

```python
User.objects.filter(email="your-email@example.com").first()
```

---

## License

No license has been specified yet.
