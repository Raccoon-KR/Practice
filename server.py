from flask import Flask, render_template, request, redirect
import pymysql

#mysql과 연동하기 위한 코드
db = pymysql.connect(host='127.0.0.1',
                     user='root',
                     password='root',
                     db='testdb',
                     charset='utf8'
                     )

cur = db.cursor()

app = Flask(__name__)

#db에 있는 값들을 가지고와 딕셔너리 형태로 만들어준다.
def getBoards():
    boards = []
    
    sql = "SELECT id,title,content,author FROM boards;"
    cur.execute(sql)
    result = cur.fetchall()

    boards = []

    for i in range(len(result)):
        boards.append({"id": result[i][0], "title": result[i][1], "content": result[i][2], "author": result[i][3]})

    return boards

# db정보를 html형식으로 바꿔주는 함수
def getContents():
    liTags = ''
    boards = getBoards()

    for board in boards:        #정보를 게시글(링크)의 목록으로 구현해준다.
        liTags = liTags + f'<li><a href="/read/{board["id"]}/">{board["title"]}</a></li>'
    return liTags


def read_board(id):
    title = ''
    content = ''
    author = ''
    boards = getBoards()

    for board in boards:
        if id == board['id']:
            title = board['title']
            content = board['content']
            author = board['author']
            break
    return title, content, author

#검색을 할때 해당 문자열이 있는지 없는지 검색해 해당되는 게시물을 구해준다.
def search_board(type, word):
    web_content = ''
    boards = getBoards()

    for board in boards:
        if board[type].find(word) != int(-1):
            web_content = web_content + f'<li><a href="/read/{board["id"]}/">{board["title"]}</a></li>'
            break

    if web_content == '':
        web_content = '<p>찾으시는 게시글이 없습니다.</p><a href= "/"</a>'

    return web_content

#웹 페이지의 코드를 중복 사용하기 위해 함수로 만들었다.
def template(contents, content, select=None, id=None):
    contextUI = ''
    
    if id != None:
        contextUI = f'''
            <li><a href="/update/{id}/">수정</a></li>
            <li><form action="/delete/{id}/" method="POST"><input type="submit" value="삭제"></form></li>
        '''
    
    if select == "read" or select == "update" or select == "create":
        return f'''<!doctype html>
            <html>
                <body>
                    <h1><a href="/">게시판</a></h1>
                    {content}
                    <ul>
                        <li><a href="/create/">create</a></li>
                        {contextUI}
                    </ul>
                </body>
            </html>
            ''' 
    else:
        return f'''<!doctype html>
            <html>
                <body>
                    <h1><a href="/">게시판</a></h1>
                    <form id="form" action="/search/" method="POST">
                        <select name="type">
                            <option selected value="">선택</option>
                            <option value="title">제목</option>
                            <option value="content">내용</option>
                            <option value="all">제목 + 내용</option>
                        </select>
                        <input type="text" name="word">
                        <input type="submit" value="검색">
                    </form>
                    <ol>
                        {contents}
                    </ol>
                    {content}

                    <ul>
                        <li><a href="/create/">create</a></li>
                        {contextUI}
                    </ul>
                </body>
            </html>
            '''
    

#main 웹 페이지 이다.
@app.route('/')
def index():
    return template(getContents(), '')

@app.route('/create/', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        content = '''
            <form action="/create/" name="board_info" method="POST">
                <p><input type="text" name="title" placeholder="제목"></p>
                <p><input type="text" name="author" placeholder="작성자"></p>
                <p><textarea name="content" placeholder="내용"></textarea></p>
                
                <p><input type="submit" value="생성"></p>
        '''
        return template(getContents(), content, "create")
    
    elif request.method == 'POST':
        sql_query = "INSERT INTO boards (title,content,author) VALUES(%s,%s,%s)"
        data = [request.form['title'], request.form['content'], request.form['author']]
        cur.execute(sql_query, data)
        db.commit()
        
        sql_query = "SELECT id FROM boards WHERE title = %s AND content = %s AND author = %s"
        cur.execute(sql_query, data)
        create_result = cur.fetchall()

        url = '/read/'+ str(create_result[0][0]) + '/'

        return redirect(url)

#게시판 정보를 읽어와 해당 글로 이동해주는 기능이다.
@app.route('/read/<int:id>/')
def read(id):
    title, content, author = read_board(id)
    return template(getContents(), f'<h2>{title}</h2>{content}', "read", id)

#게시판에 작성된 글을 수정하는 기능이다.
@app.route('/update/<int:id>/', methods = ['GET', 'POST'])
def update(id):
    if request.method == 'GET':
        title, content, author = read_board(id)
        web_content = f'''
            <form action="/update/{id}/" name="board_info" method="POST">
                <p><input type="text" name="title" placeholder="제목" value="{title}"></p>
                <p><input type="text" name="author" placeholder="작성자" value="{author}"></p>
                <p><textarea name="content" placeholder="내용">{content}</textarea></p>
                
                <p><input type="submit" value="수정"></p>
        '''
        return template(getContents(), web_content, "update", id)
    
    elif request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        boards = getBoards()

        for board in boards:
            if id == board['id']:
                board['title'] = title
                board['content'] = content
                board['author'] = author
                break
        print("update_board = ")
        print(board)
        
        sql_query = "UPDATE boards SET title=%s, content=%s, author=%s WHERE id=%s;"
        data = [board['title'], board['content'], board['author'], board['id']]
        cur.execute(sql_query, data)
        db.commit()

        url = '/read/'+ str(id) + '/'

        return redirect(url)                #수정버튼을 누르면 수정된 글로 redirection 되도록 했다.
    
#게시판에 작성된 글을 삭제하는 기능이다.
@app.route('/delete/<int:id>/', methods=['POST'])
def delete(id):
    sql_query = "DELETE FROM boards WHERE id = %s;"
    cur.execute(sql_query, id)
    db.commit()
    return redirect('/')            #글을 삭제한 후에는 메인 페이지로 redirecction 되도록 했다.

@app.route('/search/', methods = ['POST'])
def search():
    boards = getBoards()
    search_content = ''
    type = request.form['type']
    word = request.form['word']

    if type == "title":
        search_content = search_board(type, word)
    elif type == "content":
        search_content = search_board(type, word)
    elif type == "all":
        for board in boards:
            if board['title'].find(word) != int(-1) or board['content'].find(word) != int(-1):
                search_content = search_content + f'<li><a href="/read/{board["id"]}/">{board["title"]}</a></li>'
                break
            elif board['title'].find(word) == int(-1) and board['content'].find(word) == int(-1):
                search_content = '<p>찾으시는 게시글이 없습니다.</p><a href= "/"</a>'
    else:
        search_content = '<p>찾으시는 게시글이 없습니다.</p><a href= "/"</a>'
    
    return  template(search_content, '')


app.run(debug=True)