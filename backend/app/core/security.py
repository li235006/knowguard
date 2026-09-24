"""
安全凭证与加密密码学管理模块

职责:
    - 密码 Bcrypt 加盐散列 (工作因子 12) 与比对校验
    - JWT Access Token 与 Refresh Token 的生成、解析与签名校验
    - 统一权限上下文 Token 声明 (Claims) 结构编解码

架构定位:
    核心底层支撑层 (Core Infrastructure) / 安全认证基底

输入/输出契约:
    - 输入: 原始明文密码、用户标识与角色载荷
    - 输出: 散列密文、加密 JWT 字符串或验证后的 Claims 字典

作者:
    System Architect (系统架构组) & Backend Team
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.exceptions import AuthenticationError

BCRYPT_ROUNDS = 12


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与 Bcrypt 散列密文"""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码 Bcrypt 散列密文 (工作因子 12)"""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """签发 Access Token (默认 120 分钟)"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "token_type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """签发 Refresh Token (默认 7 天)"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "token_type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """解码并校验 JWT Token，无效或过期时抛出 AuthenticationError"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError(message="Token 已过期，请重新登录", code=40101)
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(message=f"无效的认证凭据: {str(e)}", code=40101)


if __name__ == "__main__":
    print("=== [Self-Test] Starting Security Module Self-Test ===")
    
    # 1. 密码 Bcrypt 12 工作因子自测
    test_pwd = "AdminSecurePassword2026!"
    hashed = get_password_hash(test_pwd)
    print(f"[Self-Test] Hashed password: {hashed}")
    assert hashed.startswith("$2b$12$"), "Bcrypt 工作因子必须为 12 ($2b$12$)"
    assert verify_password(test_pwd, hashed) is True, "密码验证必须通过"
    assert verify_password("WrongPassword", hashed) is False, "错误密码验证必须失败"

    # 2. Access Token 签发与解密自测
    sample_claims = {
        "sub": "10086",
        "username": "zhangsan",
        "dept_id": 10,
        "role_ids": [1, 2],
        "permissions": ["knowledge:view", "chat:view"]
    }
    access_token = create_access_token(sample_claims)
    decoded_access = decode_token(access_token)
    assert decoded_access["sub"] == "10086"
    assert decoded_access["token_type"] == "access"
    assert decoded_access["username"] == "zhangsan"
    print(f"[Self-Test] Access Token verification PASSED.")

    # 3. Refresh Token 签发与解密自测
    refresh_token = create_refresh_token(sample_claims)
    decoded_refresh = decode_token(refresh_token)
    assert decoded_refresh["sub"] == "10086"
    assert decoded_refresh["token_type"] == "refresh"
    print(f"[Self-Test] Refresh Token verification PASSED.")

    # 4. 过期 Token 拦截自测
    expired_token = create_access_token(sample_claims, expires_delta=timedelta(seconds=-1))
    try:
        decode_token(expired_token)
        raise AssertionError("Expired token did not raise AuthenticationError!")
    except AuthenticationError as e:
        assert e.code == 40101
        print(f"[Self-Test] Expired token correctly rejected with code {e.code}.")

    print("=== [Self-Test] All Security Module tests PASSED successfully! ===")
