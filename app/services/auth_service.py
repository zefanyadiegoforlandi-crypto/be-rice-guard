from app.utils.security import hash_password, verify_password
from app.models.schemas import UserRegister, UserLogin, UserResponse
from app.models.database import User
from app.models.database_init import get_db
from sqlalchemy.orm import Session
from typing import Optional, Tuple


class AuthService:
    """Handle authentication operations with MySQL database"""

    @staticmethod
    def register_user(user_data: UserRegister, db: Session) -> Tuple[bool, str]:
        """Register new user ke database"""
        # Check if user already exists
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            return False, "Email already registered"

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user di database dengan default role 'user'
        new_user = User(
            email=user_data.email,
            name=user_data.name,
            password_hash=hashed_password,
            role='user'  # Default role untuk user baru
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return True, "User registered successfully"

    @staticmethod
    def authenticate_user(email: str, password: str, db: Session) -> Tuple[bool, Optional[UserResponse]]:
        """Authenticate user with email and password dari database"""
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return False, None

        if not verify_password(password, user.password_hash):
            return False, None

        return True, UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            created_at=user.created_at
        )

    @staticmethod
    def get_user(email: str, db: Session) -> Optional[UserResponse]:
        """Get user by email dari database"""
        user = db.query(User).filter(User.email == email).first()
        if user:
            return UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                created_at=user.created_at
            )
        return None

    @staticmethod
    def update_name(email: str, new_name: str, db: Session) -> Tuple[bool, Optional[UserResponse]]:
        """Update user name di database"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False, None

        user.name = new_name
        db.commit()
        db.refresh(user)

        return True, UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at
        )

    @staticmethod
    def change_password(email: str, new_password: str, db: Session) -> Tuple[bool, str]:
        """Change user password di database"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False, "User not found"

        user.password_hash = hash_password(new_password)
        db.commit()

        return True, "Password berhasil diubah"
