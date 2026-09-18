# Module 9: Industry-Standard Project — Full Stack App Deployment

---

## 9.1 Project Overview

We'll build and deploy a production-grade **Task Management API** with:

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Nginx     │────▶│  Node.js    │────▶│ PostgreSQL   │
│   Reverse   │     │  REST API   │     │  Database    │
│   Proxy     │     │  (Express)  │     │              │
│   :80       │     │  :3000      │     │  :5432       │
└─────────────┘     └──────┬──────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    Redis     │
                    │    Cache     │
                    │    :6379     │
                    └──────────────┘
```

---

## 9.2 Project Structure

```
task-manager/
├── docker-compose.yml
├── docker-compose.override.yml    # Dev overrides
├── docker-compose.prod.yml        # Production overrides
├── .env.example
├── .env
├── .dockerignore
├── backend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── app.js
│   │   ├── routes/
│   │   │   └── tasks.js
│   │   ├── db.js
│   │   └── cache.js
│   └── tests/
│       └── tasks.test.js
├── nginx/
│   ├── nginx.conf
│   └── ssl/                       # For production
└── database/
    └── init.sql
```

---

## 9.3 Step 1: Application Code

### backend/package.json

```json
{
  "name": "task-manager-api",
  "version": "1.0.0",
  "scripts": {
    "start": "node src/app.js",
    "dev": "nodemon src/app.js",
    "test": "jest --coverage"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.3",
    "redis": "^4.6.12",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "morgan": "^1.10.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.2",
    "jest": "^29.7.0"
  }
}
```

### backend/src/app.js

```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const taskRoutes = require('./routes/tasks');
const { initDB } = require('./db');
const { initCache } = require('./cache');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const { pool } = require('./db');
    await pool.query('SELECT 1');
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
  } catch (err) {
    res.status(503).json({ status: 'unhealthy', error: err.message });
  }
});

app.use('/api/tasks', taskRoutes);

async function start() {
  await initDB();
  await initCache();
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
  });
}

start().catch(err => {
  console.error('Failed to start:', err);
  process.exit(1);
});
```

### backend/src/db.js

```javascript
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

async function initDB() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      )
    `);
    console.log('Database initialized');
  } finally {
    client.release();
  }
}

module.exports = { pool, initDB };
```

### backend/src/cache.js

```javascript
const { createClient } = require('redis');

let redisClient;

async function initCache() {
  redisClient = createClient({ url: process.env.REDIS_URL });
  redisClient.on('error', err => console.error('Redis error:', err));
  await redisClient.connect();
  console.log('Redis connected');
}

async function getCache(key) {
  if (!redisClient) return null;
  const data = await redisClient.get(key);
  return data ? JSON.parse(data) : null;
}

async function setCache(key, value, ttl = 300) {
  if (!redisClient) return;
  await redisClient.setEx(key, ttl, JSON.stringify(value));
}

async function clearCache(pattern) {
  if (!redisClient) return;
  const keys = await redisClient.keys(pattern);
  if (keys.length) await redisClient.del(keys);
}

module.exports = { initCache, getCache, setCache, clearCache };
```

### backend/src/routes/tasks.js

```javascript
const express = require('express');
const router = express.Router();
const { pool } = require('../db');
const { getCache, setCache, clearCache } = require('../cache');

// GET /api/tasks
router.get('/', async (req, res) => {
  try {
    const cached = await getCache('tasks:all');
    if (cached) return res.json({ source: 'cache', data: cached });

    const result = await pool.query(
      'SELECT * FROM tasks ORDER BY created_at DESC'
    );
    await setCache('tasks:all', result.rows);
    res.json({ source: 'database', data: result.rows });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/tasks
router.post('/', async (req, res) => {
  try {
    const { title, description } = req.body;
    if (!title) return res.status(400).json({ error: 'Title is required' });

    const result = await pool.query(
      'INSERT INTO tasks (title, description) VALUES ($1, $2) RETURNING *',
      [title, description]
    );
    await clearCache('tasks:*');
    res.status(201).json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/tasks/:id
router.put('/:id', async (req, res) => {
  try {
    const { title, description, status } = req.body;
    const result = await pool.query(
      `UPDATE tasks SET title=$1, description=$2, status=$3, updated_at=NOW()
       WHERE id=$4 RETURNING *`,
      [title, description, status, req.params.id]
    );
    if (!result.rows.length) return res.status(404).json({ error: 'Not found' });
    await clearCache('tasks:*');
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/tasks/:id
router.delete('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'DELETE FROM tasks WHERE id=$1 RETURNING *', [req.params.id]
    );
    if (!result.rows.length) return res.status(404).json({ error: 'Not found' });
    await clearCache('tasks:*');
    res.json({ message: 'Deleted', task: result.rows[0] });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
```

---

## 9.4 Step 2: Dockerfile (Multi-Stage)

### backend/Dockerfile

```dockerfile
# ─── Stage 1: Dependencies ──────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production

# ─── Stage 2: Development ───────────────────────
FROM node:20-alpine AS development
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npx", "nodemon", "src/app.js"]

# ─── Stage 3: Production ────────────────────────
FROM node:20-alpine AS production
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY --from=deps --chown=app:app /app/node_modules ./node_modules
COPY --chown=app:app package.json ./
COPY --chown=app:app src ./src
USER app
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
CMD ["node", "src/app.js"]
```

### backend/.dockerignore

```
node_modules
npm-debug.log
.git
.gitignore
.env
*.md
tests
coverage
.vscode
Dockerfile
.dockerignore
```

---

## 9.5 Step 3: Nginx Reverse Proxy

### nginx/nginx.conf

