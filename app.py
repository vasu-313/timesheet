from flask import Flask, render_template, request, redirect,session, url_for
import pyodbc
import bcrypt

app = Flask(__name__)

# @app.route('/')
# def home():
#     return render_template('register.html')

# @app.route('/login')
# def login():
#     return render_template('login.html')

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
        print(hashed_pw)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (NAME, EMAIL, PASSWORD_HASH) VALUES (?, ?, ?)",
            (name, email, hashed_pw.decode("utf-8"))
        )
        conn.commit()
        conn.close()

        return redirect('/login')
    else:
        return render_template("register.html")

@app.route("/home/<name>")
def home(name):
    return render_template("home.html", name=name)

# LOGIN (Authentication)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, NAME, EMAIL, PASSWORD_HASH FROM users WHERE Email = ?", (email,))
        row = cursor.fetchone()
        conn.close()

        if row:
            stored_hash = row[3]  
            if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                session["admin_id"] = row[0]
                session["admin_name"] = row[1]
                return redirect(url_for("home", name=row[1]))
            else:
                return "Invalid password", 401
        else:
            return "Admin not found", 404
    else:
        return render_template("login.html")
    

@app.route("/mysheets") 
def mysheets():
    return render_template("mysheets.html")   

@app.route("/form")
def form():
    return render_template("add-task.html")

if __name__ == '__main__':
    app.run(debug=True, port=5000)