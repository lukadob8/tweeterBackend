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
        userId = request.args.get("userId")
        user = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            if userId != None:
                cursor.execute("SELECT * FROM users WHERE id=?", [userId])
            else:
                cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
        except Exception as error:
            print("SOMETHING WENT WRONG (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if users != None:
                userData = []
                for user in users:
                    userData.append({
                        "userId": user[5],
                        "email": user[0],
                        "username": user[1],
                        "bio": user[3],
                        "birthdate": user[4]
                    })
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=200)
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
        session_rows = None
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
        except Exception as error:
            print("SOMETHING WENT WRONG (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if rows == 1 and session_rows == 1:
                userData = {
                    "userId": userId,
                    "email": email,
                    "username": username,
                    "bio": bio,
                    "birthdate": birthdate,
                    "loginToken": loginToken
                }
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=201)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)
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
                cursor.execute("UPDATE users SET birthdate=? WHERE id=?", [birthdate, userId])
            conn.commit()
            rows = cursor.rowcount
            cursor.execute("SELECT * FROM users WHERE id=?", [userId])
            user = cursor.fetchone()
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
                userData = {
                    "userId": userId,
                    "email": user[0],
                    "username": user[1],
                    "bio": user[3],
                    "birthdate": user[4]
                }
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=200)
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
            loginToken = uuid4().hex
            if userId != None:
                cursor.execute("INSERT INTO user_session(userId, loginToken) VALUES (?, ?)", [userId, loginToken])
                conn.commit()
                rows = cursor.rowcount
                cursor.execute("SELECT email, username, bio, birthdate FROM users WHERE email=? AND password=?", [email, password])
                user = cursor.fetchone()
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
                userData = {
                    "userId": userId,
                    "email": user[0],
                    "username": user[1],
                    "bio": user[2],
                    "birthdate": user[3],
                    "loginToken": loginToken
                }
                return Response(json.dumps(userData, default=str), mimetype="text/html", status=200)
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

@app.route('/api/tweets', methods = ["GET", "POST", "PATCH", "DELETE"])
def tweetActions():
    if request.method == "GET":
        conn = None
        cursor = None
        userId = request.args.get("userId")
        tweets = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            if userId == None:
                cursor.execute("SELECT tweets.*, users.username FROM tweets INNER JOIN users ON tweets.userId = users.id")
                tweets = cursor.fetchall()
            else:
                cursor.execute("SELECT tweets.*, users.username FROM tweets INNER JOIN users ON tweets.userId = users.id WHERE tweets.userId=?", [userId])
                tweets = cursor.fetchall()
        except Exception as error:
            print("SOMETHING WENT WRONG (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if tweets != None:
                userData = []
                for tweet in tweets:
                    userData.append({
                        "tweetId": tweet[3],
                        "userId": tweet[2],
                        "username": tweet[4],
                        "content": tweet[0],
                        "createdAt": tweet[1]
                    },)
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=200)
            else:
                return Response("No tweets found.", mimetype="text/html", status=500)
    elif request.method == "POST":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        content = request.json.get("content")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("INSERT INTO tweets (content, userId) VALUES(?, ?)", [content, userId])
            conn.commit()
            rows = cursor.rowcount
            cursor.execute("SELECT users.username, tweets.createdAt, tweets.id FROM users INNER JOIN tweets ON users.id = tweets.userId WHERE users.id=?", [userId])
            tweet = cursor.fetchone()
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
                userData = {
                    "tweetId": tweet[2],
                    "userId": userId,
                    "username": tweet[0],
                    "content": content,
                    "createdAt": tweet[1]
                }
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=201)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)
    elif request.method == "PATCH":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        tweetId = request.json.get("tweetId")
        content = request.json.get("content")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("SELECT userId FROM tweets WHERE id=?", [tweetId])
            tweetOwner = cursor.fetchall()[0][0]
            if userId == tweetOwner:
                cursor.execute("UPDATE tweets SET content=? WHERE id=?", [content, tweetId])
                conn.commit()
                rows = cursor.rowcount
            else:
                print("You do not own this tweet.")
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
                userData = {
                    "tweetId": tweetId,
                    "content": content
                }
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=200)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)
    elif request.method == "DELETE":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        tweetId = request.json.get("tweetId")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("SELECT userId FROM tweets WHERE id=?", [tweetId])
            tweetOwner = cursor.fetchall()[0][0]
            if userId == tweetOwner:
                cursor.execute("DELETE FROM tweets WHERE id=?", [tweetId])
                conn.commit()
                rows = cursor.rowcount
            else:
                print("You cannot delete this tweet.")
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
                return Response("Successfully deleted.", mimetype="text/html", status=204)
            else:
                return Response("An error occured", mimetype="text/html", status=500)

