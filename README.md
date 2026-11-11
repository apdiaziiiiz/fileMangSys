## Installation and Setup

Follow these steps to set up FileMangSys on a local Windows machine.

### 1. Clone the Repository

```powershell
git clone <repository-url>
cd fileMangSys
```

### 2. Create a Virtual Environment

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

For Command Prompt:

```cmd
venv\Scripts\activate.bat
```

### 3. Install Python Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Make sure `mysqlclient` is included in `requirements.txt`. It is the database driver Django uses to communicate with MySQL.

---

## MySQL Database Configuration

FileMangSys uses **MySQL** as its relational database management system (RDBMS).

MySQL stores structured application data, including:

- User accounts and authentication information.
- Departments and folders.
- Document records and metadata.
- Roles and permissions.

Uploaded documents are stored separately in Django's configured media storage directory. MySQL stores their associated records and file paths.

### 1. Download and Install MySQL

Download MySQL Community Server using the official resources:

| Resource | Link |
|---|---|
| MySQL Community Server | https://dev.mysql.com/downloads/mysql/ |
| MySQL Installer for Windows | https://dev.mysql.com/downloads/installer/ |
| MySQL Workbench | https://dev.mysql.com/downloads/workbench/ |
| MySQL Documentation | https://dev.mysql.com/doc/ |

For Windows:

1. Download and open MySQL Installer.
2. Select a setup type that includes MySQL Server.
3. Complete the installation.
4. Configure MySQL as a standalone server.
5. Set the default port to `3306`.
6. Configure authentication.
7. Set a secure password for the MySQL `root` account.
8. Configure MySQL as a Windows service.
9. Complete the configuration and start the server.

MySQL Workbench is optional. It provides a graphical interface for managing databases and users.

### 2. Verify the Installation

Open PowerShell and check the MySQL version:

```powershell
mysql --version
```

Connect to MySQL:

```powershell
mysql -u root -p
```

Enter your root password when prompted.

A successful connection displays the MySQL command prompt:

```text
mysql>
```

### 3. Create the Application Database

Execute the following SQL commands:

```sql
CREATE DATABASE filemangsys
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

Verify the database:

```sql
SHOW DATABASES;
```

### 4. Create a Database User

Create a dedicated account for the application instead of connecting Django with the MySQL root account.

```sql
CREATE USER 'filemang_user'@'localhost'
IDENTIFIED BY 'your_secure_password';
```

Grant access to the application database:

```sql
GRANT ALL PRIVILEGES ON filemangsys.*
TO 'filemang_user'@'localhost';
```

Verify the permissions:

```sql
SHOW GRANTS FOR 'filemang_user'@'localhost';
```

The application account now has the necessary privileges to manage its database.

### 5. Configure Django to Use MySQL

Open the Django settings file:

```text
ui_prototype/settings.py
```

Locate the `DATABASES` configuration and configure it as follows:

```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'filemangsys'),
        'USER': os.getenv('DB_USER', 'filemang_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }
}
```

The configuration connects Django to the local MySQL server using the dedicated application account.

### 6. Configure Environment Variables

Set the database credentials in PowerShell:

```powershell
$env:DB_NAME="filemangsys"
$env:DB_USER="filemang_user"
$env:DB_PASSWORD="your_secure_password"
$env:DB_HOST="localhost"
$env:DB_PORT="3306"
```

These variables remain available for the current PowerShell session.

**Important:** If the project uses a `.env` file, configure these values there using the environment-variable loader already implemented in the project. Never commit actual credentials to Git.

### 7. Install and Verify the MySQL Driver

Activate the virtual environment and install the driver if it is not already installed:

```powershell
pip install mysqlclient
```

Verify the installation:

```powershell
python -c "import MySQLdb; print('MySQL driver installed successfully')"
```

Add the dependency to `requirements.txt` if necessary:

```text
mysqlclient
```

Documentation:

- [mysqlclient](https://pypi.org/project/mysqlclient/)
- [Django MySQL Database Configuration](https://docs.djangoproject.com/en/6.0/ref/databases/#mysql-notes)

### 8. Test the Database Connection

Run Django's system check:

```powershell
python manage.py check
```

Then open the Django shell:

```powershell
python manage.py shell
```

Execute:

```python
from django.db import connection

connection.ensure_connection()

print(connection.vendor)
print("Database connection successful!")
```

Expected output:

```text
mysql
Database connection successful!
```

Exit the shell:

```python
exit()
```

### 9. Create Database Tables

Generate migrations when necessary:

```powershell
python manage.py makemigrations
```

Apply the migrations:

```powershell
python manage.py migrate
```

Django will create the application tables inside the `filemangsys` database.

To verify the tables, connect to MySQL:

```powershell
mysql -u filemang_user -p
```

Then execute:

```sql
USE filemangsys;
SHOW TABLES;
```

### 10. Create the Super Admin Account

```powershell
python manage.py createsuperuser
```

Follow the prompts to create the initial administrator account.

### 11. Collect Static Files

```powershell
python manage.py collectstatic --noinput
```

### 12. Start the Application

```powershell
python manage.py runserver
```

Open your browser:

```text
http://127.0.0.1:8000/
```

Log in using the Super Admin credentials created earlier.

---

## Database Troubleshooting

| Error | Possible Cause | Solution |
|---|---|---|
| `mysql is not recognized` | MySQL is not added to Windows PATH. | Add the MySQL `bin` directory to PATH. |
| `Access denied for user` | Incorrect database credentials or insufficient privileges. | Verify the username, password, and database grants. |
| `Unknown database` | The application database does not exist. | Create the `filemangsys` database. |
| `Can't connect to MySQL server` | MySQL service is stopped or connection settings are incorrect. | Start MySQL and verify the host and port. |
| `No module named MySQLdb` | MySQL Python driver is missing. | Install `mysqlclient` in the active virtual environment. |
| `Table doesn't exist` | Database migrations have not been applied. | Run `python manage.py migrate`. |

