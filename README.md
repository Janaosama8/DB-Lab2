 DB Lab 2 

 1. Team Members
Jana Ossama       2304044     Flask backend, database connection, and  documentation
Takwa Abdelrahman 2304052      testing and Frontend design and validation   


 2. Technology Stack

- Back End: Python and Flask
- Front End: HTML and CSS
- Database: MySQL
- Database Connection: PyMySQL
- Password Security: bcrypt
- Environment Configuration: python-dotenv
- Development Tools: Visual Studio Code and DBeaver

 3. Setup and Run Instructions
 
  Step 1: Install the Required Software
Install the following:
- Python
- MySQL Server
- Visual Studio Code 
- DBeaver

 Step 2: Open the Project
Open the DB-Lab2 project folder in Visual Studio Code and open a terminal in that folder.
 
 Step 3: Create and Activate a Virtual Environment

Run:
python -m venv venv

Activate it on Windows:
venv\Scripts\activate

 Step 4: Install Python Packages

Run:
pip install Flask PyMySQL bcrypt python-dotenv

 Step 5: Create the Database
1. Start the MySQL server.
2. Open DBeaver and connect to MySQL.
3. Open schema.sql.
4. Execute the SQL script to create the registration database .

 Step 6: Configure Environment Variables
- Copy env.example to env in the project root.because the example file contains the required environment variables, while env stores the actual configuration values used by the application, such as the MySQL username, password, database name, and secret key. This allows each user to configure the project for their own machine without exposing sensitive information on GitHub.
- Update the MySQL username, password, host, port, database name, and secret key as required by the application.
- Do not commit the env file because it may contain secrets.

 Step 7: Start the Flask Server

Run:
python lab.py

 Step 8: Open and Test the Website

After running the Flask application, open the local address printed in the terminal, usually:
http://127.0.0.1:5000
The website provides the following features:
1. Register: Create a new account by entering the required information.
2. Login: Log in using the registered email and password.
3. To-Do List: After logging in, add new tasks, mark tasks as completed, and delete tasks.
To test the application, register a new account, log in, and try the To-Do List features. Each user should only be able to manage their own tasks.

 4. Implemented Features 

- R1 — Registration: Users can create an account with the required information.
- R2 — Login and Logout: Users can log in and log out.
- R3 — Private To-Do List: Each user can access their own tasks.
- R4 — Add To-Do: Users can add new tasks.
- R5 — Edit To-Do: Users can edit task titles.
- R6 — Mark as Done: Users can toggle a task's completion status.
- R7 — Delete To-Do: Users can delete tasks with confirmation.
- R8 — Validation: The application validates user input and displays error messages.
- R9 — Security: Passwords are hashed, SQL queries use parameters, and task operations are restricted to the task owner.
- R10 — User Interface: The application provides a consistent interface and feedback to users.

Bonus Features
 - counting how many to-dos are open: The website displays the number of unfinished tasks for the logged-in user. The count updates when tasks are added, completed, or deleted
 - Filter Tasks (all ;open ;done )

6. Security Questions

(a) Why do UPDATE and DELETE contain AND user_id = ?, and what changes if it is removed?
It makes sure that users can edit or delete only their own tasks. Without it, they might change or delete other users' tasks.
(b) What happens if a to-do is inserted for a nonexistent user_id, and which constraint prevents it?
The insert will fail because the user does not exist. The foreign key constraint prevents this.
(c) Why store a hash instead of the password?
A hash keeps the original password hidden in the database. We use bcrypt to hash passwords and check them during login.
(d) The name column is NOT NULL. Why is an additional check needed for an empty name?
NOT NULL prevents a NULL value, but it allows an empty string or spaces. So, we check that the name is not empty before saving it.