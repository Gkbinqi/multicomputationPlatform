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
    users = db.relationship('User', backref='role')  # 表关系 一个角色可以有多个用户

    def __repr__(self):
        return 'Role %d %s' % (self.id, self.name)


# 创建数据库模型类
class User(db.Model):
    """用户表"""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)  # 主键 设置主键后默认设置自增长
    name = db.Column(db.String(32), unique=True, nullable=False)  # 用户名
    password = db.Column(db.String(32), nullable=False)  # 密码
    # 与Role形成多对一关系 外键Foreign Key, 用于关联另外一张表
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    def __repr__(self):
        return 'User %d %s %s %d' % (self.id, self.name, self.password, self.role_id)

    def check_password(self, password):
        return self.password == password


class RoomToUser(db.Model):
    """房间与用户关联表 多对多"""
    __tablename__ = 'room_user'
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class Room(db.Model):
    """房间表"""
    __tablename__ = 'room'

    # 以下内容展示在dashboard
    id = db.Column(db.Integer, primary_key=True)  # 主键 设置主键后默认设置自增长

    name = db.Column(db.String(32), unique=True, nullable=False)  # 房间名
    capacity = db.Column(db.Integer, nullable=False)  # 房间容量
    status = db.Column(db.Enum('waiting', 'running', 'finished'), default='waiting', nullable=False)

    # 以下关联内容展示在dashboard
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 表关系 外键Foreign Key, 用于关联另外一张表

    # 以下内容不展示在dashboard, 展示在房间详情页面
    password = db.Column(db.String(32), nullable=False)  # 房间密码

    result = db.Column(db.String(1000))  # 房间结果

    # 与User形成多对多关系 第三张关联表RoomToUser
    # Room 可以通过participants属性访问所有参与者 User 可以通过rooms属性访问所有房间
    participants = db.relationship('User', secondary='room_user', backref='rooms')

    # input不展示
    inputs = db.relationship('Input', backref='room')


class Input(db.Model):
    """输入表"""
    __tablename__ = 'input'
    id = db.Column(db.Integer, primary_key=True)  # 主键 设置主键后默认设置自增长
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))  # 房间ID
    input_text = db.Column(db.String(1000))  # 输入内容


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


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        role_id = 2  # 默认为普通用户角色
        # 检查是否有相同用户名
        existing_user = User.query.filter_by(name=name).first()
        if existing_user:
            return render_template('register.html'
                                   , error_message="用户名已存在！")
        else:  # 创建对象 插入数据
            new_user = User(name=name, password=password, role_id=role_id)
            db.session.add(new_user)  # session记录到数据库
            db.session.commit()  # 提交任务

            print(f'{datetime.datetime.now()}, {name, password, role_id} 注册成功')
            return redirect(url_for('login'))


@app.route('/basic_transformer/<int:uid>', methods=['GET', 'POST'])
def user(uid):
    return (f'<h1>Wow, how can you find this page?</h1>'
            f'<h1>User {uid}</h1>'
            f'<p>This is the user page for user {uid}.</p>'
            f'<a href="/login">Go back to login page</a>')


#########################
# 以下为Dashboard相关路由  #
#########################


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


# 增 查 改 删
# 增
@app.route('/create_room', methods=['GET', 'POST'])
def create_room():
    if 'id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        capacity = request.form.get('capacity')
        password = request.form.get('password')
        owner_id = session.get('id')
        new_room = Room(name=name, capacity=capacity, password=password, owner_id=owner_id
                        , status='waiting', result='')
        db.session.add(new_room)
        db.session.commit()
        flash('Room created successfully!')
        print(f'{datetime.datetime.now()}, {name, capacity, password, owner_id} 创建房间成功')
        return return_dashboard()
    return render_template('create_room.html')


# 查
@app.route('/search_room', methods=['GET'])
def search_room():
    if 'id' not in session:
        return redirect(url_for('login'))

    room_id = request.args.get('id')
    if room_id:
        room = Room.query.get(room_id)  # 使用主键查找房间
        if room:
            if session.get('role_id') == 1 or session.get('id') == room.owner_id:  # 房主或管理员无需验证
                return redirect(url_for('room', room_id=room.id))
            else:
                return redirect(url_for('password', room_id=room.id))
        else:
            flash('房间不存在')
            return return_dashboard()
    else:
        flash('请输入房间ID')
        return return_dashboard()


