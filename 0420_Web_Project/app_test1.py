import os
import time
from flask import Flask
from flask import request, redirect,render_template
import json
import re
from tempfile import mkstemp
from shutil import move, copymode
from os import fdopen, remove


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


# $env:FLASK_ENV="development"

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
        with open("static/login.txt","a",encoding="utf-8") as f: 
            f.write(f"{request.form['id']},{request.form['password']}\n")
        os.makedirs(os.path.join(f"static/USER/{request.form['id']}"))
    return redirect('/')

def replace(file_path, regex, subst, date):
    #Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh,'w',encoding="utf-8") as new_file:
        with open(file_path,'r',encoding="utf-8") as old_file:
            for line in old_file:
                if regex.findall(line)[0] != str(date):
                    new_file.write(line)
				else:
					total_message.remove(json.loads("{"+line+"}"))
					
    #Copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)
    
@app.route("/<user>/remove")
def delete_message(user):
    #date= 2020-04-21%2000:47:17
    #date= 2020-04-20%2015:54:00
    date=request.args.get('date','')
    regex = re.compile("(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2})") 
#     for line in fileinput.input("static/total_message.txt", inplace = True):
#         regex = re.compile("(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2})") 
#         if regex.findall(line)[0] != date:
#             line = line.replace(line, '')
    replace("static/total_message.txt", regex, '', date)
    return redirect(f"/{user}/home?flag=mypage")
    
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
        date=cur_dict['date']
        pictureURL=cur_dict['picture']
        content=cur_dict['content']
        contentNum=cur_dict['contentNum']
        pictureURL="../"+pictureURL
        print(id, user)
        if flag == 'mypage':
            if id == user:
                with open(content,'r',encoding='utf-8') as f:
                    total_html+=f"<li> <a href=/{user}/remove?date={date}><i class='fas fa-trash-alt'></i></a><dl><dt>'@ {id}'</dt><dd> <img src='{pictureURL}'></dd><dd>{date}</dd><dd>'{f.read()}'</dd></dl></li>"
            else:
                continue
        else:
            with open(content,'r',encoding='utf-8') as f:
                total_html+=f"<li> <dl><dt>'@ {id}'</dt><dd> <img src='{pictureURL}'></dd><dd>{date}</dd><dd>'{f.read()}'</dd></dl></li>"
    return template.format(user,total_html)

@app.route("/<user>/fileUpload", methods=['GET','POST'])
def fileUpload(user):
    template=get_template('write.html')
    contentNum=len(total_message)

    if request.method == 'GET':
        return template.format(user) 
    if request.method=='POST':  
        title=request.form['title']
        content=request.form['content']
        with open(f"static/USER/{user}/{str(int(contentNum)+1)}_content.txt", 'w',encoding='utf-8') as f:
            f.write(content)
        cont_URL=f"static/USER/{user}/{str(int(contentNum)+1)}_content.txt"
        date=time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
        f=request.files['file']
        pic_URL=f"static/USER/{user}/{str(int(contentNum)+1)}_picture.jpg"
        f.save((f"static/USER/{user}/{str(int(contentNum)+1)}_picture.jpg"))
         #total_message[0] : id(str), title(str) picture(str,URL), content(str),contentNum(str)
        with open(f"static/total_message.txt",'a',encoding='utf-8') as files:
            files.write(f'"id":"{user}", "title":"{title}", "date": "{date}", "picture": "{pic_URL}", "content":"{cont_URL}", "contentNum": "{contentNum}"\n')
       
            total_message.append(json.loads("{"+f'"id":"{user}", "title":"{title}", "date": "{date}", "picture": "{pic_URL}", "content":"{cont_URL}", "contentNum": "{contentNum}"'+"}"))
    return redirect(f"/{user}/home".format(user))