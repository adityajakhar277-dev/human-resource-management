import mysql.connector
from login_register import login_user, register_user
from feature import *

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Vidaya@1986',
    'database': 'hrms_db'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def get_employee_id(conn, user_id):
    cursor = conn.cursor()
    query = "SELECT emp_id FROM employees WHERE user_id = %s"
    try:
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    except mysql.connector.Error as err:
        print(f"Error fetching employee ID: {err}")
        return None
    finally:
        cursor.close()

def main_menu(user_data):
    print(f"\nHello {user_data['username']}, welcome back — Role: {user_data['role']}")
    employee_id = None
    if user_data['role'] == 'employee':
        conn_id = get_db_connection()
        if conn_id:
            employee_id = get_employee_id(conn_id, user_data['id'])
            conn_id.close()
            if not employee_id:
                print("Note: Your account isn't linked to an employee record yet. Some self-service features are unavailable — contact an administrator.")

    while True:
        print("\nHRMS Main Menu")
        if user_data['role'] == 'admin':
            print("1. Employee Information Management")
            print("2. Leave Management")
            print("3. Payroll Management")
            print("4. Performance Management")
            print("5. Recruitment Management")
        else:
            print("1. View My Details")
            print("2. Apply for Leave")
            print("4. View My Reviews")
        print("6. Sign out")
        choice = input("Please enter the number of your choice: ")

        conn = get_db_connection()
        if not conn:
            print("Unable to connect to database.")
            continue

        try:
            if user_data['role'] == 'admin':
                if choice == '1':
                    employee_info_menu(conn)
                elif choice == '2':
                    leave_management_menu(conn, role='admin')
                elif choice == '3':
                    calculate_payroll(conn)
                elif choice == '4':
                    performance_management_menu(conn)
                elif choice == '5':
                    recruitment_management_menu(conn)
                elif choice == '6':
                    print("Signing you out. See you soon.")
                    break
                else:
                    print("Invalid choice. Try again.")
            else:
                if choice == '1':
                    print("Showing your details...")
                elif choice == '2':
                    if employee_id:
                        apply_leave(conn, emp_id=employee_id)
                    else:
                        print("Cannot apply for leave because your employee record is not linked. Contact admin.")
                elif choice == '4':
                    print("Showing your performance history...")
                elif choice == '6':
                    print("Signing you out. See you soon.")
                    break
                else:
                    print("Invalid choice.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()

if __name__ == "__main__":
    print("--- Welcome to the HR Management System ---")
    while True:
        print("\n1. Log in\n2. Register (admin only)\n3. Exit")
        auth_choice = input("Select an option: ")
        conn = get_db_connection()
        if not conn:
            continue
        try:
            if auth_choice == '1':
                user_data = login_user(conn)
                if user_data:
                    conn.close()
                    main_menu(user_data)
            elif auth_choice == '2':
                register_user(conn, is_admin=True)
            elif auth_choice == '3':
                print("Goodbye — take care.")
                break
            else:
                print("Invalid choice.")
        finally:
            if conn and conn.is_connected():
                conn.close()