# 改
@app.route('/modify_room', methods=['GET'])
def modify_room():
    if 'id' not in session:
        return redirect(url_for('login'))

    room_id = request.args.get('id')
    room = Room.query.get(room_id)
    if room:
        return render_template('modify_room.html', room=room)
    else:
        flash('Room not found', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/update_room/<int:room_id>', methods=['POST'])
def update_room(room_id):
    if 'id' not in session:
        return redirect(url_for('login'))

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


# 删
@app.route('/delete_room', methods=['DELETE'])
def delete_room():
    if 'id' not in session:
        return redirect(url_for('login'))

    room_id = request.args.get('id')
    room = Room.query.get(room_id)
    if room:
        db.session.delete(room)
        db.session.commit()
        return 'Delete successfully', 204
    else:
        abort(404)


#######################
# 以下为房间相关路由     ##
#######################
# 输入房间密码
@app.route('/password/<int:room_id>', methods=['GET', 'POST'])
def password(room_id):
    if 'id' not in session:
        return redirect(url_for('login'))

    return render_template('password.html', room_id=room_id)


# 验证房间密码
@app.route('/verify_password/<int:room_id>', methods=['POST'])
def verify_password(room_id):
    password = request.form.get('password')
    room = Room.query.get(room_id)
    if room:
        pts = room.participants
        current_user = User.query.get(session.get('id'))
        if current_user in pts:
            print(f'{datetime.datetime.now()}, {session.get("name")} 进入房间 {room_id}')
            return redirect(url_for('room', room_id=room.id))
        elif room.password == password:
            pts.append(current_user)
            room.participants = pts
            db.session.commit()
            print(f'{datetime.datetime.now()}, {session.get("name")} 加入房间 {room_id}')
            return redirect(url_for('room', room_id=room.id))
        else:
            flash('密码错误', 'error')
            return redirect(url_for('dashboard'))
    else:
        flash('未知错误, 请联系管理员', 'error')
        return redirect(url_for('dashboard'))


@app.route('/dashboard/room/<int:room_id>', methods=['GET'])
def room(room_id):
    # 检查session是否存在
    if 'id' not in session:
        return redirect(url_for('login'))

    # 查询房间是否存在
    room = Room.query.filter_by(id=room_id).first()
    if not room:
        return abort(404)

    return render_template('room.html', room=room, participants=room.participants)


@app.route('/room/<int:room_id>/user_input', methods=['GET', 'POST'])
def user_input(room_id):
    if 'id' not in session:
        return redirect(url_for('login'))
    # 查询房间是否存在
    room = Room.query.filter_by(id=room_id).first()
    if not room:
        return abort(404)

    if request.method == 'GET':
        return render_template('user_input.html', room_id=room_id)
    elif request.method == 'POST':
        input_text = request.form.get('input')
        new_input = Input(room_id=room_id, input_text=input_text)
        db.session.add(new_input)
        db.session.commit()
        print(f'{datetime.datetime.now()}, {session.get("name")} 输入 {input_text} 到房间 {room_id}')
        return redirect(url_for('room', room_id=room_id))


@app.route('/room/<int:room_id>/compute', methods=['GET', 'POST'])
def compute(room_id):
    if 'id' not in session:
        return redirect(url_for('login'))

    room = Room.query.get(room_id)
    if not room:
        return abort(404)

    # 查询操作者是否为房主
    if session.get('id') != room.owner_id:
        return redirect(url_for('room', room_id=room.id))

    # 开始计算
    all_inputs = room.inputs
    result = ''
    for input in all_inputs:
        result += input.input_text + '\n'
    room.result = result
    room.status = 'finished'
    db.session.commit()
    print(f'{datetime.datetime.now()}, 房间 {room_id} 计算完成')
    return redirect(url_for('room', room_id=room.id))


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

        db.session.add_all([User(name='admin', password='admin', role_id=1)
                               , User(name='bot01', password='bot', role_id=2)
                               , User(name='bot02', password='bot', role_id=2)])  # session记录到数据库
        db.session.commit()  # 提交任务

        # 创建房间
        print('创建示例房间')
        for i in range(1, 11):
            room = Room(name=f'房间{i}', capacity=10, password='123456', owner_id=1
                        , status='waiting', result='')
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

        # 给房间添加参与者
        test_room = Room.query.get(1)
        print("房间初始信息如下: ")
        print(test_room.id, test_room.name, test_room.capacity, test_room.password, test_room.owner_id)
        print(test_room.participants)
        print('添加参与者如下: ')
        print(users)

        test_room.participants = users
        db.session.commit()

        print('添加后房间参与者信息如下: ')
        print(test_room.participants)
        print('用户参与房间如下')
        for user in users:
            print(user.name, user.rooms)
        print('数据库初始化完成')


if __name__ == '__main__':
    if 'y' == input('是否初始化数据库？(y/n): '):
        init_db()
    app.run(debug=True)  # 启动Flask应用
