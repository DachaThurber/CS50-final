import os
from re import S
from random import randint

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask.helpers import make_response
from flask_session import Session
from tempfile import mkdtemp
from matplotlib import collections
from datetime import datetime
from matplotlib.ticker import Formatter
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.dates as mpl_dates
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from datetime import timedelta, date
from datetime import datetime as dtdatetime
plt.style.use('seaborn-whitegrid')
from pylab import *
import numpy as np
import io
import datetime as DT

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///sleep.db")

# Make sure API key is set
#if not os.environ.get("API_KEY"):
#    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def home():
    
    # Via https://www.codegrepper.com/code-examples/python/get+current+hour+python
    current_time = (datetime.datetime.now()).hour
    eight = (datetime.time(20, 00, 0)).hour
    noon = (datetime.time(12, 00, 0)).hour
    four = (datetime.time(4, 00, 0)).hour

    # If past 8pm and before 4, show bedtime page
    if current_time >= eight or current_time <= four:
        val = bedtime()
        return val
    # If between four and noon, show wakeup page
    elif current_time <= noon and current_time >= four:
        val = wakeup()
        return val
    # Any other time, redirect to report page
    else:
        val = report()
        return val

# Not entirely sure GET and POST are both needed here
@app.route("/wakeup", methods=["GET", "POST"])
@login_required
def wakeup():
    
    name = db.execute("SELECT username FROM users WHERE id=?", session["user_id"])

    # Pull last login
    last_login = db.execute("SELECT recent_login FROM users WHERE id=?", session["user_id"])
    last_login = last_login[0]["recent_login"]

    # Save today's date
    today = datetime.datetime.today().date()
    
    # If it is a different day then when you last logged in
    if str(last_login) != str(today):

        # Reset recent_login
        db.execute("UPDATE users SET recent_login=? WHERE id=?", today, session["user_id"])

        # Feed in new affirmation
        value = randint(1, 30)
        both = db.execute("SELECT quote, link FROM affirmations WHERE id=?", value)

        quote = both[0]["quote"]
        link = both[0]["link"]

        # Update that user's current quote in SQL
        db.execute("UPDATE users SET quote = ?, link =? WHERE id=?", quote, link, session["user_id"])

        # Render page
        return render_template("wakeup.html", quote=quote, link=link, name=name[0]["username"])

    else:

        # Reset most recent login
        db.execute("UPDATE users SET recent_login=? WHERE id=?", today, session["user_id"])

        # Pull quote and link from users table
        both = db.execute("SELECT quote, link FROM users WHERE id=?", session["user_id"])
        quote = both[0]["quote"]
        link = both[0]["link"]

        return render_template("wakeup.html", name=name[0]["username"], quote=quote, link=link)

@app.route("/findfriends", methods=["GET", "POST"])
@login_required
def findfriends():
    
    if request.method == "POST":

        username = request.form.get("username")

        if not username:
            return apology("must provide valid username", 403)

        row = db.execute("SELECT id FROM users WHERE username = ?", username)

        # If user does not exist
        if not row:
            return apology("user does not exist", 403)

        follower_id = row[0]["id"]

        # Ensure username isn't current user's own ID
        if follower_id == session["user_id"]:
            return apology("cannot follow own account", 403)

        # Ensure user doesn't already follow other user
        check = db.execute("SELECT follower_id FROM followers WHERE followee_id = ?", session["user_id"])

        for x in check:
            if x.get("follower_id") == follower_id:
                return apology("you already follow this user", 403)

        db.execute("INSERT INTO followers(follower_id, followee_id) VALUES(?,?)", follower_id, session["user_id"])

        return render_template("ffsuccess.html", username=username)

    else:

        # Select all usernames from users
        following = db.execute("SELECT username FROM users")

        # Grab the usernames and save into new dict
        username = []
        for x in following:
            foo = x.get("username")
            username.append(foo)

        return render_template("findfriends.html", usernames=username)

@app.route("/bedtime", methods=["GET", "POST"])
@login_required

def bedtime():
    name = db.execute("SELECT username FROM users WHERE id=?", session["user_id"])
    return render_template("bedtime.html", name = name[0]["username"])

@app.route("/report", methods=["GET", "POST"])
@login_required
def report():

    if request.method == "POST":

        date = request.form.get("date")
        bedtime = request.form.get("bedtime")
        wakeup = request.form.get("wakeup")
        rating = request.form.get("rating")

        # Ensure fields were submitted
        if not date:
            return apology("must provide date", 403)
        if not bedtime:
            return apology("must provide bedtime", 403)
        if not wakeup:
            return apology("must provide wakeup", 403)
        #if not rating:
            #return apology("must provide rating", 403)
        
        db.execute("INSERT INTO sleeplog(date, bedtime, wakeup, rating, user_id) VALUES (?, ?, ?, ?, ?)", date, bedtime, wakeup, rating, session["user_id"])

        return redirect("/")
    else:
        return render_template("report.html")


