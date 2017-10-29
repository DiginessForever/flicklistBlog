from werkzeug.security import generate_password_hash

def connect(mysql):
	try:
		connection = mysql.get_db()
		cursor = mysql.connect().cursor()
		return cursor
	except Exception as e:
		print("There was a problem connecting to MySQL: " + str(e))
		return None

#Returns true if username/passwordHash combo exists in database.
#Get a cursor first using connect(), then pass it into this method.  Separating the functionality this way lets me keep error messages in one place.
def authenticateUser(mysql, username, password, existenceOnly):  #takes a mysql database context, username(email address), and password.
	pwHash = passwordHash(password)
	cursor = connect(mysql)
	
	if cursor != None:
		try:
			cursor.execute("select * from user;")  #user table format: userid, username, password  #TODO:  Add: confirmationToken, isConfirmed, csrfToken, tokenTimestamp
			sqlResponseData = cursor.fetchall()

			for row in sqlResponseData:
				if row[1] == username:
					if existenceOnly:
						return True
					if row[2] == pwHash:
						return True
					print("Username matched, but password did not.")
			return False
		except Exception as e:
			print("Problem authenticating user against database: " + str(e))
			return False
	else:
		return "We are experiencing technical difficulties with the database.  Please try again later."

def createUser(mysql, username, password):
	cursor = connect(mysql)
	
	if cursor != None:
		try:
			cursor.execute("INSERT INTO USER (username, password) VALUES ('" + str(username) + "','" + str(passwordHash(password)) + "');")
			connection.commit()
			return True
		except Exception as e:
			print("Problem creating user: " + str(e))
			return False
	else:
		return "We are experiencing technical difficulties with the database.  Please try again later."

def passwordHash(password):
	return generate_password_hash(password)