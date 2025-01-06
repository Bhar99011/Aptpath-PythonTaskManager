import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime
import pandas as pd

# Database Setup
def init_db():
    with sqlite3.connect('task_manager.db') as conn:
        c = conn.cursor()
        # User Table
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password BLOB)''')
        # Task Table
        c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_name TEXT NOT NULL, 
                      description TEXT, priority TEXT, deadline DATE, status TEXT, project TEXT, user_id INTEGER)''')
        conn.commit()

# Hash Password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Verify Password
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# User Registration
def register_user(username, password):
    with sqlite3.connect('task_manager.db') as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                      (username, hash_password(password)))
            conn.commit()
        except sqlite3.IntegrityError:
            return False
    return True

# User Login
def login_user(username, password):
    with sqlite3.connect('task_manager.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
    if user and verify_password(password, user[2]):
        return user[0]  # Return user_id
    return None

# Admin Login
def login_admin(password):
    return password == "admin123"  # Replace with your actual admin password

# Add Task
def add_task(task_name, description, priority, deadline, status, project, user_id):
    with sqlite3.connect('task_manager.db') as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO tasks (task_name, description, priority, deadline, status, project, user_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                  (task_name, description, priority, deadline, status, project, user_id))
        conn.commit()

# Fetch Tasks
def get_tasks(user_id):
    with sqlite3.connect('task_manager.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
        return c.fetchall()

# Delete Task
def delete_task(task_id):
    with sqlite3.connect('task_manager.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

# Update Task
def update_task(task_id, task_name, description, priority, deadline, status, project):
    with sqlite3.connect('task_manager.db') as conn:
        c = conn.cursor()
        c.execute('''UPDATE tasks 
                     SET task_name = ?, description = ?, priority = ?, deadline = ?, status = ?, project = ? 
                     WHERE id = ?''',
                  (task_name, description, priority, deadline, status, project, task_id))
        conn.commit()

# Fetch All Users
def get_all_users():
    with sqlite3.connect('task_manager.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, username FROM users")
        return c.fetchall()

# Delete User
def delete_user(user_id):
    with sqlite3.connect('task_manager.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

# Update User
def update_user(user_id, username, password):
    with sqlite3.connect('task_manager.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET username = ?, password = ? WHERE id = ?", 
                  (username, hash_password(password), user_id))
        conn.commit()

# Streamlit App
def main():
    st.title("Task Manager Application")
    menu = ["Login", "Register", "Admin"]
    choice = st.sidebar.selectbox("Menu", menu)

    init_db()  # Initialize database

    if choice == "Register":
        st.subheader("Create a New Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        confirm_password = st.text_input("Confirm Password", type='password')
        if st.button("Register"):
            if password == confirm_password:
                if register_user(username, password):
                    st.success("Account created successfully. Please login.")
                else:
                    st.error("Username already exists.")
            else:
                st.error("Passwords do not match. Please try again.")

    elif choice == "Login":
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            user_id = login_user(username, password)
            if user_id:
                st.session_state["user_id"] = user_id
                st.success("Login successful.")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")

    elif choice == "Admin":
        st.subheader("Admin - Manage Users and Tasks")
        admin_password = st.text_input("Admin Password", type="password")
        
        if admin_password:
            if login_admin(admin_password):
                st.write("Admin Panel")

                # List Users
                users = sorted(get_all_users(), key=lambda x: x[0])
                if users:
                    user_df = pd.DataFrame(users, columns=["User ID", "Username"])
                    st.subheader("Users List")
                    st.dataframe(user_df)

                    # View Tasks for a Selected User
                    selected_user_id = st.selectbox("Select User to View Tasks", options=[None] + [user[0] for user in users], format_func=lambda x: f"User {x}" if x else "Select")
                    if selected_user_id:
                        st.subheader(f"Tasks for User ID: {selected_user_id}")
                        user_tasks = get_tasks(selected_user_id)
                        if user_tasks:
                            task_df = pd.DataFrame(user_tasks, columns=["Task ID", "Task Name", "Description", "Priority", "Deadline", "Status", "Project", "User ID"])
                            st.dataframe(task_df)
                        else:
                            st.info("No tasks found for this user.")

                    # Delete User
                    user_to_delete = st.selectbox("Select User to Delete", options=[None] + [user[0] for user in users], format_func=lambda x: f"User {x}" if x else "Select")
                    if user_to_delete and st.button("Delete User"):
                        delete_user(user_to_delete)
                        st.warning(f"User {user_to_delete} deleted.")
                        st.experimental_rerun()

                    # Edit User
                    user_to_edit = st.selectbox("Select User to Edit", options=[None] + [user[0] for user in users], format_func=lambda x: f"User {x}" if x else "Select")
                    if user_to_edit:
                        new_username = st.text_input("New Username")
                        new_password = st.text_input("New Password", type="password")
                        if st.button("Update User"):
                            if new_username and new_password:
                                update_user(user_to_edit, new_username, new_password)
                                st.success(f"User {user_to_edit} updated.")
                                st.experimental_rerun()
                else:
                    st.info("No users available.")
            else:
                st.error("Invalid admin password.")
        else:
            st.info("Enter admin password to access the admin panel.")

    if "user_id" in st.session_state:
        user_id = st.session_state["user_id"]
        st.subheader("Manage Your Tasks")

        # Add Task Form
        with st.form("task_form"):
            st.write("Add a New Task")

            task_name = st.text_input("Task Name")
            description = st.text_area("Description")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            deadline = st.date_input("Deadline")
            status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
            project = st.text_input("Project")

            submitted = st.form_submit_button("Add Task")
            if submitted:
                add_task(task_name, description, priority, deadline, status, project, user_id)
                st.success("Task added successfully.")
                st.experimental_rerun()

        # Display Tasks
        tasks = get_tasks(user_id)
        if tasks:
            task_df = pd.DataFrame(tasks, columns=["Task ID", "Task Name", "Description", "Priority", "Deadline", "Status", "Project", "User ID"])
            st.subheader("Your Tasks")
            st.dataframe(task_df)

            # Delete Task Option
            task_to_delete = st.selectbox("Select Task to Delete", options=[None] + [task[0] for task in tasks], format_func=lambda x: f"Task {x}" if x else "Select")
            if task_to_delete and st.button("Delete Task"):
                delete_task(task_to_delete)
                st.warning(f"Task {task_to_delete} deleted.")
                st.experimental_rerun()

            # Edit Task Option
            task_to_edit = st.selectbox("Select Task to Edit", options=[None] + [task[0] for task in tasks], format_func=lambda x: f"Task {x}" if x else "Select")
            if task_to_edit:
                task = next(task for task in tasks if task[0] == task_to_edit)
                new_task_name = st.text_input("New Task Name", value=task[1])
                new_description = st.text_area("New Description", value=task[2])
                new_priority = st.selectbox("New Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(task[3]))
                new_deadline = st.date_input("New Deadline", value=datetime.strptime(task[4], '%Y-%m-%d').date())
                new_status = st.selectbox("New Status", ["Pending", "In Progress", "Completed"], index=["Pending", "In Progress", "Completed"].index(task[5]))
                new_project = st.text_input("New Project", value=task[6])

                if st.button("Update Task"):
                    update_task(task_to_edit, new_task_name, new_description, new_priority, new_deadline, new_status, new_project)
                    st.success(f"Task {task_to_edit} updated.")
                    st.experimental_rerun()
        else:
            st.info("No tasks available.")

if __name__ == "__main__":
    # Your code here

    main()
