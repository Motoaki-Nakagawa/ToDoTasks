
from flask import Flask
from sqlalchemy import select
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# User テーブル
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(20), default=None, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):  # パスワードをハッシュ化
        self.password = generate_password_hash(password)

    def check_password(self, password):  # パスワードが正しいか確認
        return check_password_hash(self.password, password)
    
    @classmethod  #ログイン用の認証
    def authenticate(cls, username, password):
        stmt = select(cls).where(cls.username == username)
        user = db.session.execute(stmt).scalar_one_or_none()
        if user and user.check_password(password):
            return user
        return None
    
    @classmethod
    def create_user(cls, username, password):  #ユーザー登録
        stmt = select(cls).where(cls.username == username)
        existing_user = db.session.execute(stmt).scalar_one_or_none()
        if existing_user:
            return None
        new_user = cls(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return new_user
    
    @classmethod
    def get_by_session(cls, session):  #セッションからユーザー情報を取得
        if "user_id" not in session:
            return None
        stmt = select(cls).where(cls.id == session["user_id"])
        return db.session.execute(stmt).scalar_one_or_none()


# List テーブル
class List(db.Model):
    __tablename__ = 'lists'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    listname = db.Column(db.String(30), default='New List', nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    user = db.relationship('User', backref=db.backref('lists', cascade='all, delete-orphan'))
    
    @classmethod
    def get_user_lists(cls, user_id):  #ユーザーのリスト一覧取得
        stmt = select(cls).where(cls.user_id == user_id)
        return db.session.execute(stmt).scalars().all()
    
    @classmethod
    def create_list(cls, listname, user_id):  # リストの新規作成
        new_list = cls(listname=listname, user_id=user_id)
        db.session.add(new_list)
        db.session.commit()
        return new_list


# Task テーブル
class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    taskname = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.Date, default=date.today, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('lists.id', ondelete='CASCADE'), nullable=False)

    list = db.relationship('List', backref=db.backref('tasks', cascade='all, delete-orphan'))
    
    @classmethod
    def get_tasks(cls, list_id=None, sort_order="due_date"):  # 該当リストのタスク一覧取得
        stmt = select(cls)
        if list_id:
            stmt = stmt.where(cls.list_id == list_id)
        stmt = stmt.order_by(cls.due_date if sort_order == "due_date" else cls.priority.desc())
        tasks = db.session.execute(stmt).scalars().all()
        return tasks or []
        
    @classmethod
    def create_task(cls, taskname, due_date, priority, list_id):  # タスクの新規作成
        new_task = cls(
            taskname=taskname,
            due_date=datetime.strptime(due_date, "%Y-%m-%d").date(),
            priority=priority,
            list_id=list_id,
        )
        db.session.add(new_task)
        db.session.commit()
        return new_task
    
    @classmethod
    def get_overdue_tasks(cls, days=None):  # 期限切れタスク一覧取得
        if days is None:
            stmt = select(cls).where(cls.due_date < date.today() - timedelta(days=7))
        else:
            stmt =select(cls).where(
                (cls.due_date < date.today())
                & (cls.due_date >= date.today() - timedelta(days=days))
            )
        return db.session.execute(stmt).scalars().all()