from flask import Flask, render_template, request, make_response, redirect
import sqlite3
import secrets

connection = sqlite3.connect('maindb.db')
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS loginInfo ( username varchar(255), password varchar(255) )")
cursor.execute("CREATE TABLE IF NOT EXISTS authTokenList ( authToken varchar(255), username varchar(255) )")
cursor.execute("CREATE TABLE IF NOT EXISTS messageList ( timestamp FLOAT, username varchar(255), message varchar(255) )")
cursor.execute("DELETE FROM authTokenList")
connection.commit()
connection.close()

app = Flask(__name__)

def generate_cookie(username):
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()

    response = make_response(render_template('chat.html'), 200)
    authToken = secrets.token_bytes(16).hex()

    response.set_cookie('authCookie', authToken)
    cursor.execute("SELECT * FROM authTokenList WHERE username = ?", (username,))
    fetched = cursor.fetchall()
    if (fetched == []):
        cursor.execute("INSERT INTO authTokenList (authToken, username) VALUES (?, ?)", (authToken, username))
    else:
        cursor.execute("UPDATE authTokenList SET authToken = ? WHERE username = ?", (authToken, username))
    
    conn.commit()
    conn.close()
    return response

def authorize(authToken):
    if authToken == None:
        return None
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM authTokenList WHERE authToken = ?", (authToken,))
    fetched = cursor.fetchall()
    if fetched == []:
        return None
    return fetched[0][1]

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

@app.route("/")
def index():
    username = authorize(request.cookies.get("authCookie"))
    if username == None:
        return render_template('login.html', auth='')
    else:
        return render_template('chat.html')
    
@app.route("/login", methods=["POST"])
def login():
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()

    username = request.form['username']
    password = request.form['password']

    cursor.execute("SELECT * FROM loginInfo WHERE username = ? AND password = ?", (username, password))
    fetched = cursor.fetchall()

    conn.commit()
    conn.close()

    if fetched != []:
        response = generate_cookie(username)
        #debug_database()
        return response
    else:
        return render_template('login.html', auth='Login Failed')

@app.route("/signup.html")
def signup_page():
    return render_template('signup.html', userexists='')

@app.route("/signup", methods=["POST"])
def signup():
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()

    username = request.form['username']
    password = request.form['password']

    cursor.execute("SELECT * FROM loginInfo WHERE username = ?", (username,))
    if (cursor.fetchall() != []):
        conn.commit()
        conn.close()

        return render_template('signup.html', existsalready='User exists already')
    else:
        cursor.execute("INSERT INTO loginInfo (username, password) VALUES (?, ?)", (username, password))

        conn.commit()
        conn.close()

        response = generate_cookie(username)
        #debug_database()

        return response

if __name__ == '__main__':
    app.run(debug=True)
