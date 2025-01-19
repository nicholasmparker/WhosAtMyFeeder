# Bug Report: Vite Development Server Access Issues in Docker

## Issue Description
Unable to access API endpoints through Vite's proxy in Docker container.

## Root Cause Analysis
1. Node.js was unable to connect to Flask server
2. Error showed: `ECONNREFUSED ::1:7766`
3. Node.js was trying localhost but connection was failing

## Solution
Force Node.js to use consistent localhost resolution:
```yaml
# docker-compose.yml
environment:
  - NODE_OPTIONS=--dns-result-order=ipv4first
```

## Why This Works
1. Node.js's localhost resolution was inconsistent
2. Setting dns-result-order makes it consistent
3. Allows Node.js to reliably connect to Flask
4. Not about IPv4 vs IPv6, but about consistent resolution

## Container Architecture
```
Docker Container
├── Vite Dev Server (0.0.0.0:5173)
├── Flask Backend (0.0.0.0:7766)
└── WebSocket Server (0.0.0.0:8765)
```
- All services bind to all interfaces
- Internal communication via localhost
- Port mappings for external access

## Best Practices
1. Use environment variables to control Node.js behavior
2. Keep Docker configuration minimal
3. Let tools use their defaults when possible
4. Fix connection issues at the right level

## Lessons Learned
1. Connection refused often means resolution issue
2. Focus on connection reliability, not IP versions
3. Use tool-specific solutions (NODE_OPTIONS)
4. Keep configurations simple

## Related Documentation
- [Node.js DNS Resolution](https://nodejs.org/api/cli.html#--dns-result-orderorder)
- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Vite Configuration](https://vitejs.dev/config/)
