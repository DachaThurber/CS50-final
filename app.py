<<<<<<< HEAD
# Website framework from CS50 finance

from helpers import apology, login_required, lookup, usd
=======
from helpers import apology, login_required
>>>>>>> 2f600db39a17376427c83fe5a028ed263c860eb7
import datetime as DT
import io
from pylab import *
from datetime import datetime as dtdatetime
from datetime import date
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.dates as mpl_dates
import os
from re import S
from random import randint
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask.helpers import make_response
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import matplotlib as mpl
mpl.use('Agg')
plt.style.use('seaborn-whitegrid')

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///sleep.db")

# Make sure API key is set
# if not os.environ.get("API_KEY"):
#    raise RuntimeError("API_KEY not set")

# Ensures responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Home page
@app.route("/")
@login_required
def home():

    # Creates time objects to compare against
    # Via https://www.codegrepper.com/code-examples/python/get+current+hour+python
    current_time = (DT.datetime.now()).hour
    eight = (DT.time(20, 00, 0)).hour
    noon = (DT.time(12, 00, 0)).hour
    four = (DT.time(4, 00, 0)).hour

    # If past 8pm and before 4, navigate user to bedtime page
    if current_time >= eight or current_time <= four:
        val = bedtime()
        return val
    # If between four and noon, navigate user to wakeup page
    elif current_time <= noon and current_time >= four:
        val = wakeup()
        return val
    # Any other time, navigate user to report page
    else:
        val = report()
        return val

# Page with wakeup aides
@app.route("/wakeup")
@login_required
def wakeup():

    # Pulls username of current user
    name = db.execute("SELECT username FROM users WHERE id=?", session["user_id"])

    # Pulls last login of current user
    last_login = db.execute(
        "SELECT recent_login FROM users WHERE id=?", session["user_id"])
    last_login = last_login[0]["recent_login"]

    # Save today's date
    today = dtdatetime.today().date()

    # If it is a different day then when you last logged in
    if str(last_login) != str(today):

        # Reset recent_login
        db.execute("UPDATE users SET recent_login=? WHERE id=?",
                   today, session["user_id"])

        # Display in new, randomly picked affirmation
        value = randint(1, 30)
        both = db.execute(
            "SELECT quote, link FROM affirmations WHERE id=?", value)
        quote = both[0]["quote"]
        link = both[0]["link"]

        # Update that user's current quote in SQL
        db.execute("UPDATE users SET quote = ?, link =? WHERE id=?",
                   quote, link, session["user_id"])

        # Render page with new quote, link, and current user's username
        return render_template("wakeup.html", quote=quote, link=link, name=name[0]["username"])

    # If it's the same day
    else:

        # Reset most recent_login to today
        db.execute("UPDATE users SET recent_login=? WHERE id=?",
                   today, session["user_id"])

        # Pull quote and link from users table
        both = db.execute("SELECT quote, link FROM users WHERE id=?", session["user_id"])
        quote = both[0]["quote"]
        link = both[0]["link"]

        # Render page with same quote, link, and user's username
        return render_template("wakeup.html", quote=quote, link=link, name=name[0]["username"])


@app.route("/findfriends", methods=["GET", "POST"])
@login_required
def findfriends():

    if request.method == "POST":

        # Pull inputted username
        username = request.form.get("username")

        # Check for valid inputs:
        if not username:
            return apology("must provide valid username", 403)
        row = db.execute("SELECT id FROM users WHERE username = ?", username)
        # If user does not exist
        if not row:
            return apology("user does not exist", 403)
        follower_id = row[0]["id"]
        # Ensure username isn't current user's own ID (can't follow self)
        if follower_id == session["user_id"]:
            return apology("cannot follow own account", 403)
        # Ensure user doesn't already follow other user
        check = db.execute(
            "SELECT follower_id FROM followers WHERE followee_id = ?", session["user_id"])
        for x in check:
            if x.get("follower_id") == follower_id:
                return apology("you already follow this user", 403)

        # Update followers tabel with new info
        db.execute("INSERT INTO followers(follower_id, followee_id) VALUES(?,?)",
                   follower_id, session["user_id"])

        # Render success page with new follower's username
        return render_template("ffsuccess.html", username=username)

    else:

        # Select all usernames from users
        following = db.execute("SELECT username FROM users")

        # Grab the usernames and save into new array to display in dropdown
        username = []
        for x in following:
            foo = x.get("username")
            username.append(foo)

         # Render success page with list of potential users to follow
        return render_template("findfriends.html", usernames=username)

