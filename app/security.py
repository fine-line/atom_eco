from datetime import datetime, timedelta, timezone

import jwt
import bcrypt
from pydantic import BaseModel
from jwt.exceptions import InvalidTokenError


def hash_password(password: str) -> str:
    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=password, salt=salt)
    hashed_password = hashed_password.decode('utf8')
    return hashed_password


def valid_password(password: str, hashed_password: str) -> bool:
    password = password.encode('utf-8')
    hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(
        password=password, hashed_password=hashed_password)


# openssl rand -hex 32
SECRET_KEY = "fe66e9468ae62beb0d9a9f0e268feb4a6c2542d5e490f861183d6d84fba046b1"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# JWT payload scheme:
# {
#   "sub": "role:id",
#   "exp": expiration time
# }


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(subject: str) -> Token:
    to_encode = {"sub": subject}
    token_expiration_time = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_expires_at = datetime.now(timezone.utc) + token_expiration_time
    to_encode.update({"exp": token_expires_at})
    encoded_jwt = jwt.encode(
        payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    access_token = Token(access_token=encoded_jwt, token_type="bearer")
    return access_token


def verify_access_token(access_token: str) -> str:
    try:
        payload = jwt.decode(
            jwt=access_token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        return None
    subject = payload.get("sub")
    return subject
