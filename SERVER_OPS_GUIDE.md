# CodeMan Community Server Operations & Maintenance Guide

This document summarizes the deployment strategies, configuration best practices, and troubleshooting experience gained during the development and maintenance of the CodeMan Community platform.

## 1. Deployment Architecture

### 1.1 Automated Deployment
We utilize a Python-based script (`deploy_chat_v2.py`) using `paramiko` for automated deployment. This approach is preferred over manual file transfers to ensure consistency.

**Key Steps:**
1.  **Connect**: Establish SSH connection to the remote server.
2.  **Upload**: Use SFTP to upload modified files (Backend code, Frontend `dist` or source).
3.  **Restart**: Execute remote Docker Compose commands to rebuild and restart services.

**Command Reference:**
```bash
# Rebuild frontend only
docker compose up -d --build frontend

# Restart backend (fast, no rebuild if only python code changed and mounted)
docker compose restart backend
```

### 1.2 Docker Compose
The project runs on Docker Compose, separating concerns into:
-   **Frontend**: Nginx container serving static Vue.js files.
-   **Backend**: Python/FastAPI container.
-   **Database**: MySQL (assumed based on context).

## 2. Nginx Configuration & Networking

### 2.1 Reverse Proxy Setup
Nginx acts as the gateway, routing `/api/` traffic to the backend container.

**Critical Configuration for WebSockets & Long Polling:**
```nginx
location /api/ {
    proxy_pass http://backend:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    
    # Crucial for maintaining connections
    proxy_read_timeout 86400; 
    
    # WebSocket Support (If used)
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $http_connection; # Dynamic connection header
}
```

**Lesson Learned**: Hardcoding `Connection "upgrade"` can cause issues in some environments. Using `$http_connection` is safer. Missing `proxy_read_timeout` leads to premature disconnections (e.g., 60s defaults).

## 3. Architecture Decisions: WebSocket vs. Polling

### 3.1 The Switch to HTTP Polling
Initially designed with WebSockets for real-time chat, we migrated to **HTTP Polling** for better stability and resource management in this specific environment.

**Reasons:**
-   **Stability**: WebSockets were facing frequent connection drops (Code 1006/1008) due to network intermediaries or strict firewall rules.
-   **Simplicity**: HTTP Polling eliminates the need for maintaining stateful connections on the server, simplifying load balancing and error handling.

### 3.2 Polling Optimization Strategy
To prevent resource exhaustion (client CPU/Network and Server load), we implemented **Smart Polling** in the frontend (`ChatRoom.vue`):

1.  **Page Visibility API**: 
    -   *Active Tab*: Poll every 3-5 seconds.
    -   *Hidden Tab*: **Stop polling completely**.
    -   *On Resume*: Immediately trigger a fetch.
2.  **Incremental Fetching**:
    -   Backend supports `after_id` parameter to fetch only new messages since the last received message ID, drastically reducing payload size.

## 4. Backend (FastAPI) Best Practices

### 4.1 Authentication Standardization
**Problem**: Mixing `Query` parameters (`?token=...`) and Headers for authentication caused confusion and `422` errors.
**Solution**: Standardized on `Authorization: Bearer <token>` header for all HTTP endpoints.
-   **Backend**: Use `Depends(get_current_user)`.
-   **Frontend**: Axios interceptors or explicit header configuration.

### 4.2 Error Handling
-   **422 Unprocessable Entity**: Usually indicates a mismatch between Pydantic models and sent JSON data, or missing query parameters.
-   **403 Forbidden**: Used for logic permissions (e.g., "Must be mutual friends to DM"). The frontend should handle this gracefully (e.g., show "Add Friend" button instead of crashing).

## 5. Troubleshooting Checklist

| Symptom | Probable Cause | Fix |
| :--- | :--- | :--- |
| **WebSocket connects then closes immediately** | Auth failure or Nginx timeout | Check `proxy_read_timeout`; Verify Token validity in handshake. |
| **API returns 422** | Missing field in JSON body or Query param | Check Browser Network Tab payload vs Pydantic model. |
| **"Images loaded lazily" warning** | Chrome optimization | Ignorable warning, unrelated to logic errors. |
| **High Server CPU** | Aggressive polling | Increase polling interval; Implement visibility check to stop background polling. |

## 6. Future Recommendations

1.  **Database Indexing**: Ensure `(sender_id, recipient_id, created_at)` composite indexes exist for efficient message history retrieval.
2.  **Message Pagination**: Currently fetches "last 50". Implement proper cursor-based pagination for scrolling up.
3.  **State Management**: Move Chat state (messages, contacts) to Pinia store to persist data when navigating between Forum and Chat.
