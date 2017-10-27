from flask import Flask, render_template, request, redirect #jsonify
import requests
from werkzeug.security import generate_password_hash
from flaskext.mysql import MySQL
import re
import json
import dns.resolver  #must install dnspython to get this (from command line:  "pip install dnspython" OR "conda install dnspython")
#import validate_email   #email verification easy mode - or another check I could run.

app = Flask(__name__)
#TODO:  Put this in a config file and make a config class for parsing the file in.
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
	dbUser = data["db_user"]
	dbPass = data["db_pass"]
	dbName = data["db_name"]
	dbAddress = data["db_address"]
	
app.config['MYSQL_DATABASE_USER'] = dbUser
app.config['MYSQL_DATABASE_PASSWORD'] = dbPass
app.config['MYSQL_DATABASE_DB'] = dbName
app.config['MYSQL_DATABASE_HOST'] = dbAddress
mysql.init_app(app)

@app.route("/")
def main():
	#Template html pages are in the templates sub folder.
	return render_template('login.html')

#TODO:  Create registration page - login page should have a button that redirects to it.
	#			At the registration page, email addresses are validated.  Passwords are hashed, both at the
	#			registration page and on the login page.
@app.route("/login", methods=['POST'])
def login():
	global mysql
	try:
		conn = mysql.connect()
	except Exception as e:
		print("There was a problem connecting to MySQL:")
		print(e)
	cursor = conn.cursor()
	cursor.execute("select * from user;")
	#user table format: userid, username, password
	#TODO:  Change the above to: userid, username, password, confirmationToken, isConfirmed, csrfToken, tokenTimestamp
	sqlResponseData = cursor.fetchall()

	username = request.form['username']    
	password = request.form['password']
	passwordHash = generate_password_hash(password)
	isValidated = False

	#The below two variables are for debugging purposes only.
	#usernameResult = "Username not found"
	#passwordResult = ""
	for row in sqlResponseData:
		#Note:  the below username/password check is for debugging purposes only.  Don't tell strangers what they are failing on.
		#if row[1] == username:
		#	usernameResult = "Username found"
		#	if row[2] == password:
		#		passwordResult = "Password matched!"
		#	else:
		#		passwordResult = "Incorrect password."
		#return "<!DOCTYPE html><html><body><p>" + usernameResult + "</p><p>" + passwordResult + "</p>" + "<p>" + str(sqlResponseData) + "</p></body></html>"
		if row[1] == username:
			if row[2] == password:
				isValidated = True
		
	if isValidated: #TODO render the mainPage template here.  It should have a csrf token and userid.
		return "<!DOCTYPE html><html><body><p>Welcome to the system.</p></body></html>"		
	else:  
		return "<!DOCTYPE html><html><body><p>Sorry - either that username does not exist or the password is incorrect.</p></body></html>"

@app.route("/register", methods=["GET"])
def register():
	return render_template("register.html")

@app.route("/handleRegistration", methods=["POST"])
def handleRegistration():
	#TODO  Create a registration page template in the templates folder.
	error = ""
	emailAddress = request.form['emailaddress']
	password = request.form['password']
	verifyPassword = request.form['verifyPassword']
	if password != verifyPassword:
		error = "Please make sure that your password and verified password match each other."
		return render_template("register.html", error=error)
	if (isValidEmail(emailAddress, error) != True):
		return render_template("register.html", error=error)
	if (userExists(username)):
		error = "That username already exists.  Please pick a different username.  Note: our usernames are email addresses."
		return render_template("register.html", error=error)

	error = "You should have received a verification email.  Click the link in the email to confirm."
	return render_template("login.html", error=error)

#If the user insists that their email address is real, I will try to send an email to it anyway, regardless of checks failing.
#If they can perform the verification step, I know they can see the email, so the email address must exist.
#This method will try to send emails to those email address which fail the checks...
@app.route("/itsAReallyMeMario", methods=["POST"])
def itsAReallyMeMario():
	print("itsAReallyMeMario:  Not implemented error")

#TODO: Extend the rules to implement RFC 6531: https://tools.ietf.org/html/rfc6531 (In order to support all the characters used in the world)
#TODO: Add more logic to allow quotes.
def isValidEmail(emailString, error):
	#This makes sure there is only one '@' sign, and that it has characters before and after it.
	atSignError = False
	if re.match('^[^@]+@[^@]+$', emailString) != None:
		atSignError = True
		error = '''<p>You can only have one '@' sign in your email address.</p>
				<p>It must have a name portion before the '@' and a domain portion after.</p>'''

	splitEmail = emailString.split('@') #If the above check passed, we have a name portion, @ sign, and domain portion.

	namePortion = ""
	domainPortion = ""

	if len(splitEmail) > 0:
		namePortion = splitEmail[0]
	if len(splitEmail) > 1:
		domainPortion = splitEmail[1]

	error += domainChecker(domainPortion)
	error += nameChecker(namePortion)

	if len(error > 0):
		print(error)
		return False
	else:
		return True

