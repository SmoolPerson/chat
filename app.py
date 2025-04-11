from flask import Flask, render_template, request, make_response, redirect
import sqlite3
import secrets
import hashlib

connection = sqlite3.connect('maindb.db')
cursor = connection.cursor()
# create the main tables for the program
cursor.execute("CREATE TABLE IF NOT EXISTS loginInfo ( username varchar(255), password varchar(255) )")
cursor.execute("CREATE TABLE IF NOT EXISTS authTokenList ( authToken varchar(255), username varchar(255) )")
cursor.execute("CREATE TABLE IF NOT EXISTS messageList ( timestamp FLOAT, username varchar(255), message varchar(255) )")
cursor.execute("DELETE FROM authTokenList")
connection.commit()
connection.close()

app = Flask(__name__)

# generate sha256 hash with hashlib
def generate_sha256_hash(input_string):
    encoded_string = input_string.encode('utf-8')
    sha256_hash = hashlib.sha256(encoded_string)
    hex_digest = sha256_hash.hexdigest()
    return hex_digest

# generates a request with a authentication cookie for the user
def generate_cookie(username):
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()

    response = make_response(render_template('chat.html'), 200)
    authToken = secrets.token_bytes(16).hex() # 16 random bytes are generated for the cookie

    response.set_cookie('authCookie', authToken)
    # check if a user already exists on the cookie db
    cursor.execute("SELECT * FROM authTokenList WHERE username = ?", (username,)) 
    fetched = cursor.fetchall()
    if (fetched == []):
        # insert record into list
        cursor.execute("INSERT INTO authTokenList (authToken, username) VALUES (?, ?)", (authToken, username))
    else:
        # update record in list
        cursor.execute("UPDATE authTokenList SET authToken = ? WHERE username = ?", (authToken, username))
    
    conn.commit()
    conn.close()
    return response

# takes an authtoken and returns the username if it is, and None if it doesnt exist
def authorize(authToken):
    if authToken == None: # if the parameter is None, then obviously the username is also none
        return None
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    # find username in authtoken
    cursor.execute("SELECT * FROM authTokenList WHERE authToken = ?", (authToken,))
    fetched = cursor.fetchall()
    if fetched == []: # if no username exists, return none
        return None
    return fetched[0][1]

# print debug info from db
def debug_database():
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM authTokenList")
    print("authTokenDatabase: ", cursor.fetchall())
    cursor.execute("SELECT * FROM loginInfo")
    print("loginInfoDatabase: ", cursor.fetchall())
    cursor.execute("SELECT * FROM messageList")
    db = cursor.fetchall()
    print("messageListDatabase: ", db)
    print("Length of messageList: ", len(db))
    conn.commit()
    conn.close()

# display login page and autologin user
@app.route("/")
def index():
    # authorize, auto redirect to chat.html if cookie is valid
    username = authorize(request.cookies.get("authCookie"))
    if username == None:
        return render_template('login.html', auth='')
    else:
        return render_template('chat.html')
    

# handle logic for logging in
@app.route("/chat", methods=["POST"])
def login():
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()

    username = request.form['username']
    password = request.form['password']
    # hash pw before comparing
    hashedpw = generate_sha256_hash(password)
    cursor.execute("SELECT * FROM loginInfo WHERE username = ? AND password = ?", (username, hashedpw))
    fetched = cursor.fetchall()

    conn.commit()
    conn.close()
    # if fetch does not equal [] then that means a record exists in the list
    if fetched != []:
        response = generate_cookie(username)
        #debug_database()
        return response
    else:
        return render_template('login.html', auth='Login Failed')

# render signup page
@app.route("/signup.html")
def signup_page():
    return render_template('signup.html', userexists='')

# handle logic for signing up
@app.route("/signup", methods=["POST"])
def signup():
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()

    username = request.form['username']
    password = request.form['password']
    hashedpw = generate_sha256_hash(password) # hash password
    cursor.execute("SELECT * FROM loginInfo WHERE username = ?", (username,))
    if (cursor.fetchall() != []): # if the list is not empty, the username is alrady in loginInfo
        conn.commit()
        conn.close()

        return render_template('signup.html', existsalready='User exists already')
    else:
        # insert into loginInfo the username/password
        cursor.execute("INSERT INTO loginInfo (username, password) VALUES (?, ?)", (username, hashedpw))

        conn.commit()
        conn.close()

        response = generate_cookie(username)
        #debug_database()

        return response

if __name__ == '__main__':
    app.run(debug=True)
