# 暂时用不到这个类，先注释掉

# 创建运行时房间类
# room_sequence = 1  # 房间序列号


# class RuntimeRoom:
#     def __init__(self, id, name, capacity, password, owner_id):
#         self.id = id
#         self.name = name
#         self.capacity = capacity
#         self.password = password
#         self.owner_id = owner_id
#         self.users = []
#
#     def add_user(self, user):
#         self.users.append(user)
#
#     def remove_user(self, user):
#         self.users.remove(user)
#
#     def is_full(self):
#         return len(self.users) >= self.capacity
#
#     def is_owner(self, user):
#         return user.id == self.owner_id
#
#     def toSQL(self):
#         return Room(id=self.id, name=self.name, capacity=self.capacity
#                     , password=self.password, owner_id=self.owner_id)
#
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'name': self.name,
#             'capacity': self.capacity,
#             'password': self.password,
#             'owner_id': self.owner_id
#         }
#
#     def __repr__(self):
#         return f'RuntimeRoom {self.id} {self.name} {self.capacity} {self.password} {self.owner_id} {self.users}'
#
#
# # 运行时房间工厂函数
# def create_room(name, capacity, password, owner_id):
#     global room_sequence
#     room = RuntimeRoom(room_sequence, name, capacity, password, owner_id)
#     room_sequence += 1
#     return room