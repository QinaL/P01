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
        elif not userCheck(username):
            return render_template("register.html", error="Username should only contain alphanumeric characters")
        elif not letterFirst(username):
            return render_template("register.html", error="Username cannot start with a number")

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
            c.execute("INSERT INTO {name}(Type, Object, Number) VALUES('Item', 'Hint', 2)".format(name=username))
            c.execute("INSERT INTO {name}(Type, Object, Number) VALUES('Item', 'Fire Extinguisher', 2)".format(name=username))
            '''
            preload counters into tables
            used so users can gain hints and fire extinguishers
                - every 10 qus rights = 1 hint
                - every 10 qus wrong = 1 fire extinguisher
            total is total number of qus user got right/wrong over their entire usage
            goal is of this set of 10, how close is user to getting hint/fire extinguisher
            '''
            c.execute("INSERT INTO {name}(Type, Object, Number) VALUES('Counter', 'Total Right', 0)".format(name=username))
            c.execute("INSERT INTO {name}(Type, Object, Number) VALUES('Counter', 'Goal Right', 0)".format(name=username))
            c.execute("INSERT INTO {name}(Type, Object, Number) VALUES('Counter', 'Total Wrong', 0)".format(name=username))
            c.execute("INSERT INTO {name}(Type, Object, Number) VALUES('Counter', 'Goal Wrong', 0)".format(name=username))

        else: #error: username already taken
            return render_template("register.html", error="Username taken already")
        db.commit()
        db.close()
        return redirect("/login")
    else:
        return render_template("register.html", test='&quot')

def userCheck(username):
    '''Checks if the username is only alphanumeric characters'''
    for char in username:
        if not (char.isdigit() or char.isalpha()):
            return False
    return True

def letterFirst(username):
    '''Checks if the username starts with a letter and not a number'''
    return username[0].isalpha()

@app.route("/trivia", methods=['POST', 'GET'])
def trivia():
    if request.method == 'GET':

        #randomly choose which trivia api to use
        num = random.randint(0, 2)

        if (num == 0):
            triviaInfo = triviaApi0()
        elif (num == 1):
            triviaInfo = triviaApi1()
        # trivia api 2 does not have own function b/c it uses diff template and it is short-answer while api 0 and 1 are multiple choice
        else:
            # try except in case trivia api 2 fails
            try:
                http = urllib.request.urlopen("https://jservice.io/api/random")
                questions = json.load(http)
            except:
                return render_template('error.html')

            correct= questions[0]['answer']
            # for api 2; sometimes ans is in form of <i>ans</i>, cleanSA() gets rid of <> part
            session['correct_answer'] = cleanSA(correct)
            print(session['correct_answer'])
            return render_template("triviasa.html", question=questions[0]['question'], logged=islogged(), hint=getNumOfHints(), hinted=False)

        # if api fails, error page shown; else mc qus are rendered
        if triviaInfo == "Error":
            return render_template('error.html')

        return render_template('trivia.html', question=triviaInfo[0], choices=triviaInfo[1], logged=islogged(), hint=getNumOfHints())

    #POST
    else:

        #if there is a correct_answer stored in sessions; mechanism so user can't refresh to gain new collectible
        if (session['correct_answer'] != None):
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

            correct = session['correct_answer']
            given = request.form['answer']
            loggedin = islogged()
            if correct == given or filterSA(correct, given):

                # puts this in session for when a non-loggedin user logins to get collectible
                session['collectible'] = collectible[0]
                #keeps track of whether user refreshed in gain collectible page
                session['correct_answer'] = None

                # if user is logged in, collectible info gets added to their database
                if loggedin:
                    # logged in user gets right counters increased
                    rightCounters()
                    insertCollectible()
                    return render_template('collectibles.html', loggedin = loggedin, picture=collectible[0], description = collectible[1])
                return render_template('collectibles.html', loggedin = loggedin, picture=collectible[0], description = collectible[1])
            else:
                #keeps track of whether user refreshed in gain collectible page
                session['correct_answer'] = None

                if loggedin:
                    # logged in user gets wrong counters increased
                    wrongCounters()
                return render_template('burn.html', logged = loggedin, picture=collectible[0], description = collectible[1], correct=correct, fire=getNumOfFireExtinguishers())

        #session has no correct_answer stored
        else:
            return redirect("/trivia")
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
        db = sqlite3.connect("users.db")
        c = db.cursor()

        #KeyError: 'Username' arises sometimes; if there is a session username...
        if session.get('username') != None:
            c.execute("SELECT Object FROM {user} WHERE Object=?".format(user=session['username']), (question,))
            if c.fetchone() != None:
                return triviaApi0()
            c.execute("INSERT INTO {user}(Type, Object) VALUES('Question', ?)".format(user=session['username']), (question,))
            db.commit()
            db.close()
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

    db = sqlite3.connect("users.db")
    c = db.cursor()

    #KeyError: 'Username' arises sometimes; if there is a session username...
    if session.get('username') != None:
        c.execute("SELECT Object FROM {user} WHERE Object=?".format(user=session['username']), (question,))
        if c.fetchone() != None:
            return triviaApi1()
        c.execute("INSERT INTO {user}(Type, Object) VALUES('Question', ?)".format(user=session['username']), (question,))
        db.commit()
        db.close()

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

    return correct == given

