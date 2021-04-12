from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:user@172.21.115.119:3306/training_db?charset=utf8mb4'
db = SQLAlchemy(app)


# UserTest相当于表名,当出现驼峰命名时,数据库会创建成user_test表
class UserTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # username是唯一
    email = db.Column(db.String(120), unique=True, nullable=False)  # email是唯一

    def __repr__(self):
        return '<User %r>' % self.username


def test_db():
    # 创建表
    # db.create_all()
    # 表插入数据
    db.session.add(UserTest(id=1, username="xiaoming", email="xiaoming@123.com"))
    db.session.commit()
