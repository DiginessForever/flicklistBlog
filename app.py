from flask import Flask, render_template, request, redirect, jsonify
import requests
from flask import Flask
from flaskext.mysql import MySQL #has to be installed outside of conda, but is accessible while in the source env.
import json
from werkzeug.security import generate_password_hash
from databaseHelper import * #this is my helper class with the database query methods
from validators import *
from securityHelper import *
import string
import random
#import validate_email   #email verification easy mode - or another check I could run.


app = Flask(__name__)
mysql = MySQL()

with open('config') as data_file:
	data = json.load(data_file)
	#This data file must be a text file named "config" in the same folder as app.py
	#Contents look like this (without the '#' signs, and of course substitute your user for "myuser", etc):
	#{
	#	"db_user" = "myuser"
	#	"db_password" = "mypassword"
	#	"db_name" = "my database name"
	#	"db_address" = "database server url or IP address"
	#}
	dbAddress = data["dbAddress"]
	dbName = data["dbName"]
	dbUser = data["dbUser"]
	dbPass = data["dbPass"]
	sessionTokenSecuritySigningString = data["sessionTokenSecuritySigningString"]

app.config['MYSQL_DATABASE_USER'] = dbUser
app.config['MYSQL_DATABASE_PASSWORD'] = dbPass
app.config['MYSQL_DATABASE_DB'] = dbName
app.config['MYSQL_DATABASE_HOST'] = dbAddress
mysql.init_app(app)


#@app.before_request
def csrf_protect():
	if request.method == "POST" and request.endpoint != "signup" and request.endpoint != "login":
		token = request.form['_csrf_token']
		if token == None:
			print("failed csrf_protect() -> did not have _csrf_token in the form as a hidden field")
			return render_template("login.html", error="Session timed out or security check failed.")

def csrfTokenGenerator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def sessionTokenCheck(mysql, thisUserid, givenSessionToken):
    if checkDBsessionToken(mysql, givenSessionToken, thisUserid) != True:
        print("The security check on sessionToken of userid " + str(thisUserid) + " did not match the user's session token in the DB.")
        return False
    return True

#app.jinja_env.globals['csrf_token'] = generate_csrf_token 

killedTheCSRFprotect = '''@app.before_request
def csrf_protect():
	#if 'logged_in' not in session and request.endpoint != 'login':
    #    return redirect(url_for('login'))
	print("At csrf_protect()")
	if request.method == "POST":
		if request.endpoint != 'login' and request.endpoint != "signup":
			if request.endpoint != 'handleLogin' and request.endpoint != 'handleSignup':
				thisUserid = request.form["thisUserid"]
				givenSessionToken = request.form["sessionToken"]
				print("csrf_protect() thisUserid: " + str(thisUserid) + " sessionToken: " + givenSessionToken)
				if sessionTokenCheck(mysql, thisUserid, givenSessionToken, sessionTokenSecuritySigningString) == False:
					print("@app.before_request, csrf_protect() session token check for user " + thisUserid + " token " + givenSessionToken + " failed.")
					return render_template("login.html", error="Session timed out or security check failed.")
'''

@app.route("/")
def index():
	usernameSortedDict = getUsernamesAndUseridsWithBlogPosts()
	return render_template("index.html", users=usernameSortedDict)


@app.route("/login")  #Put this in your browser URL: http://localhost:5000/
def login():
	#Template html pages are in the templates sub folder.
	return render_template('login.html', thisUserid=-1, sessionToken=-1)


#TODO:  Add a button to the html to go to the register page
@app.route("/handleLogin", methods=['POST'])
def handleLogin():
	#TODO:  More testing for sanity purposes.
	username = request.form['username']
	password = request.form['password']
	error = ""

	if authenticateUser(mysql, username, password, False):  #this method is in databaseHelper.py
		thisUserid = getUserid(mysql, username)
		if (thisUserid != ""):
			anotherPasswordHash = generate_password_hash(password)
			sessionToken = -1 #createSessionToken(mysql, thisUserid, anotherPasswordHash, sessionTokenSecuritySigningString)
			print("Authenticated, redirecting " + username + ", userid: " + str(thisUserid) + " to mainPage.html.  Session token set: " + str(sessionToken))
			#return mainPage(thisUserid, sessionToken) #let the user in since they were authenticated
			return render_template("main.html", sessionToken = sessionToken, thisUserid=thisUserid)
		else:
			print("getUserid problem for: " + username)
			return render_template("login.html", error='''This should not happen - the username/password 
				authenticated, but getUserid query could not find the username in the database...''') 
	else:  
		print("login problem for " + username + ":" + password)
		return render_template("login.html", error='''Sorry - either that username does not 
			exist or the password is incorrect.''')


#This is a catchall to consider later / split into several methods:
#	The user may have an email address my validator cannot handle.
#	They may forget their username.
#	They may forget their password.
#	When I add a locking feature, they may lock out their account and need it reset.
@app.route("/itsAReallyMeMario", methods=["POST"])
def itsAReallyMeMario():
	print("itsAReallyMeMario:  Not implemented error")


