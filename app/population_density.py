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

def validate_csv_data(df, required_cols=None):
    """Validate CSV data for required columns and data types"""
    if df.empty:
        return False, "CSV file is empty"

    if required_cols is None:
        required_cols = ['latitude', 'longitude']

    # Check for required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing required columns: {', '.join(missing_cols)}"

    # Validate coordinate ranges
    if 'latitude' in df.columns:
        if not (-90 <= df['latitude'].min() <= 90) or not (-90 <= df['latitude'].max() <= 90):
            return False, "Latitude values must be between -90 and 90"

    if 'longitude' in df.columns:
        if not (-180 <= df['longitude'].min() <= 180) or not (-180 <= df['longitude'].max() <= 180):
            return False, "Longitude values must be between -180 and 180"

    # Check for reasonable file size
    if len(df) > 50000:
        return False, "File too large. Maximum 50,000 records allowed."

    return True, "Data validation successful"

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

    # Advanced Layer Controls - Always visible
    st.markdown("---")
    st.subheader("🎛️ Spatial Analysis Layers")

    # Initialize session state for data layers
    if 'layer_data' not in st.session_state:
        st.session_state.layer_data = {}
    if 'polygons' not in st.session_state:
        st.session_state.polygons = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}

    # Default Data Layers
    st.markdown("### 📊 Default Layers")

    if st.button("📍 Load Population Density", key="load_population"):
        try:
            pop_df = pd.read_csv("docs/data/Population_Density.csv")
            st.session_state.layer_data['population_density'] = {
                'data': pop_df,
                'type': 'choropleth',
                'visible': True,
                'opacity': 0.7
            }
            st.success("✅ Population Density layer loaded!")
        except Exception as e:
            st.error(f"❌ Error loading population data: {str(e)}")

    if st.button("🏪 Load Market Data", key="load_markets"):
        try:
            market_df = pd.read_csv("docs/data/Open_Market_Data.csv")
            st.session_state.layer_data['market_data'] = {
                'data': market_df,
                'type': 'points',
                'visible': True,
                'opacity': 0.8
            }
            st.success("✅ Market Data layer loaded!")
        except Exception as e:
            st.error(f"❌ Error loading market data: {str(e)}")

    if st.button("🏬 Load Outlet Data", key="load_outlets"):
        try:
            outlet_df = pd.read_csv("docs/data/Outlet_Data.csv")
            st.session_state.layer_data['outlet_data'] = {
                'data': outlet_df,
                'type': 'points',
                'visible': True,
                'opacity': 0.8
            }
            st.success("✅ Outlet Data layer loaded!")
        except Exception as e:
            st.error(f"❌ Error loading outlet data: {str(e)}")

    # Layer Visibility Controls
    if st.session_state.layer_data:
        st.markdown("### 👁️ Layer Visibility & Filters")
        for layer_name, layer_info in st.session_state.layer_data.items():
            with st.expander(f"⚙️ {layer_name.replace('_', ' ').title()}", expanded=False):
                layer_info['visible'] = st.checkbox(
                    "Show Layer",
                    value=layer_info['visible'],
                    key=f"visible_{layer_name}"
                )

                if layer_info['visible']:
                    layer_info['opacity'] = st.slider(
                        "Opacity",
                        0.0, 1.0, layer_info['opacity'],
                        key=f"opacity_{layer_name}"
                    )

                    # Add filtering options based on layer type
                    df = layer_info['data']
                    if 'economic_class' in df.columns:
                        classes = df['economic_class'].unique()
                        selected_classes = st.multiselect(
                            "Economic Class Filter",
                            classes,
                            default=classes,
                            key=f"filter_class_{layer_name}"
                        )
                        if len(selected_classes) != len(classes):
                            # Filter the data
                            filtered_df = df[df['economic_class'].isin(selected_classes)]
                            st.session_state.layer_data[layer_name]['data'] = filtered_df
                            st.info(f"Filtered to {len(filtered_df)} records")

                    if 'status' in df.columns:
                        statuses = df['status'].unique()
                        selected_statuses = st.multiselect(
                            "Status Filter",
                            statuses,
                            default=statuses,
                            key=f"filter_status_{layer_name}"
                        )
                        if len(selected_statuses) != len(statuses):
                            filtered_df = df[df['status'].isin(selected_statuses)]
                            st.session_state.layer_data[layer_name]['data'] = filtered_df
                            st.info(f"Filtered to {len(filtered_df)} records")

    # Customer Data Upload
    st.markdown("### 📤 Customer Data Upload")
    uploaded_file = st.file_uploader(
        "Upload CSV or GeoJSON",
        type=['csv', 'geojson'],
        key="customer_upload"
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                customer_df = pd.read_csv(uploaded_file)

                # Validate the data
                is_valid, validation_message = validate_csv_data(customer_df)
                if is_valid:
                    layer_name = f"customer_{uploaded_file.name.split('.')[0]}"
                    st.session_state.layer_data[layer_name] = {
                        'data': customer_df,
                        'type': 'points',
                        'visible': True,
                        'opacity': 0.8
                    }
                    st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                    st.info(f"📊 Loaded {len(customer_df)} records")
                else:
                    st.error(f"❌ Validation failed: {validation_message}")

            elif uploaded_file.name.endswith('.geojson'):
                st.info("🗺️ GeoJSON support coming soon!")
                st.info("💡 For now, please convert to CSV format with lat/lon columns")
            else:
                st.error("❌ Unsupported file format. Please upload CSV or GeoJSON files.")

        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("💡 Check that your CSV has proper column headers and data formatting")

    # Export Options
    if st.session_state.layer_data:
        st.markdown("### 💾 Export Options")

        # Combined data export
        if st.button("📊 Export Combined Dataset", key="export_combined"):
            if st.session_state.layer_data:
                combined_data = []
                for layer_name, layer_info in st.session_state.layer_data.items():
                    if layer_info['visible']:
                        df = layer_info['data'].copy()
                        df['layer_type'] = layer_name
                        combined_data.append(df)

                if combined_data:
                    final_df = pd.concat(combined_data, ignore_index=True)
                    csv_data = final_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Combined CSV",
                        data=csv_data,
                        file_name="combined_spatial_data.csv",
                        mime="text/csv",
                        key="download_combined"
                    )

        # Individual layer exports
        if st.session_state.layer_data:
            st.markdown("#### Individual Layer Exports")
            for layer_name, layer_info in st.session_state.layer_data.items():
                if layer_info['visible']:
                    csv_data = layer_info['data'].to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {layer_name.replace('_', ' ').title()}",
                        data=csv_data,
                        file_name=f"{layer_name}.csv",
                        mime="text/csv",
                        key=f"download_{layer_name}"
                    )

    # Periodic Refresh Settings
    st.markdown("### 🔄 Auto Refresh")
    refresh_interval = st.selectbox(
        "Refresh Interval",
        ["Off", "30 seconds", "1 minute", "5 minutes"],
        key="refresh_interval"
    )
    if refresh_interval != "Off":
        st.info(f"🔄 Map will refresh every {refresh_interval}")

    # Spatial Analysis Tools
    st.markdown("### 🎯 Spatial Analysis")
    if st.button("📏 Distance Analysis", key="distance_analysis"):
        st.info("Distance analysis tools will be available")

    if st.button("📍 Buffer Analysis", key="buffer_analysis"):
        st.info("Buffer analysis tools coming soon")

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

    # Advanced Kepler.gl Map with Functional Requirements
    st.subheader("🗺️ Advanced Kepler.gl Spatial Analysis Platform")


    # Create Kepler map with all layers

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
            },
            'visState': {
                'layers': [],
                'interactionConfig': {
                    'tooltip': {
                        'enabled': True,
                        'fieldsToShow': {}
                    },
                    'brush': {
                        'enabled': True
                    }
                }
            }
        }
    }

    # Initialize Kepler map
    kepler_map = KeplerGl(height=600, config=config)

    # Add visible layers to map
    for layer_name, layer_info in st.session_state.layer_data.items():
        if layer_info['visible']:
            layer_data = layer_info['data']

            # Rename columns for Kepler
            kepler_data = layer_data.copy()
            column_mapping = {
        'latitude': 'Latitude',
        'longitude': 'Longitude',
                'lat': 'Latitude',
                'lon': 'Longitude',
                'lng': 'Longitude'
            }

            for old_col, new_col in column_mapping.items():
                if old_col in kepler_data.columns:
                    kepler_data = kepler_data.rename(columns={old_col: new_col})

            # Add to map
            kepler_map.add_data(
                data=kepler_data,
                name=layer_name.replace('_', ' ').title()
            )

    # Display the map
    keplergl_static(kepler_map)
    # Data Summary
    st.markdown("### 📊 Layer Summary")
    if st.session_state.layer_data:
        summary_data = []
        for layer_name, layer_info in st.session_state.layer_data.items():
            summary_data.append({
                'Layer': layer_name.replace('_', ' ').title(),
                'Type': layer_info['type'],
                'Records': len(layer_info['data']),
                'Visible': '✅' if layer_info['visible'] else '❌',
                'Opacity': f"{layer_info['opacity']:.1f}"
            })

        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df)
    else:
        st.info("👆 Load default layers or upload customer data to get started!")
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
