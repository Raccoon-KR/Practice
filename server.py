from flask import Flask, render_template, request, redirect, Blueprint, send_file
import pymysql, os

#mysql과 연동하기 위한 코드
db = pymysql.connect(host='127.0.0.1',
                     user='root',
                     password='root',
                     db='testdb',
                     charset='utf8'
                     )

cur = db.cursor()

app = Flask(__name__)

verify = None
private_verify = None

#db에 있는 값들을 가지고와 딕셔너리 형태로 만들어준다.
def getBoards():
    boards = []
    
    sql = "SELECT boards.id,title,content,author,file_name  FROM boards LEFT JOIN users ON boards.author_id = users.id;"
    cur.execute(sql)
    result = cur.fetchall()

    for i in range(len(result)):
        boards.append({
            "id": result[i][0],
            "title": result[i][1],
            "content": result[i][2],
            "author": result[i][3],
            "file_name": result[i][4]
            })

    return boards


#회원가입한 user의 정보를 db에서 가지고 오는 함수
def getUsers():
    users = []
    
    sql = "SELECT * FROM users;"
    cur.execute(sql)
    result = cur.fetchall()

    for i in range(len(result)):
        users.append({
            "id": result[i][0],
            "author": result[i][1],
            "user_id": result[i][2],
            "password": result[i][3],
            })

    return users


# db정보를 html형식으로 바꿔주는 함수
def getContents():
    liTags = ''
    boards = getBoards()

    for board in boards:        #정보를 게시글(링크)의 목록으로 구현해준다.
        liTags = liTags + f'<li><a href="/read/{board["id"]}/">{board["title"]}</a></li>'
    return liTags


# db에서 정보들을 읽어오는 함수
def read_board(id):
    title, content, author, file_name = '', '', '', ''
    boards = getBoards()

    for board in boards:
        if id == board['id']:
            title = board['title']
            content = board['content']
            author = board['author']
            file_name = board['file_name']
            break
    return title, content, author, file_name


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
def template(contents, content, verify=None, select=None, id=None, file_name = None):
    contextUI = ''
    
    if id != None:
        contextUI = f'''
            <li><a href="/update/{id}/">수정</a></li>
            <li><form action="/delete/{id}/" method="POST"><input type="submit" value="삭제"></form></li>
        '''
    
    if verify == None:
        return f'''<!doctype html>
            <html>
                <body>
                    {content}
                    <p>
                        <h1><a href="/">게시판</a></h1>
                        <h4><a href="/secret_login/">Private 게시판</a></h4>
                    </p>
                    <form action="/login/" id="sign_up" method="POST">
                        <p>
                            <input type="text" name="id" placeholder="id"><br>
                            <input type="text" name="password" placeholder="password">
                            <button type="submit"> 로그인 </button>
                        </p>
                    </form>
                    <p>
                        <button type="button" onclick="location.href='http://127.0.0.1:5000/sign_up/' "> 회원가입 </button>
                        <button type="button" onclick="location.href='http://127.0.0.1:5000/find_id/' "> 아이디 찾기 </button>
                        <button type="button" onclick="location.href='http://127.0.0.1:5000/find_pw/' "> 비밀번호 찾기 </button>
                    </p>
                </body>
            </html>
        '''
    
    elif verify != None:
        if select == "read" or select == "update" or select == "create":
            if file_name != None:
                return f'''<!doctype html>
                    <html>
                        <body>
                            <h1><a href="/">게시판</a></h1>
                            {content}
                            <br>
                            <form action="/download/{id}/">
                                {file_name}
                                <input type="submit" value="다운로드">
                            </form>
                            <ul>
                                <li><a href="/create/">create</a></li>
                                {contextUI}
                            </ul>
                        </body>
                    </html>
                    '''
            elif file_name == None:
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
                        <p>
                            <h1><a href="/">게시판</a></h1>
                            <h4><a href="/secret_login/">Private 게시판</a></h4>
                        </p>
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


