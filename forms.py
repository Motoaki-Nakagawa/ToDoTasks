from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    RadioField,
    HiddenField,
)
from wtforms.validators import DataRequired, EqualTo, Length, Optional, Regexp


# ログイン用フォーム
class LoginForm(FlaskForm):
    username = StringField("ユーザー名", validators=[DataRequired()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    submit = SubmitField("Log In")


# サインアップ用フォーム
class SignUpForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        validators=[
            DataRequired(),
            Length(max=50, message="ユーザー名は50文字以下にしてください"),
            Regexp(
                r"^[a-zA-Z0-9_]+$", message="ユーザー名は半角英数字とアンダーバーで入力してください"
            ),
        ],
    )
    password = PasswordField(
        "パスワード",
        validators=[
            DataRequired(),
            Length(
                min=8, max=20, message="パスワードは8文字以上20文字以下にしてください"
            ),
            Regexp(
                r"^[a-zA-Z0-9]+$", message="パスワードは半角英数字で入力してください"
            ),
        ],
    )
    confirm_password = PasswordField(
        "パスワードの確認",
        validators=[
            DataRequired(),
            EqualTo("password", message="パスワードが一致しません"),
        ],
    )
    submit = SubmitField("Sign Up")


# 新規リスト作成フォーム
class NewListForm(FlaskForm):
    listname = StringField(
        "新規リスト名：",
        validators=[
            DataRequired(),
            Length(max=30, message="新しいリスト名は30文字以下にしてください"),
        ],
    )
    submit = SubmitField("Create List")


# 新規タスク作成フォーム
class NewTaskForm(FlaskForm):
    taskname = StringField(
        "新規タスク名：",
        validators=[
            DataRequired(),
            Length(max=50, message="新しいタスク名は50文字以下にしてください"),
        ],
    )
    due_date = StringField("タスク期日：", validators=[DataRequired()])
    priority = SelectField(
        "優先度：",
        choices=[(1, "!（低）"), (2, "!!（中）"), (3, "!!!（高）")],
        coerce=int,
    )
    list_id = SelectField("タスク登録先：", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Add Task")


# タスク削除フォーム
class DeleteTaskForm(FlaskForm):
    task_id = HiddenField("Task ID", validators=[DataRequired()])
    submit = SubmitField("Delete Task")


# リスト削除フォーム
class DeleteListForm(FlaskForm):
    list_id = HiddenField("List ID", validators=[DataRequired()])
    submit = SubmitField("Delete List")


# 設定フォーム
class SettingsForm(FlaskForm):
    nickname = StringField(
        "新しいニックネーム",
        validators=[
            Optional(),
            Length(max=20, message="ニックネームは20文字以下にしてください"),
        ],
    )
    old_password = PasswordField("現在のパスワード", validators=[Optional()])
    new_password = PasswordField(
        "新しいパスワード",
        validators=[
            Optional(),
            Length(
                min=8,
                max=20,
                message="New password must be between 8 and 20 characters.",
            ),
        ],
    )
    confirm_password = PasswordField(
        "パスワードの確認",
        validators=[
            Optional(),
            EqualTo("new_password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Apply Changes")
