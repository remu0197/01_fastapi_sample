from venv import create
from fastapi import Depends, Query, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from . import models, schemas

oauth2_shceme = OAuth2PasswordBearer(tokenUrl="token")


# 問題 1
def authenticate(db: Session, email: str, password: str):
    return db.query(models.User).filter(models.User.email == email and models.User.hashed_password == password).first()


# 問題 1
def create_token(user_id: int):
    # 簡易的にトークンを作成
    return str(user_id) + "_ACCESS_TOKEN"


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(
        email=user.email,
        hashed_password=fake_hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token = create_token(user_id=db_user.id)
    return {"user": db_user, "token": token}


# 問題 3
def delete_user(db: Session, user_id: int):
    # 削除対象のユーザを無効化
    delete_target = db.query(models.User).filter(models.User.id == user_id).first()
    delete_target.is_active = False

    # タスク引継ぎ先のユーザの探索
    takeovered_target = None
    active_users = db.query(models.User).filter(models.User.is_active == True).all()
    for user in active_users:
        if user.is_active and (takeovered_target is None or takeovered_target.id > user.id):
            takeovered_target = user

    # タスク引継ぎ先がない場合
    if takeovered_target is None:
        raise HTTPException(status_code=400, detail="Target user to take over tasks does not exist.")

    # タスクの引継ぎ処理
    items = db.query(models.Item).filter(models.Item.owner_id == user_id).all()
    for item in items:
        item.owner_id = takeovered_target.id

    # データベース更新
    db.commit()

    return {
        "delete_user_id": delete_target.id,
        "takeovered_user_id": takeovered_target.id
    }


# 問題 1
def get_user_id_from_token(token: str = Depends(oauth2_shceme)):
    return int(token.split("_")[0])


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


# 問題 2
def get_user_items(user_id: int, db: Session):
    all_items = get_items(db)
    user_items = []

    for item in all_items:
        if item.owner_id == user_id:
            user_items.append(item)

    return user_items


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
