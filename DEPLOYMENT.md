# Deployment Information

## Public URLs

### Backend API (ai-agent-production)
https://ai-agent-production-k5rm.onrender.com

### Frontend Chat App (vaccine-assistant-frontend-personal)
https://vaccine-assistant-frontend-personal.onrender.com

## Platform
Render (Free Plan, Region: Singapore)

## Test Commands

### Health Check
```bash
curl https://ai-agent-production-k5rm.onrender.com/health
# Expected: {"status": "ok", "uptime_seconds": ..., "version": "1.0.0", ...}
```

### Readiness Check
```bash
curl https://ai-agent-production-k5rm.onrender.com/ready
# Expected: {"ready": true}
```

### API Test (without authentication)
```bash
curl -i -X POST https://ai-agent-production-k5rm.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
# Expected: 401 Unauthorized
```

### API Test (with authentication)
```bash
curl -X POST https://ai-agent-production-k5rm.onrender.com/ask \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "My name is Alice"}'
# Expected: 200 OK with response
```

### Conversation History Test (Alice Test)
```bash
curl -X POST https://ai-agent-production-k5rm.onrender.com/ask \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "What is my name?"}'
# Expected: 200 OK with response mentioning "Alice"
```

## Environment Variables Set
- `PORT`: 10000 (Tự động bởi Render)
- `AGENT_API_KEY`: dev-key-change-me (API key để test)
- `ENVIRONMENT`: production
