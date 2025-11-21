import hashlib
import getpass
import mysql.connector

def hash_password(password):
    """Return SHA-256 hash of the provided password."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(conn, is_admin=False):
    """Register a new user. For admins set is_admin=True."""
    username = input("Choose a username: ").strip()
    while True:
        password = getpass.getpass("Choose a password (input hidden): ").strip()
        confirm = getpass.getpass("Confirm password: ").strip()
        if password != confirm:
            print("Passwords did not match. Please try again.")
        elif not password:
            print("Password cannot be empty. Please try again.")
        else:
            break

    role = 'admin' if is_admin else 'employee'
    hashed_pass = hash_password(password)
    
    cursor = conn.cursor()
    try:
        query = "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, hashed_pass, role))
        conn.commit()
        print(f"User '{username}' created successfully as {role}.")
    except mysql.connector.Error as err:
        print(f"Registration failed: {err}")
    finally:
        cursor.close()

def login_user(conn):
    """Authenticate and return a small user dict on success."""
    username = input("Username: ").strip()
    password = getpass.getpass("Password (input hidden): ").strip()
    hashed_pass = hash_password(password)
    
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, username, role, password_hash FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    cursor.close()

    if user and user['password_hash'] == hashed_pass:
        print(f"Welcome back, {user['username']}!")
        return {'id': user['id'], 'username': user['username'], 'role': user['role']}
    else:
        print("Login failed: incorrect username or password.")
        return None