```nginx
upstream api {
    server api:3000;
}

server {
    listen 80;
    server_name localhost;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # API proxy
    location /api/ {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
    }

    # Health check
    location /health {
        proxy_pass http://api;
    }

    location / {
        return 200 '{"message": "Task Manager API - use /api/tasks"}';
        add_header Content-Type application/json;
    }
}
```

---

## 9.6 Step 4: Database Init Script

### database/init.sql

```sql
-- Seed data for development
INSERT INTO tasks (title, description, status) VALUES
  ('Set up Docker', 'Learn Docker fundamentals', 'completed'),
  ('Build REST API', 'Create Express.js API', 'in_progress'),
  ('Add caching', 'Implement Redis caching layer', 'pending'),
  ('Write tests', 'Add unit and integration tests', 'pending'),
  ('Deploy to production', 'Set up CI/CD pipeline', 'pending')
ON CONFLICT DO NOTHING;
```

---

## 9.7 Step 5: Docker Compose Files

### docker-compose.yml (Base)

```yaml
services:
  api:
    build:
      context: ./backend
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
      PORT: "3000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - frontend
      - backend

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 128mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
    networks:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "${APP_PORT:-80}:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - api
    networks:
      - frontend

volumes:
  postgres-data:
  redis-data:

networks:
  frontend:
  backend:
```

### docker-compose.override.yml (Development — auto-loaded)

```yaml
services:
  api:
    build:
      target: development
    volumes:
      - ./backend/src:/app/src
    ports:
      - "3000:3000"
      - "9229:9229"
    environment:
      NODE_ENV: development
    command: npx nodemon --inspect=0.0.0.0:9229 src/app.js

  db:
    ports:
      - "5432:5432"
    volumes:
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro

  redis:
    ports:
      - "6379:6379"

  nginx:
    ports:
      - "8080:80"
```

### docker-compose.prod.yml (Production)

```yaml
services:
  api:
    build:
      target: production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
    environment:
      NODE_ENV: production
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  db:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G

  redis:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M

  nginx:
    restart: unless-stopped
    ports:
      - "80:80"
```

### .env.example

```bash
DB_USER=taskmanager
DB_PASSWORD=change_me_in_production
DB_NAME=taskdb
APP_PORT=80
```

---

## 9.8 Step 6: Running the Project

```bash
# ─── Development ─────────────────────────────────

# Copy env file
cp .env.example .env

# Start in development mode
docker compose up -d --build

# Output:
# [+] Building 15.2s (12/12) FINISHED
# [+] Running 5/5
#  ✔ Network task-manager_frontend  Created
#  ✔ Network task-manager_backend   Created
#  ✔ Container task-manager-db-1    Healthy
#  ✔ Container task-manager-redis-1 Healthy
#  ✔ Container task-manager-api-1   Started
#  ✔ Container task-manager-nginx-1 Started

# Check status
docker compose ps

# Output:
# NAME                      STATUS          PORTS
# task-manager-api-1        Up (healthy)    0.0.0.0:3000->3000/tcp
# task-manager-db-1         Up (healthy)    0.0.0.0:5432->5432/tcp
# task-manager-nginx-1      Up              0.0.0.0:8080->80/tcp
# task-manager-redis-1      Up (healthy)    0.0.0.0:6379->6379/tcp

# Test the API
curl http://localhost:8080/health
# {"status":"healthy","timestamp":"2024-01-15T12:00:00.000Z"}

curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn Docker","description":"Complete the Docker course"}'
# {"id":6,"title":"Learn Docker","description":"Complete the Docker course",...}

curl http://localhost:8080/api/tasks
# {"source":"database","data":[...]}

# Second request hits cache
curl http://localhost:8080/api/tasks
# {"source":"cache","data":[...]}

# View logs
docker compose logs -f api

# ─── Production ──────────────────────────────────

# Start with production config
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Verify
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

---

## 9.9 Step 7: Common Operations

```bash
# Database access
docker compose exec db psql -U taskmanager -d taskdb
taskdb=# SELECT * FROM tasks;
taskdb=# \q

# Redis access
docker compose exec redis redis-cli
127.0.0.1:6379> KEYS *
127.0.0.1:6379> GET tasks:all
127.0.0.1:6379> exit

# Run tests
docker compose exec api npm test

# Database backup
docker compose exec db pg_dump -U taskmanager taskdb > backup.sql

# Database restore
docker compose exec -T db psql -U taskmanager taskdb < backup.sql

# View resource usage
docker compose stats --no-stream

# Rebuild single service
docker compose up -d --build api

# Scale API (if using production config without fixed ports)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale api=3

# Full cleanup
docker compose down -v
```

---

## 9.10 Troubleshooting This Project

### API Can't Connect to Database
```bash
# Check if db is healthy
docker compose ps db
# If "starting" or "unhealthy":
docker compose logs db

# Common fix: Wait for health check
docker compose exec api wget -qO- http://localhost:3000/health
```

### Port Conflict
```bash
# Change port in .env
APP_PORT=8081
docker compose up -d
```

### Data Not Persisting After Restart
```bash
# Verify volumes exist
docker volume ls | grep task-manager

# Ensure you used "docker compose down" NOT "docker compose down -v"
```

---

## Module 9 Summary

- Multi-stage Dockerfiles separate dev/prod concerns
- Docker Compose orchestrates all services with one command
- Override files (`docker-compose.override.yml`) customize per environment
- Health checks with `condition: service_healthy` ensure proper startup order
- Network isolation: frontend services can't directly access the database
- Named volumes persist database and cache data across restarts
- Nginx reverse proxy handles routing and security headers

---

**Next Module: [Module 10 - Advanced Topics](module-10-advanced.md)**
