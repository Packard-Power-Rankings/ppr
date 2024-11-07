"""Admin service class that creates a single admin,
    generates password hash and stores in database, checks
    if password is correct, and generates an access token

    Raises:
        HTTPException: 401 Unauthorized Access
        HTTPException: 500 Server Error
        HTTPException: 404 Not Found
        HTTPException: 400 Bad Request
        credentials_exception: 401 Unauthorized Access

    Returns:
        None
"""

import os
from typing import Annotated
from datetime import datetime, timedelta, timezone
import motor.motor_asyncio
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError
from schemas.items import TokenData, Token

ACCESS_TOKEN_TIME = 60.0
ALGORITHM = "HS256"
MONGO_DETAILS = \
    f"mongodb+srv://{os.getenv("MONGO_USER")}:{os.getenv("MONGO_PASS")}@" \
    "sports-cluster.mx1mo.mongodb.net/" \
    "?retryWrites=true&w=majority&appName=Sports-Cluster"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client['admin_details']
admin = database.get_collection('admin')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/token")


class AdminServices():
    def __init__(self):
        self.admin_collection = admin

    async def create_admin(self, username: str, password: str) -> str:
        try:
            existing_admin = await self.admin_collection.find_one({})
            if existing_admin:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Admin Already Exists"
                )
            hashed_pass = self.hashed_password(password)
            new_admin = {
                "username": username,
                "password": hashed_pass
            }
            result = await self.admin_collection.insert_one(new_admin)
            return str(result.inserted_id)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error has occurred"
            ) from exc

    async def login(
        self,
        form_data: OAuth2PasswordRequestForm
    ) -> Token:
        access_token = await self.verify_admin(
            form_data.username,
            form_data.password
        )
        return Token(access_token=access_token, token_type="bearer")

    @staticmethod
    async def get_current_admin(
        token: str = Depends(oauth2_scheme)
    ):
        admin_service = AdminServices()
        return await admin_service.get_current_user(token)

    async def verify_admin(self, username: str, password: str) -> str:
        admin = await self.admin_collection.find_one({"username": username})
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        hash_pass = admin["password"]
        if self.check_password(password, hash_pass):
            return self.generate_access_token({"sub": username}, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Password"
        )

    async def get_current_user(
        self,
        token: Annotated[str, Depends(oauth2_scheme)]
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        try:
            payload = jwt.decode(
                token,
                os.getenv("SECRET_KEY"),
                algorithms=[ALGORITHM]
            )
            username: str = payload.get('sub')
            if username is None:
                raise credentials_exception
            return TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
        
    def generate_access_token(
        self,
        data: dict,
        expires_delta = timedelta | None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = \
                datetime.now(timezone.utc) \
                    + expires_delta
        else:
            expire = \
                datetime.now(timezone.utc) \
                    + timedelta(minutes=ACCESS_TOKEN_TIME)

        to_encode.update({'exp': expire})
        encode_jwt = jwt.encode(
            to_encode,
            os.getenv('SECRET_KEY'),
            algorithm=ALGORITHM
        )
        return encode_jwt

    @staticmethod
    def hashed_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(
            password=password.encode('utf-8'),
            salt=salt
        ).decode('utf-8')

    @staticmethod
    def check_password(submitted_pass: str, hashed_pass: str) -> bool:
        return bcrypt.checkpw(
            submitted_pass.encode("utf-8"),
            hashed_pass.encode('utf-8')
        )