#회원가입 화면
def sign_up_template(alert = None):
    if alert == None :
        return  '''<!doctype html>
                <html>
                    <body>
                        <h1><a href="/">게시판</a></h1>
                        <form action="/sign_up_check/" name="sign_up_info" method="POST">
                            <br>사용자 이름<br>
                            <input type="text" name="author">
                            <br>아이디<br>
                            <input type="text" name="author_id">
                            <br>비밀번호<br>
                            <input type="text" name="author_pw">
                            <br>비밀번호 확인<br>
                            <input type="text" name="pw_check">

                            <br><br><button type="submit"> 회원가입 </button>
                        </form>
                    </body>
                </html>
                '''
    
    elif alert != None :
        return  f'''<!doctype html>
                <html>
                    <body>
                        {alert}
                        <h1><a href="/">게시판</a></h1>
                        <form action="/sign_up_check/" name="sign_up_info" method="POST">
                            <br>사용자 이름<br>
                            <input type="text" name="author">
                            <br>아이디<br>
                            <input type="text" name="author_id">
                            <br>비밀번호<br>
                            <input type="text" name="author_pw">
                            <br>비밀번호 확인<br>
                            <input type="text" name="pw_check">

                            <br><br><button type="submit"> 회원가입 </button>
                        </form>
                    </body>
                </html>
                '''

# 아이디와 비밀번호를 찾는 html
def find_template(i, alert = None):
    if i == 0:
        if alert == None :
            return '''<!doctype html>
                    <html>
                        <body>
                            <h1><a href="/">게시판</a></h1>
                            <form action="/id_check/" name="sign_up_info" method="POST">
                                <br>사용자의 이름을 입력해주세요<br>
                                <input type="text" name="author">
                                <br>사용자의 비밀번호를 입력해주세요<br>
                                <input type="text" name="author_pw">

                                <br><br><button type="submit"> 아이디 찾기 </button>
                            </form>
                        </body>
                    </html>
                    '''
        elif alert != None :
            return f'''<!doctype html>
                    <html>
                        {alert}
                        <body>
                            <h1><a href="/">게시판</a></h1>
                            <form action="/id_check/" name="sign_up_info" method="POST">
                                <br>사용자의 이름을 입력해주세요<br>
                                <input type="text" name="author">
                                <br>사용자의 비밀번호를 입력해주세요<br>
                                <input type="text" name="author_pw">

                                <br><br><button type="submit"> 아이디 찾기 </button>
                            </form>
                        </body>
                    </html>
                    '''
    elif i == 1:
        if alert == None :
            return '''<!doctype html>
                    <html>
                        <body>
                            <h1><a href="/">게시판</a></h1>
                            <form action="/pw_check/" name="sign_up_info" method="POST">
                                <br>사용자의 이름을 입력해주세요<br>
                                <input type="text" name="author">
                                <br>사용자의 아이디를 입력해주세요<br>
                                <input type="text" name="author_id">

                                <br><br><button type="submit"> 비밀번호 찾기 </button>
                            </form>
                        </body>
                    </html>
                    '''
        elif alert != None :
            return f'''<!doctype html>
                    <html>
                        {alert}
                        <body>
                            <h1><a href="/">게시판</a></h1>
                            <form action="/pw_check/" name="sign_up_info" method="POST">
                                <br>사용자의 이름을 입력해주세요<br>
                                <input type="text" name="author">
                                <br>사용자의 아이디를 입력해주세요<br>
                                <input type="text" name="author_id">

                                <br><br><button type="submit"> 비밀번호 찾기 </button>
                            </form>
                        </body>
                    </html>
                    '''


#                   여기서 부터 private 게시판을 위한 함수


def private_template(contents, content, select=None, id=None):
    contextUI = ''
    if id != None:
        contextUI = f'''
            <li><a href="/private_update/{id}/" method="POST">수정</a></li>
            <li><form action="/private_delete/{id}/" method="POST"><input type="submit" value="삭제"></form></li>
        '''
    print(select)
    if select == "read" or select == "update" or select == "create":
        return f'''<!doctype html>
            <html>
                <body>
                    <h1><a href="/private/">Private 게시판 </a></h1>
                    <h4><a href="/">게시판</a></h4>
                    {content}
                    <ul>
                        <li><a href="/private_create/" method="POST">create</a></li>
                        {contextUI}
                    </ul>
                </body>
            </html>
            ''' 
    else:
        return f'''<!doctype html>
            <html>
                <body>
                    <h1><a href="/private/">Private 게시판 </a></h1>
                    <h4><a href="/">게시판</a></h4>
                    <form id="form" action="/private_search/" method="POST">
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
                        <li><a href="/private_create/" method="POST">create</a></li>
                        {contextUI}
                    </ul>
                </body>
            </html>
            '''

        
def private_login(alert):
    return f'''<!doctype html>
            <html>
                <body>
                    <p>
                        <a>{alert}</a>
                        <h1><a href="/">게시판</a></h1>
                        <h4><a href="/secret_login/">Private 게시판</a></h4>
                    </p>
                    <form action="/private_login_check/" id="sign_up" method="POST">
                        <p>"비밀번호를 입력해 주세요"</p>
                        <p>
                            <input type="text" name="password" placeholder="password">
                            <button type="submit"> 로그인 </button>
                        </p>
                    </form>
                </body>
            </html>
        '''