# Page with bedtime aides
@app.route("/bedtime", methods=["GET", "POST"])
@login_required
def bedtime():

    # Pulls current user's username to embed in page
    name = db.execute("SELECT username FROM users WHERE id=?",
                      session["user_id"])

    return render_template("bedtime.html", name=name[0]["username"])

# Page where you input your sleeping data
@app.route("/report", methods=["GET", "POST"])
@login_required
def report():

    if request.method == "POST":

        # Pulls info inputted on page
        date = request.form.get("date")
        bedtime = request.form.get("bedtime")
        wakeup = request.form.get("wakeup")

        # Ensure fields were submitted
        if not date:
            return apology("must provide date", 403)
        if not bedtime:
            return apology("must provide bedtime", 403)
        if not wakeup:
            return apology("must provide wakeup", 403)

        # Loads info into sleeplog
        db.execute("INSERT INTO sleeplog(date, bedtime, wakeup, user_id) VALUES (?, ?, ?, ?)",
                   date, bedtime, wakeup, session["user_id"])

        # Sends user back to homepage
        return redirect("/")

    else:
        return render_template("report.html")


# With help from https://medium.com/@rovai/from-data-to-graph-a-web-jorney-with-flask-and-sqlite-6c2ec9c0ad0
global numSamples
global country
global state
global gender
global username

# Page that displays graphs comparing users' data
@app.route("/data", methods=["GET", "POST"])
def data():
    global numSamples
    global country
    global state
    global gender
    global username

    # Get user input
    if request.method == "POST":

        numSamples=maxRowsTable()
        country = ''
        state = ''
        gender = ''
        username = 'nothing'

        if (numSamples > 101):
            numSamples = 100

        numSamples = int (request.form['numSamples'])

        if request.form['country']:
            country = request.form['country']

        if country == 'US':
            state = request.form['state']

        gender = request.form['gender']

        if request.form['userMenu']:
            username = request.form['userMenu']

        numMaxSamples = maxRowsTable()

        if (numSamples > numMaxSamples):
            numSamples = (numMaxSamples)

        templateData = {
            'numSamples': numSamples
        }

        # Select ids from users that current user is following
        following = db.execute("SELECT follower_id FROM followers WHERE followee_id=?", session["user_id"])

        # Grab the usernames and save into new array to load into dropdown
        usernames = []
        for x in following:
            foo = db.execute("SELECT username FROM users WHERE id=?", x.get("follower_id"))
            faz = foo[0]["username"]
            usernames.append(faz)

        return render_template('data.html', **templateData, usernames=usernames) 

    else:

        numSamples=maxRowsTable()
        country = ''
        state = ''
        gender = ''
        username = 'nothing'

        # Select ids from users that current user is following
        following = db.execute("SELECT follower_id FROM followers WHERE followee_id=?", session["user_id"])

        # Grab the usernames and save into new array to load into dropdown
        usernames = []
        for x in following:
            foo = db.execute(
                "SELECT username FROM users WHERE id=?", x.get("follower_id"))
            faz = foo[0]["username"]
            usernames.append(faz)

        return render_template("data.html", usernames=usernames)

