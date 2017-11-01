from models import *
from validators import *
import string
import random
#import validate_email   #email verification easy mode - or another check I could run.


#@app.before_request
def csrf_protect():
	if request.method == "POST" and request.endpoint != "signup" and request.endpoint != "login":
		if request.endpoint != "handleSignup" and request.endpoint != "handleLogin":
			givenSessionToken = request.form['sessionToken']
			thisUserid = request.form['thisUserid']
			if givenSessionToken == None:
				print("failed csrf_protect() -> did not have sessionToken in the request form.")
				return render_template("login.html", error="Session timed out or security check failed.")
			if User.checkSessionToken(db, thisUserid, givenSessionToken) == False:
				print("failed csrf_protect(), form sessionToken did not match user's DB sessionToken.")
				return render_template("login.html", error="Session timed out or security check failed.")

def updateUsersSessionToken(thisUserid):
	newToken = csrfTokenGenerator()
	User.updateSessionToken(db, thisUserid, newToken)
	return newToken

def csrfTokenGenerator(size=15, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

@app.route("/")
def index():
	usernameSortedDict = BlogPost.getUsersWithPosts()
	return render_template("index.html", users=usernameSortedDict)


@app.route("/login")  #Put this in your browser URL: http://localhost:5000/
def login():
	#Template html pages are in the templates sub folder.
	return render_template('login.html')


#TODO:  Add a button to the html to go to the register page
@app.route("/handleLogin", methods=['POST'])
def handleLogin():
	#TODO:  More testing for sanity purposes.
	username = request.form['username']
	password = request.form['password']
	error = ""

	isValidUser, user = User.authenticate(db, username, password)
	if isValidUser and user != None:
			print("In handleLogin:  Updating session token for user '" + username + "'.")
			updateUsersSessionToken(user.userid)
			print("Authenticated, redirecting " + username + ", userid: " + str(user.id) + " to blog.html.")
			#return mainPage(thisUserid, sessionToken) #let the user in since they were authenticated
			return render_template("blog.html", thisUserid=thisUserid, sessionToken=user.sessionToken)
	else:
		print("Login authentication failed attempt for: " + username)
		return render_template("login.html", error=''''Either the user does not exist or that password is 
			incorrect.  Please try again.''') 


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

	passwordHash = generate_password_hash(password)
	if User.authenticate(db, username, passwordHash):  #method is in databaseHelper.py
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
	if User(db, username, passwordHash, emailAddress):
	#if createUser(mysql, username, passwordHash, emailAddress):  #This method is in databaseHelper.py.
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
	#blogList = getBlogList(mysql)
	blogList = BlogPost.getAllBlogPosts(db)
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
	if User.checkSessionToken(db, thisUserid, givenSessionToken):
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