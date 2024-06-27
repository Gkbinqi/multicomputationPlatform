# 导入基本模块
import datetime
import os
from flask import (Flask, render_template, request, redirect, url_for, session, make_response
, json, jsonify, abort, flash)
from wtforms import Form, StringField, PasswordField, SubmitField, validators  # 类型
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, Email, EqualTo  # 验证数据不能为空 验证数据是否相同

# 导入登录模块


# 导入数据库模块
from flask_sqlalchemy import SQLAlchemy
import pymysql

pymysql.install_as_MySQLdb()

# 创建app实例
app = Flask(__name__)


# 配置设置 包括数据库连接信息
class Config:
    """配置参数"""
    SECRET_KEY = os.urandom(16)  # 设置密钥
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/flaskdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app.config['JSON_AS_ASCII'] = False

app.config.from_object(Config)  # 从Config类中加载配置参数
db = SQLAlchemy(app)  # 创建数据库实例


class Role(db.Model):
    """角色表"""
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)  # 主键 设置主键后默认设置自增长
    name = db.Column(db.String(32), unique=True)  # 角色名

    def __repr__(self):
        return 'Role %d %s' % (self.id, self.name)


# 创建数据库模型类
class User(db.Model):
    """用户表"""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)  # 主键 设置主键后默认设置自增长
    name = db.Column(db.String(32), unique=True)  # 用户名
    password = db.Column(db.String(32))  # 密码
    # 表关系 一个用户只能由一种角色 一个角色可以有多个用户 外键Foreign Key, 用于关联另外一张表
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    def __repr__(self):
        return 'User %d %s %s %d' % (self.id, self.name, self.password, self.role_id)

    def check_password(self, password):
        return self.password == password


class Room(db.Model):
    """房间表"""
    __tablename__ = 'room'

    id = db.Column(db.Integer, primary_key=True)  # 主键 设置主键后默认设置自增长
    name = db.Column(db.String(32), unique=True)  # 房间名
    capacity = db.Column(db.Integer)  # 房间容量
    password = db.Column(db.String(32))  # 房间密码 自动生成
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 表关系 一个房间可以有多个用户 外键Foreign Key, 用于关联另外一张表

    participants = db.relationship('User', secondary='room_user', backref='rooms')


room_user = db.Table('room_user',
                     db.Column('room_id', db.Integer, db.ForeignKey('room.id'), primary_key=True),
                     db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
                     )

# 登录管理模块
# 使用session记录用户登录状态
# session设置如下:
# session['id'] = user.id
# session['name'] = user.name
# session['role_id'] = user.role_id
# session.permanent = True  # 设置session过期时间为永久

'''''''''''''''''
***以下为路由模块***
'''''''''''''''''


@app.route('/', methods=['GET', 'POST'])  # 定义路由
def root():
    # 检查session是否存在
    if 'id' in session:
        uid = session.get('id')
        user = User.query.filter_by(id=uid).first()
        if user:
            return redirect(url_for('dashboard'))
        else:
            session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        if not name or not password:
            return render_template('login.html'
                                   , error_message="请填写用户名和密码！")

        user = User.query.filter_by(name=name).first()

        if user and user.check_password(password):
            session['id'] = user.id
            session['name'] = user.name
            session['role_id'] = user.role_id
            print(f'{datetime.datetime.now()}, {name} 登录成功')
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html'
                                   , error_message="用户名或密码无效！")

    return render_template('login.html')  # GET请求返回登录页面


@app.route('/logout')
def logout():
    if 'id' not in session:
        abort(401)
    name = session.get('name')
    session.pop('id')
    session.pop('name')
    session.pop('role_id')
    print(f'{datetime.datetime.now()}, {name} 登出成功')
    return redirect(url_for('login'))


@app.route('/basic_transformer/<int:uid>', methods=['GET', 'POST'])
def user(uid):
    return (f'<h1>Wow, how can you find this page?</h1>'
            f'<h1>User {uid}</h1>'
            f'<p>This is the user page for user {uid}.</p>')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        role_id = 2  # 默认为普通用户角色
        # 检查是否有相同用户名
        user = User.query.filter_by(name=name).first()
        if user:
            return render_template('register.html'
                                   , error_message="用户名已存在！")
        else:  # 创建对象 插入数据
            user = User(name=name, password=password, role_id=role_id)
            db.session.add(user)  # session记录到数据库
            db.session.commit()  # 提交任务

            print(f'{datetime.datetime.now()}, {name, password, role_id} 注册成功')
            return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'id' not in session:
        return redirect(url_for('login'))
    rooms = Room.query.all()
    return render_template('dashboard.html', rooms=rooms)