# With help from https://medium.com/@rovai/from-data-to-graph-a-web-jorney-with-flask-and-sqlite-6c2ec9c0ad0
def getHistData(numSamples, country, state, gender, username):
    
    # Pulls current user's information from sleeplog
    data = db.execute("SELECT * FROM sleeplog WHERE user_id = ? ORDER BY date DESC LIMIT "+str(numSamples), session["user_id"])
    dates = []
    bedtimes = []
    wakeups = []

    # Saves user's information into respective arrays
    for row in reversed(data):
        dates.append((list(row.values()))[0])
        bedtimes.append((list(row.values()))[1])
        wakeups.append((list(row.values()))[2])
    
    ave_data = []

    # If there is a value in the username field
    if username != 'nothing':

        # Set ave_data to hold that username's info on specified days
        ave_data = db.execute("SELECT date, bedtime, wakeup FROM sleeplog JOIN users ON user_id=id WHERE username = ? AND date BETWEEN ? AND ? ORDER BY date DESC", username, dates[0], dates[len(dates)-1])
    
    # Else if there is no value in username field
    else:

        # And there is a value in the country field
        if country != '':

            # Set ave_data to hold data from users from that country on specified days
            ave_data = db.execute("SELECT date, bedtime, wakeup FROM sleeplog JOIN users ON user_id=id WHERE (user_id != ? OR user_id IS NULL) AND country = ? AND date BETWEEN ? AND ? ORDER BY date DESC", session["user_id"], country, dates[0], dates[len(dates)-1])
            
            # If there is a value in the state field
            if state != '':

                # Set ave_data to hold data from users from that country & state on specified days
                ave_data = db.execute("SELECT date, bedtime, wakeup FROM sleeplog JOIN users ON user_id=id WHERE (user_id != ? OR user_id IS NULL) AND country = ? AND state = ? AND date BETWEEN ? AND ? ORDER BY date DESC", session["user_id"], country, state, dates[0], dates[len(dates)-1])
        
        # Else if there is a value in the gender field
        elif gender != '':

            # And there is value in the country field
            if country != '':

                # Set ave_data to hold data from users from that country & same gender on specified days
                ave_data = db.execute("SELECT date, bedtime, wakeup FROM sleeplog JOIN users ON user_id=id WHERE (user_id != ? OR user_id IS NULL) AND country = ? AND gender = ? AND date BETWEEN ? AND ? ORDER BY date DESC", session["user_id"], country, gender, dates[0], dates[len(dates)-1])
                
                # If there is value in the state field
                if state != '':

                    # Set ave_data to hold data from users from that country, state, & same gender on specified days
                    ave_data = db.execute("SELECT date, bedtime, wakeup FROM sleeplog JOIN users ON user_id=id WHERE (user_id != ? OR user_id IS NULL) AND country = ? AND state = ? AND gender = ? AND date BETWEEN ? AND ? ORDER BY date DESC", session["user_id"], country, state, gender, dates[0], dates[len(dates)-1])
            
            # Else if country is not filled
            else:

                # Only set ave_data to hold data from users across same gender on specified days
                ave_data = db.execute("SELECT date, bedtime, wakeup FROM sleeplog JOIN users ON user_id=id WHERE (user_id != ? OR user_id IS NULL) AND gender = ? AND date BETWEEN ? AND ? ORDER BY date DESC", session["user_id"], gender, dates[0], dates[len(dates)-1])
        
        # Else if gender is not filled set ave_data to hold data from all users on specified days
        else:
            ave_data = db.execute("SELECT date, bedtime, wakeup FROM sleeplog WHERE (user_id != ? OR user_id IS NULL) AND date BETWEEN ? AND ? ORDER BY date DESC", session["user_id"], dates[0], dates[len(dates)-1])
    
    ave_dates = []
    ave_bedtimes = []
    ave_wakeups = []

    # Saves ave_data's information into respective arrays
    for row in reversed(ave_data):
        ave_dates.append((list(row.values()))[0])
        ave_bedtimes.append((list(row.values()))[1])
        ave_wakeups.append((list(row.values()))[2])

    # Return info
    return dates, bedtimes, wakeups, ave_dates, ave_bedtimes, ave_wakeups

# With help from https://medium.com/@rovai/from-data-to-graph-a-web-jorney-with-flask-and-sqlite-6c2ec9c0ad0
def maxRowsTable():
    maxNumberRows = 2
    for row in db.execute("SELECT COUNT(bedtime) FROM sleeplog WHERE user_id = ?", session["user_id"]):
        maxNumberRows = ((list(row.values()))[0])

    return maxNumberRows

