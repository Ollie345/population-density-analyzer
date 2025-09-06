import warnings
import streamlit as st
import pandas as pd
import numpy as np
import re
import plotly.express as px
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl
import hashlib
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import psycopg2

# Import database configuration
try:
    from database_config import DATABASE_URL
except ImportError:
    # Fallback configuration if import fails
    DATABASE_URL = "postgresql://population_user:population123@localhost:5432/population_db"

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="keplergl.*")
warnings.filterwarnings("ignore", message=".*pkg_resources.*deprecated.*", category=UserWarning)


# ---------------------------------------------------------
# Database Models and Configuration
# ---------------------------------------------------------

# Database configuration (imported from database_config.py)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def init_database():
    """Initialize database and create tables"""
    db = None
    try:
        Base.metadata.create_all(bind=engine)
        # Create default admin user if it doesn't exist
        db = get_db()
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                password_hash=hash_password("admin123"),
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
    finally:
        if db:
            db.close()

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    """Authenticate a user with PostgreSQL"""
    db = None
    try:
        db = get_db()
        user = db.query(User).filter(User.username == username).first()
        if user and user.password_hash == hash_password(password):
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            db.commit()
            # Store admin status before closing session
            is_admin = user.is_admin
            return True, is_admin
        return False, False
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False, False
    finally:
        if db:
            db.close()

