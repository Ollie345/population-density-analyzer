#!/usr/bin/env python3
"""
Setup script for Population Density Analyzer
Run this script to set up the entire project environment.
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible!")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible. Please use Python 3.8+")
        return False

def create_virtual_environment():
    """Create virtual environment"""
    if os.path.exists("venv"):
        print("ℹ️  Virtual environment already exists!")
        return True

    return run_command("python -m venv venv", "Creating virtual environment")

def install_dependencies():
    """Install Python dependencies"""
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
    else:
        activate_cmd = "source venv/bin/activate"

    commands = [
        f"{activate_cmd} && pip install --upgrade pip",
        f"{activate_cmd} && pip install -r requirements.txt"
    ]

    for cmd in commands:
        if not run_command(cmd, "Installing dependencies"):
            return False
    return True

def setup_database():
    """Setup PostgreSQL database"""
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
    else:
        activate_cmd = "source venv/bin/activate"

    cmd = f"{activate_cmd} && python database/setup_postgres.py"
    return run_command(cmd, "Setting up PostgreSQL database")

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("# Environment Variables for Population Density Analyzer\n")
            f.write("# Copy this file to .env and update with your values\n")
            f.write("DATABASE_URL=postgresql://population_user:population123@localhost:5432/population_db\n")
        print("✅ Created .env template file!")
    else:
        print("ℹ️  .env file already exists!")

def main():
    """Main setup function"""
    print("🚀 Population Density Analyzer - Setup")
    print("=" * 50)

    # Change to project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Create .env file
    create_env_file()

    print("\n🎉 Basic setup completed!")
    print("\n📋 Next steps:")
    print("1. Install and configure PostgreSQL")
    print("2. Update database credentials in database/database_config.py")
    print("3. Run: python database/setup_postgres.py")
    print("4. Start the app: streamlit run app/population_density.py")

    # Ask if user wants to setup database
    response = input("\n❓ Do you want to setup PostgreSQL database now? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        if setup_database():
            print("\n🎊 Setup completed successfully!")
            print("You can now run: streamlit run app/population_density.py")
        else:
            print("\n⚠️  Database setup failed. Please check PostgreSQL installation.")
    else:
        print("\nℹ️  Skipping database setup. Run 'python database/setup_postgres.py' when ready.")

if __name__ == "__main__":
    main()
