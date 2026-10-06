@echo off
echo [AUTARCH] Starting autonomous systems...
cd /d C:\UMBRA_CORE

REM Start MCP server
start "UMBRA MCP Server" python mcp_core\umbra_mcp_server.py

REM Wait for MCP to start
timeout /t 3 /nobreak >nul

REM Start AUTARCH orchestrator
start "AUTARCH Orchestrator" python autarch\orchestrator.py

echo [AUTARCH] All systems started
echo [AUTARCH] MCP: http://localhost:8000
echo [AUTARCH] Orchestrator: Running continuous loop
pause