def private_getBoards():
    boards = []
    
    sql = "SELECT * FROM private_boards;"
    cur.execute(sql)
    result = cur.fetchall()

    boards = []

    for i in range(len(result)):
        boards.append({"id": result[i][0], "title": result[i][1], "content": result[i][2]})

    return boards

def private_getContents():
    liTags = ''
    boards = private_getBoards()

    for board in boards:        #정보를 게시글(링크)의 목록으로 구현해준다.
        liTags = liTags + f'<li><a href="/private_read/{board["id"]}/">{board["title"]}</a></li>'
    return liTags

def private_read_board(id):
    title = ''
    content = ''
    boards = private_getBoards()

    for board in boards:
        if id == board['id']:
            title = board['title']
            content = board['content']
            break
    return title, content

def private_search_board(type, word):
    web_content = ''
    boards = private_getBoards()

    for board in boards:
        if board[type].find(word) != int(-1):
            web_content = web_content + f'<li><a href="/private_read/{board["id"]}/">{board["title"]}</a></li>'
            break

    if web_content == '':
        web_content = '<p>찾으시는 게시글이 없습니다.</p><a href= "/private/"</a>'

    return web_content



#                      여기서부터 본 게시판을 위한 route



#main 웹 페이지 이다.
@app.route('/', methods=['GET', 'POST'])
def index():
    return template(getContents(), '', verify)


