from flask import Flask, flash, redirect, url_for, render_template, request

app = Flask(__name__)
app.secret_key = "secret123"   # REQUIRED for flash

DUMMY_USERNAME = "admin"
DUMMY_PASSWORD = "1234"

@app.route("/")
def example():
    return "examples learning "

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username != DUMMY_USERNAME:
            flash("Username is wrong", "error")
            return redirect(url_for("login"))

        if password != DUMMY_PASSWORD:
            flash("Password is wrong", "error")
            return redirect(url_for("login"))

        flash("Login successful", "success")
        return redirect(url_for("dashboard"))

    return render_template("examples/login.html")


@app.route("/dashboard")
def dashboard():
    return render_template("examples/dashboard.html")



# example for date update 

@app.route("/example")
def example_for_date():
    return render_template("examples/date-example.html")

if __name__ == "__main__":
    app.run(debug=True, port=3000)


