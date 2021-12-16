from os import urandom
from flask import Flask, render_template, request, session, redirect
import sqlite3, os.path
import json
import urllib

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

#login takes the user object and sets cookies
@app.route("/login",  methods=['GET', 'POST'])
def login():
    return render_template('login.html')

# authentication of login; verifies login information
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
        c.execute("SELECT username FROM users WHERE username=? ", (username,)) #SYNTAX: ADD , after to refer to entire username, otherwise SQL will count each char as a binding... -_-
        # username inputted by user is not found in database
        if c.fetchone() == None:
            return render_template("login.html", error="Wrong username, double check or register")
        # username is found
        else:
            c.execute("SELECT password FROM users WHERE username=? ", (username,))
            # password associated with username in database does not match password inputted

            #c.fetchone() returns a tuple with the password
            #first convert the tuple into the password string only, then compare
            if ( ''.join(c.fetchone()) ) != password:
                return render_template("login.html", error="Wrong password")
            # password is correct
            else:
                session['username'] = username
                session['password'] = password
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
        c.execute("SELECT username AND password FROM users WHERE username=? AND password=?", (username, password))

        if (c.fetchone() == None): #user doesn't exist; continue with registration
            c.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username, password))
            table = "CREATE TABLE {name}(Type TEXT, Object TEXT)".format(name=username)
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
    #http = urllib.request.urlopen("https://api.trivia.willfry.co.uk/questions?limit=20") #HTTP Response object (containing the JSON info); contains 20 questions
    http = urllib.request.urlopen("https://api.trivia.willfry.co.uk/questions?limit=1") #HTTP Response object (containing the JSON info); contains 1 question
    questions = json.load(http) #questions is a list of dictionaries; each dictionary entry is a question + answers + info
    print(questions)

    for value in questions: #for every dictionary in the questions list
        question = value.get('question') #store the value of the key 'question'; is a string
        correct_answer = value.get('correctAnswer') #is a string
        incorrect_answers = value.get('incorrectAnswers') #is a list of strings

        print(question)
    return render_template("trivia.html", question=question, correct=correct_answer, incorrect=incorrect_answers)

'''
@app.route("/")
def rest_demo():
    http = request.urlopen("https://api.nasa.gov/planetary/apod?api_key=qsb4nvuGri4tJe3q6REknzJbP5xO1OZnJBDfLKMG") #HTTP Response object (containing the JSON info)
    print(http)
    j = json.load(http) #j is a dictionary (key-value pairs) of the JSON info
    print(j)
    link = j['url'] #get the value of the 'url' key
    print(link)
    explanation = j['explanation'] #get the value of the 'explanation' key
    print(explanation)
    #render an html template with the picture (using url) and explanation
    return render_template("main.html", pic = link, description = explanation)
'''

if __name__ == "__main__":
    app.debug = True
    app.run()
