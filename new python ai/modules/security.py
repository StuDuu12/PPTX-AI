"""
Security utilities cho AI PowerPoint Generator
Xử lý mã hóa API keys và bảo mật session
"""

import hashlib
import base64
import os
from cryptography.fernet import Fernet
from typing import Optional

class SecurityManager:
    def __init__(self):
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Tạo hoặc load encryption key"""
        key_file = ".security_key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Mã hóa API key"""
        encrypted = self.fernet.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Giải mã API key"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception:
            return ""
    
    def hash_session_id(self, session_data: str) -> str:
        """Tạo session hash"""
        return hashlib.sha256(session_data.encode()).hexdigest()[:16]
    
    def validate_api_key_format(self, api_key: str) -> bool:
        """Validate API key format"""
        # Gemini API key format validation
        if api_key.startswith('AIzaSy') and len(api_key) == 39:
            return True
        return False
    
    def sanitize_filename(self, filename: str) -> str:
        """Làm sạch tên file để tránh path traversal"""
        import re
        # Chỉ giữ ký tự an toàn
        safe_chars = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
        return safe_chars[:50]  # Giới hạn độ dài

def get_client_ip(request) -> str:
    """Lấy IP của client (cho rate limiting)"""
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.headers.get('X-Real-IP', 'unknown')

class RateLimiter:
    def __init__(self, max_requests: int = 10, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Kiểm tra rate limit"""
        import time
        now = time.time()
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Xóa requests cũ
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.time_window
        ]
        
        # Kiểm tra limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        self.requests[client_id].append(now)
        return True

# Global rate limiter
rate_limiter = RateLimiter(max_requests=20, time_window=3600)  # 20 requests/hour
