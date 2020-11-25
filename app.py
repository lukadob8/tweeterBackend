import mariadb
from flask import Flask, request, Response
import json
import dbcreds
from flask_cors import CORS
from uuid import uuid4

app = Flask(__name__)
CORS(app)

@app.route('/api/users', methods = ["GET", "POST", "PATCH", "DELETE"])
def userAction():
    if request.method == "GET":
        conn = None
        cursor = None
        userId = request.args.get("id")
        user = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            if userId != None:
                cursor.execute("SELECT * FROM users WHERE id=?", [userId])
            else:
                cursor.execute("SELECT * FROM users")
            user = cursor.fetchall()
        except Exception as error:
            print("SOMETHING WENT WRONG (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if user != None:
                return Response(json.dumps(user, default=str), mimetype="application/json", status=200)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)
    elif request.method == "POST":
        conn = None
        cursor = None
        email = request.json.get("email")
        username = request.json.get("username")
        password = request.json.get("password")
        bio = request.json.get("bio")
        birthdate = request.json.get("birthdate")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users(email, username, password, bio, birthdate) VALUES (?, ?, ?, ?, ?)", [email, username, password, bio, birthdate])  
            conn.commit()  
            rows = cursor.rowcount
            cursor.execute("SELECT id FROM users WHERE username=? AND password=?", [username, password])
            userId = cursor.fetchall()[0][0]
            loginToken = uuid4().hex
            cursor.execute("INSERT INTO user_session (userId, loginToken) VALUES (?, ?)", [userId, loginToken])
            conn.commit()
            session_rows = cursor.rowcount
            # cursor.execute("SELECT id, username, email, bio, birthdate FROM users WHERE id=?", [userId])
            # userData = cursor.fetchall()
        except Exception as error:
            print("SOMETHING WENT WRONG (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if rows == 1:
                return Response("User added!", mimetype="text/html", status=201)
            else:
                return Response("Failed to add user, an error occured.", mimetype="text/html", status=500)
            if session_rows == 1:
                return Response(json.dumps(loginToken, default=str), mimetype="application/json", status=201)
            else:
                return Response("Failed to create login token.", mimetype="text/html", status=500)
            # if userData != None:
            #     return Response(json.dumps(userData, default=str), mimetype="application/json", status=201)
            # else:
            #     return Response("There was an error.", mimetype="text/html", status=500)
    elif request.method == "PATCH":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        email = request.json.get("email")
        username = request.json.get("username")
        password = request.json.get("password")
        bio = request.json.get("bio")
        birthdate = request.json.get("birthdate")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            if email != "" and email != None:
                cursor.execute("UPDATE users SET email=? WHERE id=?", [email, userId])
            if username != "" and username != None:
                cursor.execute("UPDATE users SET username=? WHERE id=?", [username, userId])
            if password != "" and password != None:
                cursor.execute("UPDATE users SET password=? WHERE id=?", [password, userId])
            if bio != "" and bio != None:
                cursor.execute("UPDATE users SET bio=? WHERE id=?", [bio, userId])
            if birthdate != "" and birthdate != None:
                # cursor.execute("UPDATE users SET birthdate=? INNER JOIN user_session ON user_session.userId = users.id WHERE user_session.loginToken=?", [birthdate, loginToken])
                cursor.execute("UPDATE users SET birthdate=? WHERE id=?", [birthdate, userId])
            conn.commit()
            rows = cursor.rowcount
        except Exception as error:
            print("Something went wrong (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if rows == 1:
                return Response("Updated successfully!", mimetype="text/html", status=204)
            else:
                return Response("Failed to updated, something went wrong.", mimetype="text/html", status=500)
    elif request.method == "DELETE":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        password = request.json.get("password")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("DELETE FROM user_session WHERE userId=?", [userId])
            cursor.execute("DELETE FROM users WHERE password=? AND id=?", [password, userId])
            conn.commit()
            rows = cursor.rowcount
        except Exception as error:
            print("Something went wrong (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if rows == 1:
                return Response("Your profile has been deleted.", mimetype="text/html", status=204)
            else:
                return Response("An error occured trying to delete your profile.", mimetype="text/html", status=500)


@app.route('/api/login', methods = ["POST", "DELETE"])
def login():
    if request.method == "POST":
        conn = None
        cursor = None
        email = request.json.get("email")
        password = request.json.get("password")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email=? AND password=?", [email, password])
            userId = cursor.fetchall()[0][0]
            if userId != None:
                loginToken = uuid4().hex
                cursor.execute("INSERT INTO user_session(userId, loginToken) VALUES (?, ?)", [userId, loginToken])
                rows = cursor.rowcount
                cursor.execute("SELECT email, username, bio, birthdate FROM users WHERE email=? AND password=?", [email, password])
                # user = cursor.fetchone()
    
                
            else:
                print("User does not exist. Incorrect login info.")
        except Exception as error:
            print("Something went wrong (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if rows == 1:
                # userData = {
                #     "userId": userId,
                #     "email": user[0],
                #     "username": user[1],
                #     "bio": user[] 
                # }


                return Response(json.loads(userData), mimetype="text/html", status=200)
            else:
                return Response("Login failed.", mimetype="text/html", status=500)
    elif request.method == "DELETE":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_session WHERE loginToken=?", [loginToken])
            conn.commit()
            rows = cursor.rowcount
        except Exception as error:
            print("Something went wrong (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if rows == 1:
                return Response("Logged out successfully.", mimetype="text/html", status=204)
            else:
                return Response("Logout failed.", mimetype="text/html", status=500)