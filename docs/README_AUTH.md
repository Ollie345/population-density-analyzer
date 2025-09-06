# 🔐 Authentication System for Population Density Analyzer

## Overview
This Streamlit application now includes a secure authentication system with PostgreSQL database integration that requires users to login before accessing the population density analysis tools.

## 🚀 Features

### ✅ Authentication Features
- **PostgreSQL Integration**: Secure database-backed authentication
- **Secure Login System**: Username and password authentication
- **Password Hashing**: SHA-256 password hashing for security
- **Session Management**: Persistent login sessions using Streamlit's session state
- **Admin User Management**: Admin users can add new users
- **Logout Functionality**: Secure logout with session cleanup
- **User Activity Tracking**: Last login timestamps

### 👥 User Roles
- **Regular Users**: Can access all data analysis features
- **Admin Users**: Can manage users and access all features

## 📋 Demo Credentials

For testing purposes, the following demo account is available:

| Username | Password   | Role  |
|----------|------------|-------|
| admin    | admin123   | Admin |

**Note**: Additional users can be created by the admin through the User Management section in the app.

## 🐘 PostgreSQL Setup

### Prerequisites
- PostgreSQL server installed and running
- Python packages: `psycopg2-binary`, `sqlalchemy` (already installed)

### 1. Create Database
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE population_db;

# Create user (optional, replace with your credentials)
CREATE USER population_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE population_db TO population_user;
\q
```

### 2. Configure Database Connection
Edit the `database_config.py` file and update the DATABASE_URL:

```python
# In database_config.py
DATABASE_URL = "postgresql://your_username:your_password@localhost:5432/population_db"
```

### 3. Run Database Setup
```bash
# Activate virtual environment
source ~/.pyenv/versions/3.12.9/envs/streamlit_venv/bin/activate

# Run setup script
python setup_postgres.py
```

This will:
- ✅ Connect to your PostgreSQL database
- ✅ Create the necessary tables
- ✅ Create the default admin user (admin/admin123)

### 4. Alternative: Manual Setup
If you prefer to set up manually:

```python
# In Python console or script
from setup_postgres import setup_database
setup_database()
```

## 🔧 How to Use

### 1. Starting the Application
```bash
# Activate your virtual environment
source ~/.pyenv/versions/3.12.9/envs/streamlit_venv/bin/activate

# Run the Streamlit app
streamlit run "population density.py"
```

### 2. Login Process
1. Open the application in your browser
2. You'll see a login page with demo credentials
3. Enter a valid username and password
4. Click "Login" to access the application

### 3. Admin Features
- Login as "admin" with password "admin123"
- Access the "User Management" section in the sidebar
- Add new users with custom usernames and passwords
- View all registered users

## 🔒 Security Features

### Password Security
- Passwords are hashed using SHA-256
- Plain text passwords are never stored
- Secure authentication checking

### Session Security
- Login status is maintained in session state
- Automatic logout on session end
- Secure session cleanup on logout

## 🛠️ Production Deployment

### ⚠️ Important Security Notes

**This demo implementation is NOT suitable for production use!**

For production deployment, you should:

1. **Use a Real Database**: Replace the in-memory USER_DB with:
   - PostgreSQL
   - MySQL
   - MongoDB
   - SQLite (for simple deployments)

2. **Implement Proper Authentication**:
   - OAuth integration (Google, GitHub, etc.)
   - JWT tokens
   - LDAP integration
   - SAML authentication

3. **Add Security Measures**:
   - HTTPS enforcement
   - Rate limiting
   - Password complexity requirements
   - Account lockout after failed attempts
   - Two-factor authentication (2FA)

4. **Environment Variables**:
   - Store sensitive data in environment variables
   - Use `.env` files with `python-dotenv`

### Example Production Setup

```python
import os
from dotenv import load_dotenv
import bcrypt  # More secure than hashlib

load_dotenv()

# Secure password hashing
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Database connection for user management
def authenticate_user(username, password):
    # Connect to your database and verify credentials
    pass
```

## 📚 Code Structure

### Authentication Functions
- `hash_password()`: Secure password hashing
- `authenticate_user()`: User authentication
- `login_page()`: Login UI component
- `logout()`: User logout
- `check_authentication()`: Authentication status check

### User Management (Admin Only)
- `is_admin()`: Check admin privileges
- `add_user()`: Add new users
- `user_management_section()`: Admin UI for user management

## 🔄 Session Management

The application uses Streamlit's session state to:
- Track authentication status
- Store current username
- Maintain user session across page refreshes
- Automatically handle login/logout states

## 🚨 Security Best Practices

1. **Never store passwords in plain text**
2. **Use HTTPS in production**
3. **Implement proper session timeout**
4. **Add input validation and sanitization**
5. **Use environment variables for sensitive data**
6. **Regular security audits and updates**

## 📞 Support

For questions about the authentication system or production deployment, please refer to:
- Streamlit documentation: https://docs.streamlit.io/
- Security best practices: OWASP guidelines
- Database integration: Your preferred database documentation
