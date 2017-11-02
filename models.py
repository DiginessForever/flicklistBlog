from werkzeug.security import check_password_hash, generate_password_hash
import requests
import json
from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy

  
app = Flask(__name__)
#The file I am importing below is named config and is in the same folder as app.py.
#It has json formatted text and looks like this (without the '#' signs, and remove the <> signs that surround
#the places you need to insert the db address, username, password, and database name (instance name - 
#database servers can have multiple databases on them, each one is called an instance / has a different name))
#{
#"dbAddress" = "<some IP or URL to your database server>",
#"dbName" = "<database name>",
#"dbUser" = "<database user name>",
#"dbPass" = "<dbPass>"
#}
with open('config') as data_file:
	data = json.load(data_file)
	dbAddress = data["dbAddress"]
	dbName = data["dbName"]
	dbUser = data["dbUser"]
	dbPass = data["dbPass"]
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://" + dbUser + ":" + dbPass + "@" + dbAddress + ":3306/" + dbName
app.config["SQLALCHEMY_ECHO"] = True


db = SQLAlchemy(app)
db.Model.metadata.reflect(bind=db.engine)


class User(db.Model):
    __tablename__ = 'user'

    def __init__(self, db, username, password, email):
        try:
            self = db.session.query(User).filter(User.username==username) #.one()
        except Exception as e:
            print("In init User():  Failed to load an existing user into the model for user '" + username + "' " + str(e))
        self.username=username
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
        

    def delete(db, userid):
        try:
            self = db.session.query(User).filter(User.id == userid).one()
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            print("In User.delete(): failed to delete userid '" + self.id + "', username '" + self.username + "': " + str(e))
    

    def getAllUsers(db):
        return db.session.query(User).all()


    #Setting this to blank would "logout" the user.
    #This is because csrf_protect prevents POST requests from going through other
    #than login and signup.
    def updateSessionToken(db, userid, token):
        try:
            self = db.session.query(User).filter(User.id == userid).one()
            self.sessionToken = token
            db.session.add(self)
            db.session.commit()
            print("In User.updateSessionToken(): Successfully updated the token for userid '" + userid + "'.")
            return True
        except Exception as e:
            print("In User.updateSessionToken() failed to update token: " + str(e))
            return False


    def checkSessionToken(db, userid, givenToken):
        try:
            user = db.session.query(User).filter(User.id == userid).one()
        except Exception as e:
            print("In checkSessionToken(): issue looking up userid: " + userid + ": " + str(e))
        if user:
            if user.sessionToken == givenToken:
                print("In User.checkSessionToken():  token match confirmed for userid '" + user.id + "', username '" + user.username + "'.")
                return True
            else:
                print("In checkSessionToken() - token and given token do not match")
        else:
            print("In checkSessionToken() - user by given id '" + userid + "' not found.")
        return False


    def logout(db, userid):
        updateSessionToken(db, userid, "")
    

    def authenticate(db, username, password):
        try:
            user = db.session.query(User).filter(User.username == username).one() #User.query.filter_by(username=username).all()
        except Exception as e:
            print("User.authenticate: User '" + username + ": " + str(e))
            return False, None
        if user.password == password:
            print("User.authenticate: User '" + username + "': login succeeded.")
            return True, user
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
    

    def getUsersWithPosts(db):
        blogs = BlogPost.query.filter_by(userid=userid).all()
        userNameDict = {}
        for blog in blogs:
            userNameDict[blog.username] = blog.userid
        return sorted(userNameDict)