# With help from https://medium.com/@rovai/from-data-to-graph-a-web-jorney-with-flask-and-sqlite-6c2ec9c0ad0
@app.route('/plot/bedtime')
def plot_bedtime():

    # Get user data
    dates, bedtimes, wakeups, ave_dates, ave_bedtimes, ave_wakeups = getHistData(numSamples, country, state, gender, username)

    ys = [DT.datetime.strptime(time, "%H:%M") for time in bedtimes]
    ave_ys = [DT.datetime.strptime(time, "%H:%M") for time in ave_bedtimes]
    xs = [date.fromisoformat(ddate) for ddate in dates]
    ave_xs = [date.fromisoformat(ddate) for ddate in ave_dates]

    # Format and plot in matplotlib
    fig = Figure()
    axis = fig.add_subplot(111)
    axis.set_title("Bedtime")
    axis.set_xlabel("Next Morning")
    axis.grid(True)
    axis.plot(ave_xs, ave_ys,'.',label='User Data')
    axis.plot(xs, ys,'.',label='Your Data')
    
    # More matplotlib formatting
    x_formatter = mpl_dates.DateFormatter("%Y-%m-%d")
    y_formatter = mpl_dates.DateFormatter("%H:%M")
    axis.xaxis.set_major_formatter(x_formatter)
    axis.yaxis.set_major_formatter(y_formatter)

    axis.tick_params(labelrotation=45)
    fig.tight_layout()
    fig.legend(loc='upper left')

    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

# With help from https://medium.com/@rovai/from-data-to-graph-a-web-jorney-with-flask-and-sqlite-6c2ec9c0ad0
@app.route('/plot/wakeup')
def plot_wakeup():

    # Get user data
    dates, bedtimes, wakeups, ave_dates, ave_bedtimes, ave_wakeups = getHistData(numSamples, country, state, gender, username)
    
    ys = [DT.datetime.strptime(time,"%H:%M") for time in wakeups]
    ave_ys = [DT.datetime.strptime(time,"%H:%M") for time in ave_wakeups]
    xs = [date.fromisoformat(ddate) for ddate in dates]
    ave_xs = [date.fromisoformat(ddate) for ddate in ave_dates]
    
    # Format and plot in matplotlib
    fig = Figure()
    axis = fig.add_subplot(111)
    axis.set_title("Wakeup Time")
    axis.set_xlabel("Morning")
    axis.grid(True)
    axis.plot(ave_xs, ave_ys,'.',label='User Data')
    axis.plot(xs, ys,'.',label='Your Data')
    
    # More matplotlib formatting
    x_formatter = mpl_dates.DateFormatter("%Y-%m-%d")
    y_formatter = mpl_dates.DateFormatter("%H:%M")
    axis.xaxis.set_major_formatter(x_formatter)
    axis.yaxis.set_major_formatter(y_formatter)
    
    axis.tick_params(labelrotation=45)
    fig.tight_layout()
    fig.legend(loc='upper left')
    
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

# Page for login
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# Page to register users
@app.route("/register", methods=["GET", "POST"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for existing usernames
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username is unique
        if len(rows) == 1:
            return apology("username already in use", 400)

        # Ensure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 400)

        # Store user's information
        username = request.form.get("username")
        hash = generate_password_hash(request.form.get("password"))
        country = request.form.get("country")
        state = request.form.get("state")
        gender = request.form.get("gender")
        birthday = request.form.get("birthday")
        today = DT.datetime.today().date()
        value = randint(1, 30)
        both = db.execute(
            "SELECT quote,link FROM affirmations WHERE id=?", value)
        quote = both[0]["quote"]
        link = both[0]["link"]

        # If state is filled, load all other info and state info into state column
        if state != "":
            db.execute("INSERT INTO users (username, hash, country, state, gender, birthday, recent_login, quote, link) VALUES(?,?,?,?,?,?,?,?,?)",
                       username, hash, country, state, gender, birthday, today, quote, link)
        # If state is not filled, load all other info and NOT state info
        else:
            db.execute("INSERT INTO users (username, hash, country, gender, birthday) VALUES(?,?,?,?,?)",
                       username, hash, country, gender, birthday)

        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

# When errors occur
def errorhandler(e):
    if not isinstance(e, HTTPException):
        e = InternalServerError()

    # Return apology function (built out in helpers.py)
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)