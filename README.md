# 📊 Population Density Analyzer

A comprehensive Streamlit web application for analyzing population density data with interactive visualizations, user authentication, and PostgreSQL database integration.

## 🌟 Features

### ✅ Core Functionality
- **Interactive Data Visualization**: Plotly charts for population analysis
- **Advanced Geographic Mapping**: Kepler.gl choropleth maps for spatial data with layer management
- **CSV Data Processing**: Automatic data cleaning and type conversion
- **Real-time Filtering**: Dynamic multi-layer filtering by economic class, status, and custom criteria
- **Layer Management**: Load default layers (Population, Markets, Outlets) with button controls
- **Customer Data Upload**: File upload with validation for CSV datasets
- **Export Features**: Download filtered datasets as CSV files
- **Data Validation**: Comprehensive validation for uploaded data (coordinates, file size, required fields)

### 🔐 Authentication & Security
- **PostgreSQL Authentication**: Secure database-backed user management
- **Password Hashing**: SHA-256 encryption for user passwords
- **Role-based Access**: Admin and regular user permissions
- **Session Management**: Secure login/logout with session tracking

### 👥 User Management
- **Admin Dashboard**: User creation and management interface
- **Activity Logging**: Track user login times and activities
- **Multi-user Support**: Concurrent user access with individual sessions

### 🎛️ Advanced Spatial Analysis Features
- **Default Data Layers**: Pre-loaded Population, Market, and Outlet datasets
- **Layer Transparency**: Opacity controls for overlapping layers
- **Multi-layer Filtering**: Filter by economic class, status, and custom criteria
- **Customer Data Integration**: Upload and overlay custom datasets
- **Export Capabilities**: Download filtered datasets and combined results
- **Real-time Updates**: Dynamic map updates without page refresh

## 🚀 Quick Start

### 📦 Deployment Notes
- **Streamlit Cloud**: Uses `packages.txt` for system dependencies
- **PyArrow**: Version 15.0.2 is pinned to use pre-built wheels
- **Build Tools**: cmake and build-essential are included in packages.txt
- **Python Version**: Compatible with Python 3.8+

### 🔧 Troubleshooting Deployment Issues
If you encounter pyarrow build errors during deployment:
1. The `packages.txt` file includes necessary build tools
2. Specific package versions are pinned to avoid compilation issues
3. All dependencies use versions with available pre-built wheels

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/population-density-analyzer.git
   cd population-density-analyzer
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database:**
   ```bash
   # Install PostgreSQL if not already installed
   sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
   # or
   brew install postgresql  # macOS

   # Start PostgreSQL service
   sudo systemctl start postgresql  # Linux
   # or
   brew services start postgresql   # macOS
   ```

5. **Configure database:**
   ```bash
   # Run the database setup script
   python database/setup_postgres.py
   ```

6. **Run the application:**
   ```bash
   streamlit run app/population_density.py
   ```

## 🚀 Deployment Options

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t population-analyzer .
docker run -p 8502:8502 population-analyzer
```

### Streamlit Cloud Deployment
1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Set the main file path: `app/population_density.py`
5. Add environment variables in Streamlit Cloud settings

### Traditional Server Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="your_production_db_url"

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8502 app.population_density:app
```

## 📁 Project Structure

```
population-density-analyzer/
├── app/
│   └── population_density.py      # Main Streamlit application
├── database/
│   ├── database_config.py         # Database configuration
│   └── setup_postgres.py         # Database setup script
├── docs/
│   └── README_AUTH.md            # Authentication documentation
├── config/
│   └── .streamlit/
│       └── config.toml           # Streamlit configuration
├── data/
│   └── (sample data files)       # Data files directory
├── requirements.txt               # Python dependencies
├── README.md                     # This file
└── .gitignore                   # Git ignore file
```

## 🗄️ Database Setup

### PostgreSQL Configuration

1. **Create Database:**
   ```sql
   CREATE DATABASE population_db;
   CREATE USER population_user WITH PASSWORD 'population123';
   GRANT ALL PRIVILEGES ON DATABASE population_db TO population_user;
   ```

2. **Environment Variables:**
   ```bash
   export DATABASE_URL="postgresql://population_user:population123@localhost:5432/population_db"
   ```

3. **Initialize Database:**
   ```bash
   python database/setup_postgres.py
   ```

### Default Admin User
- **Username:** `admin`
- **Password:** `admin123`
- **Role:** Administrator

## 📊 Usage

### For Regular Users
1. **Login** with your credentials
2. **Upload CSV** files containing population data
3. **Explore Visualizations:**
   - Population bar charts by LGA
   - Interactive Kepler.gl maps
   - Population density scatter plots
4. **Filter Data** by state selection

### For Administrators
1. **Access Admin Panel** (sidebar after login)
2. **Add New Users** with custom credentials
3. **View User List** with activity tracking
4. **Manage Permissions** (admin/regular user roles)

## 🔧 Configuration

### Database Configuration
Edit `database/database_config.py`:
```python
DATABASE_URL = "postgresql://your_user:your_password@localhost:5432/population_db"
```

### Streamlit Configuration
Edit `config/.streamlit/config.toml`:
```toml
[server]
runOnSave = true
headless = true
port = 8502
```

## 📈 Data Format

### Required CSV Columns
- `lga`: Local Government Area name
- `state`: State name
- `population`: Population count
- `latitude`: Geographic latitude
- `longitude`: Geographic longitude
- `area`: Area in square kilometers
- `density`: Population density

### Sample Data Structure
```csv
lga,state,population,latitude,longitude,area,density
Abuja Municipal,Abuja,2000000,9.0765,7.3986,200,10000
Lagos Mainland,Lagos,1500000,6.5244,3.3792,150,10000
```

## 🔒 Security Features

- **Password Hashing**: SHA-256 with salt
- **SQL Injection Protection**: Parameterized queries
- **Session Security**: Secure session management
- **Access Control**: Role-based permissions
- **Activity Monitoring**: Login tracking

## 🚀 Deployment

### Local Development
```bash
streamlit run app/population_density.py --server.port 8502
```

### Production Deployment
```bash
# Using Docker
docker build -t population-analyzer .
docker run -p 8502:8502 population-analyzer

# Or using Streamlit Cloud
# Deploy directly from GitHub repository
```

## 🛠️ Development

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test locally
3. Commit changes: `git commit -m "Add new feature"`
4. Push to branch: `git push origin feature/new-feature`
5. Create Pull Request

### Code Style
- Follow PEP 8 guidelines
- Use type hints for function parameters
- Add docstrings to all functions
- Keep functions small and focused

## 📚 API Documentation

### Authentication Functions
- `authenticate_user(username, password)`: Verify user credentials
- `add_user(username, password, is_admin)`: Create new user
- `get_all_users()`: Retrieve user list (admin only)

### Data Processing Functions
- `parse_lga_text(raw_text)`: Parse text data into DataFrame
- `clean_lga_data(df)`: Clean and format data
- `get_db()`: Get database session

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Error:**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql

   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

2. **Import Errors:**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

3. **Permission Errors:**
   ```bash
   # Grant database permissions
   psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE population_db TO population_user;"
   ```

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in `docs/`
- Review the authentication guide in `docs/README_AUTH.md`

## 🔄 Updates

### Version History
- **v1.0.0**: Initial release with basic functionality
- **v1.1.0**: Added PostgreSQL authentication
- **v1.2.0**: Integrated Kepler.gl maps
- **v1.3.0**: Enhanced user management system

---

**Built with ❤️ using Streamlit, PostgreSQL, and modern Python practices.**
