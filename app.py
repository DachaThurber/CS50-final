import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, isfloat

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
db = SQL("sqlite:///finance.db")

# API key: pk_2a422b407e2748bda5a627ed4de7008a
# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    
    # list of stocks owned and their net shares and net price (a degenerate value to be replaced later)
    stocks = db.execute("SELECT symbol, SUM(shares) AS shares, SUM(price) AS price FROM transactions WHERE user_id = ? GROUP BY symbol", session["user_id"])
    
    # save cash holdings value
    balance_d = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    balance = balance_d[0]["cash"]
    
    # calculate current stock holding net prices and the value of total assets
    total = balance
    for stock in stocks:
        c_value = lookup(stock["symbol"])
        if c_value:
            stock["price"] = c_value["price"] * stock["shares"]
            total += stock["price"]

    # render index page
    return render_template("index.html", stocks=stocks, total=total, balance=balance, usd=usd)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quote = lookup(symbol)
        shares = request.form.get("shares")

        # if symbol is invalid
        if not quote:
            return apology("invalid symbol")
        
        # if shares field left blank
        elif not shares:
            return apology("must input number of shares")

        # if shares value is invalid
        elif not shares.isnumeric() or (float(int(float(shares))) != float(shares)) or int(shares) < 1:
            return apology("invalid number of shares")
        
        # if valid buy request
        else:

            # save total cash amount
            cash_d = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            cash = cash_d[0].get("cash")

            # if not enough cash
            if float(cash) < (float(shares) * float(quote["price"])):
                return apology("insufficient funds")

            # if buy request is possible
            else:
                db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?,?,?,?)", session["user_id"], symbol, shares, quote["price"])
                new_cash = cash - (float(shares) * quote["price"])
                db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, session["user_id"])
                return redirect("/")

    # User reached route via GET
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    
    #retreive transaction data
    history = db.execute("SELECT symbol, price, shares, time FROM transactions WHERE user_id = ?", session["user_id"])

    return render_template("history.html", history=history, usd=usd)


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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST
    if request.method == "POST":

        quote = lookup(request.form.get("symbol"))

        # if invalid symbol
        if not quote:
            return apology("invalid symbol")
        
        # if valid quote attempt
        else:
            return render_template("quoted.html", quote=quote, usd=usd)

    # User reached route via GET
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)
        
        # Query database for existing usernames
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username is unique
        if len(rows) == 1:
            return apology("username already in use", 400)

        # Ensure password was submitted
        if not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password and confirmation", 400)

        # Ensure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 400)

        # Store User's information
        username = request.form.get("username")
        hash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES(?,?)", username, hash)

        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # User reached route via POST
    if request.method == "POST":

        # retrieve information about sell request
        symbol = request.form.get("symbol")
        quote = lookup(symbol)
        shares = request.form.get("shares")
        stocks = db.execute("SELECT symbol, SUM(shares) FROM transactions WHERE symbol = ? AND user_id = ? GROUP BY symbol", symbol, session["user_id"])
        cash_d = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = cash_d[0].get("cash")

        # if invalid symbol
        if not quote:
            return apology("invalid symbol")

        # if shares field left blank
        elif not shares:
            return apology("must input number of shares")

        # if invalid number of shares requested
        elif not shares.isnumeric() or (float(int(float(shares))) != float(shares)) or int(shares) < 1:
            return apology("invalid number of shares")

        # if user doesn't have enough such stocks to sell
        elif stocks[0]["SUM(shares)"] < float(shares):
            return apology("insuffient stocks")

        # if valid sell request
        else:
            db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?,?,?,?)", session["user_id"], symbol, -1.0 * float(shares), -1.0 * quote["price"])
            new_cash = cash + float(shares) * quote["price"]
            db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, session["user_id"])
            return redirect("/")

    # User reached route via GET
    else:

        symbols = db.execute("SELECT DISTINCT symbol FROM transactions WHERE user_id=?", session["user_id"])

        return render_template("sell.html", symbols=symbols)

@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    """Add Cash"""

    # User reached route via POST
    if request.method == "POST":

        # amount of cash to add
        cash = request.form.get("cash")

        # if cash to add field was left blank
        if not cash:
            return apology("enter cash amount")

        # if invalid cash amount requested
        elif not isfloat(cash) or float(cash) < 0.0:
            return apology("invalid cash amount")

        # if valid cash add request
        else:

            # update SQL database to reflect added cash
            cash_d = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            current_cash = cash_d[0].get("cash")
            db.execute("UPDATE users SET cash = ? WHERE id = ?", current_cash + float(cash), session["user_id"])
            return render_template("cashed.html")

    # User reached route via GET
    else:
        return render_template("cash.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)