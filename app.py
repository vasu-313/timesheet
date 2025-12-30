from flask import Flask, render_template, request, redirect,session, url_for,abort,flash
import pyodbc
import bcrypt
from functools import wraps

app = Flask(__name__)



app.secret_key = "your_secret_key_here"   # Needed for session management

conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=VASU\SQLEXPRESS;"
    "Database=vasudb;"
    "Trusted_Connection=yes;"
)

def get_connection():
    return pyodbc.connect(conn_str)



# CREATE (Insert new record with hashed password)

@app.route("/", methods=["GET", "POST"])
def create_admin():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Hash the password before storing
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        # print(hashed_pw)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO timesheet_users (Name, Email, Password) VALUES (?, ?, ?)",
            (name, email, hashed_pw.decode("utf-8"))
        )
        conn.commit()
        conn.close()

        return redirect('login')
    else:
        return render_template("auth/register.html")






# login 
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ID, Name, Email, Password, Role FROM timesheet_users WHERE Email = ?",
            (email,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            flash("User not found", "error")   # 🔔 added
            return redirect(url_for("login"))

        user_id = row[0]
        name = row[1]
        stored_hash = row[3]
        role = row[4]

        # PASSWORD CHECK
        try:
            is_valid = bcrypt.checkpw(
                password.encode("utf-8"),
                stored_hash.encode("utf-8")
            )
        except ValueError:
            # TEMP fallback (plain-text admin password)
            is_valid = password == stored_hash

        if not is_valid:
            flash("Invalid password", "error")   # 🔔 added
            return redirect(url_for("login"))

        # LOGIN SUCCESS
        session["user_id"] = user_id
        session["user_name"] = name
        session["role"] = role


        if role.lower() == "admin":
            return redirect(url_for("admin"))
        else:
            return redirect(url_for("home"))

    return render_template("auth/login.html")




# get all tasks for particular user function
def timesheet_data(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT TaskId, UserId, TaskDate, Projects, TaskType, Task, Activity, WorkTime, TaskDescription
        FROM timesheet_tasks
        WHERE UserId = ?
        ORDER BY  TaskId DESC
    """, (user_id,))

    rows = cursor.fetchall()
    # print(rows)
    columns = [c[0] for c in cursor.description]
    conn.close()
    return(rows,columns)

# insert task function 
def insert_timesheet_task(user_id, date, project, task_type, task, activity, time, description):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO timesheet_tasks
        (UserId, TaskDate, Projects, TaskType, Task, Activity, WorkTime, TaskDescription)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, date, project, task_type, task, activity, time, description))

    conn.commit()
    conn.close()


def get_logged_in_user():
    user_id = session.get("user_id")
    user_name = session.get("user_name")

    if not user_id:
        return None, None

    return user_id, user_name

# this is for user can only access home page 
def home_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "role" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "user":
            return abort(403)

        return func(*args, **kwargs)
    return wrapper

@app.route("/home", methods=["GET", "POST"])
@home_required
def home():
    user_id, name = get_logged_in_user()
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        insert_timesheet_task(
            user_id=user_id,
            date=request.form.get("date"),
            project=request.form.get("project"),
            task_type=request.form.get("TaskType"),
            task=request.form.get("task"),
            activity=request.form.get("activity"),
            time=request.form.get("time"),
            description=request.form.get("description")
        )

    rows, columns = timesheet_data(user_id)
    data = [dict(zip(columns, row)) for row in rows]

    return render_template("userPages/home.html", active_page="home", data=data, name=name)

# delete task function 
def delete_task(task_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM timesheet_tasks
        WHERE TaskId = ? AND UserId = ?
    """, (task_id, user_id))

    conn.commit()
    conn.close()


@app.route("/delete-task/<int:task_id>", methods=["POST"])
def delete_task_route(task_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    delete_task(task_id, user_id)
    return redirect(url_for("home"))





# update 

def update_task(task_id, user_id, form_data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE timesheet_tasks
        SET
            TaskDate = ?,
            Projects = ?,
            TaskType = ?,
            Task = ?,
            Activity = ?,
            WorkTime = ?,
            TaskDescription = ?
        WHERE TaskId = ? AND UserId = ?
    """, (
        form_data["date"],
        form_data["project"],
        form_data["TaskType"],
        form_data["task"],
        form_data["activity"],
        form_data["time"],
        form_data["description"],
        task_id,
        user_id
    ))

    conn.commit()
    cursor.close()
    conn.close()



@app.route("/update-task/<int:task_id>", methods=["POST"])
def update_task_route(task_id):
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    update_task(task_id, user_id, request.form)

    return redirect(url_for("home"))


@app.route("/mysheets")
def mysheets():
    user_id, name = get_logged_in_user()
    return render_template("/userPages/mysheets.html", active_page="mysheets" , name=name )


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/login')

# this is for admin can only access admin page 
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "role" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            return abort(403)

        return func(*args, **kwargs)
    return wrapper


# admin page 
@app.route("/admin")
@admin_required
def admin():
    name = session.get("user_name")
    return render_template("adminPages/admin-home.html", name=name)




if __name__ == '__main__':
    app.run(debug=True, port=5000)






