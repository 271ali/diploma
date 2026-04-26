from datetime import datetime, timedelta, timezone
import jwt
from core.config import SECRET_KEY,ALGORITHM

def create_access_token(user_id):
    expire=datetime.now(timezone.utc) + timedelta(minutes=15)
    payload= {"sub": str(user_id), "exp": int(expire.timestamp())}
    encode_jwt=jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)
    return encode_jwt

def decode_access_token(token):
    try:
        payload =jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return int(payload.get('sub'))
    except jwt.PyJWTError:
        return None

