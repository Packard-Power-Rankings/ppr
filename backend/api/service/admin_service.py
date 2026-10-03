"""Authentication and single-admin account operations."""

import os
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from api.config.settings import is_production, required_secret
from api.database import admin_database as database
from api.schemas.items import TokenData, Token, LogoutResponse

ACCESS_TOKEN_TIME = 60.0
ALGORITHM = "HS256"
AUTH_COOKIE_NAME = "ppr_admin_session"
MAX_PASSWORD_BYTES = 72
admin = database.get_collection('admin')
_DUMMY_PASSWORD_HASH = bcrypt.hashpw(
    b"invalid-password-used-for-timing-only",
    bcrypt.gensalt(),
).decode("utf-8")


def _credentials_exception(detail: str = "Could not validate credentials"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _auth_cookie_path() -> str:
    root_path = os.getenv("ROOT_PATH", "").strip().rstrip("/")
    return f"{root_path}/" if root_path else "/"


class AdminServices:
    def __init__(self):
        """Initializes the collection from the database
        """
        self.admin_collection = admin

    async def create_admin(self, username: str, password: str) -> str:
        """Creates a new admin and checks if an admin
        already exists in the database

        Args:
            username (str): Username
            password (str): Password

        Raises:
            HTTPException: Internal Server Error
            HTTPException: Unauthorized Access

        Returns:
            str: The id returned from the insertion into the
            database
        """
        existing_admin = await self.admin_collection.find_one({})
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An admin account already exists",
            )
        new_admin = {
            "username": username,
            "password": self.hashed_password(password),
        }
        result = await self.admin_collection.insert_one(new_admin)
        return str(result.inserted_id)

    async def login(
        self,
        form_data: OAuth2PasswordRequestForm,
        response: Response,
    ) -> Token:
        """Verifies the admin username and the password are
        correct

        Args:
            form_data (OAuth2PasswordRequestForm): Username and Password

        Returns:
            Token: Returns the login token
        """
        access_token = await self.verify_admin(
            form_data.username,
            form_data.password
        )
        response.set_cookie(
            key=AUTH_COOKIE_NAME,
            value=access_token,
            max_age=int(ACCESS_TOKEN_TIME * 60),
            httponly=True,
            secure=is_production(),
            samesite="strict",
            path=_auth_cookie_path(),
        )
        return Token(access_token=access_token, token_type="bearer")

    async def logout(
        self,
        response: Response
    ) -> LogoutResponse:
        response.delete_cookie(
            AUTH_COOKIE_NAME,
            path=_auth_cookie_path(),
            secure=is_production(),
            httponly=True,
            samesite="strict",
        )
        return LogoutResponse(message="Logout Successful")

    @staticmethod
    async def get_current_admin(request: Request):
        """Gets the current admin based on the verified
        token

        Args:
            request (Request): Incoming request

        Returns:
            TokenData: JSON Web Token to store in frontend
            for a set amount of time without reverification
        """
        admin_service = AdminServices()
        return await admin_service.get_current_user(request)

    async def verify_admin(self, username: str, password: str) -> str:
        """Verifies that the admin is logging in

        Args:
            username (str): Username
            password (str): Password

        Raises:
            HTTPException: Not Found
            HTTPException: Bad Request

        Returns:
            str: A generated JWT access token
        """
        admin_record = None
        if 1 <= len(username) <= 64:
            admin_record = await self.admin_collection.find_one({"username": username})

        stored_hash = (
            admin_record.get("password")
            if admin_record and isinstance(admin_record.get("password"), str)
            else _DUMMY_PASSWORD_HASH
        )
        password_matches = self.check_password(password, stored_hash)
        if admin_record and password_matches:
            return self.generate_access_token({"sub": username}, None)
        raise _credentials_exception("Invalid username or password")

    async def get_current_user(
        self,
        request: Request
    ):
        """Gets the current user

        Args:
            request (Request): Incoming request that holds auth info

        Raises:
            credentials_exception: Unauthorized
            credentials_exception: Unauthorized

        Returns:
            TokenData: Returns token data
        """
        credentials_exception = _credentials_exception()

        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        if not token:
            token = request.cookies.get(AUTH_COOKIE_NAME)

        if not token:
            raise credentials_exception

        try:
            payload = jwt.decode(
                token,
                required_secret("SECRET_KEY"),
                algorithms=[ALGORITHM]
            )
            username: str = payload.get('sub')
            if username is None:
                raise credentials_exception
            current_admin = await self.admin_collection.find_one(
                {"username": username},
                {"_id": 1},
            )
            if not current_admin:
                raise credentials_exception
            return TokenData(username=username)

        except ExpiredSignatureError as exc:  # Token is expired
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired, please log in again"
            ) from exc
        except InvalidTokenError as exc:
            raise credentials_exception from exc

    def generate_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Generates the JWT for ease of access

        Args:
            data (dict): Specific information for JWT structure
            expires_delta (Optional[timedelta], optional): 
                Time frame for JWT structure. Defaults to None.

        Returns:
            str: The encoded JWT string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + \
                timedelta(minutes=ACCESS_TOKEN_TIME)

        to_encode.update({'exp': expire})
        to_encode.update({'iat': datetime.now(timezone.utc)})
        encode_jwt = jwt.encode(
            to_encode,
            required_secret("SECRET_KEY"),
            algorithm=ALGORITHM
        )
        return encode_jwt

    async def validate_token(
        self,
        request: Request
    ):
        try:
            user = await self.get_current_user(request)
            return {"status": "valid", "username": user.username}
        except HTTPException:
            return {"status": "invalid"}

    @staticmethod
    def hashed_password(password: str) -> str:
        """Hashes the password for storage in the database

        Args:
            password (str): Password

        Returns:
            str: The hashed password
        """
        encoded_password = password.encode("utf-8")
        if len(encoded_password) > MAX_PASSWORD_BYTES:
            raise ValueError("Password cannot exceed 72 UTF-8 bytes")
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(
            password=encoded_password,
            salt=salt
        ).decode('utf-8')

    @staticmethod
    def check_password(submitted_pass: str, hashed_pass: str) -> bool:
        """Compares the entered password to the stored
        password to see if they are equal

        Args:
            submitted_pass (str): Entered Password
            hashed_pass (str): Password in DB

        Returns:
            bool: Whether they are matched or not
        """
        try:
            encoded_password = submitted_pass.encode("utf-8")
            if len(encoded_password) > MAX_PASSWORD_BYTES:
                return False
            return bcrypt.checkpw(
                encoded_password,
                hashed_pass.encode('utf-8')
            )
        except (TypeError, ValueError):
            return False
