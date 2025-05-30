# app/utils/permissions.py

from fastapi import Depends, HTTPException, status
from ..utils.auth import get_current_user
from ..models import User

def require_role(roles: list):
    def role_checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user
    return role_checker
