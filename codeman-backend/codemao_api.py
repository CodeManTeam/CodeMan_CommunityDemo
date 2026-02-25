import httpx
import json
import base64
from typing import Optional, Dict, Any
from config import CODEMAO_PID

CODEMAO_API_BASE = "https://api.codemao.cn"

def decode_jwt_payload(token: str) -> Dict[str, Any]:
    try:
        parts = token.split('.')
        if len(parts) < 2:
            return {}
        payload = parts[1]
        # Add padding if needed for base64
        payload += '=' * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return {}

class CodemaoAPI:
    async def login(self, identity: str, password: str) -> Dict[str, Any]:
        """
        Attempt to login to Codemao using username/phone/email and password.
        Returns the user data and token if successful.
        """
        url = f"{CODEMAO_API_BASE}/tiger/v3/web/accounts/login"
        # pid is often required for web login, using a common one or empty
        payload = {
            "identity": identity,
            "password": password,
            "pid": CODEMAO_PID
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                print(f"DEBUG: Login Status: {response.status_code}")
                print(f"DEBUG: Login Response: {response.text}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Handle 401/403 specifically
                if e.response.status_code in [401, 403]:
                    raise Exception("Invalid credentials")
                raise e
            except Exception as e:
                raise Exception(f"Login failed: {str(e)}")

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Fetch user details using the authentication token.
        Uses JWT payload as primary source for ID, then tries API for details.
        """
        user_info = {}
        
        # 1. Extract ID from JWT (Primary Source)
        jwt_data = decode_jwt_payload(token)
        user_id = jwt_data.get("user_id")
        
        if user_id:
            user_info["id"] = user_id
            user_info["nickname"] = f"User {user_id}" # Default
            user_info["avatar_url"] = "https://static.codemao.cn/codemao-logo.png" # Default
            user_info["description"] = "Programming Cat User" # Default
        
        # 2. Try to fetch full details from API (Enhancement)
        # Try multiple endpoints
        endpoints = [
            f"{CODEMAO_API_BASE}/web/users/details", # Try public endpoint first
            f"{CODEMAO_API_BASE}/creation-tools/v1/user/center", # Try authenticated endpoint
        ]
        
        async with httpx.AsyncClient() as client:
            for url in endpoints:
                try:
                    params = {}
                    if "details" in url and user_id:
                        params = {"id": user_id}
                    
                    headers = {}
                    cookies = {}
                    if "center" in url:
                        cookies = {"authorization": token}
                        headers = {"Authorization": f"Bearer {token}"} # Try both
                    
                    print(f"DEBUG: Fetching user info from {url}...")
                    response = await client.get(url, params=params, cookies=cookies, headers=headers)
                    print(f"DEBUG: Status {response.status_code} for {url}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Update with real data if available
                        if data.get("id"): user_info["id"] = data.get("id")
                        if data.get("nickname"): user_info["nickname"] = data.get("nickname")
                        if data.get("avatar_url"): user_info["avatar_url"] = data.get("avatar_url")
                        if data.get("description"): user_info["description"] = data.get("description")
                        break # Success!
                except Exception as e:
                    print(f"Error fetching user info from {url}: {e}")
        
        return user_info

codemao_api = CodemaoAPI()
