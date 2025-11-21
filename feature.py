import mysql.connector
from datetime import date

# NOTE: Expected DB schema details were removed from this file to reduce clutter.
# See db_config.md in the project root for database setup notes and expected tables.


# ---------------------------
# EMPLOYEE MANAGEMENT
# ---------------------------

def employee_info_menu(conn):
    while True:
        print("\n### Employee Info Menu ###")
        print("1. Add a new employee (enter personal & job details)")
        print("2. List all employees and view details")
        print("3. Edit an employee's details")
        print("4. Return to previous menu")
        choice = input("What would you like to do? ")

        if choice == '1':
            add_employee(conn)
        elif choice == '2':
            view_employee(conn)   # will list all employees first
        elif choice == '3':
            update_employee(conn)
        elif choice == '4':
            break
        else:
            print("Invalid choice.")


def add_employee(conn):
    print("\n--- Add a New Employee ---")
    first_name = input("First name: ").strip()
    last_name = input("Last name: ").strip()
    email = input("Email address: ").strip()
    phone = input("Phone number (e.g. +1-555-555-5555): ").strip()
    department = input("Department (e.g. Sales, HR): ").strip()
    job_title = input("Job title: ").strip()

    # Validate salary entry
    while True:
        salary_str = input("Salary (numbers only, e.g. 45000): ").strip()
        try:
            salary = float(salary_str)
            break
        except ValueError:
            print("That doesn't look like a number. Please enter the salary as digits only.")

    cursor = conn.cursor()
    query = """
        INSERT INTO employees (first_name, last_name, email, phone, department, job_title, salary)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(query, (first_name, last_name, email, phone, department, job_title, salary))
        conn.commit()
        new_id = cursor.lastrowid
        print(f"Employee {first_name} {last_name} added — employee ID {new_id}.")
    except mysql.connector.Error as err:
        print(f"Unable to add employee: {err}")
    finally:
        cursor.close()


def view_employee(conn):
    """
    Show a list of all employees with key details and latest rating info.
    Then allow user to enter an employee ID to view full details + reviews.
    """
    cursor = conn.cursor(dictionary=True)

    # Fetch all employees
    cursor.execute("SELECT emp_id, first_name, last_name, job_title, department, salary FROM employees ORDER BY emp_id")
    employees = cursor.fetchall()

    if not employees:
        print("\nNo employees found.")
        cursor.close()
        return

    # For each employee fetch latest review (if any)
    print("\n--- Employees List ---")
    for emp in employees:
        emp_id = emp['emp_id']
        # get latest review
        cursor.execute("""
            SELECT rating, review_date
            FROM performance_reviews
            WHERE emp_id = %s
            ORDER BY review_date DESC, review_id DESC
            LIMIT 1
        """, (emp_id,))
        latest = cursor.fetchone()
        rating_text = f"Latest Rating: {latest['rating']} (on {latest['review_date']})" if latest else "Rating not added yet"

        print(f"{emp['emp_id']}. {emp['first_name']} {emp['last_name']} | Job: {emp.get('job_title', '---')} | Dept: {emp.get('department','---')} | Salary: {emp.get('salary')}")
        print(f"   {rating_text}")

    # Ask user if they want details for a specific employee
    emp_id_in = input("\nEnter Employee ID to view full details (or press Enter to go back): ").strip()
    if not emp_id_in:
        cursor.close()
        return

    cursor.execute("SELECT * FROM employees WHERE emp_id = %s", (emp_id_in,))
    employee = cursor.fetchone()

    if not employee:
        print("Employee not found.")
        cursor.close()
        return

    print("\n--- Employee Details ---")
    for key, value in employee.items():
        print(f"{key.replace('_',' ').title()}: {value}")

    # Show all performance reviews for this employee (if any)
    cursor.execute("""
        SELECT review_date, rating, comments
        FROM performance_reviews
        WHERE emp_id = %s
        ORDER BY review_date DESC, review_id DESC
    """, (emp_id_in,))
    reviews = cursor.fetchall()
    if reviews:
        print("\nPerformance Reviews:")
        for r in reviews:
            print(f" - {r['review_date']}: Rating {r['rating']} | {r['comments']}")
    else:
        print("\nPerformance Reviews: Rating not added yet")

    cursor.close()


def update_employee(conn):
    emp_id = input("Enter Employee ID to update: ").strip()

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees WHERE emp_id = %s", (emp_id,))
    employee = cursor.fetchone()

    if not employee:
        print("❌ Error: Employee not found.")
        cursor.close()
        return

    print("\n--- Current Employee Details ---")
    print(f"Name: {employee['first_name']} {employee['last_name']}")
    print(f"Phone: {employee.get('phone','---')}")
    print(f"Job Title: {employee.get('job_title','---')}")
    print(f"Department: {employee.get('department','---')}")
    print(f"Salary: {employee['salary']}")

    new_first = input("New First Name (leave blank = no change): ").strip()
    new_last = input("New Last Name (leave blank = no change): ").strip()
    new_phone = input("New Phone (leave blank = no change): ").strip()
    new_job = input("New Job Title (leave blank = no change): ").strip()
    new_dept = input("New Department (leave blank = no change): ").strip()
    new_salary_str = input("New Salary (leave blank = no change): ").strip()

    updates = []
    values = []

    if new_first:
        updates.append("first_name = %s")
        values.append(new_first)
    if new_last:
        updates.append("last_name = %s")
        values.append(new_last)
    if new_phone:
        updates.append("phone = %s")
        values.append(new_phone)
    if new_job:
        updates.append("job_title = %s")
        values.append(new_job)
    if new_dept:
        updates.append("department = %s")
        values.append(new_dept)
    if new_salary_str:
        try:
            new_salary = float(new_salary_str)
            updates.append("salary = %s")
            values.append(new_salary)
        except ValueError:
            print("Invalid salary entered. Salary not changed.")

    if not updates:
        print("No changes entered.")
        cursor.close()
        return

    values.append(emp_id)
    update_query = "UPDATE employees SET " + ", ".join(updates) + " WHERE emp_id = %s"

    try:
        cursor.execute(update_query, tuple(values))
        conn.commit()
        print("✅ Employee updated successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()


# ---------------------------
# LEAVE MANAGEMENT
# ---------------------------

def leave_management_menu(conn, role):
    while True:
        print("\n### Leave Management Menu ###")

        if role == 'admin':
            print("1. Apply Leave for Employee")
            print("2. Approve/Reject Leave Requests")
            print("3. Back to Main Menu")
            admin_choice = input("Enter choice: ")

            if admin_choice == '1':
                emp_id = input("Enter Employee ID: ")
                apply_leave(conn, emp_id)

            elif admin_choice == '2':
                approve_leave(conn)

            elif admin_choice == '3':
                break

            else:
                print("Invalid choice.")

        else:
            print("Access denied.")
            break


def apply_leave(conn, emp_id):
    print("\n--- Leave Request ---")
    start_date = input("Start date (YYYY-MM-DD): ").strip()
    end_date = input("End date (YYYY-MM-DD): ").strip()
    reason = input("Reason for leave (short explanation): ").strip()

    cursor = conn.cursor()
    query = """
        INSERT INTO leaves (emp_id, start_date, end_date, reason, status)
        VALUES (%s, %s, %s, %s, 'Pending')
    """

    try:
        cursor.execute(query, (emp_id, start_date, end_date, reason))
        conn.commit()
        print("Leave request submitted — status: Pending. Your manager will review it shortly.")
    except mysql.connector.Error as err:
        print(f"Could not submit leave: {err}")
    finally:
        cursor.close()


def approve_leave(conn):
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT l.leave_id, e.emp_id, e.first_name, e.last_name,
               l.start_date, l.end_date, l.reason
        FROM leaves l
        JOIN employees e ON l.emp_id = e.emp_id
        WHERE l.status = 'Pending'
    """

    cursor.execute(query)
    pending = cursor.fetchall()

    if not pending:
        print("No pending leave requests.")
        cursor.close()
        return

    print("\n--- Pending Leave Requests ---")
    for leave in pending:
        print(f"ID {leave['leave_id']} | {leave['first_name']} {leave['last_name']}")
        print(f"   {leave['start_date']} ➝ {leave['end_date']} | {leave['reason']}\n")

    leave_id = input("Enter Leave ID to process (0 to cancel): ").strip()
    if leave_id == '0':
        cursor.close()
        return

    action = input("Approve or Reject? (A/R): ").upper().strip()

    if action == 'A':
        status = "Approved"
    elif action == 'R':
        status = "Rejected"
    else:
        print("Invalid choice.")
        cursor.close()
        return

    try:
        cursor.execute("UPDATE leaves SET status=%s WHERE leave_id=%s", (status, leave_id))
        conn.commit()
        print(f"✅ Leave {leave_id} marked as {status}.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()


# ---------------------------
# PAYROLL MANAGEMENT
# ---------------------------

def calculate_payroll(conn):
    print("\n### Payroll Calculator ###")

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT emp_id, first_name, last_name, salary FROM employees ORDER BY emp_id")
    employees = cursor.fetchall()

    if not employees:
        print("No employees found.")
        cursor.close()
        return

    print("\n--- Employee List ---")
    for emp in employees:
        print(f"{emp['emp_id']}. {emp['first_name']} {emp['last_name']}  | Salary: {emp['salary']}")

    emp_id = input("\nEnter Employee ID to calculate payroll: ").strip()

    cursor.execute("SELECT * FROM employees WHERE emp_id = %s", (emp_id,))
    emp = cursor.fetchone()

    if not emp:
        print("Employee not found.")
        cursor.close()
        return

    basic_salary = float(emp["salary"])

    # HRA fixed proportion
    hra = basic_salary * 0.24

    # Option B: If salary < 10000, remove both PF and Insurance
    if basic_salary < 10000:
        pf = 0.0
        insurance = 0.0
    else:
        pf = basic_salary * 0.12
        insurance = 1500.0

    gross_salary = basic_salary + hra
    deductions = pf + insurance
    net_salary = gross_salary - deductions

    # Safety: ensure net salary not negative
    if net_salary < 0:
        net_salary = 0.0

    print("\n--- Payroll Summary ---")
    print(f"Employee: {emp['first_name']} {emp['last_name']}")
    print(f"Basic salary: {basic_salary}")
    print(f"HRA (24%): {hra}")
    print(f"Provident Fund (12%): -{pf}")
    print(f"Insurance: -{insurance}")
    print(f"Net (take-home): {net_salary}")

    save = input("\nWould you like to save this payroll record? (Y/N): ").upper().strip()

    if save == "Y":
        query = """
            INSERT INTO payroll (emp_id, basic_salary, hra, pf, insurance, net_salary, generated_on)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (emp_id, basic_salary, hra, pf, insurance, net_salary, date.today()))
            conn.commit()
            print("Payroll record saved.")
        except mysql.connector.Error as err:
            print(f"Could not save payroll: {err}")

    cursor.close()


# ---------------------------
# PERFORMANCE MANAGEMENT
# ---------------------------

def performance_management_menu(conn):
    while True:
        print("\n### Performance Management ###")
        print("1. Add a performance review for an employee")
        print("2. See reviews for an employee")
        print("3. Return to previous menu")
        choice = input("Choose an action: ").strip()

        if choice == '1':
            record_performance_review(conn)
        elif choice == '2':
            view_reviews_for_employee(conn)
        elif choice == '3':
            break
        else:
            print("Invalid choice.")


def record_performance_review(conn):
    emp_id = input("Employee ID: ").strip()
    # verify employee exists
    c = conn.cursor()
    c.execute("SELECT emp_id FROM employees WHERE emp_id = %s", (emp_id,))
    if not c.fetchone():
        print("Employee not found.")
        c.close()
        return
    c.close()

    while True:
        rating_str = input("Rating (1-5): ").strip()
        try:
            rating = int(rating_str)
            if 1 <= rating <= 5:
                break
            else:
                print("Rating must be between 1 and 5.")
        except ValueError:
            print("Invalid rating. Enter an integer between 1 and 5.")

    comments = input("Comments: ").strip()
    today = date.today().strftime("%Y-%m-%d")

    cursor = conn.cursor()
    query = """INSERT INTO performance_reviews 
               (emp_id, review_date, rating, comments) 
               VALUES (%s, %s, %s, %s)"""

    try:
        cursor.execute(query, (emp_id, today, rating, comments))
        conn.commit()
        print("✅ Review recorded.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()


def view_reviews_for_employee(conn):
    emp_id = input("Employee ID to view reviews: ").strip()

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees WHERE emp_id = %s", (emp_id,))
    emp = cursor.fetchone()
    if not emp:
        print("Employee not found.")
        cursor.close()
        return

    print(f"\nReviews for {emp['first_name']} {emp['last_name']}:")

    cursor.execute("""
        SELECT review_date, rating, comments
        FROM performance_reviews
        WHERE emp_id = %s
        ORDER BY review_date DESC, review_id DESC
    """, (emp_id,))
    reviews = cursor.fetchall()

    if not reviews:
        print("Rating not added yet.")
    else:
        for r in reviews:
            print(f" - {r['review_date']}: Rating {r['rating']} | {r['comments']}")

    cursor.close()


# ---------------------------
# RECRUITMENT MANAGEMENT
# ---------------------------

def recruitment_management_menu(conn):
    while True:
        print("\n### Recruitment Management Menu ###")
        print("1. Add Job Opening")
        print("2. View All Job Openings")
        print("3. Update Job Opening")
        print("4. Back to Main Menu")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            add_job_opening(conn)
        elif choice == '2':
            view_job_openings(conn)
        elif choice == '3':
            update_job_opening(conn)
        elif choice == '4':
            break
        else:
            print("Invalid choice.")


def add_job_opening(conn):
    print("\n--- Add Job Opening ---")
    title = input("Job Title: ").strip()
    while True:
        salary_str = input("Salary Offered: ").strip()
        try:
            salary = float(salary_str)
            break
        except ValueError:
            print("Invalid salary. Enter a numeric value.")
    work_hours = input("Work Hours (e.g., 9 AM - 6 PM): ").strip()

    query = """
        INSERT INTO job_openings (title, salary_offered, work_hours, status)
        VALUES (%s, %s, %s, 'Open')
    """

    cursor = conn.cursor()
    try:
        cursor.execute(query, (title, salary, work_hours))
        conn.commit()
        print("✅ Job opening added successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()


def view_job_openings(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM job_openings ORDER BY job_id")
    jobs = cursor.fetchall()
    cursor.close()

    if not jobs:
        print("No job openings available.")
        return

    print("\n--- Job Openings ---")
    for job in jobs:
        print(f"ID: {job['job_id']} | {job['title']}")
        print(f"Salary: {job['salary_offered']} | Hours: {job['work_hours']}")
        print(f"Status: {job['status']}\n")


def update_job_opening(conn):
    job_id = input("Enter Job ID to update: ").strip()

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM job_openings WHERE job_id=%s", (job_id,))
    job = cursor.fetchone()

    if not job:
        print("Job opening not found.")
        cursor.close()
        return

    print("\n--- Current Job Details ---")
    print(f"Title: {job['title']}")
    print(f"Salary: {job['salary_offered']}")
    print(f"Work Hours: {job['work_hours']}")
    print(f"Status: {job['status']}")

    new_salary = input("New Salary (leave blank = no change): ").strip()
    new_hours = input("New Work Hours (leave blank = no change): ").strip()
    new_status = input("New Status (Open/Closed) (leave blank = no change): ").strip()

    updates = []
    values = []

    if new_salary:
        try:
            values.append(float(new_salary))
            updates.append("salary_offered = %s")
        except ValueError:
            print("Invalid salary entered. Salary not changed.")
    if new_hours:
        updates.append("work_hours = %s")
        values.append(new_hours)
    if new_status:
        updates.append("status = %s")
        values.append(new_status)

    if not updates:
        print("No changes entered.")
        cursor.close()
        return

    values.append(job_id)
    query = "UPDATE job_openings SET " + ", ".join(updates) + " WHERE job_id=%s"

    try:
        cursor.execute(query, tuple(values))
        conn.commit()
        print("✅ Job updated successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()


# ---------------------------
# MAIN MENU (example)
# ---------------------------

def main_menu(conn):
    # Example role; adjust role handling/integration as needed
    role = 'admin'  # Or logic to determine role
    while True:
        print("\n=== Main Menu ===")
        print("1. Employee Info")
        print("2. Leave Management")
        print("3. Payroll")
        print("4. Performance Management")
        print("5. Recruitment")
        print("6. Exit")
        choice = input("Enter choice: ").strip()

        if choice == '1':
            employee_info_menu(conn)
        elif choice == '2':
            leave_management_menu(conn, role)
        elif choice == '3':
            calculate_payroll(conn)
        elif choice == '4':
            performance_management_menu(conn)
        elif choice == '5':
            recruitment_management_menu(conn)
        elif choice == '6':
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")


# ---------------------------
# Run (example connection)
# ---------------------------

if __name__ == "__main__":
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="your_user",
            password="your_password",
            database="your_database"
        )
        main_menu(conn)
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
    finally:
        try:
            if conn.is_connected():
                conn.close()
        except Exception:
            pass