#게시판을 생성하는 기능
@app.route('/create/', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        content = f'''
            <form action="/create/" name="board_info" method="POST" enctype="multipart/form-data", target='blankifr'>
                <p><input type="text" name="title" placeholder="제목"></p>
                <p><textarea name="content" placeholder="내용"></textarea></p>
                <p><input type="file" name="file" multiple/></p>

                <p><input type="submit" value="생성"></p>
        '''
        return template(getContents(), content, verify, "create")
    
    elif request.method == 'POST':
        if request.form['title'] == '' :
            alert = f'''<script>
                alert("제목을 입력해 주세요!")
                </script>
                '''
            return template(getContents(), alert, verify)
        else :
            f = request.files['file']
            f_split = str(f).split("'")[1]

            sql_query = "INSERT INTO boards (title,content,author_id,file_name) VALUES(%s,%s,%s,%s)"
            data = [request.form['title'], request.form['content'], verify, f_split]
            cur.execute(sql_query, data)
            db.commit()

            if not f:
                pass
            else :
                f.save('./upload/' + f.filename)
            
            sql_query = "SELECT id FROM boards WHERE title = %s AND content = %s AND author_id = %s AND file_name = %s"
            cur.execute(sql_query, data)
            create_result = cur.fetchall()

            url = '/read/'+ str(create_result[0][0]) + '/'

            return redirect(url)


#게시판 정보를 읽어와 해당 글로 이동해주는 기능이다.
@app.route('/read/<int:id>/')
def read(id):
    title, content, author, file_name = read_board(id)

    return template(getContents(), f'<h2>{title}</h2>{content}', verify, "read", id, file_name)


#게시판에 작성된 글을 수정하는 기능이다.
@app.route('/update/<int:id>/', methods = ['GET', 'POST'])
def update(id):
    if request.method == 'GET':
        title, content, author, file_name = read_board(id)
        web_content = f'''
            <form action="/update/{id}/" name="board_info" method="POST">
                <p><input type="text" name="title" placeholder="제목" value="{title}"></p>
                <p><textarea name="content" placeholder="내용">{content}</textarea></p>
                
                <p><input type="submit" value="수정"></p>
        '''
        return template(getContents(), web_content, verify, "update", id)
    
    elif request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        users = getUsers()
        for user in users:
            if verify == user['id']:    #글을 작성한 사용자만 수정을 할 수 있다.
                boards = getBoards()
                for board in boards:
                    if id == board['id']:
                        board['title'] = title
                        board['content'] = content
                        break
                sql_query = "UPDATE boards SET title=%s, content=%s WHERE id=%s;"
                data = [board['title'], board['content'], board['id']]
                cur.execute(sql_query, data)
                db.commit()

                url = '/read/'+ str(id) + '/'

                return redirect(url)        #수정버튼을 누르면 수정된 글로 redirection 되도록 했다.
            else:
                web_content = f'''
                    <script>
                        alert("사용자가 작성한 게시판만 수정이 가능합니다.")
                    </script>

                '''
                return template(getContents(), web_content, verify)


#게시판에 작성된 글을 삭제하는 기능이다.
@app.route('/delete/<int:id>/', methods=['POST'])
def delete(id):
    sql_query = "DELETE FROM boards WHERE id = %s;"
    cur.execute(sql_query, id)
    db.commit()
    return redirect('/')            #글을 삭제한 후에는 메인 페이지로 redirecction 되도록 했다.


#게시판의 제목,내용에서 검색을 해서 찾아주는 기능
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


#첫 화면에서 회원가입 버튼을 눌렀을 때 회원가입 사이트로 redirect해주는 기능
@app.route('/sign_up/', methods=['GET', 'POST'])
def sign_up():
    return sign_up_template()


#회원가입 정보를 다 입력하면 중복 비교후 회원가입을 완료해주는 기능
@app.route('/sign_up_check/', methods=['GET', 'POST'])
def sign_up_check():
    author = request.form['author']
    author_id = request.form['author_id']
    author_pw = request.form['author_pw']
    check_pw = request.form['pw_check']
    users = getUsers()
    error = None

    for user in users:
        if user['user_id'] == author_id:
            error = "중복된 아이디가 있습니다. 다시 입력해주세요."
            break
        elif author_pw != check_pw:
            error = "입력하신 비밀번호가 일치하지 않습니다. 다시 입력해주세요."
            break
        elif author_id == "" :
            error = "아이디를 입력해주세요."
            break
        elif author_pw == "" :
            error = "비밀번호를 입력해주세요."
            break
        elif author == "" :
            error = "이름을 입력해주세요."
            break

    if error == None:
        sql_query = "INSERT INTO users (author,user_id,password) VALUES(%s,%s,%s)"
        data = [request.form['author'], request.form['author_id'], request.form['author_pw']]

        cur.execute(sql_query, data)
        db.commit()

        return template(getContents(), '')
    
    elif error != None :
        alert = f'''<script>
        alert("{error}")
        </script>
        '''
        return sign_up_template(alert)


#login했을 때 아이디 비밀번호를 check하는 기능
@app.route('/login/', methods=['POST'])
def login():
    user_id = request.form['id']
    password = request.form['password']
    users = getUsers()
    global verify

    for user in users:
        if user_id == user['user_id'] and password == user['password']:
            verify = user['id']
            break

    return template(getContents(), '', verify)


#사용자에게 id를 찾기 위한 회원정보를 받는 기능
@app.route('/find_id/')
def find_id():
    return  find_template(0)


#사용자에게 비밀번호를 찾기 위한 회원정보를 받는 기능
@app.route('/find_pw/')
def find_pw():
    return  find_template(1)


#id를 찾기위해 이름과, 비밀번호를 입력받아, db와 비교해서 아이디를 알려주는 기능
@app.route('/id_check/', methods=['GET', 'POST'])
def id_check():
    author = request.form['author']
    password = request.form['author_pw']
    users = getUsers()

    for user in users:
        if author == user['author'] and password == user['password']:
            alert = f'''<script>
                alert("찾으시는 id는 {user['user_id']} 입니다.")
                </script>
                '''
            return template(getContents(), alert, verify)
        elif author != user['author'] or password != user['password']:
            alert = f'''<script>
                alert("입력하신 정보에 맞는 회원정보가 존재하지 않습니다. 다시 입력해주세요.")
                </script>
                '''
            return find_template(0, alert)


#비밀번호를 찾기위해 이름과, id를 입력받아, db와 비교해서 비밀번호를 알려주는 기능
@app.route('/pw_check/', methods=['GET', 'POST'])
def pw_check():
    author = request.form['author']
    user_id = request.form['author_id']
    users = getUsers()

    for user in users:
        if author == user['author'] and user_id == user['user_id']:
            alert = f'''<script>
                alert("찾으시는 비밀번호는 {user['password']} 입니다.")
                </script>
                '''
            return template(getContents(), alert, verify)
        elif author != user['author'] or user_id != user['user_id']:
            alert = f'''<script>
                alert("입력하신 정보에 맞는 회원정보가 존재하지 않습니다. 다시 입력해주세요.")
                </script>
                '''
            return find_template(1, alert)
    return


#게시판에 올린 파일을 다운로드 할 수 있게 하는 기능
@app.route('/download/<int:id>/')
def download(id):
    title, content, author, file_name = read_board(id)
    files = os.getcwd() + "\\upload\\" +  file_name

    return send_file(files, as_attachment=True)




#                   여기서 부터 private 게시판을 위한 route

@app.route('/secret_login/', methods = ['GET', 'POST'])
def secret_login():
    return private_login("")

@app.route('/private_login_check/', methods = ['GET','POST'])
def private_login_check():
    global private_verify
    if "1234" == request.form["password"] :
        private_verify = 1
        print(private_verify)
        return private_template(private_getContents(), '')
        
    else :
        alert = f'''<script>
                alert("알맞은 비밀번호가 아닙니다. 확인 후 다시 입력해주세요")
                </script>
                '''
        return private_login(alert)

@app.route('/private/', methods = ['GET', 'POST'])
def private():
    global private_verify
    if private_verify == None :
        alert = f'''<script>
                    alert("비밀번호를 입력해야 접속 할 수 있습니다. 비밀번호를 입력해주세요.")
                    </script>
                    '''
        return private_login(alert)
    else :
        return private_template(private_getContents(), '', private_verify)

@app.route('/private_create/', methods = ['GET', 'POST'])
def private_create():
    global private_verify
    print("/private_create/")
    print(private_verify)
    if private_verify != None :
        content = '''
            <form action="/private_create_board/" name="board_info" method="POST">
                <p><input type="text" name="private_title" placeholder="제목"></p>
                <p><textarea name="private_content" placeholder="내용"></textarea></p>
                
                <p><input type="submit" value="생성"></p>
        '''
        return private_template(private_getContents(), content, '' "create")
    else :
        alert = f'''<script>
                    alert("비밀번호를 입력해야 접속 할 수 있습니다. 비밀번호를 입력해주세요.")
                    </script>
                    '''
        return private_login(alert)

@app.route('/private_create_board/', methods = ['GET', 'POST'])
def private_create_board():
    sql_query = "INSERT INTO private_boards (title,content) VALUES(%s,%s)"
    data = [request.form['private_title'], request.form['private_content']]
    cur.execute(sql_query, data)
    db.commit()
        
    sql_query = "SELECT id FROM private_boards WHERE title = %s AND content = %s"
    cur.execute(sql_query, data)
    create_result = cur.fetchall()

    url = '/private_read/'+ str(create_result[0][0]) + '/'

    return redirect(url)

@app.route('/private_read/<int:id>/', methods = ['GET', 'POST'])
def private_read(id):
    title, content = private_read_board(id)
    return private_template(private_getContents(), f'<h2>{title}</h2>{content}', "read", id)

@app.route('/private_update/<int:id>/', methods = ['GET', 'POST'])
def private_update(id):
    if request.method == 'GET':
        title, content = private_read_board(id)
        web_content = f'''
            <form action="/private_update/{id}/" name="board_info" method="POST">
                <p><input type="text" name="title" placeholder="제목" value="{title}"></p>
                <p><textarea name="content" placeholder="내용">{content}</textarea></p>
                
                <p><input type="submit" value="수정"></p>
        '''
        return private_template(private_getContents(), web_content, "update", id)
    
    elif request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        boards = private_getBoards()

        for board in boards:
            if id == board['id']:
                board['title'] = title
                board['content'] = content
                break
        
        sql_query = "UPDATE private_boards SET title=%s, content=%s WHERE id=%s;"
        data = [board['title'], board['content'], board['id']]
        cur.execute(sql_query, data)
        db.commit()

        url = '/private_read/'+ str(id) + '/'

        return redirect(url)                 #수정버튼을 누르면 수정된 글로 redirection 되도록 했다.

@app.route('/private_delete/<int:id>/', methods=['POST'])
def private_delete(id):
    sql_query = "DELETE FROM private_boards WHERE id = %s;"
    cur.execute(sql_query, id)
    db.commit()
    return redirect('/private/')            #글을 삭제한 후에는 메인 페이지로 redirecction 되도록 했다.

@app.route('/private_search/', methods = ['POST'])
def private_search():
    boards = private_getBoards()
    search_content = ''
    type = request.form['type']
    word = request.form['word']

    if type == "title":
        search_content = private_search_board(type, word)
    elif type == "content":
        search_content = private_search_board(type, word)
    elif type == "all":
        for board in boards:
            if board['title'].find(word) != int(-1) or board['content'].find(word) != int(-1):
                search_content = search_content + f'<li><a href="/private_read/{board["id"]}/">{board["title"]}</a></li>'
                break
            elif board['title'].find(word) == int(-1) and board['content'].find(word) == int(-1):
                search_content = '<p>찾으시는 게시글이 없습니다.</p><a href= "/private/"</a>'
    else:
        search_content = '<p>찾으시는 게시글이 없습니다.</p><a href= "/private/"</a>'
    
    return  private_template(search_content, '')


app.run(debug=True)
