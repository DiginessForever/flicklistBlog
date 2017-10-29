from flask import Flask, render_template, request, redirect #jsonify
import requests
from flask import Flask
from flaskext.mysql import MySQL
import re
import json
import dns.resolver  #must install dnspython to get this (from command line:  "pip install dnspython" OR "conda install dnspython")
from databaseHelper import * #this is my helper class with the database query methods
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
	dbAddress = data["dbAddress"]
	dbName = data["dbName"]
	dbUser = data["dbUser"]
	dbPass = data["dbPass"]

app.config['MYSQL_DATABASE_USER'] = dbUser
app.config['MYSQL_DATABASE_PASSWORD'] = dbPass
app.config['MYSQL_DATABASE_DB'] = dbName
app.config['MYSQL_DATABASE_HOST'] = dbAddress
mysql.init_app(app)


@app.route("/")  #Put this in your browser URL: http://localhost:5000/
def main():
	#Template html pages are in the templates sub folder.
	return render_template('login.html')


#TODO:  Make button on login page that redirects to register page.
#TODO:  Create the user at the registration page.
@app.route("/login", methods=['POST'])   #http://localhost:5000/login
def login():
	username = request.form['username']
	password = request.form['password']
	error = ""

	if authenticateUser(mysql, username, password, False):  #this method is in databaseHelper.py
		#TODO render the mainPage template here.  It should later have a csrf token and userid.
		return "<!DOCTYPE html><html><body><p>Welcome to the system.</p></body></html>"
	else:  
		error = "<p>Sorry - either that username does not exist or the password is incorrect.</p>"
		return render_template("login.html", error=error)


@app.route("/register", methods=["GET"])
def register():
	return render_template("register.html")


@app.route("/handleRegistration", methods=["POST"])
def handleRegistration():
	#TODO  Create a registration page template in the templates folder.
	error = ""
	username = request.form["username"]
	emailAddress = request.form['emailAddress']
	password = request.form['password']
	verifyPassword = request.form['verifyPassword']

	if re.match("^[^\s]{3,20}$", username) == None:
		print("Username spaces or length error.")
		usernameError = "Your username should not contain spaces and should be 3-20 characters long."
		return render_template("register.html", usernameError=usernameError,
			username=username, emailAddress=emailAddress)

	if authenticateUser(mysql, username, password, True) == True:  #method is in databaseHelper.py
		#TODO:  The user may forget their password, have two methods supporting pass reset.
		print("username exists")
		return render_template("register.html", 
			userNameError="That username already exists. Please pick a different username.",
			username=username,
			emailAddress=emailAddress)

	error = isValidPassword(password, verifyPassword)
	if len(error) > 0:
		print("password spaces, length, or verification error")
		return render_template("register.html", passwordError=error, username=username, emailAddress=emailAddress)

	if len(emailAddress) > 0:
		error = isValidEmail(emailAddress)
		if len(error) > 0:
			print("Email address validation error.")
			return render_template("register.html", username=username, emailaddress=emailAddress,
				emailAddressError=error)	

	if createUser(mysql, username, password, emailAddress):  #This method is in databaseHelper.py.
		#return render_template("login.html", error="Thank you for signing up.  Please login.")
		return "<!DOCTYPE html><html><body>Welcome " + username + "!</body></html>"  #Bah humbug!
	else:
		print("Create user error.")
		return render_template("register.html", error="We are experiencing technical difficulties.  Please try again later.")


#If the user insists that their email address is real, I will try to send an email to it anyway, regardless of checks failing.
#If they can perform the verification step, I know they can see the email, so the email address must exist.
#This method will try to send emails to those email address which fail the checks...
@app.route("/itsAReallyMeMario", methods=["POST"])
def itsAReallyMeMario():
	print("itsAReallyMeMario:  Not implemented error")


def isValidPassword(password, password2):
	error = ""
	if re.match("^[^\s]{3,20}$", password) == None:
		error += "Your password should not contain spaces and be 3-20 characters long."
	if password != password2:
		error += "Your password verification does not match the password."
	return error


