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
    # when logged out user answers qu right, collectibe is added to session; then when they log in, collectible in session is added to table
    if 'collectible' in session.keys() and islogged:
        insertCollectible()
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
        c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, UNIQUE(username))")
        c.execute("SELECT username AND password FROM users WHERE username=? AND password=?", (username, password))

        if (c.fetchone() == None): #user doesn't exist; continue with registration
            c.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username, password))
            table = "CREATE TABLE {name}(Type TEXT, Object TEXT, Number INT)".format(name=username)
            c.execute(table)

            #preload hints and fire extinguishers in each user; default 2 each
            #FIX UP SO INCLUDES ? ? ?
            c.execute("INSERT INTO {name}(Type, Object, Number) VALUES('item', 'hint', 2)".format(name=username))

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
        num = 1#random.randint(0, 2)
        if (num == 0):
            http = urllib.request.urlopen("https://api.trivia.willfry.co.uk/questions?limit=1") #HTTP Response object (containing the JSON info); contains 1 question
            questions = json.load(http) #questions is a list of dictionaries; each dictionary entry is a question + answers + info
            print(questions)
            for value in questions: #for every dictionary in the questions list
                question = value.get('question') #store the value of the key 'question'; is a string
                session['correct_answer'] = value.get('correctAnswer') #is a string
                incorrect_answers = value.get('incorrectAnswers') #is a list of strings
                incorrect_answers.append(session['correct_answer'])
            random.shuffle(incorrect_answers)
        elif (num == 1):
            http = urllib.request.urlopen("https://opentdb.com/api.php?amount=1&difficulty=hard")
            questions = json.load(http)
            
            '''
            what the api gives is vv complicated compared to previous api, also the key name for this api was the variable name of the last                 api so it gets confusing, but point is this api is processed in diff format than last one
            '''
            print(questions)
            print(questions['results'][0])
            
            session['correct_answer'] = questions['results'][0]['correct_answer']
            question= questions['results'][0]['question'] 
            incorrectAnswers = [] #list for containing all the other answer choices
            for value in questions['results'][0]['incorrect_answers']: 
                incorrectAnswers.append(value)
            random.shuffle(incorrectAnswers)

            print(session['correct_answer'])
            print(islogged())
            
            return render_template("trivia.html", question=question, choices=incorrectAnswers)
        else:
            http = urllib.request.urlopen("https://jservice.io/api/random")
            questions = json.load(http)
            session['correct_answer'] = questions[0]['answer']
            print(session['correct_answer'])
            return render_template("triviasa.html", question=questions[0]['question'])
        
        
        questions = json.load(http) #questions is a list of dictionaries; each dictionary entry is a question + answers + info
        print(questions)
        for value in questions: #for every dictionary in the questions list
            question = value.get('question') #store the value of the key 'question'; is a string
            session['correct_answer'] = value.get('correctAnswer') #is a string
            incorrect_answers = value.get('incorrectAnswers') #is a list of strings
            incorrect_answers.append(session['correct_answer'])
            random.shuffle(incorrect_answers)

        print(session['correct_answer'])
        print(islogged())
        return render_template("trivia.html", question=question, choices=incorrect_answers)

        '''
                username = request.form.get("username")

                db = sqlite3.connect('users.db')
                c = db.cursor()
                #c.execute("SELECT Number FROM {name} WHERE Object=?",("Hint",).format(name=username))
                hint = c.fetchone()
                print(hint)
                return render_template("trivia.html", question=question, choices=incorrect_answers, hints=hint)
        '''
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

        # for testing specific animal function
        # collectible = dog() #cat() #axolotl()

        # when api fails
        if collectible == "Error":
            return render_template('error.html')

        if session['correct_answer'] == request.form['answer']:

            loggedin = islogged()
            print(loggedin)
            #print(session.get('username'))
            session['collectible'] = collectible[0]

            # if user is logged in, collectible info gets added to their database
            if loggedin:
                insertCollectible()
                return render_template('collectibles.html', loggedin = loggedin, picture=collectible[0], description = collectible[1])
            return render_template('collectibles.html', loggedin = loggedin, picture=collectible[0], description = collectible[1])
        else:
            return render_template('burn.html', picture=collectible[0], description = collectible[1])

    '''
    collectibles from apis are animal-specific (there is a separate function for each animal type)
    because each api gives us information in a different format from each other
    '''

#for axolotl collectibles, returns tuples of pic, description back to trivia
def axolotl():
    # in case api fails
    try:
        http = urllib.request.urlopen("https://axoltlapi.herokuapp.com/")
        axolotl_dict = json.load(http) #axolotl_dict is a dictionary; holds key-value pairs
        print(axolotl_dict['url'])
        while "i.imgur" in axolotl_dict['url']:
            print("cringe imgur cleansed")
            http = urllib.request.urlopen("https://axoltlapi.herokuapp.com/")
            axolotl_dict = json.load(http)
    except:
        return "Error"

    pic = axolotl_dict.get("url") #picture of axolotl
    desc = axolotl_dict.get("facts")
    collectibleInfo = (pic, desc)

    return collectibleInfo

#for dog collectibles, returns tuples of pic, description back to trivia
def dog():
    try:
        http = urllib.request.urlopen("https://dog.ceo/api/breeds/image/random")
        dog_dict = json.load(http) #dog_dict is a dictionary; holds key-value pairs
    except:
        return "Error"

    pic = dog_dict.get("message") #picture of dog
    desc = "It is forbidden to dog"
    collectibleInfo = (pic, desc)

    return collectibleInfo

#for cat collectibles, returns tuples of pic, description back to trivia
def cat():
    try:
        http = urllib.request.urlopen("https://api.thecatapi.com/v1/images/search")
        cat_dict = json.load(http)[0] #cat_dict is a dictionary; holds key-value pairs
    except:
        return "Error"

    pic = cat_dict.get("url") #picture of cat
    desc = "Please do not the cat"
    collectibleInfo = (pic, desc)

    return collectibleInfo

# inserts collectible into user's table
def insertCollectible():
    db = sqlite3.connect("users.db")
    c = db.cursor()
    c.execute("INSERT INTO {name}(Type, Object, Number) VALUES('Collectible', ?, 1)".format(name=session.get('username')), (session['collectible'],))
    session.pop('collectible')
    db.commit()
    db.close()

@app.route("/profile", methods=['POST', 'GET'])
def profile():
   try:
        username = session['username']
   except:
        return render_template('profile.html', loggedIn=False)
   collectibles = []
   db = sqlite3.connect('users.db')
   c = db.cursor()
   c.execute("SELECT Object FROM {name} WHERE Type='Collectible'".format(name=username))
   collectibles=c.fetchall()
   i=0
   while (i < len(collectibles)):
        collectibles[i]=collectibles[i][0]
        i+=1
   db.commit()
   db.close()
   print(collectibles)
   return render_template('profile.html', loggedIn=True, collection=collectibles)
    
if __name__ == "__main__":
    app.debug = True
    app.run()
