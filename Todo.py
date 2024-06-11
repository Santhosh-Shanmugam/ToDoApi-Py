import streamlit as st
import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="santhosh",
    host="localhost",
    port="5432"
)

with conn.cursor() as cursor:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todo_list (
            id SERIAL PRIMARY KEY,
            task TEXT NOT NULL,
            status BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            time_spent INTERVAL DEFAULT '00:00:00'
        );
    ''')
    conn.commit()

# Initialize session state
if 'start_time' not in st.session_state:
    st.session_state.start_time = None

if 'current_task_id' not in st.session_state:
    st.session_state.current_task_id = None

if 'time_updating' not in st.session_state:
    st.session_state.time_updating = False

# Define functions
def add_task(task):
    if task:
        with conn.cursor() as cursor:
            cursor.execute('INSERT INTO todo_list (task) VALUES (%s);', (task,))
            conn.commit()
        st.success("Task added successfully!")
    else:
        st.warning("Please enter a task.")

def delete_task(task_id):
    with conn.cursor() as cursor:
        cursor.execute('DELETE FROM todo_list WHERE id = %s;', (task_id,))
        conn.commit()
    st.success("Task deleted successfully!")

def mark_done(task_id):
    with conn.cursor() as cursor:
        cursor.execute('UPDATE todo_list SET status = TRUE, updated_at = %s WHERE id = %s;', (datetime.now(), task_id))
        conn.commit()
    st.success("Task marked as done!")

def edit_task(task_id, new_task_text):
    if new_task_text:
        with conn.cursor() as cursor:
            cursor.execute('UPDATE todo_list SET task = %s, updated_at = %s WHERE id = %s;', (new_task_text, datetime.now(), task_id))
            conn.commit()
        st.success("Task edited successfully!")
    else:
        st.warning("Please enter a new task.")

def get_tasks():
    with conn.cursor() as cursor:
        cursor.execute('SELECT id, task, status, time_spent FROM todo_list ORDER BY id;')
        tasks = cursor.fetchall()
    return tasks

def start_tracking_time(task_id):
    st.session_state.start_time = datetime.now()
    st.session_state.current_task_id = task_id
    st.session_state.time_updating = True

def stop_tracking_time():
    if st.session_state.start_time and st.session_state.current_task_id:
        stop_time = datetime.now()
        time_spent = stop_time - st.session_state.start_time
        with conn.cursor() as cursor:
            cursor.execute('UPDATE todo_list SET time_spent = time_spent + %s WHERE id = %s;', (time_spent, st.session_state.current_task_id))
            conn.commit()
        st.session_state.time_updating = False
        st.session_state.start_time = None
        st.session_state.current_task_id = None

# UI layout
st.title("To-Do List")

# Add task
task_input = st.text_input("Enter a new task")
if st.button("Add Task"):
    add_task(task_input)

# Display tasks
tasks = get_tasks()
if tasks:
    for index, (task_id, task, status, time_spent) in enumerate(tasks):
        task_status = "Done" if status else "Pending"
        time_spent_str = str(time_spent) if time_spent else "00:00:00"
        st.write(f"{index + 1}. {task} - {task_status} - Time Spent: {time_spent_str}")

        # Edit task
        edit_input = st.text_input(f"Edit task {index + 1}", key=f"edit_{task_id}")
        if st.button(f"Edit task ", key=f"save_{task_id}"):
            edit_task(task_id, edit_input)

        # Mark as done
        if st.button(f"Mark as Done", key=f"done_{task_id}"):
            mark_done(task_id)

        # Delete task
        if st.button(f"Delete ", key=f"delete_{task_id}"):
            delete_task(task_id)

        # Start time tracking
        if st.button(f"Start Time ", key=f"start_{task_id}"):
            start_tracking_time(task_id)

        # Stop time tracking
        if st.button(f"Stop Time ", key=f"stop_{task_id}"):
            stop_tracking_time()

# Running time display
if st.session_state.time_updating:
    elapsed_time = datetime.now() - st.session_state.start_time
    hours, remainder = divmod(elapsed_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
    st.write(f"Running Time: {time_str}")

    # Auto-refresh every second to update the running time
    st.experimental_rerun()

# Close the database connection when the app is closed
def on_closing():
    conn.close()

on_closing()