# With help from https://medium.com/@rovai/from-data-to-graph-a-web-jorney-with-flask-and-sqlite-6c2ec9c0ad0
global numSamples
@app.route("/data", methods=["GET", "POST"])
def data():

    bool = 1 

    if request.method == "POST":
        global numSamples
        numSamples = maxRowsTable()
        if (numSamples > 101):
            numSamples = 100
        numSamples = int (request.form['numSamples'])
        country = request.form['country']
        state = ''
        if country == 'US':
            state = request.form['state']
        gender = request.form['gender']
        numMaxSamples = maxRowsTable()
        if (numSamples > numMaxSamples):
            numSamples = (numMaxSamples)
        templateData = {
      		'numSamples'	: numSamples
	    }
        dates, bedtimes, wakeups, ratings, ave_dates, ave_bedtimes, ave_wakeups, ave_ratings = getHistData(numSamples)
    
        '''ys_hour = [DT.datetime.strptime(time, '%H:%M').hour for time in bedtimes]
        ys_min = [DT.datetime.strptime(time, '%H:%M').minute for time in bedtimes]
        ys_hour_min = [datetime.time(ys_hour[i], ys_min[i], 00) for i in range (len(ys_hour))]
        ys = [DT.datetime.strptime(time,"%H:%M") for time in bedtimes]
        return render_template('ffsuccess.html', username = ys)'''
        return render_template('data.html', **templateData) 

    else:

        # Select ids from users that current user is following
        following = db.execute("SELECT follower_id FROM followers WHERE followee_id=?", session["user_id"])

        # Grab the usernames and save into new dict
        usernames = []
        for x in following:
            foo = db.execute("SELECT username FROM users WHERE id=?", x.get("follower_id"))
            faz = foo[0]["username"]
            usernames.append(faz)

        # If there are no usernames, set boolean
        if not usernames:
            bool = 0

        # Pass new dict into render template
        return render_template("data.html", usernames=usernames, check=bool)

def getHistData(numSamples):

    '''all_dates = db.execute("SELECT date FROM sleeplog")
    for date in all_dates:
        null_dates = db.execute("SELECT date FROM sleeplog WHERE user_id IS NULL")
        if date not in null_dates:
            db.execute("INSERT INTO sleeplog (date) VALUES (?)", date.get('date'))'''

    data = db.execute("SELECT * FROM sleeplog WHERE user_id = ? ORDER BY date DESC LIMIT "+str(numSamples), session["user_id"])
    dates = []
    bedtimes = []
    wakeups = []
    ratings = []

    for row in reversed(data):
        dates.append((list(row.values()))[0])
        bedtimes.append((list(row.values()))[1])
        wakeups.append((list(row.values()))[2])
        ratings.append((list(row.values()))[3])

    ave_data = db.execute("SELECT date, bedtime, wakeup, rating FROM sleeplog WHERE (user_id != ? OR user_id IS NULL) AND date BETWEEN ? AND ? ORDER BY date DESC", session["user_id"], dates[0], dates[len(dates)-1])
    ave_dates = []
    ave_bedtimes = []
    ave_wakeups = []
    ave_ratings = []
    
    for row in reversed(ave_data):
        ave_dates.append((list(row.values()))[0])
        ave_bedtimes.append((list(row.values()))[1])
        ave_wakeups.append((list(row.values()))[2])
        ave_ratings.append((list(row.values()))[3])

    return dates, bedtimes, wakeups, ratings, ave_dates, ave_bedtimes, ave_wakeups, ave_ratings

def maxRowsTable():
    maxNumberRows = 2
    for row in db.execute("SELECT COUNT(bedtime) FROM sleeplog WHERE user_id = ?", session["user_id"]):
        maxNumberRows=((list(row.values()))[0])
        
    return maxNumberRows

@app.route('/plot/bedtime')
def plot_bedtime():
    dates, bedtimes, wakeups, ratings, ave_dates, ave_bedtimes, ave_wakeups, ave_ratings = getHistData(numSamples)

    ys = [DT.datetime.strptime(time,"%H:%M") for time in bedtimes]
    ave_ys = [DT.datetime.strptime(time,"%H:%M") for time in ave_bedtimes]
    xs = [date.fromisoformat(ddate) for ddate in dates]
    ave_xs = [date.fromisoformat(ddate) for ddate in ave_dates]
    
    fig = Figure()
    axis = fig.add_subplot(111)
    axis.set_title("Bedtime")
    axis.set_xlabel("Next Morning")
    axis.grid(True)
    axis.plot(ave_xs, ave_ys,'.',label='Average User Data')
    axis.plot(xs, ys,'.',label='Your Data')
    
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

@app.route('/plot/wakeup')
def plot_wakeup():
    dates, bedtimes, wakeups, ratings, ave_dates, ave_bedtimes, ave_wakeups, ave_ratings = getHistData(numSamples)
    ys = wakeups
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Wakeup")
    axis.set_xlabel("Mornings")
    axis.grid(True)
    xs = dates
    axis.plot(xs, ys, 'o', color='black')
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # Query database for existing usernames
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username is unique
        if len(rows) == 1:
            return apology("username already in use", 400)

        # Ensure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 400)

        # Store User's information
        username = request.form.get("username")
        hash = generate_password_hash(request.form.get("password"))
        country = request.form.get("country")
        state = request.form.get("state")
        gender = request.form.get("gender")
        birthday = request.form.get("birthday")
        today = datetime.datetime.today().date()
        value = randint(1, 30)
        both = db.execute("SELECT quote,link FROM affirmations WHERE id=?", value)
        quote = both[0]["quote"]
        link = both[0]["link"]

        if state != "":
            db.execute("INSERT INTO users (username, hash, country, state, gender, birthday, recent_login, quote, link) VALUES(?,?,?,?,?,?,?,?,?)", username, hash, country, state, gender, birthday, today, quote, link)
        else:
            db.execute("INSERT INTO users (username, hash, country, gender, birthday) VALUES(?,?,?,?,?)", username, hash, country, gender, birthday)

        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
