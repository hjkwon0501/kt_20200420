import re
import json
import requests
import time
from bs4 import BeautifulSoup
import requests
from flask import Flask, render_template, request,session,redirect,jsonify
import pymysql
import os

app = Flask(__name__, 
            static_folder="static",
            template_folder="views")
app.secret_key = 'sookbun'
# 자동갱신 되도록 설정
app.config['ENV'] = 'development'
app.config['DEBUG'] = True

db = pymysql.connect(
    user='root',
    passwd='test123',
    host='localhost',
    db='0424project',
    charset='utf8',
    cursorclass=pymysql.cursors.DictCursor
)

cursor = db.cursor()
@app.route("/", methods=['GET','POST'])
def login():

    message=''
    if request.method == 'POST':
        cursor.execute(f"select id, password from user where id = '{request.form['id']}'") # where id = 'test'
        user_info = cursor.fetchone()   
        if user_info is None:
            message = "<p>회원이 아닙니다.</p>"
        else:
            cursor.execute(f"""
             select * from user 
             where id = '{request.form['id']}' and 
                  password = SHA2('{request.form['password']}', 256)""")
            user_info = cursor.fetchone()

            if user_info is None:
                message = "<p>패스워드를 확인해 주세요</p>"
            else:
                    # 로그인 성공에는 메인으로
                session['user'] = user_info
                return redirect('/home')
 
    return render_template('login.html', message = message) 

@app.route('/createMember',methods=['get','post'])
def createmember():
    if request.method=='POST':
        id=request.form['id']
        password=request.form['password']
        query=f"""insert into user(id,password) values ('{id}',SHA2('{password}',256))"""
        message=''
        try:
            cursor.execute(query)
            db.commit()
            os.makedirs(os.path.join(f"static/USER/{id}"))
            message= "<p>회원가입이 성공적으로 되었습니다.</p>" 
        except:
            message= "<p>아이디가 중복입니다.</p>" 
        #아이디 중복시 fail msg 입력 해야함 
        
        return render_template('login.html', message =message ) 
    return render_template('createMember.html') 

@app.route('/home')
def home():
    flag=request.args.get('flag','') #mypage 분기점 
    if flag=='mypage':
        contents=getFileList(flag)
    else: 
        contents=getFileList('home')
    
    return render_template('home.html', contents = contents, userID=session['user']['id']) 



def getFileList(flag):
    #조건에 따라 파일 정보를 
    total_html=""
    query="select * from total_message"
    if flag =='mypage':
        query+=f" where writer = '{session['user']['id']}'"
        cursor.execute(query)
        data=cursor.fetchall()
        for i in data:
            with open(i['content'],'r',encoding='utf-8') as f:
                total_html+=f"""<li> <dl><dt>'@ {i['writer']}'<a href="/fileUpload?content_id={i['content_id']}"><i class="fas fa-pen" style='float:right; padding:2px'></i></a> <a href="/delete?pictureURL={i['picture']}"><i class='fas fa-trash-alt' style='float:right; padding:2px' 7x></i></a></dt><dd> <img src="{i['picture']}"></dd><dd>{i['date']}</dd><dd>'{f.read()}'</dd></dl></li>"""
    else:      
        cursor.execute(query)
        data=cursor.fetchall()        
        for i in data:
            with open(i['content'],'r',encoding='utf-8') as f:
                total_html+=f"<li> <dl><dt>'@ {i['writer']}'</dt><dd><img src='{i['picture']}'></dd><dd>{i['date']}</dd><dd>'{f.read()}'</dd></dl></li>"

    return total_html

@app.route("/fileUpload", methods=['GET','POST'])  #title, content, file
def fileUpload():   
    if request.method == 'GET': #title_modi text_modi file_modi
        flag='write'
        content_id=request.args.get('content_id','')
        title_modi=''
        text_modi=''
        file_modi=''
        if content_id !='':
            cursor.execute(f"select title, content, picture from total_message where content_id = '{content_id}'") # where id = 'test'
            feed_info = cursor.fetchone() 
            title_modi=feed_info['title']
            with open(feed_info['content'], 'r', encoding='utf-8') as f:
                text_modi=f.read()
            file_modi=feed_info['picture']
            flag=content_id
        return render_template('write.html',userID=session['user']['id'],title_modi=title_modi, text_modi=text_modi, file_modi=file_modi,flag=flag) 
    
    elif request.method=='POST':  
        flag=request.args.get('flag','')
        #flag : write , modify
        date=time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))
        
        
        title=request.form['title']
        user=session['user']['id']
        content=f"static/USER/{user}/{date}_content.txt"
        if flag=='write':     
            with open(content, 'a',encoding='utf-8') as f:
                f.write(request.form['content'])

            f=request.files['file']
            picture=f"static/USER/{user}/{date}_picture.jpg"
            f.save(picture)
            sql = f"""
                insert into total_message (writer,title,date, picture, content)
                values ('{user}', '{title}','{date}','{picture}','{content}')
            """
        else:
            ###################################그림, 글 UPDATE 해야함(쿼리 정상)
            sql = f"""
                update total_message set 
                title='{title}',
                date='{date}'   
                where content_id={flag}
            """
            f.save()
            print(sql)
        cursor.execute(sql)
        db.commit()
        
    return redirect("/home?flag=home")

@app.route('/delete',methods=['POST','GET'])
def remove():
 
    pictureURL=request.args.get('pictureURL','')
    contentURL=pictureURL.replace('picture.jpg','content.txt')

    #fine file&list Index where file exist
    cursor.execute(f"delete from total_message where writer ='{session['user']['id']}' and picture = '{pictureURL}'")
    db.commit() 
    
    #remove real File
    os.remove(pictureURL)
    os.remove(contentURL)
    
    return redirect("/home")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# python 파일명으로 실행을 위해서 필요
app.run(port=8001)
