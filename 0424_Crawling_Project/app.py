import re
import json
import requests
import time
from bs4 import BeautifulSoup
import requests
from flask import Flask, render_template, request,session,redirect,jsonify
import pymysql
import os
from selenium import webdriver
import base64
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

@app.route('/home', methods=['get','post'])
def home():
    searchID=''
    flag=request.args.get('flag','') #mypage 분기점 
    if flag =='search':
        searchID=request.form['searchID']
    contents=getFileList(flag, searchID )
    return render_template('home.html', contents = contents, userID=session['user']['id']) 



def getFileList(flag, searchID):
    #조건에 따라 파일 정보를 
    total_html=""
    query="select * from total_message"
    if flag =='mypage':
        query+=f" where writer = '{session['user']['id']}'"
        cursor.execute(query)
        data=cursor.fetchall()
        for i in data:
            with open(i['content'],'r',encoding='utf-8') as f:
                total_html+=f"""<li> <dl><dt>'@ {i['writer']}'<a href="/changePicture?content_id={i['content_id']}"><i class="fas fa-camera" style='float:right; padding:2px'></i></a><a href="/fileUpload?content_id={i['content_id']}"><i class="fas fa-pen" style='float:right; padding:2px'></i></a> <a href="/delete?pictureURL={i['picture']}"><i class='fas fa-trash-alt' style='float:right; padding:2px' 7x></i></a></dt><dd> <img src="{i['picture']}"></dd><dd>{i['date']}</dd><dd>'{f.read()}'</dd></dl></li>"""
    elif flag =='search':
        query+=f" where writer LIKE '%{searchID}%'"
        cursor.execute(query)
        data=cursor.fetchall()
        for i in data:
            with open(i['content'],'r',encoding='utf-8') as f:
                total_html+=f"<li> <dl><dt>'@ {i['writer']}'</dt><dd><img src='{i['picture']}'></dd><dd>{i['date']}</dd><dd>'{f.read()}'</dd></dl></li>"
    else:      
        cursor.execute(query)
        data=cursor.fetchall()        
        for i in data:
            with open(i['content'],'r',encoding='utf-8') as f:
                total_html+=f"<li> <dl><dt>'@ {i['writer']}'</dt><dd><img src='{i['picture']}'></dd><dd>{i['date']}</dd><dd>'{f.read()}'</dd></dl></li>"

    return "<ul>"+total_html+"</ul>"

@app.route("/fileUpload", methods=['GET','POST'])  #title, content, file
def fileUpload():
    date=time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))
    user=session['user']['id']
    
    
    if request.method == 'GET': #title_modi text_modi file_modi
        flag='write'
        title_modi=''
        text_modi=''
        file_modi=''
        content_id=request.args.get('content_id','')  # content_id 있으면 modify, 없으면 write 
        if content_id !='':
            cursor.execute(f"select title, content, picture from total_message where content_id = '{content_id}'") # where id = 'test'
            feed_info = cursor.fetchone() 
            title_modi=feed_info['title']
            with open(feed_info['content'], 'r', encoding='utf-8') as f: #EOF
                text_modi=f.read()
            print(text_modi)
            file_modi=feed_info['picture']
            flag=content_id
        return render_template('write.html',userID=session['user']['id'],title_modi=title_modi, text_modi=text_modi, file_modi=file_modi,flag=flag) 
    
    elif request.method=='POST':  
        flag=request.args.get('flag','')    #flag : write , content_id
        title=request.form['title']         #글 제목 
        #content,picture URL 선지정
        content=f"static/USER/{user}/{date}_content.txt"
        picture=f"static/USER/{user}/{date}_picture.jpg"
        #사진 저장 
        f=request.files['file']
        f.save(picture)
        #content 저장 
        with open(content, 'a',encoding='utf-8') as f:
                f.write(request.form['content'])
                
        if flag=='write':     
            sql = f"""
                insert into total_message (writer,title,date, picture, content)
                values ('{user}', '{title}','{date}','{picture}','{content}')
            """
        else:
            #기존 정보 호출
            cursor.execute(f"select picture, content from total_message where content_id = '{flag}'")
            feed_info=cursor.fetchone()
            #기존(구 파일) 삭제
            
            os.remove(feed_info['picture'])
            os.remove(feed_info['content'])
            
            sql = f"""
                update total_message set 
                title='{title}',
                date='{date}' ,
                picture='{picture}',
                content='{content}'
                where content_id='{flag}'
            """
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

