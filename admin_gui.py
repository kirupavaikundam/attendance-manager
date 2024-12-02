import sqlite3
import tkinter as tk
from tkinter import messagebox

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('attendance.db')
    return conn

# Function to add a new employee
def add_employee():
    firstname = entry_firstname.get()
    lastname = entry_lastname.get()
    employee_id = entry_employee_id.get()
    email = entry_email.get()
    password = entry_password.get()
    employee_type = employee_type_var.get()  # Get the selected employee type

    if not firstname or not lastname or not email or not employee_id or not password or not employee_type:
        messagebox.showerror("Error", "All fields are required")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if email or employee_id already exists
    cursor.execute('SELECT * FROM User WHERE email = ? OR employee_id = ?', (email, employee_id))
    existing_user = cursor.fetchone()

    if existing_user:
        messagebox.showerror("Error", "Email or Employee ID already exists. Choose a different one.")
    else:
        # Insert the new employee into the database
        cursor.execute('INSERT INTO User (firstname, lastname, email, employee_id, password, employee_type) VALUES (?, ?, ?, ?, ?, ?)', 
                       (firstname, lastname, email, employee_id, password, employee_type))
        conn.commit()
        messagebox.showinfo("Success", f"Employee {firstname} {lastname} added successfully!")
    
    conn.close()

# Initialize the Tkinter app
app = tk.Tk()
app.title("Employee Management - Admin Panel")

# Define font style and size
font_style = ("Arial", 14)
entry_font_style = ("Arial", 14)

# First Name label and entry field
label_firstname = tk.Label(app, text="First Name", font=font_style)
label_firstname.pack(pady=5)
entry_firstname = tk.Entry(app, font=entry_font_style, width=30)
entry_firstname.pack(pady=5)

# Last Name label and entry field
label_lastname = tk.Label(app, text="Last Name", font=font_style)
label_lastname.pack(pady=5)
entry_lastname = tk.Entry(app, font=entry_font_style, width=30)
entry_lastname.pack(pady=5)

# Employee ID label and entry field
label_employee_id = tk.Label(app, text="Employee ID", font=font_style)
label_employee_id.pack(pady=5)
entry_employee_id = tk.Entry(app, font=entry_font_style, width=30)
entry_employee_id.pack(pady=5)

# Email label and entry field
label_email = tk.Label(app, text="Email", font=font_style)
label_email.pack(pady=5)
entry_email = tk.Entry(app, font=entry_font_style, width=30)
entry_email.pack(pady=5)

# Password label and entry field
label_password = tk.Label(app, text="Password", font=font_style)
label_password.pack(pady=5)
entry_password = tk.Entry(app, show="*", font=entry_font_style, width=30)
entry_password.pack(pady=5)

# Employee Type (Onsite/Offsite)
employee_type_var = tk.StringVar(value="onsite")
label_employee_type = tk.Label(app, text="Employee Type", font=font_style)
label_employee_type.pack(pady=5)
onsite_radio = tk.Radiobutton(app, text="Onsite", variable=employee_type_var, value="onsite", font=entry_font_style)
onsite_radio.pack(pady=5)
offsite_radio = tk.Radiobutton(app, text="Offsite", variable=employee_type_var, value="offsite", font=entry_font_style)
offsite_radio.pack(pady=5)

# Submit button
submit_button = tk.Button(app, text="Add Employee", font=font_style, command=add_employee)
submit_button.pack(pady=20)

# Increase window size
app.geometry("500x600")

# Run the app
app.mainloop()


# Initialize the Tkinter app
app = tk.Tk()
app.title("Employee Management - Admin Panel")

# Define font style and size
font_style = ("Arial", 14)
entry_font_style = ("Arial", 14)

# First Name label and entry field
label_firstname = tk.Label(app, text="First Name", font=font_style)
label_firstname.pack(pady=5)
entry_firstname = tk.Entry(app, font=entry_font_style, width=30)
entry_firstname.pack(pady=5)

# Last Name label and entry field
label_lastname = tk.Label(app, text="Last Name", font=font_style)
label_lastname.pack(pady=5)
entry_lastname = tk.Entry(app, font=entry_font_style, width=30)
entry_lastname.pack(pady=5)

# Employee ID label and entry field
label_employee_id = tk.Label(app, text="Employee ID", font=font_style)
label_employee_id.pack(pady=5)
entry_employee_id = tk.Entry(app, font=entry_font_style, width=30)
entry_employee_id.pack(pady=5)

# Email label and entry field
label_email = tk.Label(app, text="Email", font=font_style)
label_email.pack(pady=5)
entry_email = tk.Entry(app, font=entry_font_style, width=30)
entry_email.pack(pady=5)

# Password label and entry field
label_password = tk.Label(app, text="Password", font=font_style)
label_password.pack(pady=5)
entry_password = tk.Entry(app, show="*", font=entry_font_style, width=30)
entry_password.pack(pady=5)

# Submit button
submit_button = tk.Button(app, text="Add Employee", font=font_style, command=add_employee)
submit_button.pack(pady=20)

# Increase window size
app.geometry("500x500")

# Run the app
app.mainloop()
