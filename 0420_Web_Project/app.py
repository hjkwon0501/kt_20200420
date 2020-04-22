import os
import time
from flask import Flask
from flask import request, redirect,render_template
import json
# $env:FLASK_ENV="development"

app=Flask(__name__, static_folder='static')
    #total_message -> type: list , content: dictionary 
    #total_message[0] : id(str), title(str), picture(str,URL), content(str),contentNum(str)
total_message=[]
# total_message=[{'id':'test1',
#                 'title':'test1',
#                'picture':'static/USER/test1/1_picture.jpg',
#                 'content':'static/USER/test1/1_content.txt',
#                 'contentNum':'1'
#                }]

def get_template(filename):
    with open(filename,'r',encoding='utf-8') as f:
        template=f.read()
    return template


@app.route("/", methods=['GET','POST'])
def login():
    template=get_template('login.html')
    
    if request.method == 'GET':
        return template.format('')
    else:
        with open("static/login.txt", 'r',encoding='utf-8') as f:
            while(True):
                data= f.readline().strip()
                if not data: break
                id, pw=data.split(",")                
                if id == str(request.form['id']) :
                    if pw == str(request.form['password']):
                        return redirect(f"/{id}/home")
                    else:
                        return template.format("패스워드가 틀렸습니다.")                
        return template.format("회원이 아닙니다.")
        
@app.route("/createMember", methods=['GET','POST'])
def createMember():
    template=get_template('createMember.html')
    
    if request.method == 'GET':
        return template+"GET" 
    else: # # id password
        with open("static/login.txt","a",encoding="UTF-8") as f: 
            f.write(f"{request.form['id']},{request.form['password']}\n")
        os.makedirs(os.path.join(f"static/USER/{request.form['id']}"))
    return redirect('/')

@app.route("/<user>/home", methods=['GET','POST'])
def home(user):
    #total_message -> type: list , content: dictionary 
    #total_message[0] : id(str), picture(str,URL), content(str),contentNum(str)
    flag=request.args.get('flag','')
    template=get_template('home.html')
    total_html=""

    if(len(total_message)==0):
        with open('static/total_message.txt','r',encoding='utf-8') as f:      
            for i in f:
                if(i!=''):
                    total_message.append(json.loads("{"+i+"}"))

    for i in range(len(total_message)):
        cur_dict=total_message[i]
        id=cur_dict['id']
        if flag=='mypage':
            if id!=user:
                continue
        pictureURL=cur_dict['picture']
        content=cur_dict['content']
        contentNum=cur_dict['contentNum']
        pictureURL="../"+pictureURL
        with open(content,'r',encoding='utf-8') as f:
            total_html+=f"<li> <dl><dt>'@ {id}'</dt><dd> <img src='{pictureURL}'></dd><dd>'{f.read()}'</dd></dl></li>"
    return template.format(user,total_html)

@app.route("/<user>/write",  methods=['GET','POST'])
def write(user):
    template=get_template('write.html')
    if request.method == 'GET':
        return template.format(user) 
    else:
        title=request.form['title']
        content=request.form['content']
        date=time.strftime('%Y-%m-%d', time.localtime(time.time()))
    return template.format(user)

@app.route("/<user>/fileUpload", methods=['GET','POST'])
def fileUpload(user):
    contentNum=len(total_message)
    if request.method=='POST':  
        title=request.form['title']
        content=request.form['content']
        with open(f"static/USER/{user}/{str(int(contentNum)+1)}_content.txt", 'w',encoding='utf-8') as f:
            f.write(content)
        cont_URL=f"static/USER/{user}/{str(int(contentNum)+1)}_content.txt"
        date=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        f=request.files['file']
        pic_URL=f"static/USER/{user}/{str(int(contentNum)+1)}_picture.jpg"
        f.save((f"static/USER/{user}/{str(int(contentNum)+1)}_picture.jpg"))
         #total_message[0] : id(str), title(str) picture(str,URL), content(str),contentNum(str)
        with open(f"static/total_message.txt",'a',encoding='utf-8') as files:
            files.write(f'"id":"{user}", "title":"{title}", "date": "{date}", "picture": "{pic_URL}", "content":"{cont_URL}", "contentNum": "{contentNum}"\n')
       
            total_message.append(json.loads("{"+f'"id":"{user}", "title":"{title}", "date": "{date}", "picture": "{pic_URL}", "content":"{cont_URL}", "contentNum": "{contentNum}"'+"}"))
    return redirect(f"/{user}/home".format(user))

# @app.route("/<user>/myPage")
# def myPage(user):
#     template=get_template('home.html')
#     total_html=""
#     for i in range(len(total_message)):
#         cur_dict=total_message[i]
#         if cur_dict['id']!=user:
#             continue
#         id=cur_dict['id']
#         pictureURL=cur_dict['picture']
#         content=cur_dict['content']
#         contentNum=cur_dict['contentNum']
#         pictureURL="../"+pictureURL
#         with open(content,'r',encoding='utf-8') as f:
# #             total_html+=f"<li> '{user}' <img src='{pictureURL}'>'{f.read()}'</li>"
#             total_html+=f"<li> <dl><dt>'@ {id}'</dt><dd> <img src='{pictureURL}'></dd><dd>'{f.read()}'</dd></dl></li>"
#     return template.format(user,total_html)