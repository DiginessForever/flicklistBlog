Instructions:
1.  Install miniconda3.
https://conda.io/miniconda.html   (Choose the installer with Python 3.6 or higher)
2.  Install git (Windows only - other OSs sensibly already come with git installed)
https://git-scm.com/  (if you are on Mac or Linux, you already have git)
When git is installed, run git-bash -> it will open up a command window.  All commands below (other than the SQL
commands) will be entered into this git-bash window.
3.  Install MySQL and MySQL Workbench
https://dev.mysql.com/downloads/installer/  (if on Linux, look up the apt-get install and configure process)
Alternatively, if you want a cheap cloud database server for $10/month (DigitalOcean), check out this step-by-step process for setting one up:  https://drive.google.com/file/d/0B5ZDoUi8N1MuN2Q0dFBSNWxaeVU/view
4.  Clone the repo (if you are on Windows, you will use git-bash to run the commands - it gets installed with git):
"git clone https://github.com/DiginessForever/flicklistBlog"  (This will copy this repo into a subdirectory named flicklistBLog in the directory you are currently in.  It will be ready for use with git.)
Navigate into that directory:  "cd flicklistBlog"
5.  Create a Conda/Python virtual environment with all required dependencies (and then some, I haven't pared it down yet):
"conda create --name <env> --file dependecies.txt"    (get rid of the <> characters and change "env" to whatever you want to call your environment)
6. Activate your virtual environment:
"source activate <env>" (once again, get rid of the <> characters, change env to whatever you called the environment)
7.  Start MySQL and MySQL Workbench.  Use MySQL Workbench to connect to MySQL (login with the root user you setup
when you installed MySQL).
Run these SQL commands from MySQL Workbench while connected to MySQL to create your database, user, and starting tables (each command ends in a ';' character):
"CREATE DATABASE database1;"
"USE database1;"
"CREATE user 'myfirstuser'@'%' IDENTIFIED by 'myfirstpassword';"
GRANT ALL PRIVILEGES ON *.* to 'myfirstuser'%'
GRANT ALL PRIVILEGES ON 'database1'.* TO 'myfirstuser'@'%'
GRANT ALL PRIVILEGES ON 'database1'.'property' TO 'myfirstuser'@'%'
"CREATE TABLE user (
    id int NOT NULL,
    username varchar(20) NOT NULL,
    password varchar(20) NOT NULL,
    sessionToken varchar(15) NULL,
    createdDate datetime NULL,
    lastRequest datetime NULL,
    emailAddress varchar(256) NULL,
    PRIMARY KEY(id)
);"
"CREATE TABLE blogpost (
    id int NOT NULL,
    userid int NOT NULL,
    postTitle varchar(256) NOT NULL,
    postText varchar(5000) NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(userid) REFERENCES user(id)
);"
"FLUSH PRIVILEGES;"
8.  Change line 25 of models.py to match your database.  If you are using MySQL on your own computer, it will look like this (for the above configured user/pass and database name):
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://myfirstuser:myfirstpassword@localhost:3306/database1"
9.  Start the application (enter this command from git-bash, from within the top level folder of the cloned repository):
"python app.py"
Wait until it says that it's listening.
10.  Open a browser an navigate to this address:  "localhost:5000/register"
You should be able to create new users here, and running the following command in MySQL Workbench should show them
in the database:
"SELECT * FROM user;"

Basic Explanation of the system:
Flask is a webserver and it listens by default on port 5000.  So that's where localhost:5000 comes from.
The "/register" portion of the above address comes from the @app.route statements above the Python methods in
the app.py file.  At the bare minimum in the method below one of these routes, you will have a
render_template() statement.  That will serve one of the html files in the templates sub-directory.

"/register" or "/login" are both routes that have only a render_template statement, so you can go to those pages first
from your browser.
If you look in templates/register.html, it has an html form in it.  The form's action parameter has the route that it
will call.  Check out app.py to find the @app.route statement that matches that.  Note that @app.route's methods must
include the method that register.html's form declares.
To pull the values from the form's input fields into the Python code, these statements are used:
someVariable = request.form["someInputFieldName"]

Next, SQLAlchemy is a library that is used to connect to the database.  Check out models.py for how this is done.
Note that there are two methods for defining classes (these match the database tables).  In User, I use the
automapper to pull the database column names into the class as properties.
In blogpost, I am declaring properties which I have to make sure match the blogpost table (I have not debugged through
this class yet, and it likely doesn't work currently).  I will probably change this to automapping like User.

If you want to see how I am connecting from the front methods to the database methods, check out the handleLogin()
method in app.py:
It gets the username and password from the login.html page's form.  It calls some validator methods to make sure
the user is entering enough characters, etc.  Then, it calls authenticate(), which is in the models.py file.
That method interacts with the database to make sure that username/password combination exists.