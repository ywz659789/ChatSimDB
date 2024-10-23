from flask import Flask, render_template, request, jsonify,session
import pymysql
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_cors import CORS
import datetime

pymysql.install_as_MySQLdb()

app = Flask(__name__)
# 配置数据库连接的用户名，密码，端口和数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:2w1qaszx@localhost:3306/study'  # 请根据实际情况修改
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'your_secret_key'  # 设置一个密钥，用于会话


# 创建SQLAlchemy实例
db = SQLAlchemy(app)
CORS(app)
USER_ID = 0

def User(ID):
    query = text("SELECT PersonalInfo FROM user WHERE ID = :ID")
    params = {'ID': ID}
    messages = db.session.execute(query, params)
    for s in messages:
        personalInfo = s[0]

    return personalInfo


# 查询所有历史消息
def select_message_all(group_id):
    message_list = []
    query = text("CALL history_messages(:group_id)")
    params = {'group_id': group_id}
    messages = db.session.execute(query, params)
    for s in messages:
        dic = {
            'id': s[0],
            'content': s[1],
            'sender': s[2],
            'receiver': s[3],
            'timestamp': s[4]
        }
        message_list.append(dic)
    return message_list

# 调用存储过程发送消息
def call_insert_message(content, sender, receiver):
    query = text("CALL insert_message(:content, :sender,:receiver)")
    params = {'content': content, 'sender': sender, 'receiver': receiver}
    result = db.session.execute(query, params)
    db.session.commit()
    return result.fetchall()


# 删除消息
def call_sub_message(id, user_id):
    sql0 = text("SELECT sender FROM history_message WHERE id = :id")
    params0 = {'id': id}
    sender_result = db.session.execute(sql0, params0)
    sender = sender_result.fetchone()[0]  # 获取结果的第一行的第一列
    #print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!sender=", int(sender)," user_id=",int(user_id))
    if (int(sender) == int(user_id)):
        sql = text("CALL delete_chat_record(:id)")
        params = {'id': id}
        db.session.execute(sql, params)
        db.session.commit()
        print("成功！")
        return "成功撤回"

# 前后端交互
@app.route('/')
def hello_world():
    return render_template("login.html")  # 跳转到登录网页


@app.route('/login', methods=['POST'])
def login():
    ID = request.form.get('ID')
    password = request.form.get('password')
    personalInfo = User(ID)
    #print("ID:", ID)
    #print("password:", password, "personalInfo:", personalInfo)

    if password == personalInfo:
        session['user_id'] = ID  # 在会话中存储用户 ID
        return render_template("chat.html")  # 跳转到chat.html文件
    else:
        return render_template("login.html")


@app.route('/get_chat_history', methods=['GET'])
def show_message_list():
    response_object = {'status': 'success'}
    group_id = request.args.get('group_id')
    messages = select_message_all(group_id)
    response_object['message'] = '查询该群所有聊天记录成功!'
    response_object['data'] = messages
    return jsonify(response_object)


# 在路由中调用存储过程发送消息
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    sender = session['user_id']  # 从会话中获取用户 ID
    content = request.form.get('content')
    receiver = request.form.get('receiver')
    result = call_insert_message(content, sender, receiver)
    return jsonify(result)


@app.route('/delete_message', methods=['POST'])
def delete_message():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    user_id = session['user_id']
    id = request.form['id']
    result = call_sub_message(id, user_id)
    db.session.commit()
    if result == "只能撤回自己发出的消息":
        return jsonify({"status": "error", "message": result}), 403
    return jsonify({"status": "success", "message": result})


if __name__ == '__main__':
    app.run(debug=True)
