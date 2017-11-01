from flask import Flask, render_template, request, redirect, jsonify
import requests
import json
#from flaskext.mysql import MySQL #has to be installed outside of conda, but is accessible while in the source env.
#from databaseHelper import * #This had the flask-mysql methods -moved to databaseHelper.py.bak - I stopped using it.
#mysql = MySQL()  #This was also needed for flask-mysql
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import mapper #, Query
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.automap import automap_base
#import sqlalchemy
  
app = Flask(__name__)

with open('config') as data_file:
	data = json.load(data_file)
	#This data file must be a text file named "config" in the same folder as app.py
    #I am not committing it to github for security reasons because I use a cloud database.
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
	#sessionTokenSecuritySigningString = data["sessionTokenSecuritySigningString"]

#These are the old configure statements for when I was using flask-mysql:
#app.config['MYSQL_DATABASE_USER'] = dbUser
#app.config['MYSQL_DATABASE_PASSWORD'] = dbPass
#app.config['MYSQL_DATABASE_DB'] = dbName
#app.config['MYSQL_DATABASE_HOST'] = dbAddress
#mysql.init_app(app)

#-------------------
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://" + dbUser + ":" + dbPass + "@" + dbAddress + ":3306/" + dbName
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app)
engine = db.engine
db.Model.metadata.reflect(bind=engine)
meta = db.metadata

db_session = scoped_session(
    sessionmaker(
        autocommit=True, autoflush=True, bind=engine
    )
)

Base = automap_base()
Base.prepare(engine, reflect=True)

User = Base.classes.user


#class User(db.Model):
class User(Base.classes.user):
    #Removing the model properties: 
    #found an article about database table automapping.
    #If I do that, I won't have to manually change the User model's properties when I change the database table!
    #http://docs.sqlalchemy.org/en/latest/core/reflection.html

    # id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # username = db.Column(db.String(20), nullable=False)
    # password = db.Column(db.String(120), nullable=False)
    # sessionToken = db.Column(db.String(15))
    # overallBlogTitle = db.Column(db.String(256))
    # email = db.Column(db.String((256)))
    
    def __init__(self, db, username, password, email):
        #Autoload the properties from the database
        #TODO:  Is engine the same thing as db above, or does it need to be instantiated separately?
        #try:
            #self = db.Model.metadata.tables('user', meta)
            #Table('user', metadata, autoload_with=engine, extend_existing=True)
            #self = Tadb.Model.metadata.tables('user', meta, autoload=True, autoload_with=engine, extend_existing=True)
            #self = Table('user', meta, autoload_with=engine, extend_existing=True)
            #self.metadata.reflect(extend_existing=True, only=['user'])
        #except Exception as e:
        #    print("In init User(): failed to map table user - " + str(e))
        try:
            self = db.session.query(User).filter_by(username=username).one()
        except Exception as e:
            print("In init User():  Failed to load an existing user into the model for user '" + username + "' " + str(e))
        self.usernam=username
        self.password=password
        self.emailAddress=emailAddress
        try:
            db.session.add(self)
            db.session.commit()
            print("In init User():  Inserted or updated user '" + username + "'")
            return True
        except Exception as e:
            print("In init User(): insert or update exception on user '" + username + "': " + str(e))
            return False
        
    def delete(db):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            print("In User.delete(): failed to delete userid '" + self.userid + "', username '" + self.username + "': " + str(e))
    
    def getAllUsers(db):
        return User.query.all()

    #Setting this to blank would "logout" the user.
    #This is because csrf_protect prevents POST requests from going through other
    #than login and signup.
    def updateSessionToken(db, userid, token):
        try:
            self = User.query.get(userid)
            self.sessionToken = token
            db.session.add(self)
            db.session.commit()
            print("In User.updateSessionToken(): Successfully updated the token for userid '" + userid + "'.")
            return True
        except Exception as e:
            print("In User.updateSessionToken() failed to update token: " + str(e))
            return False

    def checkSessionToken(db, userid, givenToken):
        user = User.query.get(userid)
        if user:
            if user.sessionToken == givenToken:
                print("In User.checkSessionToken():  token match confirmed for userid '" + user.userid + "', username '" + user.username + "'.")
                return True
            else:
                print("In checkSessionToken() - token and given token do not match")
        else:
            print("In checkSessionToken() - user by given id '" + userid + "' not found.")
        return False

    def logout(db, userid):
        updateSessionToken(db, userid, "")
    
    def authenticate(db, username, password):
        users = User.query.filter_by(username=username).all()
        if users == None:
            print("In User.authenticate(): failed to get a list object from DB for user '" + username + "'.")
        if len(users) == 0:
            print("In User.authenticate):  Username '" + username + "' does not exist in the database.")
            return False, None
        if len(users) == 1:
            #Called it this because hashes will many times be different every time you generate one from a string.
            anotherPasswordHash = generate_password_hash(password)
            if check_password_hash(users[0].password, anotherPasswordHash):
                print("In User.authenticate(): check of password hashes confirmed username '" + username + "'.")
                return True, users[0]
            else:
                print("In User.authenticate():  User '" + username + "' failed the password check.")
                return False, None
        if len(users) > 1:
            print("In User.authenticate():  More than one user with username of '" + username + "'")
            return False, None
        print("In User.authenticate(): Strange: [users list is not None, and not a list] here it is: '" + str(users) + "' for user '" + username + "'")
        return False, None

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    userid = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(20), nullable=False) #I know this is not normalized, but I don't want to query across.
    postTitle = db.Column(db.String(256), nullable=False)
    postText = db.Column(db.String(5000), nullable=False)

    def __init__(self, db, userid, username, postTitle, postText):
        self.userid=userid
        self.username=username
        self.postTitle=postTitle
        self.postText=postText
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            print("BlogPost() constructor db save exception: " + str(e))
            return False   

    def delete(db):
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            print("BlogPost delete exception: " + str(e))
            return False

    def getBlogPostById(db, postId):
        self = BlogPost.query.get(postId)

    def updatePost(db, postId, postTitle, postText):
        self = BlogPost.query.get(postId)
        self.postTitle = postTitle
        self.postText = postText
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            print("BlogPost update exception: " + str(e))
            return False
    
    def getAllBlogPosts(db):
        return BlogPost.query.all()
    
    #Ugly, but I'm not that good at SQLAlchemy yet:
    def getUsersWithPosts(db):
        blogs = BlogPost.query.filter_by(userid=userid).all()
        userNameDict = {}
        for blog in blogs:
            userNameDict[blog.username] = blog.userid
        return sorted(userNameDict)