@app.route('/api/tweet-likes', methods = ["GET", "POST", "DELETE"])
def tweetLikeActions():
    if request.method == "GET":
        conn = None
        cursor = None
        tweetId = request.args.get("tweetId")
        tweetLikes = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT tweet_likes.tweetId, tweet_likes.userId, users.username FROM tweet_likes INNER JOIN users ON users.id = tweet_likes.userId WHERE tweet_likes.tweetId = ?", [tweetId])
            likes = cursor.fetchall()
        except Exception as error:
            print("SOMETHING WENT WRONG (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if likes != None:
                userData = []
                for like in likes:
                    userData.append({
                        "tweetId": like[0],
                        "userId": like[1],
                        "username": like[2]
                    })
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=200)
            else:
                return Response("No likes", mimetype="text/html", status=500)
    elif request.method == "POST":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        tweetId = request.json.get("tweetId")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("INSERT INTO tweet_likes(tweetId, userId) VALUES(?, ?)", [tweetId, userId])
            conn.commit()
            rows = cursor.rowcount
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
                return Response("Tweet liked.", mimetype="text/html", status=201)
            else:
                return Response("Tweet not liked.", mimetype="text/html", status=500)
    elif request.method == "DELETE":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        tweetId = request.json.get("tweetId")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("DELETE FROM tweet_likes WHERE tweetId=? AND userId=?", [tweetId, userId])
            conn.commit()
            rows = cursor.rowcount
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
                return Response("Tweet unliked.", mimetype="text/html", status=204)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)

@app.route('/api/comments', methods = ["GET", "POST", "PATCH", "DELETE"])
def commentActions():
    if request.method == "GET":
        conn = None
        cursor = None
        tweetId = request.args.get("tweetId")
        comments = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT comments.*, users.username FROM comments INNER JOIN users ON comments.userId = users.id WHERE comments.tweetId=?", [tweetId])
            comments = cursor.fetchall()
        except Exception as error:
            print("SOMETHING WENT WRONG (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if comments != None:
                userData = []
                for comment in comments:
                    userData.append({
                        "commentId": comment[4],
                        "tweetId": comment[2],
                        "userId": comment[3],
                        "username": comment[5],
                        "content": comment[0],
                        "createdAt": comment[1]
                    })
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=200)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)
    elif request.method == "POST":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        tweetId = request.json.get("tweetId")
        content = request.json.get("content")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("INSERT INTO comments(content, tweetId, userId) VALUES(?, ?, ?)", [content, tweetId, userId])
            conn.commit()
            rows = cursor.rowcount
            cursor.execute("SELECT id FROM comments WHERE content=? AND userId=?", [content, userId])
            commentId = cursor.fetchall()[0][0]
            cursor.execute("SELECT comments.*, users.username FROM comments INNER JOIN users ON users.id = comments.userId WHERE comments.id=?", [commentId])
            comment = cursor.fetchall()
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
                userData = {
                    "commentId": comment[0][4],
                    "tweetId": tweetId,
                    "userId": userId,
                    "username": comment[0][5],
                    "content": content,
                    "createdAt": comment[0][1]
                }
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=201)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)
    elif request.method == "PATCH":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        commentId = request.json.get("commentId")
        content = request.json.get("content")
        comment = None
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("SELECT userId FROM comments WHERE id=?", [commentId])
            commentOwner = cursor.fetchall()[0][0]
            if userId == commentOwner:
                cursor.execute("UPDATE comments SET content=? WHERE id=?", [content, commentId])
                conn.commit()
                rows = cursor.rowcount
            else:
                print("You cannot edit a comment you did not make.")
            if rows == 1:
                cursor.execute("SELECT comments.*, users.username FROM comments INNER JOIN users ON users.id = comments.userId WHERE comments.id=?", [commentId])
                comment = cursor.fetchall()
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
                userData = {
                    "commentId": commentId,
                    "tweetId": comment[0][2],
                    "userId": userId,
                    "username": comment[0][5],
                    "content": content,
                    "createdAt": comment[0][1]
                }
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=200)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)
    elif request.method == "DELETE":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        commentId = request.json.get("commentId")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("SELECT userId FROM comments WHERE id=?", [commentId])
            commentOwner = cursor.fetchall()[0][0]
            if userId == commentOwner:
                cursor.execute("DELETE FROM comments WHERE id=?", [commentId])
                conn.commit()
                rows = cursor.rowcount
            else:
                print("You cannot delete a comment that you did not write.")
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
                return Response("Comment deleted.", mimetype="text/html", status=204)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)