'''
- some correct ans given by api are in form of <i>House</i>; this filters out the <> mess
- not part of filterSA b/c <> mess needs to be out in session['correct_answer']
    - so it doesn't appear if user gets qu wrong and correct_answer is displayed in burn.html
    - and so <> part is not given in the SA hint
'''
def cleanSA(correct):
    substring = "<"
    if substring in correct:
        # gets rid of first three characters (<i>)
        correct = correct[3:]
        # finds and gets rid of the behind </i>
        index = correct.find(substring)
        correct = correct[:index]
    return correct


''' collectible functions; for POST /trivia; returns tuples of pic, description'''

#for axolotl collectibles
def axolotl():
    # in case api fails
    try:
        http = urllib.request.urlopen("https://axoltlapi.herokuapp.com/")
        axolotl_dict = json.load(http) #axolotl_dict is a dictionary; holds key-value pairs
        print(axolotl_dict['url'])
        if session.get("username") != None:
            db = sqlite3.connect("users.db")
            c = db.cursor()
            c.execute("SELECT * FROM {user} WHERE Object=?".format(user=session['username']), (axolotl_dict['url'],))
            while "i.imgur" in axolotl_dict['url'] or c.fetchone() != None:
                print("cringe imgur cleansed")
                http = urllib.request.urlopen("https://axoltlapi.herokuapp.com/")
                axolotl_dict = json.load(http)
                c.execute("SELECT * FROM {user} WHERE Object=?".format(user=session['username']), (axolotl_dict['url'],))
        else:
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
        if session.get("username") != None:
            db = sqlite3.connect("users.db")
            c = db.cursor()
            c.execute("SELECT * FROM {user} WHERE Object=?".format(user=session['username']), (dog_dict['message'],))
            while c.fetchone() != None:
                http = urllib.request.urlopen("https://dog.ceo/api/breeds/image/random")
                axolotl_dict = json.load(http)
                c.execute("SELECT * FROM {user} WHERE Object=?".format(user=session['username']), (dog_dict['message'],))
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
        if session.get("username") != None:
            db = sqlite3.connect("users.db")
            c = db.cursor()
            c.execute("SELECT * FROM {user} WHERE Object=?".format(user=session['username']), (cat_dict['url'],))
            while c.fetchone() != None:
                http = urllib.request.urlopen("https://api.thecatapi.com/v1/images/search")
                axolotl_dict = json.load(http)
                c.execute("SELECT * FROM {user} WHERE Object=?".format(user=session['username']), (cat_dict['url'],))
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

        # decrease num of hints in db
        hintUsed()

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

        clue = session['correct_answer']
        # if clue is 2 or less letters; only first letter is given; otherwise, first 2 letters is given
        if len(clue) > 2:
            clue = clue[0:2]
        else:
            clue = clue[0:1]

        # decrease num of hints in db
        hintUsed()

        # hint button is not longered shown; can't use mutliple hints in same SA question (unlike mc)
        return render_template('triviasa.html', question=question, hinted=True, clue=clue)

