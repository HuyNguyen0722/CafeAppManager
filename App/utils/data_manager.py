import json
import hashlib
import os
import uuid
import shutil

# --- Path Setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
IMAGES_DIR = os.path.join(DATA_DIR, 'images') # Directory for menu item images
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
MENU_FILE = os.path.join(DATA_DIR, 'menu.json')
TABLES_FILE = os.path.join(DATA_DIR, 'tables.json')

# --- Helper Functions ---
def _ensure_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(IMAGES_DIR): # Ensure images directory also exists
        os.makedirs(IMAGES_DIR)

def _load_json(file_path, default_data=None):
    _ensure_dir()
    if not os.path.exists(file_path):
        if default_data is not None:
            _save_json(file_path, default_data)
        return default_data if default_data is not None else []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default_data if default_data is not None else []

def _save_json(file_path, data):
    _ensure_dir()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def copy_image_to_data(source_path):
    """Copies an image to the data/images folder and returns the new relative path."""
    if not source_path or not os.path.exists(source_path):
        return ""
    
    _ensure_dir()
    
    try:
        filename = f"{uuid.uuid4()}{os.path.splitext(source_path)[1]}"
        destination = os.path.join(IMAGES_DIR, filename)
        shutil.copy(source_path, destination)
        # Return a relative path to be stored in JSON, making the project portable
        return os.path.join('data', 'images', filename)
    except Exception as e:
        print(f"Error copying image: {e}")
        return ""


# --- User Management ---
def get_users():
    default_users = [
        {"username": "admin", "password": hash_password("admin"), "role": "admin"},
        {"username": "nhanvienA", "password": hash_password("123"), "role": "staff"}
    ]
    return _load_json(USERS_FILE, default_users)

def add_user(user_data):
    users = get_users()
    users.append(user_data)
    _save_json(USERS_FILE, users)

def update_user(username, new_data):
    users = get_users()
    for user in users:
        if user['username'] == username:
            user.update(new_data)
            break
    _save_json(USERS_FILE, users)

def delete_user(username):
    users = get_users()
    users = [user for user in users if user['username'] != username]
    _save_json(USERS_FILE, users)

# --- Menu Management ---
def get_menu():
    return _load_json(MENU_FILE, [])

def add_menu_item(item_data):
    menu = get_menu()
    menu.append(item_data)
    _save_json(MENU_FILE, menu)

def update_menu_item(item_id, new_data):
    menu = get_menu()
    for item in menu:
        if item.get('id') == item_id:
            item.update(new_data)
            break
    _save_json(MENU_FILE, menu)

def delete_menu_item(item_id):
    menu = get_menu()
    menu = [item for item in menu if item.get('id') != item_id]
    _save_json(MENU_FILE, menu)
    
def migrate_menu_to_include_ids():
    menu = get_menu()
    updated = False
    for item in menu:
        if 'id' not in item:
            item['id'] = str(uuid.uuid4())
            updated = True
    if updated:
        _save_json(MENU_FILE, menu)

# --- Table Management ---
def get_tables():
    default_tables = [
        {"id": i, "status": "Trống", "order": {}, "employee": None} for i in range(1, 16)
    ]
    return _load_json(TABLES_FILE, default_tables)

def save_tables(tables_data):
    _save_json(TABLES_FILE, tables_data)

