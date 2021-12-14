from os import urandom 
from flask import Flask, render_template, request, session, redirect
import sqlite3, os.path

app = Flask(__name__)
app.secret_key = urandom(32)

def islogged():
    return 'username' in session.keys()

@app.route("/", methods=['GET', 'POST'])
def home():
    db = sqlite3.connect("users.db")
    c = db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, UNIQUE(username))")
    db.commit()
    db.close()
    return render_template('home.html')
    
@app.route("/login",  methods=['GET', 'POST'])
def login():
    return render_template('login.html')

# authication of login
@app.route("/auth", methods=['GET', 'POST'])
def auth():
    if (request.method == 'POST'):
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT username AND password FROM users WHERE username=? AND password=?", (request.form['username'], request.form['password']))
        user = c.fetchone()
        if (user != None):
            session['username'] = request.form['username']
            session['password'] = request.form['password']
        db.close()
    return redirect('/')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if (request.method == 'POST'):
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT username AND password FROM users WHERE username=? AND password=?", (request.form['username'], request.form['password']))
        if (c.fetchone() == None):
            c.execute("INSERT INTO users(username, password) VALUES(?, ?)", (request.form['username'], request.form['password']))
            table = "CREATE TABLE {name}(Type TEXT, Object TEXT)".format(name=request.form['username'])
            c.execute(table)
        db.commit()
        db.close()
        return redirect("/")
    else:
        return render_template("register.html")
        
    
@app.route("/trivia", methods=['POST', 'GET'])
def trivia():
    return redirect('/')

if __name__ == "__main__":
    app.debug = True
    app.run()
    
