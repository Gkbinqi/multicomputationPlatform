# 导入基本模块
import datetime
import os
from flask import (Flask, render_template, request, redirect, url_for, session, make_response
, json, jsonify, abort, flash)

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
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 表关系 外键Foreign Key, 用于关联另外一张表
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


def return_dashboard():
    if session.get('role_id') == 1:
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('dashboard'))


@app.route('/', methods=['GET', 'POST'])  # 定义路由
def root():
    # 检查session是否存在
    if 'id' in session:
        uid = session.get('id')
        user = User.query.filter_by(id=uid).first()
        if user:
            if session.get('role_id') == 1:
                return redirect(url_for('admin_dashboard'))
            else:
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
            if session.get('role_id') == 1:
                return redirect(url_for('admin_dashboard'))
            else:
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


# 登录过后的页面


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'id' not in session:
        return redirect(url_for('login'))

    rooms = Room.query.all()
    return render_template('dashboard.html', rooms=rooms)


@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if 'id' not in session:
        return redirect(url_for('login'))
    if session.get('role_id') != 1:
        return redirect(url_for('dashboard'))

    rooms = Room.query.all()
    return render_template('admin_dashboard.html', rooms=rooms)


@app.route('/create_room', methods=['GET', 'POST'])
def create_room():
    if 'id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        capacity = request.form.get('capacity')
        password = request.form.get('password')
        owner_id = session.get('id')
        new_room = Room(name=name, capacity=capacity, password=password, owner_id=owner_id)
        db.session.add(new_room)
        db.session.commit()
        flash('Room created successfully!')
        print(f'{datetime.datetime.now()}, {name, capacity, password, owner_id} 创建房间成功')
        return redirect(url_for('admin_dashboard'))
    return render_template('create_room.html')


@app.route('/modify_room', methods=['GET'])
def modify_room():
    room_id = request.args.get('id')
    room = Room.query.get(room_id)
    if room:
        return render_template('modify_room.html', room=room)
    else:
        flash('Room not found', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/update_room/<int:room_id>', methods=['POST'])
def update_room(room_id):
    room = Room.query.get(room_id)
    if room:  # 房间存在
        room.name = request.form['name']
        room.capacity = request.form['capacity']
        room.password = request.form['password']
        room.owner_id = request.form['owner_id']
        db.session.commit()
        flash('Room updated successfully', 'success')
    else:
        flash('Room not found', 'error')
        abort(404)
    return redirect(url_for('admin_dashboard'))


@app.route('/search_room', methods=['GET'])
def search_room():
    room_id = request.args.get('id')
    if room_id:
        room = Room.query.filter_by(id=room_id).first()  # 在数据库中查找房间
        if room:
            if session.get('role_id') == 1 or session.get('id') == room.owner_id:  # 房主或管理员无需验证
                return redirect(url_for('room', room_id=room.id))
            else:
                return redirect(url_for('password', room_id=room.id))
        else:
            flash('房间不存在')
            return_dashboard()
    else:
        flash('请输入房间ID')
        return_dashboard()


@app.route('/delete_room', methods=['DELETE'])
def delete_room():
    room_id = request.args.get('id')
    room = Room.query.get(room_id)
    if room:
        db.session.delete(room)
        db.session.commit()
        return 'Delete successfully', 204
    else:
        abort(404)


@app.route('/password/<int:room_id>', methods=['GET', 'POST'])
def password(room_id):
    return render_template('password.html', room_id=room_id)


@app.route('/verify_password/<int:room_id>', methods=['POST'])
def verify_password(room_id):
    password = request.form.get('password')
    room = Room.query.get(room_id)
    if room and room.password == password:
        # 向关系表中添加用户
        # room_user.insert().values(room_id=room_id, user_id=session.get('id'))
        # db.session.commit()
        print(f'{datetime.datetime.now()}, {session.get("name")} 进入房间 {room_id}')
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

    # 将用户添加到房间参与者列表
    # if session.get('id') not in room.participants:
    #     room_user.insert((room_id, session.get('id')))
    #     db.session.commit()

    if request.method == 'GET':
        # 查询房间参与者
        participants = room.participants
        return render_template('room.html', room=room, participants=participants)
    elif request.method == 'POST':
        if 'quit' in request.form:
            # 退出房间
            room.participants.remove(session.get('id'))
            db.session.commit()
            return redirect(url_for('dashboard'))
    return render_template('room.html', room=room)


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