# decrease number of hints in user's table
def hintUsed():
    hint=getNumOfHints()
    hint -= 1
    db = sqlite3.connect('users.db')
    c = db.cursor()
    c.execute("UPDATE {name} SET Number = ? WHERE Object=?".format(name=session['username']), (hint, "Hint",))
    db.commit()
    db.close()
    return 0

# extinguish burning collectible if user is logged in
@app.route("/extinguish", methods=['POST', 'GET'])
def extinguish():
    # if user manually goes here, they are redirected /trivia
    if request.method == "GET":
        return redirect("/trivia")
    # when extinguish button is pressed
    else:
        pic = request.form.get("Collectible")
        desc = request.form.get("Description")

        # decrease num of extinguishers in db
        extinguisherUsed()
        # insert collectible into individual's table
        session["collectible"] = pic
        insertCollectible()

        #collectible is safe from flames now; display gain page with that same collectible
        return render_template('collectibles.html', loggedin = islogged(), picture=pic, description=desc)

# decrease number of fire extinguishers in user's table
def extinguisherUsed():
    fire=getNumOfFireExtinguishers()
    fire -= 1
    db = sqlite3.connect('users.db')
    c = db.cursor()
    c.execute("UPDATE {name} SET Number = ? WHERE Object=?".format(name=session['username']), (fire, "Fire Extinguisher",))
    db.commit()
    db.close()
    return 0

@app.route("/profile", methods=['POST', 'GET'])
def profile():

    return render_template('profile.html', loggedIn= islogged(), numOfCollectibles= getNumOfCollectibles(), numOfHints= getNumOfHints(), numOfFireExtinguishers= getNumOfFireExtinguishers(), numOfAchievements = getNumOfAchievements(), numOfRightQus= getNumOfCounter("Total Right"), numOfWrongQus = getNumOfCounter("Total Wrong"), goalRight = getNumOfCounter("Goal Right"), goalWrong = getNumOfCounter("Goal Wrong"))
    '''
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
    '''

@app.route("/collection", methods=['POST', 'GET'])
def collection():
    # stops users that are not logged in from seeing collection and getting error
    if not islogged():
        return redirect("/profile")
    else:
        collectibles = []
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT Object FROM {name} WHERE Type='Collectible'".format(name=session['username']))
        collectibles=c.fetchall()
        i=0
        while (i < len(collectibles)):
            collectibles[i]=collectibles[i][0]
            i+=1
        db.commit()
        db.close()
        return render_template('collection.html', collection=collectibles)

@app.route("/achievements", methods=['POST', 'GET'])
def achievements():
    if not islogged():
        return redirect("/profile")
    else:
        achievements = getAchievements()
        return render_template('achievements.html', first= achievements[0], master= achievements[1], god= achievements[2])

@app.route("/specials", methods=['POST', 'GET'])
def specials():
    if not islogged():
        return redirect("/profile")
    else:
        achievements = getAchievements()
        return render_template('specials.html', first= achievements[0], master= achievements[1], god= achievements[2])

def getNumOfCollectibles():
    if islogged():
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT COUNT(*) FROM {name} WHERE Type=?".format(name=session['username']), ("Collectible",))
        collectible = c.fetchone()[0] #c.fetchone gives a tuple, so [0] to get the number
    else:
        collectible=-1
    return collectible

def getAchievements():
    '''
    first touch achievement: at least one collectible
    master: 50 collectibles
    trivia god: 100 collectibles
    '''
    achievements= [False, False, False]
    if islogged():
        collectible= getNumOfCollectibles()
        achievements[0] = collectible > 0
        achievements[1] = collectible > 49
        achievements[2] = collectible > 99
    return achievements

def getNumOfAchievements():
    if islogged():
        count = 0;
        achievements = getAchievements()
        for status in achievements:
            if status:
                count += 1
    else:
        count=-1
    return count