@app.route('/api/comment-likes', methods = ["GET", "POST", "DELETE"])
def commentLikeActions():
    if request.method == "GET":
        conn = None
        cursor = None
        commentId = request.args.get("commentId")
        likes = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT comment_likes.commentId, comment_likes.userId, users.username FROM comment_likes INNER JOIN users ON users.id = comment_likes.userId WHERE comment_likes.commentId=?", [commentId])
            likes = cursor.fetchall()
        except Exception as error:
            print("SOMETHING WENT WRONG (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if likes != None:
                userData = []
                for like in likes:
                    userData.append({
                        "commentId": like[0],
                        "userId": like[1],
                        "username": like[2]
                    })
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=200)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)
    elif request.method == "POST":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        commentId = request.json.get("commentId")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("INSERT INTO comment_likes(commentId, userId) VALUES(?, ?)", [commentId, userId])
            conn.commit()
            rows = cursor.rowcount
            cursor.execute("SELECT comment_likes.*, users.username FROM comment_likes INNER JOIN users ON users.id = comment_likes.userId WHERE comment_likes.commentId=?", [commentId])
            like = cursor.fetchall()
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
                userData = {
                    "commentId": like[0][0],
                    "userId": like[0][1],
                    "username": like[0][3]
                }
                return Response(json.dumps(userData, default=str), mimetype="application.json", status=201)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)
    elif request.method == "DELETE":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        commentId = request.json.get("commentId")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("SELECT userId FROM comment_likes WHERE commentId=?", [commentId])
            likeOwner = cursor.fetchall()[0][0]
            if userId == likeOwner:
                cursor.execute("DELETE FROM comment_likes WHERE commentId=? AND userId=?", [commentId, userId])
                conn.commit()
                rows = cursor.rowcount
            else:
                print("You cannot delete other people's comments.")
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
                return Response("Comment unliked.", mimetype="text/html", status=204)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)

@app.route('/api/follows', methods = ["GET", "POST", "DELETE"])
def followsActions():
    if request.method == "GET":
        conn = None
        cursor = None
        userId = request.args.get("userId")
        follows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT follow.followedId, users.email, users.username, users.bio, users.birthdate FROM follow INNER JOIN users ON users.id = follow.followedId WHERE follow.followerId=?", [userId])
            follows = cursor.fetchall()
        except Exception as error:
            print("SOMETHING WENT WRONG (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if follows != None:
                userData = []
                for follow in follows:
                    userData.append({
                        "userId": follow[0],
                        "email": follow[1],
                        "username": follow[2],
                        "bio": follow[3],
                        "birthdate": follow[4]
                    })
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=200)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)
    elif request.method == "POST":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        followId = request.json.get("followId")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            if userId != followId:
                cursor.execute("INSERT INTO follow(followerId, followedId) VALUES(?, ?)", [userId, followId])
                conn.commit()
                rows = cursor.rowcount
            else:
                print("You cannot follow yourself.")
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
                return Response("User followed.", mimetype="text/html", status=204)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)
    elif request.method == "DELETE":
        conn = None
        cursor = None
        loginToken = request.json.get("loginToken")
        followId = request.json.get("followId")
        rows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [loginToken])
            userId = cursor.fetchall()[0][0]
            cursor.execute("DELETE FROM follow WHERE followerId=? AND followedId=?", [userId, followId])
            conn.commit()
            rows = cursor.rowcount
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
                return Response("User unfollowed.", mimetype="text/html", status=204)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)

@app.route('/api/followers', methods = ["GET"])
def followersActions():
    if request.method == "GET":
        conn = None
        cursor = None
        userId = request.json.get("userId")
        follows = None
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT follow.followedId, users.email, users.username, users.bio, users.birthdate FROM follow INNER JOIN users ON users.id = follow.followerId WHERE follow.followerId=?", [userId])
            follows = cursor.fetchall()
        except Exception as error:
            print("SOMETHING WENT WRONG (THIS IS LAZY)")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if follows != None:
                userData = []
                for follow in follows:
                    userData.append({
                        "userId": follow[0],
                        "email": follow[1],
                        "username": follow[2],
                        "bio": follow[3],
                        "birthdate": follow[4]
                    })
                return Response(json.dumps(userData, default=str), mimetype="application/json", status=200)
            else:
                return Response("An error occured.", mimetype="text/html", status=500)