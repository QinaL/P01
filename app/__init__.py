from os import urandom
from flask import Flask, render_template, request, session, redirect
import sqlite3, os.path
import json
import urllib
import random

app = Flask(__name__)
app.secret_key = urandom(32)

def islogged():
    return 'username' in session.keys()

@app.route("/", methods=['GET', 'POST'])
def home():
    print(session)
    return render_template('home.html')

@app.route("/logout",  methods=['GET', 'POST'])
def logout():
    # try except is for when user is not logged in and does /logout anyways and a KeyError occurs
    try:
        session.pop('username')
        session.pop('password')
    except KeyError:
        return redirect("/")
    return redirect("/")

#login takes the user object and sets cookies
@app.route("/login",  methods=['GET', 'POST'])
def login():
    # stops a loggedin user when they try to log in
    if islogged():
        return render_template('loggedlock.html')
    #create users table so user can login
    db = sqlite3.connect("users.db")
    c = db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, UNIQUE(username))")
    db.commit()
    db.close()
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
        #in case users goes straight to /register w/o running /login code
        c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, UNIQUE(username))")
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
                print(session['username'])
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
            table = "CREATE TABLE {name}(Type TEXT, Object TEXT, Number INT)".format(name=username)
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
    if request.method == 'GET':
        http = urllib.request.urlopen("https://api.trivia.willfry.co.uk/questions?limit=1") #HTTP Response object (containing the JSON info); contains 1 question
        questions = json.load(http) #questions is a list of dictionaries; each dictionary entry is a question + answers + info

        for value in questions: #for every dictionary in the questions list
            question = value.get('question') #store the value of the key 'question'; is a string
            session['correct_answer'] = value.get('correctAnswer') #is a string
            incorrect_answers = value.get('incorrectAnswers') #is a list of strings
            incorrect_answers.append(session['correct_answer'])
            random.shuffle(incorrect_answers)

        print(session['correct_answer'])
        print(islogged())

        return render_template("trivia.html", question=question, choices=incorrect_answers)

    #POST
    else:
        # randomly choose a collectible
        num = random.randint(0, 2) #[0,n]; inclusive
        if (num == 0):
            collectible = axolotl()
        elif (num == 1):
            collectible = dog()
        else:
            collectible= cat()
        '''
        collectibles from apis are animal-specific (there is a separate function for each animal type)
        because each api gives us information in a different format from each other

        collectible is a tuple of (pic, description) given from each function
        it allows render_template to be in trivia and not in animal-specific functions
        so it avoids repeating code of rendering template and inserting data into table
        it will also make it easier to incorporate the differing paths of burn or keep collectible and of login or not
        '''

        if session['correct_answer'] == request.form['answer']:
            # for testing specific animal function
            #collectible = cat() #dog() #axolotl()

            loggedin = islogged()
            print(loggedin)
            #print(session.get('username'))

            # if user is logged in, collectible info gets added to their database
            if loggedin:
                db = sqlite3.connect('users.db')
                c = db.cursor()
                c.execute("INSERT INTO {name}(Type, Object, Number) VALUES('Collectible', ?, 1)".format(name=session.get('username')), (collectible[0],))
                db.commit()
                db.close()

            return render_template('collectibles.html', loggedin = loggedin, picture=collectible[0], description = collectible[1])
        else:
            return render_template('burn.html', picture=collectible[0], description = collectible[1])

    '''
    collectibles from apis are animal-specific (there is a separate function for each animal type)
    because each api gives us information in a different format from each other
    '''

#for axolotl collectibles, returns tuples of pic, description back to trivia
def axolotl():
    http = urllib.request.urlopen("https://axoltlapi.herokuapp.com/")
    axolotl_dict = json.load(http) #axolotl_dict is a dictionary; holds key-value pairs

    pic = axolotl_dict.get("url") #picture of axolotl
    desc = axolotl_dict.get("facts")
    collectibleInfo = (pic, desc)

    return collectibleInfo

#for dog collectibles, returns tuples of pic, description back to trivia
def dog():
    http = urllib.request.urlopen("https://dog.ceo/api/breeds/image/random")
    dog_dict = json.load(http) #dog_dict is a dictionary; holds key-value pairs

    pic = dog_dict.get("message") #picture of dog
    desc = "It is forbidden to dog"
    collectibleInfo = (pic, desc)

    return collectibleInfo

#for cat collectibles, returns tuples of pic, description back to trivia
def cat():
    http = urllib.request.urlopen("https://api.thecatapi.com/v1/images/search")
    cat_dict = json.load(http)[0] #cat_dict is a dictionary; holds key-value pairs

    pic = cat_dict.get("url") #picture of cat
    desc = "Please do not the cat"
    collectibleInfo = (pic, desc)

    return collectibleInfo


if __name__ == "__main__":
    app.debug = True
    app.run()
