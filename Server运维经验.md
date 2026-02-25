# Server 运维经验与维护指南

本文档记录了 CodeMan Community 服务器（IP: 192.227.152.240）的部署架构、配置细节及常见问题处理方案，供后续运维参考。

## 1. 系统架构概览

- **部署方式**: Docker Compose
- **部署根目录**: `/opt/codeman`
- **容器服务**:
  - `codeman-backend`: Python/FastAPI 后端服务 (Port 8000)
  - `codeman-frontend`: Vue3/Nginx 前端服务 (Port 80)

## 2. 关键文件与路径

| 文件/目录 | 路径 | 说明 |
| :--- | :--- | :--- |
| **Docker 配置** | `/opt/codeman/docker-compose.yml` | 服务编排文件 |
| **数据库** | `/opt/codeman/codeman-backend/database.db` | SQLite 数据库文件 (需定期备份) |
| **RSA 私钥** | `/opt/codeman/codeman-backend/private_key.pem` | **[重要]** 登录加密私钥。必须持久化，否则重启会导致旧用户/前端缓存公钥失效。 |
| **后端代码** | `/opt/codeman/codeman-backend/` | Python 源码 |
| **前端源码** | `/opt/codeman/codeman-frontend/` | Vue 源码 (构建时使用) |
| **遗留站点** | `/var/www/html` | 旧的 php-proxy-app (已停用 httpd) |

## 3. 常用运维命令

所有命令建议在部署根目录下执行：
```bash
cd /opt/codeman
```

### 服务管理
```bash
# 启动所有服务 (后台运行)
docker compose up -d

# 停止所有服务
docker compose down

# 重启特定服务 (例如仅重启后端)
docker compose restart backend

# 更新代码后重新构建并启动 (例如前端)
docker compose up -d --build frontend
```

### 日志查看
```bash
# 查看后端实时日志 (最后 50 行)
docker logs -f --tail 50 codeman-backend

# 查看前端 (Nginx) 访问日志
docker logs -f --tail 50 codeman-frontend
```

## 4. 故障排查记录 (Troubleshooting)

### (1) 登录失败：400 Bad Request (Decryption failed)
*   **现象**: 用户登录时提示“密码错误”或服务器日志显示 RSA 解密失败。
*   **原因**: 后端容器重启后，默认会重新生成 RSA 密钥对。如果用户使用的是旧公钥加密（前端缓存），后端新私钥无法解密。
*   **解决方案**: 代码已修改为优先读取本地 `private_key.pem`。
    *   **检查**: 确保 `/opt/codeman/codeman-backend/` 下存在 `private_key.pem` 文件。

### (2) 请求被拦截：403 Forbidden
*   **现象**: API 请求返回 403，日志显示 `Access Denied`。
*   **原因**: `main.py` 中的反爬虫中间件 (`anti_scraping_middleware`) 校验 `Referer` 或 `Origin` 失败。
*   **解决方案**:
    1.  查看日志中被拒绝的 Origin/Referer。
    2.  修改 `main.py` 中的 `allowed_hosts` 列表，添加合法域名或 IP。
    3.  重启后端: `docker compose restart backend`。

### (3) 前端容器启动失败：Port 80 Occupied
*   **现象**: `docker compose up` 报错 `bind: address already in use`。
*   **原因**: 系统自带的 `httpd` (Apache) 服务占用了 80 端口。
*   **解决方案**:
    ```bash
    systemctl stop httpd
    systemctl disable httpd
    docker compose up -d frontend
    ```

### (4) 数据库重置
*   **场景**: 需要清空所有数据（用户、帖子等）。
*   **操作**:
    ```bash
    docker compose down
    rm /opt/codeman/codeman-backend/database.db
    docker compose up -d
    # 系统会自动创建新的空数据库文件
    ```

## 5. 备份策略

建议定期备份以下核心数据：
1.  **数据库**: `database.db`
2.  **密钥**: `private_key.pem` (丢失会导致所有已保存的加密数据无法解密)
3.  **配置**: `.env` (如果有)

## 6. CDN 接入指南

*   **源站 IP**: `192.227.152.240`
*   **源站端口**: `80` (HTTP)
*   **回源 Host**: 建议设置为您的域名 (如 `codeman.community`)，并在后端 `main.py` 的 `allowed_hosts` 中添加该域名，防止被 403 拦截。

---
*文档生成时间: 2026-02-24*
