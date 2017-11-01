from werkzeug.security import check_password_hash
import time


#TODO:  Mentorship - divide this into digestable parts to introduce each section:
#			-- SQL queries:  SELECT * FROM <table> WHERE
#			-- SQL inserts:  INSERT INTO <table> (column1, column2) VALUES (value1, value2)
#			-- How to handle the connection (shown in insert() currently)
#		Change the README.md at the flicklistBlog github repo to include instructions on
#			installing Flask and Flask-MySQL.

#TODO:  Refactor:  Once all methods are using query() or insert(), get rid of this method.


def connect(mysql):
	try:
		connection = mysql.connect()
		cursor = mysql.connect().cursor()
		return cursor, connection
	except Exception as e:
		print("There was a problem connecting to MySQL: " + str(e))
		return None


def query(mysql, queryTxt):
	try:
		connection = mysql.connect()
		cursor = connection.cursor()
		data = []
		try:
			cursor.execute(queryTxt)
			cursor.execute(queryTxt)
			data = cursor.fetchall()
			connection.close()
			return data
		except Exception as e:
			connection.close()
			print("Problem inserting into db: " + str(e))
			return "We experienced a problem requesting that information from the database.  Please try again later."
	except Exception as f:
		print("Problem getting a db connection or cursor: " + str(f))
		return "We are experiencing a database outage.  Please try again later."


#TODO:  Refactor this and all methods calling, handle the user feedback text here.
def insert(mysql, insertCmd):
	try:
		connection = mysql.connect()
		cursor = connection.cursor()
		try:
			cursor.execute(insertCmd)
			connection.commit()
			connection.close() #TODO: Test
			return True
		except Exception as e:
			print("Problem inserting into db: " + str(e))
			connection.rollback()
			return False
	except Exception as f:
		print("Problem getting a db connection or cursor: " + str(f))
		return False


#Returns true if username/passwordHash combo exists in database.
#TODO:  Refactor to use the query() method, will reduce code length - DRY principle.
def authenticateUser(mysql, username, password, checkExistenceOnly):
	cursor, connection = connect(mysql)  #TODO test
	
	if cursor != None:
		try:
			cursor.execute("select * from user;")
			sqlResponseData = cursor.fetchall()

			for row in sqlResponseData:
				if row[1] == username:
					if checkExistenceOnly:
						return True
					if check_password_hash(row[2], password):
						return True
			connection.close()
			return False
		except Exception as e:
			print("Problem authenticating user against database: " + str(e))
			connection.close()
			return False
	else:
		connection.close()
		return "We are experiencing technical difficulties with the database.  Please try again later."


def createUser(mysql, username, passwordHash, emailAddress):
	if emailAddress == "":
		emailAddress = "null"
	else:
		emailAddress = "'" + emailAddress + "'"

	query = "INSERT INTO user (username, password, emailaddress) VALUES ('"
	query += username + "','" + passwordHash + "'," + emailAddress #+ "','" 
	#TODO:  Figure out how to pass dates successfully to MySQL:
	#query += time.strftime('%Y-%m-%d %H:%M:%S')	
	query += ");"
	print(query)

	return insert(mysql, query)

def getUserid(mysql, username):
	queryString="SELECT id FROM user WHERE username='" + username + "';"
	data = query(mysql, queryString)

	for row in data:
		return row[0]
	return ""


def updateSessionToken(mysql, thisUserid, sessionToken):
	print("In updateSessionTOken() - session token: " + str(sessionToken))
	try:
		cursor, connection = connect(mysql)
		cursor.execute("""UPDATE user SET sessionToken='%s' WHERE id='%s'""", (sessionToken, thisUserid))
		connection.commit()
		connection.close()
	except Exception as e:
		print("Exception in updateSessionToken(): " + str(e))
		return False
	print("leaving updateSessionToken()")
	return True


def checkDBsessionToken(mysql, sessionToken, userid):
	queryStr = "SELECT sessionToken FROM user WHERE id = '" + str(userid) + "';"
	data = query(queryStr)
	for row in data:
		if row[0] == sessionToken:
			return True
		print("checkDBsessionToken() check for user " + str(userid) + " given token " + str(sessionToken) + " failed to match " + row[0])
	print("checkDBsessionToken failed on user " + str(userid) + ", givenToken " + str(sessionToken))
	return False


def createBlogPost(mysql, userid, postTitle, postText):
	#TODO: Text this
	queryStr += "INSERT INTO blogPost (userid, postTitle, postText) VALUES ('"
	queryStr += str(userid) + "','" + postTitle + "','" + postText + "');"
	print(query)
		
	if insert(mysql, queryStr):
		return True
	else:
		return False


def getBlogPost(mysql, postId):
	queryStr = "SELECT * from blogPost WHERE id = '" + str(postId) + "';"
	data = query(queryStr)
	return data


def getBlogList(mysql):
	#TODO:  Test this
	queryStr = "SELECT id, overallBlogTitle FROM user WHERE id in (SELECT userid FROM blogPost);"
	return query(mysql, queryStr) #Will not return a row for users who have not put up a blog post yet.


def getAuthorsBlogList(mysql, userid):
	#TODO:  Test this
	queryStr = "SELECT postTitle, postText FROM blogPost where userid = '" + str(userid) + "';"
	return query(mysql, queryStr)


def getUsernamesAndUseridsWithBlogPosts(mysql):
	queryStr = "SELECT username, id FROM user WHERE id in (SELECT userid FROM blogPost);"
	data = query(mysql, queryStr)
	usernameDict = {}
	for row in data:
		usernameDict[row[0]] = row[1]
	return sorted(usernameDict)