@app.route("/signup", methods=["GET"])
def signup():
	return render_template("signup.html")


@app.route("/handleSignup", methods=["POST"])
def handleSignup():
	#TODO  More testing, sanity purposes.  Commit and make another repo.
	error = ""
	username = request.form["username"]
	emailAddress = request.form['emailAddress']
	password = request.form['password']
	verifyPassword = request.form['verifyPassword']

	if re.match("^[^\s]{3,20}$", username) == None:
		print("Username spaces or length error.")
		usernameError = "Your username should not contain spaces and should be 3-20 characters long."
		return render_template("signup.html", usernameError=usernameError,
			username=username, emailAddress=emailAddress)

	if authenticateUser(mysql, username, password, True):  #method is in databaseHelper.py
		print("username exists")
		return render_template("signup.html", 
			userNameError="That username already exists. Please pick a different username.",
			username=username,
			emailAddress=emailAddress)

	passwordError = isValidPassword(password, verifyPassword)
	if len(passwordError) > 0:
		print("password spaces, length, or verification error")
		return render_template("signup.html", passwordError=passwordError, 
			username=username, emailAddress=emailAddress)

	if len(emailAddress) > 0:
		emailAddressError = isValidEmail(emailAddress)
		if len(emailAddressError) > 0:
			print("Email address validation error.")
			return render_template("signup.html", username=username, emailaddress=emailAddress,
				emailAddressError=emailAddressError)	

	passwordHash = generate_password_hash(password)
	if createUser(mysql, username, passwordHash, emailAddress):  #This method is in databaseHelper.py.
		#return render_template("login.html", error="Thank you for signing up.  Please login.")
		return render_template("login.html", error="Thank you for signing up, please login!")
	else:
		print("Create user error.")
		return render_template("signup.html", 
		   error="We are experiencing technical difficulties.  Please try again later.",
		   username=username, emailAddress=emailAddress)


@app.route("/blog", methods=["GET"])
def blog():
	#TODO: Test, Debug
	thisUserid = request.form["thisUserid"]
	sessionToken = request.form["sessionToken"]
	blogList = getBlogList(mysql)
	return render_template("blog.html", blogList=blogList, 
		thisUserid=thisUserid, sessionToken=sessionToken)


@app.route("/viewBlog", methods=["GET"])
def viewBlog():
	#TODO:  Test, Debug
	thisUserid = request.form["thisUserid"]
	sessionToken = request.form["sessionToken"]
	blogUserid = request.form["userid"]
	blogList = getAuthorsBlogList(mysql, blogUserid)
	return render_template("viewBlog.html", blogList=blogList, 
		thisUserid=thisUserid, sessionToken=sessionToken)


@app.route("/viewPost", methods=["GET"])
def viewPost():
	#TODO:  Test, Debug
	thisUserid = request.form["thisUserid"]
	sessionToken = request.form["sessionToken"]
	postId = request.form["postId"]
	#TODO database call to get this post's title and text
	data = getBlogPost(mysql, postId)
	userid = data[1]
	postTitle = data[2]
	postText = data[3]
	
	return render_template("viewPost", userid=userid, postTitle=postTitle, postText=postText, 
		thisUserid=thisUserid, sessionToken=sessionToken)


@app.route("/newPost", methods=["GET"])
def newPost():
	userid = request.form["thisUserid"]
	givenSessionToken = request.form["sessionToken"]
	if sessionTokenCheck(mysql, thisUserid, givenSessionToken, sessionTokenSecuritySigningString):
		return render_template("newPost.html", thisUserId=thisUserid, sessionToken=givenSessionToken)
	else:
		return render_template("login.html", error="Session timed out or security check failed.")


@app.route("/handleNewPost", methods=["POST"])
def handleCreatePost():
	#TODO:  Test, Debug
	thisUserid = request.form["thisUserid"]
	givenSessionToken = request.form["sessionToken"]
	postTitle = request.form["postTitle"]
	postText = request.form["postText"]

	notNormalChars = "^[^\w\s]+$"
	
	if re.match(notNormalChars +"{1,50}", title):
		postTitleError = "Post title may not exceed a maximum of 50 characters.  It may contain alphanumerics and white space."
		return render_template("blogPost.html", thisUserid=thisUserid,
			postTitle=postTitle, postTitleError=postTitleError, postText=postText)

	if re.match(notNormalChars +"{1,5000", postText):
		textError = "Post text maximum length is 5000 characters.  It may only contain alphanumerics and white space."
		return render_template("blogPost.html", thisUserid=thisUserid,
			postTitle=postTitle, postText=postText, textError=textError)

	createBlogPost(mysql, userid, postTitle, postText)
				
	#TODO make "templates/viewPost.html"
	return render_template("viewPost.html", userid=userid,
		postTitle=postTitle, text=text)


if __name__ == "__main__":
	app.run()