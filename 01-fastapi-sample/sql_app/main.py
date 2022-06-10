from msilib import schema
from msilib.schema import Directory
from typing import List

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(redoc_url="/docs/redoc")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 問題 1
@app.get("/login/{email}/{password}/")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = crud.authenticate(db, email, password)
    if not user:
        raise HTTPException(status_code=400, detail="This user is not registered")

    token = crud.create_token(user.id)

    return {
        "user": user,
        "token": token,
    }


@app.get("/health-check")
def health_check(db: Session = Depends(get_db)):
    return {"status": "ok"}


@app.post("/users/")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


# 問題 3
@app.delete("/users/{user_id}/delete/")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    delete_results = crud.delete_user(db, user_id)
    return delete_results


# 問題 1
@app.get("/me/", response_model=schemas.User)
def read_current_user(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(crud.get_user_id_from_token)
):
    current_user = read_user(
        user_id=current_user_id,
        db=db
    )
    return current_user


# 問題 2
@app.get("/me/items/", response_model=List[schemas.Item])
def read_my_items(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(crud.get_user_id_from_token)
):
    items = crud.get_user_items(
        user_id=current_user_id,
        db=db
    )
    return items
