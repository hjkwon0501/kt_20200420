# import pymysql

# db = pymysql.connect(
#     user='root',
#     passwd='test123',
#     host='localhost',
#     db='0424project',
#     charset='utf8',
#     cursorclass=pymysql.cursors.DictCursor
# )

# cursor = db.cursor()

# query="insert into user values('test',SHA2('tt',256))"
# try:
    
#     print(cursor.execute(query))
# except Exception as e :
#     logger.exception(e)
#     logger.error(e)
with open('static/USER/test/1_content.txt','r',encoding='utf-8') as f:
    print(f.read())

with open('static/USER/test/1_content.txt','w',encoding='utf-8') as f:
    f.write('modify')