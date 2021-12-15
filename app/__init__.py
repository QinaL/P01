from os import urandom
from flask import Flask, render_template, request, session, redirect
import sqlite3, os.path
import urllib, json

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

# authentication of login
@app.route("/auth", methods=['GET', 'POST'])
def auth():
    if (request.method == 'POST'):

        username = request.form.get("username")
        password = request.form.get("password")

        #error handling for empty username
        if username == '':
            return render_template("login.html", error="Empty username, who are you?")

        db = sqlite3.connect('users.db')
        c = db.cursor()

        c.execute("SELECT username FROM users WHERE username=? ", (username,))
        # username inputted by user is not found in database
        if c.fetchone() == None:
            return render_template("login.html", error="Wrong username, spell correctly or register")
        # username is found
        else:
            c.execute("SELECT password FROM users WHERE username=? ", (username,))
            # password associated with username in database does not match password inputted
            passin = c.fetchone()[0];
            print(passin)
            if passin != password:
                return render_template("login.html", error="Wrong password")
            # password is correct
            else:
                session['username'] = request.form['username']
                session['password'] = request.form['password']
        db.close()
        return redirect('/')
    #get method
    else:
        return redirect('/login')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if (request.method == 'POST'):
        username = request.form.get("username")
        password = request.form.get("password")
        reenterpasswd = request.form.get("reenterpasswd")

        #error handling
        if username == '':
            return render_template("register.html", error="Empty username, who are you?")
        elif password == '':
            return render_template("register.html", error="Empty password, you'll get hacked y'know :)")
        elif password != reenterpasswd:
            return render_template("register.html", error="Passwords don't match")

        #look in users.db and see if user with username and password combination exists
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT username AND password FROM users WHERE username=? AND password=?", (request.form['username'], request.form['password']))

        if (c.fetchone() == None): #user doesn't exist; continue with registration
            c.execute("INSERT INTO users(username, password) VALUES(?, ?)", (request.form['username'], request.form['password']))
            table = "CREATE TABLE {name}(Type TEXT, Object TEXT)".format(name=request.form['username'])
            c.execute(table)
        else: #error: username already taken
            return render_template("register.html", error="Username taken already")
        db.commit()
        db.close()
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/trivia", methods=['POST', 'GET'])
def trivia():
    #just start
    if (request.method == 'GET'):
        question = urllib.request.urlopen("https://api.trivia.willfry.co.uk/questions?limit=5")
        text = json.load(question)
        question = text[0]['question']
        id = text[0]['id']
        session['correctAnswer'] = text[0]['correctAnswer']
        wrong = [session['correctAnswer']]
        for x in text[0]['incorrectAnswers']:
            wrong.append(x)
        return render_template("trivia.html", question, id, wrong)
    else:
        if request.form['answer'] == session['correctAnswer']:
            return redirect('/trivia')
        else:
            return redirect('/')

if __name__ == "__main__":
    app.debug = True
    app.run()
    #test