def login_page():
    """Display login page"""
    st.title("🔐 Login to Population Density Analyzer")

    # Database status
    try:
        init_database()
        st.success("✅ Database connection successful!")
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        st.info("Please check your PostgreSQL configuration in database_config.py")

    # Demo credentials info
    with st.expander("📋 Demo Credentials (for testing)"):
        st.write("**Default users:**")
        st.code("""
admin     / admin123 (Admin)
        """)
        st.info("⚠️ Use admin account to add more users via the User Management section.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            authenticated, is_admin = authenticate_user(username, password)
            if authenticated:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.is_admin = is_admin
                st.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.is_admin = False
    st.info("You have been logged out")
    st.rerun()

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

def is_admin():
    """Check if current user is admin"""
    return st.session_state.get('is_admin', False)

def add_user(username, password, make_admin=False):
    """Add a new user to PostgreSQL (admin only)"""
    if not is_admin():
        return False, "Only admins can add users"

    db = None
    try:
        db = get_db()
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return False, "Username already exists"

        # Create new user
        new_user = User(
            username=username,
            password_hash=hash_password(password),
            is_admin=make_admin
        )
        db.add(new_user)
        db.commit()
        return True, f"User {username} added successfully!"
    except Exception as e:
        return False, f"Error adding user: {str(e)}"
    finally:
        if db:
            db.close()

def get_all_users():
    """Get all users from database (admin only)"""
    if not is_admin():
        return []

    db = None
    try:
        db = get_db()
        users = db.query(User).all()
        user_list = []
        for user in users:
            user_list.append({
                'username': user.username,
                'is_admin': user.is_admin,
                'created_at': user.created_at,
                'last_login': user.last_login
            })
        return user_list
    except Exception as e:
        st.error(f"Error fetching users: {str(e)}")
        return []
    finally:
        if db:
            db.close()

def user_management_section():
    """Admin user management section"""
    if is_admin():
        st.sidebar.subheader("👥 User Management")

        with st.sidebar.expander("Add New User"):
            new_username = st.text_input("New Username", key="new_user")
            new_password = st.text_input("New Password", type="password", key="new_pass")
            make_admin = st.checkbox("Make user admin", key="make_admin")
            if st.button("Add User"):
                success, message = add_user(new_username, new_password, make_admin)
                if success:
                    st.success(message)
                    # Clear the form
                    st.rerun()
                else:
                    st.error(message)

        with st.sidebar.expander("Current Users"):
            users = get_all_users()
            if users:
                st.write("**Registered Users:**")
                for user in users:
                    admin_badge = "👑" if user['is_admin'] else ""
                    last_login = user['last_login'].strftime("%Y-%m-%d %H:%M") if user['last_login'] else "Never"
                    st.write(f"• {user['username']} {admin_badge} (Last login: {last_login})")
            else:
                st.write("No users found.")

# ---------------------------------------------------------
# Step 1: Function to parse raw messy text into a DataFrame
# ---------------------------------------------------------
def parse_lga_text(raw_text: str) -> pd.DataFrame:
    # Split lines and strip spaces
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Container for rows
    records = []

    i = 0
    while i < len(lines):
        try:
            lga = lines[i]
            hasc_state = lines[i + 1].split()  # e.g. "AB.AN Abia"
            hasc = hasc_state[0]
            state = " ".join(hasc_state[1:])
            capital = lines[i + 2]

            # Fix numbers with spaces inside (like "155 600")
            pop = re.sub(r"\s+", "", lines[i + 3])
            lat = lines[i + 4]
            lon = lines[i + 5]
            area = lines[i + 6]
            density = lines[i + 7]

            records.append({
                "LGA": lga,
                "HASC": hasc,
                "State": state,
                "Capital": capital,
                "Population": pop,
                "Latitude": lat,
                "Longitude": lon,
                "AreaKm": area,
                "Density": density
            })
            i += 8
        except Exception:
            i += 1  # skip bad block

    df = pd.DataFrame(records)
    return df


# ---------------------------------------------------------
# Step 2: Clean the DataFrame
# ---------------------------------------------------------
def clean_lga_data(df: pd.DataFrame) -> pd.DataFrame:
    # Make a copy to avoid modifying the original
    df = df.copy()

    # Clean column names: remove BOM, strip spaces, replace special chars, lowercase
    df.columns = (
        df.columns.str.strip()
        .str.replace('\ufeff', '', regex=False)  # Remove BOM character
        .str.replace('ï»¿', '', regex=False)     # Remove BOM as visible characters
        .str.replace(r'[()]', '', regex=True)    # Remove parentheses
        .str.replace(' ', '_', regex=False)
        .str.lower()
    )

    # Define column types explicitly
    string_cols = ["lga", "hasc", "state", "capital"]
    numeric_cols = ["population", "latitude", "longitude", "areakm", "area_km", "density"]

    # Ensure string columns remain as strings and clean them
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Fix numeric columns
    for col in numeric_cols:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.strip()
                .str.replace(" ", "", regex=False)
                .str.replace(",", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ---------------------------------------------------------
# Step 3: Streamlit App
# ---------------------------------------------------------
st.set_page_config(page_title="LGA Data Explorer", layout="wide")

# Check authentication
if not check_authentication():
    login_page()
    st.stop()  # Stop execution if not authenticated

# Main App (only shown if authenticated)
st.title("📊 LGA Data Analyzer")

# Add logout button in sidebar
with st.sidebar:
    st.write(f"👤 Logged in as: **{st.session_state.username}**")
    if st.button("🚪 Logout"):
        logout()

    # Add user management for admin
    user_management_section()

st.sidebar.header("Data Input")
option = st.sidebar.radio("Choose input type:", ["Upload CSV", "Paste Text"])

df = None  # initialize to avoid NameError

if option == "Upload CSV":
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            # Read file content into memory to avoid file pointer issues
            file_content = uploaded_file.getvalue().decode('utf-8-sig')  # utf-8-sig handles BOM
            # Read CSV with explicit dtype specification to prevent type inference issues
            raw_df = pd.read_csv(pd.io.common.StringIO(file_content), dtype=str)
        except UnicodeDecodeError:
            try:
                # Try latin1 encoding if utf-8 fails
                uploaded_file.seek(0)  # Reset file pointer
                file_content = uploaded_file.getvalue().decode('latin1')
                raw_df = pd.read_csv(pd.io.common.StringIO(file_content), dtype=str)
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
                st.error("Please ensure the file is a valid CSV and try different encodings.")
                raw_df = None
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            raw_df = None

        if raw_df is not None:
            st.write("Raw Data Types:", raw_df.dtypes.to_dict())
            st.write("Raw Data Sample:", raw_df.head(3))
            df = clean_lga_data(raw_df)
            st.write("Cleaned Data Types:", df.dtypes.to_dict())
            st.write("Cleaned Data Sample:", df.head(3))


elif option == "Paste Text":
    raw_text = st.text_area("Paste your raw LGA text here:", height=300)
    if st.button("Parse Text") and raw_text:
        raw_df = parse_lga_text(raw_text)
        df = clean_lga_data(raw_df)
    else:
        df = None
else:
    df = None

# ---------------------------------------------------------
# Step 4: Display & Analysis
# ---------------------------------------------------------
if df is not None and not df.empty:
    st.subheader("🔍 Cleaned Data")
    st.dataframe(df)

    # Sidebar filters
    states = df["state"].dropna().unique()
    selected_states = st.sidebar.multiselect("Select State(s)", states, default=states)
    filtered_df = df[df["state"].isin(selected_states)]

    # Summary statistics
    st.subheader("📈 Summary Statistics")
    st.write(filtered_df.describe(include="all"))

    # Population bar chart
    st.subheader("👥 Population by LGA")
    fig_pop = px.bar(filtered_df, x="lga", y="population", color="state", height=500)
    st.plotly_chart(fig_pop, use_container_width=True)

    # Map visualization
    st.subheader("🗺️ Geographic Distribution")
    fig_map = px.scatter_map(
        filtered_df,
        lat="latitude",
        lon="longitude",
        size="population",
        color="state",
        hover_name="lga",
        map_style="carto-positron",
        zoom=5,
        height=600
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # Kepler.gl Choropleth Map
    st.subheader("🗺️ Kepler.gl Population Density Choropleth")

    # Prepare data for Kepler map
    kepler_data = filtered_df.copy()
    kepler_data = kepler_data.rename(columns={
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        'population': 'Population',
        'lga': 'LGA',
        'state': 'State'
    })

    # Create Kepler map configuration
    config = {
        'version': 'v1',
        'config': {
            'mapState': {
                'latitude': 9.0820,
                'longitude': 8.6753,
                'zoom': 5.5
            },
            'mapStyle': {
                'styleType': 'dark'
            }
        }
    }

    # Create Kepler map
    map_1 = KeplerGl(height=600, config=config)
    map_1.add_data(data=kepler_data, name='Population Density')

    # Display Kepler map
    keplergl_static(map_1)

    # Density analysis
    st.subheader("🌍 Population Density")
    # Use area_km if available, otherwise fallback to areakm
    area_col = "area_km" if "area_km" in filtered_df.columns else "areakm"
    fig_density = px.scatter(
        filtered_df,
        x=area_col,
        y="density",
        size="population",
        color="state",
        hover_name="lga"
    )
    st.plotly_chart(fig_density, use_container_width=True)
else:
    st.info("👆 Upload a CSV or paste raw text to start analysis")