@app.route('/search_room', methods=['GET'])
def search_room():
    room_id = request.args.get('id')
    if room_id:
        room = Room.query.filter_by(id=room_id).first()  # 在数据库中查找房间
        if room:
            return redirect(url_for('password', room_id=room.id))
        else:
            flash('房间不存在')
            return redirect(url_for('dashboard'))
    else:
        flash('请输入房间ID')
        return redirect(url_for('dashboard'))


@app.route('/password/<int:room_id>', methods=['GET', 'POST'])
def password(room_id):
    return render_template('password.html', room_id=room_id)


@app.route('/verify_password/<int:room_id>', methods=['POST'])
def verify_password(room_id):
    password = request.form.get('password')
    room = Room.query.get(room_id)
    if room and room.password == password:
        return redirect(url_for('room', room_id=room.id))
    else:
        flash('密码错误', 'error')
        return redirect(url_for('dashboard'))


@app.route('/dashboard/room/<int:room_id>', methods=['GET', 'POST'])
def room(room_id):
    # 检查session是否存在
    if 'id' not in session:
        return redirect(url_for('login'))
    # 查询房间是否存在
    room = Room.query.filter_by(id=room_id).first()
    if not room:
        return abort(404)

    if request.method == 'GET':
        return render_template('room.html', room=room)
    elif request.method == 'POST':
        if 'join' in request.form:
            # 加入房间
            if room.capacity > len(room.invited_users):
                room.invited_users.append(session['id'])
                db.session.commit()
                return redirect(url_for('room', room_id=room_id))
            else:
                return render_template('room.html', room=room, error_message='房间已满！')
        elif 'quit' in request.form:
            # 退出房间
            room.invited_users.remove(session['id'])
            db.session.commit()
            return redirect(url_for('room', room_id=room_id))
        elif 'invite' in request.form:
            # 邀请用户
            user_name = request.form.get('user_name')
            user = User.query.filter_by(name=user_name).first()
            if user:
                room.invited_users.append(user.id)
                db.session.commit()
                return redirect(url_for('room', room_id=room_id))
            else:
                return render_template('room.html', room=room, error_message='用户不存在！')
        elif 'create' in request.form:
            # 创建房间
            name = request.form.get('name')
            capacity = request.form.get('capacity')
            password = request.form.get('password')
            owner_id = session['id']
            # 检查是否有相同房间名
            room = Room.query.filter_by(name=name).first()
            if room:
                return render_template('room.html', room=room, error_message='房间名已存在！')
            else:  # 创建对象 插入数据
                room = Room(name=name, capacity=capacity, password=password, owner_id=owner_id)
                db.session.add(room)  # session记录到数据库
                db.session.commit()  # 提交任务
                return redirect(url_for('room', room_id=room.id))
        else:
            return redirect(url_for('room', room_id=room_id))
    return render_template('room.html')


# 自定义错误页面
@app.errorhandler(401)
def handle_401(err):
    return render_template('401.html'), 401, err.description


@app.errorhandler(404)
def handle_404(err):
    return render_template('404.html'), 401, err.description


def init_db():
    with app.app_context():
        # 清楚所有表格
        db.drop_all()
        # 创建所有表格
        db.create_all()

        # 创建对象 插入数据
        db.session.add_all([Role(name='admin'), Role(name='user')])
        db.session.commit()

        # 创建对象 插入数据
        admin = User(name='admin', password='admin', role_id=1)  # 给用户分配角色
        bot01 = User(name='bot01', password='bot', role_id=2)
        bot02 = User(name='bot02', password='bot', role_id=2)
        db.session.add_all([admin, bot01, bot02])  # session记录到数据库
        db.session.commit()  # 提交任务

        global current_rooms  # 使用全局变量 需使用global关键字声明
        # 创建房间
        print('创建示例房间')
        for i in range(1, 11):
            room = Room(name=f'房间{i}', capacity=10, password='123456', owner_id=1)
            db.session.add(room)  # session记录到数据库
        db.session.commit()

        # 查询数据
        # 查询所有用户
        users = User.query.all()
        for user in users:
            print(user.name, user.password, user.role_id)

        # 查询所有房间
        rooms = Room.query.all()
        for room in rooms:
            print(room.id, room.name, room.capacity, room.password, room.owner_id)


if __name__ == '__main__':
    if 'y' == input('是否初始化数据库？(y/n): '):
        init_db()
    app.run(debug=True)  # 启动Flask应用