@app.route('/changePicture',methods=['get','post'])
def changePicture():
    
    content_id=request.args.get('content_id','')
    contents=f"""
        <div class="write-content">
            <form action='/changePicture?content_id={content_id}' method='post' enctype="multipart/form-data"> 
                <div>
                    <span><i class="fas fa-caret-right"></i>제목</span>
                    <input type='text' name='title' placeholder='검색어를 입력하세요'>  
                </div>
                <div>
                    <button type='submit'>제출</button>
                </div>
            </form>
        </div>
        """    
    if request.method == 'POST':
        searchTag=request.form['title']
        contents+=getImageFromGoogle(searchTag,content_id)
    return render_template('home.html', contents = contents, userID=session['user']['id']) 

@app.route('/changePicture/save')
def changePictureAndSave():
    imgURL=request.args.get('imgURL') # base64 URL
    content_id=request.args.get('content_id') 
    query=f"select picture from total_message where content_id = '{content_id}'"

    cursor.execute(f"select picture from total_message where content_id = '{content_id}'") # where id = 'test'
    picture = (cursor.fetchone())['picture']
    #파일 바꾸기
    #test
    testDummy="URL IS...\n", #data:image/jpeg;base64,
  
    #
    
    if("base64" in imgURL[:len('data:image/jpeg;base64,/')]):
        pictureURL=imgURL[len('data:image/jpeg;base64,'):]   
        with open(picture,'wb') as f:
            f.write(base64.b64decode(pictureURL.replace(' ', '+')))    
            
    elif("http" in imgURL[:len('data:image/jpeg;base64,/')]):
        res=requests.get(imgURL)
        with open(picture,'wb') as f:
            f.write(res.content)    
    
    return redirect('/home')  
    
def getImageFromGoogle(searchTag,content_id):
    from selenium import webdriver
    options=webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('disable-dev-shm-usage')

    driver = webdriver.Chrome('chrome/chromedriver.exe',options=options)#
    driver.implicitly_wait(3)
    url=f"https://www.google.com/search?q={searchTag}&rlz=1C1CHBD_koKR896KR896&source=lnms&tbm=isch&sa=X&ved=2ahUKEwiPiYu4tofpAhWSZt4KHY1CATgQ_AUoAXoECBcQAw&biw=903&bih=722&dpr=1.25"
    driver.get(url)
 
    html=driver.page_source
    soup=BeautifulSoup(html,'html.parser')
    tags=soup.select('.rg_i')
    regex=re.compile('src="(.+?)"')
    URL_List=[]
    htmlString=""
    for index,URL in enumerate(tags):  
        origin=re.findall(regex,str(URL))[0]
        URL_List.append(origin)
    for i in URL_List:
        htmlString+=f"""<a href='/changePicture/save?imgURL={i}&content_id={content_id}'><img src='{i}'></a>"""  #/changePicture/save    img URL,content_id 
    return htmlString
# python 파일명으로 실행을 위해서 필요
app.run(port=8001)



#             if("base64" in (origin[:len('data:image/jpeg;base64,/')])):
# #                 pictureURL=(re.findall(regex,str(URL))[0])[len('data:image/jpeg;base64,'):]   
#                 pictureURL=origin
#                 URL_List.append(pictureURL)
# #                 with open(f'0426Cat/{index+1}cat.jpg','wb') as f:
# #                     f.write(base64.b64decode(pictureURL))    
#             elif("http" in (origin[:len('data:image/jpeg;base64,/')])):
#                 pictureURL=origin
#                 URL_List.append(pictureURL)
#                #res=requests.get(pictureURL)
# #                 with open(f'0426Cat/{index+1}cat.jpg','wb') as f:
# #                     f.write(res.content)    