def rightCounters():
    db = sqlite3.connect('users.db')
    c = db.cursor()

    # increases total right counter by 1
    totalRight = getNumOfCounter("Total Right")
    totalRight += 1
    c.execute("UPDATE {name} SET Number = ? WHERE OBJECT =?".format(name=session['username']), (totalRight, "Total Right",))

    # increases goal right counter by 1
    goalRight = getNumOfCounter("Goal Right")
    goalRight += 1
    # if user reaches set of 10 qus right --> gets 1 hint
    if goalRight == 10:
        # increases num of hint in db
        hint=getNumOfHints()
        hint += 1
        c.execute("UPDATE {name} SET Number = ? WHERE Object=?".format(name=session['username']), (hint, "Hint",))
        # reset this set of right qus
        goalRight = 0
    c.execute("UPDATE {name} SET Number = ? WHERE OBJECT =?".format(name=session['username']), (goalRight, "Goal Right",))
    db.commit()
    db.close()
    return 0

def wrongCounters():
    db = sqlite3.connect('users.db')
    c = db.cursor()

    # increases total wrong counter by 1
    totalWrong = getNumOfCounter("Total Wrong")
    totalWrong += 1
    c.execute("UPDATE {name} SET Number = ? WHERE OBJECT =?".format(name=session['username']), (totalWrong, "Total Wrong",))

    # increases goal wrong counter by 1
    goalWrong = getNumOfCounter("Goal Wrong")
    goalWrong += 1
    # if user reaches set of 10 qus wrong --> gets 1 fire extinguisher
    if goalWrong == 10:
        # increases num of fire extinguisher in db
        fe=getNumOfFireExtinguishers()
        fe += 1
        c.execute("UPDATE {name} SET Number = ? WHERE Object=?".format(name=session['username']), (fe, "Fire Extinguisher",))
        # reset this set of wrong qus
        goalWrong = 0
    c.execute("UPDATE {name} SET Number = ? WHERE OBJECT =?".format(name=session['username']), (goalWrong, "Goal Wrong",))
    db.commit()
    db.close()
    return 0

def getNumOfFireExtinguishers():
    if islogged():
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT Number FROM {name} WHERE Object=?".format(name=session['username']), ("Fire Extinguisher",))
        fe = c.fetchone()[0] #c.fetchone gives a tuple, so [0] to get the number
    else:
        fe=-1
    return fe

# counter is a string that denotes which counter in db is being asked for; e.g. "Total Right", "Goal Right", "Total Wrong", "Goal Wrong"
def getNumOfCounter(counter):
    if islogged():
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT Number FROM {name} WHERE Object=?".format(name=session['username']), (counter,))
        counter = c.fetchone()[0]
    else:
        counter = -1
    return counter

'''
def getNumOfRightQus():
    if islogged():
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT Number FROM {name} WHERE Object=?".format(name=session['username']), ("Total Right",))
        totalRight = c.fetchone()[0] #c.fetchone gives a tuple, so [0] to get the number
    else:
        totalRight=-1
    return totalRight

def getNumOfGoalRight():
    if islogged():
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT Number FROM {name} WHERE Object=?".format(name=session['username']), ("Goal Right",))
        goalRight = c.fetchone()[0] #c.fetchone gives a tuple, so [0] to get the number
    else:
        goalRight=-1
    return goalRight

def getNumOfWrongQus():
    if islogged():
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT Number FROM {name} WHERE Object=?".format(name=session['username']), ("Total Wrong",))
        totalWrong = c.fetchone()[0] #c.fetchone gives a tuple, so [0] to get the number
    else:
        totalWrong=-1
    return totalWrong

def getNumOfGoalWrong():
    if islogged():
        db = sqlite3.connect('users.db')
        c = db.cursor()
        c.execute("SELECT Number FROM {name} WHERE Object=?".format(name=session['username']), ("Goal Wrong",))
        goalWrong = c.fetchone()[0] #c.fetchone gives a tuple, so [0] to get the number
    else:
        goalWrong=-1
    return goalWrong
'''

if __name__ == "__main__":
    app.debug = True
    app.run()
