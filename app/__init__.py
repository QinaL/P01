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
    # for purely testing
    if islogged():
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT * FROM {name}".format(name=session['username']))
        print(c.fetchall())
        
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
            c.execute("INSERT INTO {name}(Type, Object, Number) VALUES('Item', 'Hint', 2)".format(name=username))

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
        
        #randomly choose which trivia api to use 
        num = 2#random.randint(0, 2)
        
        if (num == 0):
            triviaInfo = triviaApi0()
        elif (num == 1):
            triviaInfo = triviaApi1()
        # trivia api 2 does not have own function b/c it uses diff template and it is short-answer while api 0 and 1 are multiple choice
        else:
            # try except in case api fails
            try:
                http = urllib.request.urlopen("https://jservice.io/api/random")
                questions = json.load(http)
            except:
                return render_template('error.html')
            
            session['correct_answer'] = questions[0]['answer']
            print(session['correct_answer'])
            return render_template("triviasa.html", question=questions[0]['question'], logged=islogged(), hint=getNumOfHints())
        
        # if api fails, error page shown; else mc qus are rendered
        if triviaInfo == "Error":
            return render_template('error.html')
        return render_template('trivia.html', question=triviaInfo[0], choices=triviaInfo[1], logged=islogged(), hint=getNumOfHints())
        
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
        
        if session['correct_answer'] == request.form['answer'] or filterSA(session['correct_answer'], request.form['answer']):
            loggedin = islogged()
            
            # puts this in session for when a non-loggedin user logins to get collectible 
            session['collectible'] = collectible[0]

            # if user is logged in, collectible info gets added to their database
            if loggedin:
                insertCollectible()
                return render_template('collectibles.html', loggedin = loggedin, picture=collectible[0], description = collectible[1])
            return render_template('collectibles.html', loggedin = loggedin, picture=collectible[0], description = collectible[1])
        else:
            return render_template('burn.html', picture=collectible[0], description = collectible[1])

''' api trivia functions (only 0 and 1, api 2 has diff format); for GET /trivia; return tuples of question, answer choices '''
        
# processing trivia api 0
def triviaApi0():
    #try except in case api fails
    try: 
        #gets info from api; HTTP Response object (containing the JSON info); contains 1 question
        http = urllib.request.urlopen("https://api.trivia.willfry.co.uk/questions?limit=1") 
        #questions is a list of dictionaries; each dictionary entry is a question + answers + info
        questions = json.load(http) 
    except: 
        return "Error"
            
    print(questions)
            
    #processes info 
    for value in questions: #for every dictionary in the questions list
        question = value.get('question') #store the value of the key 'question'; is a string
        session['correct_answer'] = value.get('correctAnswer') #is a string
        incorrect_answers = value.get('incorrectAnswers') #is a list of strings
    #add correct answer so incorrect_answer has all possible answer choices
    incorrect_answers.append(session['correct_answer'])
    #randomize order answer choices appear
    random.shuffle(incorrect_answers)
            
    print(session['correct_answer'])
    print(islogged())
    
    triviaInfo = (question, incorrect_answers)
    return triviaInfo
    
# processing trivia api 1
def triviaApi1():
    # try except in case api fails
    try:
        #gets info from api
        http = urllib.request.urlopen("https://opentdb.com/api.php?amount=1&difficulty=hard")
        questions = json.load(http)
    except:
        return "Error"
    '''
    what the api gives is vv complicated compared to previous api, also the key name for this api was the variable name of the last     
    api so this api is processed in diff format than last one
    '''
    #for debugging
    print(questions)
    print(questions['results'][0])
            
    #processes info 
    session['correct_answer'] = questions['results'][0]['correct_answer']
    question= questions['results'][0]['question'] 
    incorrectAnswers = [] #list for containing all the other answer choices
    for value in questions['results'][0]['incorrect_answers']: 
        incorrectAnswers.append(value)
    #add correct answer so incorrectAnswer has all possible answer choices
    incorrectAnswers.append(session['correct_answer'])
    #randomize order answer choices appear
    random.shuffle(incorrectAnswers)

    print(session['correct_answer'])
    print(islogged())
    
    triviaInfo=(question, incorrectAnswers)
    return triviaInfo

'''
for trivia api 2
returns true or false; filters to check if given ans matches correct answer
'''
def filterSA(correct, given):

    # makes both strings all lowercase to make case irrelevant in 
    correct = correct.lower()
    given = given.lower()
    
    # removes any " in strings in case answer is a book/album/etc that has quotes around it
    # will not require users to put quotes around answers of such 
    removeChar="\""
    for char in removeChar:
        correct = correct.replace(char,"")
    for char in removeChar:
        given = given.replace(char,"")
    
    # some correct ans given by api are in form of <i>House</i>; this filters out the <> mess
    substring = "<"
    if substring in correct:
        # gets rid of first three characters (<i>)
        correct = correct[3:]
        # finds and gets rid of the behind </i>
        index = correct.find(substring)
        correct = correct[:index]
    
    return correct == given
    
    
''' collectible functions; for POST /trivia; returns tuples of pic, description'''
    
#for axolotl collectibles
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

#for dog collectibles
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

#for cat collectibles
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

# for mc qus; gets rid of 1 wrong answer choice
@app.route("/hint", methods=['POST', 'GET'])
def hint():
    # if users manually goes to /hint, they will be redirected to /trivia
    if request.method == "GET":
        return redirect("/trivia")
    # when use hint button is pressed
    else:
        question = request.form.get('Question')
        choices = request.form.get('Choices')
        '''
        choices when received from request is a string in the look of a list
        ex: "['Mark Messier', 'Maurice Richard', 'Wayne Gretzky', 'Sidney Crosby']"
        we have to convert this string back into list type
        '''
        removeChar="[]'"
        # iterates through each character in removeChar and deletes it from the choices string
        for char in removeChar:
            choices = choices.replace(char,"")
        choices = list(choices.split(", "))
        
        # gets rid of one wrong answer choice
        correct = session['correct_answer']
        print(correct)
        for ans in choices:
            if ans != correct: 
                choices.remove(ans)
                break
        
        # decrease number of hints in database
        hint=getNumOfHints()
        hint -= 1
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("UPDATE {name} SET Number = ? WHERE Object=?".format(name=session['username']), (hint, "Hint",))
        db.commit()
        db.close()
        
        # if after getting rid of 1 wrong ans choice, there is only 1 choice left, hint button has to disappear
        logged = islogged()
        if len(choices) == 1:
            logged = False # even tho, user is logged in, this is manually changed to False to make hint button disappear
        
        return render_template('trivia.html', question=question, choices=choices, logged=logged, hint=getNumOfHints())
    
    
# gets how many hints a user has    
def getNumOfHints():
    if islogged():
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT Number FROM {name} WHERE Object=?".format(name=session['username']), ("Hint",))
        hint = c.fetchone()[0] #c.fetchone gives a tuple, so [0] to get the number
    else:
        hint=-1
    return hint

# for SA qus; first letter is given
@app.route("/hintSA", methods=['POST', 'GET'])
def hintsa():
    # if user manually goes here, they are redirected /trivia
    if request.method == "GET":
        return redirect("/trivia")
    # when hint button is pressed
    else:
        question= request.form.get('Question')
        return render_template('triviasa.html', question=question)

if __name__ == "__main__":
    app.debug = True
    app.run()
