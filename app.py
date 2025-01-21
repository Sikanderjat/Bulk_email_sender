from flask import Flask ,render_template,request
import sqlite3 as sql
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import os
app=Flask(__name__)
SESSION_FILE="session.json"
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/emailautomation",methods=["post","get"])
def aftersignup():
    try:
        if request.method == "POST":
            username=request.form.get("username")
            email=request.form.get("email")
            password=request.form.get("password")
            con_password=request.form.get("con_password")

            conn=sql.connect("database.db")
            c=conn.cursor()
            c.execute('''create table if not exists user(
                id integer unique primary key autoincrement,
                email varchar not null ,
                username varchar not null unique,
                password text not null,
                con_password text not null )''')
            if password==con_password:
                c.execute("insert into user (email ,username,password,con_password) values(? ,?,?,?)",(email,username,password,con_password))
                conn.commit()
                c.execute("select * from user")
                print(c.fetchall()) 
                with open(SESSION_FILE, 'w') as f:
                    f.write(username)
                conn.close()
                return render_template("emailautomation.html")
            else:
                conn.close()
                return render_template("signup.html",msg="password and confirm password does not match")
        else:
            conn.close()
            return render_template("signup.html") 
            
    except sql.IntegrityError as e:
        print(e)
        if c.execute("select username from user where username =?",(username,)).fetchone():
            print("already")
            conn.close()
            return render_template("signup.html",msg="username already exists")
        else:
            return render_template("signup.html",msg=e) 

@app.route("/emailautomation1",methods=["post","get"])
def afterlogin():
    try:
        if request.method=="POST":
            username=request.form.get("username")
            password=request.form.get("password")
            print(username,password)
            conn=sql.connect("database.db")
            c=conn.cursor()
            c.execute("select password from user where username =?", (username,))
            user=c.fetchone()   
            with open(SESSION_FILE, 'w') as f:
                f.write(username)
            conn.close()
            if user[0]==password:
                return render_template("emailautomation.html",msg="login successful")
            else:
                return render_template("login.html",msg="invalid username or password")
        else:
            return render_template("login.html") 
    except Exception as e:
        return render_template("login.html",msg=e)     
        
@app.route("/sendemail",methods=["post"])
def sendemail():
    try:
        with open(SESSION_FILE, 'r') as f:
            username = f.read().strip()

        file=request.files.get("file")
        email=request.form.get("email")
        app_password=request.form.get("app_password")
        subject=request.form.get("subject")
        message=request.form.get("message")
        print(file)

        if 'file' not in request.files:
            return render_template("emailautomation.html",msg="file not found")
        
        
        elif file and allowed_file(file.filename):
            file_data=file.read()
            file_name=file.filename
            conn=sql.connect("database.db")
            c=conn.cursor()

            c.execute('''create table if not exists file(
                    id integer primary key autoincrement,
                    username text not null,
                    filename text not null,
                    filedata blob not null)''')
            c.execute("insert into file (username,filename,filedata) values(?,?,?)",(username,file_name,file_data))
            conn.commit()

            c.execute("select filedata from file where username =? ORDER BY id DESC LIMIT 1",(username,))
            f=c.fetchone()[0]
            file_data=io.BytesIO(f)
            # print(file_data)

            data =pd.read_excel(file_data) #getting data from bool1.xlsx file
            print(email,app_password,subject,message)
            print(data)
            email_address = data.get("email").dropna()  # This will drop NaN values
            data_list=list(email_address) # store emails into a list

            print(data_list)

            
            server =smtplib.SMTP("smtp.gmail.com",587)
            server.starttls()
           
            server.login(email,app_password)
            from_ ="email"
            To_=data_list
            msg = MIMEMultipart()
            msg['From'] = from_
            msg['subject']=subject
            text_content=message                

            text=MIMEText(text_content,"plain")
            msg.attach(text)

            server.sendmail(from_,To_,msg.as_string())
            print("email send successfully")
            server.quit()
            conn.close()
            return render_template("emailautomation.html",msg=f"email sent successfully to {data_list}")
        
        else:
            conn.close()
            return render_template("emailautomation.html",msg="file must be xlsx formate")
        

    except Exception as e:
        print(e)
        return render_template("emailautomation.html",msg=e)
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx'}

@app.route("/logout")
def logout():
    
    if os.path.exists(SESSION_FILE):
        
        os.remove(SESSION_FILE)
        print("You have been logged out.")
        return render_template("home.html",msg="You have been logged out.")
    else:
        print("No active session found.")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