def domainChecker(domainPortion):
	#Here are the rules (these have been updated, but I'll go with these for starters):
	#1.  Can have alphanumerics.
	#2.  Can have dashes '-', but they cannot be the first or last character.
	#3.  Must have at least a top and bottom level domain:
	#		For instance, in gmail.com, "com" is the top level and "gmail" is the bottom level.
	#		This means that there will be at least one '.' (period), though there could be more.
	#4.  Each level must be at least 3 characters, and none of the levels can be more than 63 characters.
	#5.  This validator fails if there are more than four levels in the domain part of the email address.  TODO: Is there an authoritative rule?
	domainError = ""
	if len(domainPortion) == 0:
		return "<p>Your email address must include a domain portion</p>"

	if re.match('^[A-Za-z0-9-.]+$', domainPortion) != None:
		domainError += "<p>Your fully qualified domain name should only have alphanumeric characters, dashes, and periods.</p>"

	if domainPortion[0] == '-' or domainPortion[len(domainPortion) - 1] == '-':
		domainError += "<p>Dashes must not be the first or last characters.</p>"

	#If there are periods with text around them, check the levels:
	if re.match('^[A-Za-z0-9-.]+.[A-Za-z0-9-.]+$', emailString) != None:
		levels = domainPortion.split['.']
		if len(levels) < 1 or len(levels) > 4:  #TODO:  Find the authoritative rule on number of TLDs allowed.
			domainError += "<p>You must have between one and four levels to the domain name (TLDs).</p>" 
		else:
			for level in level:
				if len(level) > 63:
					domainError += "<p>No domain level may have more than 63 characters</p>"
					#domainError += "<p>The level which breaks that rule is: " + level[0:62] + "...</p>"

	#Finally, I will do a domain name server check using dnspython.  I will tell the user if there's no email server detected on that domain.
	answers = dns.resolver.query(domainPortion, 'MX')  #pyDNS also has methods for stuff like this.
	if len(answers) <= 0:
		domainError += "<p>That domain does not seem to have an email server.  A DNS resolution failed to find MX records."

	return domainError

def nameChecker(namePortion):
	nameError = ""
	#Here I check the local-part (the part before the '@' sign) of the email address.  
	#Local-Part Rules:
	#1.  The local part cannot have more than 64 characters.
	#2.  It cannot have the period '.' as the first or last character.
	#3.  It can have alphanumerics and these special characters (and nothing else):
	#         !#$%&'*+-/=?^_`{|}~    
	#Converter:  http://www.rapidtables.com/code/text/ascii-table.htm
	#These are their ASCII codes: \x21 \x23 \x24 \x25 \x26 \x27 \x2A \x2B \2D \x2F \x3D \? \x5E
	#\x5F \x7B \x7C \x7D \x7E
	#Regex attempt:  "^[A-Za-z0-9.\x21\x23-\x27\x2A\x2B\x2D\x2F\x3D\?\x5E\x5F\x7B\x7C-\x7E]+$"

	#4.  It can also have the '.' (period, ASCII 46) character, 
	#		but the period can't be the first or last character or be repeated consecutively.
	#5.  I am not going to allow quotes in the email address as I have 6 days left to do 2 more assignments after this one.

	if re.match("^[^A-Za-z0-9.\x33\x35-\x39\x42\x43\x45\x47\x61\x63\x94-\x96\x123-\x126]+$", namePortion) != None:
		nameError += "<p>The name portion of the email address can only contain the following types of characters: alphanumerics, periods, and the following special chars: `\~\!\@\#\$\%\^\&\*\_\-+/=\?\{\}\|</p>"
		
	return nameError
	
if __name__ == "__main__":
	app.run()

#TODO:  Implement this section as a replacement or addition to the email validation later.
	#I want the user to use their email address.  This will serve as their user name.
	#This is how I would normally do this, if this wasn't an exercise designed to get down and dirty with regex:
	#1.  First the user enters an email, I use the validate_email module to check whether it follows email addr rules.
	#2.  I use validate_email the second time to make sure the server is really an email server.
	#3.  I use validate_email to query the server (without sending an email) to see if the email exists.
	#4.  I create the user record with column IsConfirmed set to false.
	#5.  I send an email to the address asking for confirmation, with a random code, which I store in the user record.
	#6.  The user hits my server at the /confirmEmail, enters the code - if it is correct, I set IsConfirmed to true.
	
	#Here's Python's built-in validator module:
	#if (validate_email(username)):  #checks against email format rules.
	#	if (validate_email(username), check_mx=true):  #check the domain to make sure it has an email server (by querying for an MX response)
	#		if (validate_email('example@example.com',verify=True)):
	#			print("Yay - it's a valid email, but I can't use this method because they want me to struggle with the notorious regex email problem.")
