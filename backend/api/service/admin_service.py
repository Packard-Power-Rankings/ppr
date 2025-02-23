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
from typing import Annotated, Optional
from datetime import datetime, timedelta, timezone
import motor.motor_asyncio
from fastapi import HTTPException, Depends, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from api.schemas.items import TokenData, LoginResponse

ACCESS_TOKEN_TIME = 60.0
ALGORITHM = "HS256"
MONGO_DETAILS = \
    f"mongodb+srv://{os.getenv("MONGO_USER")}:{os.getenv("MONGO_PASS")}@" \
    "sports-cluster.mx1mo.mongodb.net/" \
    "?retryWrites=true&w=majority&appName=Sports-Cluster"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client['admin_details']
admin = database.get_collection('admin')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token/")


class AdminServices():
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
        form_data: OAuth2PasswordRequestForm,
        response: Response
    ) -> LoginResponse:
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
            "access_token",
            value=access_token,
            httponly=True,
            secure=False,       # Change for production
            samesite="lax",     # Change for production
        )
        return LoginResponse(message="Login successful")

    @staticmethod
    async def get_current_admin(
        request: Request
    ):
        """Gets the current admin based on the verified
        token

        Args:
            token (str, optional): Token from verification.
            Defaults to Depends(oauth2_scheme).

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
        request: Request
    ):
        """Gets the current user

        Args:
            token (Annotated[str, Depends): Token Scheme

        Raises:
            credentials_exception: Unauthorized
            credentials_exception: Unauthorized

        Returns:
            TokenData: Returns token data
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        token = request.cookies.get("access_token")
        if not token:
            raise credentials_exception

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

        except ExpiredSignatureError:  # Token is expired
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired, please log in again"
            )
        except InvalidTokenError:
            return credentials_exception
        
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
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_TIME)

        to_encode.update({'exp': expire})
        encode_jwt = jwt.encode(
            to_encode,
            os.getenv('SECRET_KEY'),
            algorithm=ALGORITHM
        )
        return encode_jwt

    @staticmethod
    def hashed_password(password: str) -> str:
        """Hashes the password for storage in the database

        Args:
            password (str): Password

        Returns:
            str: The hashed password
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(
            password=password.encode('utf-8'),
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
        return bcrypt.checkpw(
            submitted_pass.encode("utf-8"),
            hashed_pass.encode('utf-8')
        )
