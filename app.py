import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import select
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, User, Task, List
from datetime import datetime, date, timedelta
from forms import (
    LoginForm,
    SignUpForm,
    NewTaskForm,
    SettingsForm,
    NewListForm,
    DeleteTaskForm,
    DeleteListForm,
)

app = Flask(__name__)
app.secret_key = "your_secret_key"

# データベースの定義と初期化
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL', 'sqlite:///instance/todo_tasks.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
db.init_app(app)
migrate = Migrate(app, db)


# 接続時にログインページにリダイレクト（セッションが切れていない場合はホームにリダイレクト）
@app.route("/")
def redirect_to():
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


# ログインページのルート
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit(): # バリデーションの確認
        user = User.authenticate(form.username.data, form.password.data) # 登録済みか確認
        if user and user.check_password(form.password.data):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("ログインしました", "success")
            return redirect(url_for("home"))
        flash("ユーザー名またはパスワードが間違っています", "danger")
    return render_template("login.html", form=form)


# サインアップのルート
@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignUpForm()
    if form.validate_on_submit(): # バリデーションの確認
        print("ok!")
        new_user = User.create_user(form.username.data, form.password.data) # すでに登録されていないかの確認
        if new_user:
            flash("アカウントを作成しました", "success")
            return redirect(url_for("login"))
        flash("このユーザー名はすでに存在します", "danger")
    return render_template("signup.html", form=form)


# ホームのルート
@app.route("/home", methods=["GET", "POST"])
def home():
    user = User.get_by_session(session)
    if not user:
        flash("ログインしてください", "danger")
        return redirect(url_for("login"))

    user_lists = List.get_user_lists(user.id) #ユーザーIDに紐づいたリストの取得
    list_choices = [(l.id, l.listname) for l in user_lists] if user_lists else [] # プルダウン用のリスト取得
    task_form = NewTaskForm()
    task_form.list_id.choices = list_choices # プルダウン用のリスト内タスク取得
    list_form = NewListForm()
    delete_form = DeleteTaskForm()


    # 新規リスト作成
    if list_form.validate_on_submit() and "create_list" in request.form:
        List.create_list(list_form.listname.data, user.id)
        flash("新しいリストを作成しました", "success")
        return redirect(url_for("home"))

    # 新規タスク作成
    if task_form.validate_on_submit() and "add_task" in request.form:
        Task.create_task(
            task_form.taskname.data,
            task_form.due_date.data,
            task_form.priority.data,
            task_form.list_id.data,
        )
        flash("新しいタスクを追加しました", "success")
        return redirect(url_for("home"))

    # ソート順とリストの選択
    sort_order = request.args.get("sort_order", "due_date") # ソート順の取得
    selected_list_id = request.args.get("selected_list_id", None) # 選択したリストのID取得

    if not selected_list_id and user_lists:
        selected_list_id = user_lists[0].id # ユーザーの最初のリストを取得
    elif selected_list_id:
        try:
            selected_list_id = int(selected_list_id)
        except ValueError:
            selected_list_id = None

    tasks = Task.get_tasks(selected_list_id, sort_order) if selected_list_id else [] # リストIDがある場合、タスクを取得
    overdue_7_tasks = Task.get_overdue_tasks(days=7) # 七日以内の期日切れタスクの取得
    overdue_7_plus_tasks = Task.get_overdue_tasks() # それ以上の期日切れタスクの取得

    return render_template(
        "home.html",
        user=user,
        task_form=task_form,
        list_form=list_form,
        delete_form=delete_form,
        tasks=tasks,
        lists=user_lists,
        sort_order=sort_order,
        selected_list_id=selected_list_id,
        overdue_7_tasks=overdue_7_tasks,
        overdue_7_plus_tasks=overdue_7_plus_tasks,
    )


# タスク削除のルート
@app.route("/delete_task", methods=["POST"])
def delete_task():
    user = User.get_by_session(session)
    if not user:
        flash("ログインしてください。", "danger")
        return redirect(url_for("login"))

    delete_form = DeleteTaskForm(request.form)
    if delete_form.validate_on_submit(): # バリデーションの確認と削除タスクのID取得
        task_id = delete_form.task_id.data

        # タスクとそのリストが現在のユーザーに属しているか確認
        stmt = select(Task).join(List).where(
            Task.id == task_id,
            List.user_id == user.id
        )
        task = db.session.execute(stmt).scalar_one_or_none()

        if task:
            db.session.delete(task)
            db.session.commit()
            flash("タスクを削除しました。", "success")
        else:
            flash("このタスクを削除する権限がありません。", "danger")
    else:
        flash("フォームの入力が無効です。", "danger")

    return redirect(url_for("home"))



# リスト削除のルート
@app.route("/delete_list", methods=["POST"])
def delete_list():
    user = User.get_by_session(session)
    if not user:
        flash("ログインしてください。", "danger")
        return redirect(url_for("login"))

    form = DeleteListForm()
    if form.validate_on_submit(): # バリデーションの確認と削除リストのID取得
        list_id = form.list_id.data

        # リストが現在のユーザーに属しているか確認
        stmt = select(List).where(
            List.id == list_id,
            List.user_id == session["user_id"]
        )
        list_to_delete = db.session.execute(stmt).scalar_one_or_none()

        if list_to_delete: # リスト削除ができる場合、コミット
            db.session.delete(list_to_delete)
            db.session.commit()
            flash("リストと関連タスクを削除しました。", "success")

            remaining_lists = List.get_user_lists(user.id) # 次のリストを選択
            if remaining_lists:
                next_list_id = remaining_lists[0].id
                return redirect(url_for("home", selected_list_id=next_list_id))
            else:
                flash(
                    "すべてのリストが削除されました。新しいリストを作成してください。",
                    "info",
                )
                return redirect(url_for("home"))
        else:
            flash("このリストを削除する権限がありません。", "danger")
    else:
        flash("フォームの入力が無効です。", "danger")

    return redirect(url_for("home"))



# セッティングのルート
@app.route("/settings", methods=["GET", "POST"])
def settings():
    user = User.get_by_session(session)
    if not user:
        return redirect(url_for("login"))

    form = SettingsForm()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_nickname":  # Updateボタン
            if form.nickname.data.strip():
                user.nickname = form.nickname.data.strip()
                db.session.commit()
                flash("Nickname updated successfully.", "success")
        elif action == "delete_nickname":  # Deleteボタン
            user.nickname = None
            db.session.commit()
            flash("Nickname deleted successfully.", "success")

        elif action == "update_password":  # パスワードの更新
            if form.old_password.data and user.check_password(form.old_password.data):
                if form.new_password.data:
                    user.set_password(form.new_password.data)
                    db.session.commit()
                    flash("Password updated successfully.", "success")
            else:
                flash("Current password is incorrect.", "danger")

        return redirect(url_for("settings"))

    return render_template("settings.html", form=form)


# アバウトのルート
@app.route("/about")
def about():
    return render_template("about.html")


# ログアウトのルート
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