#TODO: Extend the rules to implement RFC 6531: https://tools.ietf.org/html/rfc6531 (In order to support all the characters used in the world)
#TODO: Add more logic to allow quotes.
def isValidEmail(emailString):
	splitEmail = ""
	namePortion = ""
	domainPortion = ""
	error = ""

	#This makes sure there is only one '@' sign, and that it has characters before and after it.
	atSignError = False
	if re.match('^[^@]+@[^@]+$', emailString) == None:
		atSignError = True
		error = '''You can only have one '@' sign in your email address.  It must have a name portion before the '@' and a domain portion after.'''
	else:
		if re.match("^[^\s]{1,256}$", emailString) == None:
			error += "Please limit your email address to no more than 256 characters in length.  Also, no spaces.  Thank you."
		splitEmail = emailString.split('@') #If the above check passed, we have a name portion, @ sign, and domain portion.
		namePortion = splitEmail[0]
		domainPortion = splitEmail[1]
		error += domainChecker(domainPortion)
		error += nameChecker(namePortion)

	return error


#Here are the rules (these have been updated, but I'll go with these for starters):
#1.  Can have alphanumerics.
#2.  Can have dashes '-', but they cannot be the first or last character.
#3.  Must have at least a top and bottom level domain:
#		For instance, in gmail.com, "com" is the top level and "gmail" is the bottom level.
#		This means that there will be at least one '.' (period), though there could be more.
#4.  Each level must be at least 3 characters, and none of the levels can be more than 63 characters.
#5.  This validator fails if there are more than four levels in the domain part of the email address.
#TODO: Is there an authoritative rule for #5?
def domainChecker(domainPortion):
	domainError = ""
	if len(domainPortion) == 0:
		return "<p>Your email address must include a domain portion</p>"
	else:
		if re.match('^[^A-Za-z0-9-.]+$', domainPortion) != None:
			domainError += "<p>Your fully qualified domain name should only have alphanumeric characters, dashes, and periods.</p>"

		if domainPortion[0] == '-' or domainPortion[len(domainPortion) - 1] == '-':
			domainError += "<p>Dashes must not be the first or last characters.</p>"

		#If there are periods with text around them, check the levels:
		if re.match('^[A-Za-z0-9-.]+.[A-Za-z0-9-.]+$', domainPortion) != None:
			levels = domainPortion.split('.')
			if len(levels) < 1 or len(levels) > 4:  #TODO:  Find the authoritative rule on number of TLDs allowed.
				domainError += "You must have between one and four levels to the domain name (TLDs)." 
			else:
				for level in levels:
					if len(level) > 63:
						domainError += "No domain level may have more than 63 characters"
						#domainError += "<p>The level which breaks that rule is: " + level[0:62] + "...</p>"

		#Finally, I will do a domain name server check using dnspython.  I will tell the user if there's no email server detected on that domain.
		answers = ""
		try:
			answers = dns.resolver.query(domainPortion, 'MX')  #pyDNS also has methods for stuff like this.
		except dns.resolver.NXDOMAIN:
			domainError += "Domain not found."
		except Exception as e:
			print("Problem resolving to email server: " + str(e))
		if len(answers) == 0:
			domainError += "That domain does not seem to have an email server.  A DNS resolution failed to find MX records."

	return domainError


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
def nameChecker(namePortion):
	nameError = ""

	if re.match("^[^A-Za-z0-9.\x21\x23-\x27\x2A\x2B\x2D\x2F\x3D\?\`\x5E\x5F\x7B\x7C-\x7E]+$", namePortion) != None:
		nameError += '''<p>The name portion of the email address can only contain the following types of characters: alphanumerics, periods,
					 and the following special chars: \`\~\!\@\#\$\%\^\&\*\_\-+/=\?\{\}\|</p>'''

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

#TODO:  Consider all the characters that need to be escaped...where do they need to be escaped?  I think I will HTML escape them by going over every
#		value coming into the system and replacing those characters with escaped characters.  I will then need to perform email tests using the escaped
#		characters, and if they don't work, unescape that character set when sending to email addresses with those in the address.
#		" ' < > & ` , ! @ $ % ( ) = + { } [ ] and space(which can be used to break out of an unquoted HTML attribute value)
#		& = &amp;
#		< = &lt;
#		> = &gt;
#		" = &quot;
#		' = &#39;
#		http://www.theukwebdesigncompany.com/articles/entity-escape-characters.php
#		Always specify a charset so you don't get UTF-7.  If the attacker can get IE to render in UTF-7, you're done.
#		Specify UTF-8 in both HTTP response headers and <meta> tag.
