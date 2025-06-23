#!/bin/zsh

echo "=== DEBUGGING BENCHMARK ISSUES ==="
alias timeout="gtimeout"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}1. Checking Apache Bench installation:${NC}"
echo "AB Location: $(which ab)"
echo "AB Version:"
ab -V
echo "AB Path in \$PATH: $(echo $PATH | tr ':' '\n' | grep -E '(bin|sbin)' | head -5)"

echo -e "\n${YELLOW}2. Testing AB with simple command:${NC}"
echo "Testing ab with httpbin.org..."
ab -n 5 -c 1 http://httpbin.org/get 2>&1 | head -10

echo -e "\n${YELLOW}3. Checking local services:${NC}"
echo "Spring Boot Health Check:"
curl -s -w "HTTP %{http_code} - Time: %{time_total}s\n" http://localhost:8080/health 2>/dev/null || echo "FAILED"

echo "Bun+Hono Health Check:"
curl -s -w "HTTP %{http_code} - Time: %{time_total}s\n" http://localhost:3000/health 2>/dev/null || echo "FAILED"

echo -e "\n${YELLOW}4. Testing AB with local services:${NC}"
echo "Testing Spring Boot with ab..."
timeout 10s ab -n 5 -c 1 http://localhost:8080/health 2>&1 | grep -E "(Requests per second|Failed requests|Connect|Error)" || echo "AB test failed"

echo "Testing Bun+Hono with ab..."
timeout 10s ab -n 5 -c 1 http://localhost:3000/health 2>&1 | grep -E "(Requests per second|Failed requests|Connect|Error)" || echo "AB test failed"

echo -e "\n${YELLOW}5. Shell and Environment Check:${NC}"
echo "Current shell: $SHELL"
echo "ZSH version: $ZSH_VERSION"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"

echo -e "\n${YELLOW}6. Testing timeout command:${NC}"
echo "Testing timeout command..."
timeout 5s sleep 2 && echo "Timeout works" || echo "Timeout failed with exit code: $?"

echo -e "\n${YELLOW}7. Manual AB command test:${NC}"
echo "Running exact AB command from script..."

# Simulate the exact command from your script
SPRING_URL="http://localhost:8080"
tps=5
DURATION=60
total_requests=$((tps * DURATION))
output_file="/tmp/debug_springboot_health_5tps.txt"
timeout_duration=$((DURATION + 30))

echo "Command: timeout ${timeout_duration}s ab -n $total_requests -c $tps -k -q \"$SPRING_URL/health\""
echo "Executing..."

timeout ${timeout_duration}s ab -n $total_requests -c $tps -k -q "$SPRING_URL/health" > "$output_file" 2>&1
exit_code=$?

echo "Exit code: $exit_code"
echo "Output file size: $(wc -l < "$output_file" 2>/dev/null || echo "0") lines"
echo "First 10 lines of output:"
head -10 "$output_file" 2>/dev/null || echo "No output file"

echo -e "\n${YELLOW}8. System Resource Check:${NC}"
echo "Available memory:"
free -h 2>/dev/null || vm_stat 2>/dev/null | head -5 || echo "Memory info not available"

echo "Load average:"
uptime

echo "Disk space:"
df -h . | tail -1

echo -e "\n${YELLOW}9. Process Check:${NC}"
echo "Services running on target ports:"
lsof -i :8080 2>/dev/null || echo "Nothing on port 8080"
lsof -i :3000 2>/dev/null || echo "Nothing on port 3000"

echo -e "\n${GREEN}=== DEBUG COMPLETE ===${NC}"
echo -e "If AB is working with external URLs but failing with localhost,"
echo -e "the issue is likely with your local services, not AB itself."
