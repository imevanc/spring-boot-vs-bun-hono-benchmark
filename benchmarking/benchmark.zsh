#!/bin/zsh

echo "==================================================="
echo "API Performance Benchmark: Spring Boot vs Bun+Hono"
echo "==================================================="
alias timeout="gtimeout"

# Configuration
SPRING_URL="http://localhost:8080"
BUN_URL="http://localhost:3000"
DURATION=60
WARMUP_DURATION=10

# TPS levels to test - start with lower values for debugging
TPS_LEVELS=(5 10 15 30 40 100 1000)

# Endpoints to test - using zsh associative array syntax
typeset -A ENDPOINTS
ENDPOINTS=(
    health "GET"
    "users/123" "GET"
    compute "GET"
    echo "POST"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if service is running with detailed output
check_service() {
    local url=$1
    local name=$2
    
    echo -n "Checking $name service at $url... "
    
    # Use curl with more verbose error handling
    local response=$(curl -s -w "%{http_code}" -o /tmp/health_check.txt --connect-timeout 5 --max-time 10 "$url/health" 2>&1)
    local curl_exit_code=$?
    local http_code="${response: -3}"
    
    if [[ $curl_exit_code -eq 0 ]] && [[ "$http_code" =~ ^[2-3][0-9][0-9]$ ]]; then
        echo -e "${GREEN}OK (HTTP $http_code)${NC}"
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}  Curl exit code: $curl_exit_code${NC}"
        if [[ $curl_exit_code -ne 0 ]]; then
            echo -e "${RED}  Error: Connection failed - is the service running?${NC}"
        else
            echo -e "${RED}  HTTP Code: $http_code${NC}"
        fi
        return 1
    fi
}

# Function to test individual endpoint before benchmarking
test_endpoint() {
    local url=$1
    local endpoint=$2
    local method=$3
    local name=$4
    
    echo -n "  Testing $name $endpoint ($method)... "
    
    if [[ "$method" == "POST" ]]; then
        echo '{"test": "benchmark", "id": 123, "data": "sample"}' > /tmp/test_post_data.json
        local response=$(curl -s -w "%{http_code}" -o /tmp/endpoint_test.txt \
                        --connect-timeout 5 --max-time 10 \
                        -H "Content-Type: application/json" \
                        -d @/tmp/test_post_data.json \
                        "$url/$endpoint" 2>&1)
    else
        local response=$(curl -s -w "%{http_code}" -o /tmp/endpoint_test.txt \
                        --connect-timeout 5 --max-time 10 \
                        "$url/$endpoint" 2>&1)
    fi
    
    local curl_exit_code=$?
    local http_code="${response: -3}"
    
    if [[ $curl_exit_code -eq 0 ]] && [[ "$http_code" =~ ^[2-3][0-9][0-9]$ ]]; then
        echo -e "${GREEN}OK (HTTP $http_code)${NC}"
        return 0
    else
        echo -e "${RED}FAILED (Exit: $curl_exit_code, HTTP: $http_code)${NC}"
        return 1
    fi
}

# Function to warmup service
warmup_service() {
    local url=$1
    local name=$2
    
    echo "Warming up $name service..."
    # Use a gentler warmup
    ab -n 10 -c 2 "$url/health" > /dev/null 2>&1
    sleep 1
}

# Function to run benchmark with better error handling
run_benchmark() {
    local url=$1
    local endpoint=$2
    local method=$3
    local tps=$4
    local framework=$5
    
    local total_requests=$((tps * DURATION))
    local output_file="/tmp/${framework}_${endpoint//\//_}_${tps}tps.txt"
    
    # Adjust timeout based on expected duration
    local timeout_duration=$((DURATION + 60))
    
    # For very high TPS, limit concurrent connections to prevent overwhelming
    local concurrent_connections=$tps
    if [[ $tps -gt 100 ]]; then
        concurrent_connections=100
    fi
    
    echo -n "    Running $framework $endpoint at ${tps}TPS (${total_requests} requests, ${concurrent_connections} concurrent)... "
    
    if [[ "$method" == "POST" ]]; then
        echo '{"test": "benchmark", "id": 123, "data": "sample"}' > /tmp/post_data.json
        timeout ${timeout_duration}s ab -n $total_requests -c $concurrent_connections \
            -T "application/json" -p /tmp/post_data.json \
            -k -q "$url/$endpoint" > "$output_file" 2>&1
    else
        timeout ${timeout_duration}s ab -n $total_requests -c $concurrent_connections \
            -k -q "$url/$endpoint" > "$output_file" 2>&1
    fi
    
    local exit_code=$?
    
    # Check if command timed out or failed
    if [[ $exit_code -eq 124 ]]; then
        echo -e "${RED}TIMEOUT${NC}"
        echo "$framework,$endpoint,$method,$tps,0,0,0,0,0,TIMEOUT" >> benchmark_results.csv
        return 1
    elif [[ $exit_code -ne 0 ]]; then
        echo -e "${RED}FAILED (Exit: $exit_code)${NC}"
        echo "$framework,$endpoint,$method,$tps,0,0,0,0,0,FAILED" >> benchmark_results.csv
        return 1
    fi
    
    # Check if ab actually completed successfully
    if ! grep -q "Complete requests" "$output_file"; then
        echo -e "${RED}INCOMPLETE${NC}"
        echo "$framework,$endpoint,$method,$tps,0,0,0,0,0,INCOMPLETE" >> benchmark_results.csv
        return 1
    fi
    
    # Extract metrics with better error handling
    local rps=$(grep "Requests per second" "$output_file" | awk '{print $4}' | head -1)
    local avg_time=$(grep "Time per request" "$output_file" | head -1 | awk '{print $4}')
    local p50_time=$(grep "50%" "$output_file" | awk '{print $2}')
    local p95_time=$(grep "95%" "$output_file" | awk '{print $2}')
    local p99_time=$(grep "99%" "$output_file" | awk '{print $2}')
    local failed=$(grep "Failed requests" "$output_file" | awk '{print $3}')
    local completed=$(grep "Complete requests" "$output_file" | awk '{print $3}')
    
    # Default values if parsing fails
    rps=${rps:-0}
    avg_time=${avg_time:-0}
    p50_time=${p50_time:-0}
    p95_time=${p95_time:-0}
    p99_time=${p99_time:-0}
    failed=${failed:-0}
    completed=${completed:-0}
    
    echo "$framework,$endpoint,$method,$tps,$rps,$avg_time,$p50_time,$p95_time,$p99_time,$failed,$completed" >> benchmark_results.csv
    
    if [[ "$rps" != "0" ]] && [[ -n "$rps" ]] && (( $(echo "$rps > 0" | bc -l) )); then
        echo -e "${GREEN}${rps} RPS (${completed} completed, ${failed} failed)${NC}"
    else
        echo -e "${RED}FAILED (${completed} completed, ${failed} failed)${NC}"
        # Show first few lines of ab output for debugging
        echo -e "${YELLOW}  Debug info:${NC}"
        head -10 "$output_file" | while read line; do
            echo "    $line"
        done
    fi
}

# Function to get system stats
get_system_stats() {
    local url=$1
    local framework=$2
    
    local stats=$(curl -s --connect-timeout 2 --max-time 5 "$url/stats" 2>/dev/null)
    if [[ $? -eq 0 ]]; then
        echo "$stats" > "/tmp/${framework}_stats.json"
    fi
}

# Main execution
main() {
    # Check prerequisites
    echo "Checking prerequisites..."
    
    if ! command -v ab &> /dev/null; then
        echo -e "${RED}Apache Bench (ab) is not installed.${NC}"
        echo "Install with: brew install httpd (macOS) or apt-get install apache2-utils (Ubuntu)"
        exit 1
    fi
    
    if ! command -v bc &> /dev/null; then
        echo -e "${RED}bc calculator is not installed.${NC}"
        echo "Install with: brew install bc (macOS) or apt-get install bc (Ubuntu)"
        exit 1
    fi
    
    # Check services
    echo -e "\n${YELLOW}Checking services...${NC}"
    
    local spring_ok=0
    local bun_ok=0
    
    if check_service $SPRING_URL "Spring Boot"; then
        spring_ok=1
    else
        echo -e "${RED}Spring Boot service not available${NC}"
    fi
    
    if check_service $BUN_URL "Bun+Hono"; then
        bun_ok=1
    else
        echo -e "${RED}Bun+Hono service not available${NC}"
    fi
    
    if [[ $spring_ok -eq 0 ]] && [[ $bun_ok -eq 0 ]]; then
        echo -e "${RED}No services are running. Please start at least one service.${NC}"
        exit 1
    fi
    
    # Test individual endpoints before running benchmarks
    echo -e "\n${YELLOW}Testing individual endpoints...${NC}"
    
    for endpoint in "${(@k)ENDPOINTS}"; do
        method=${ENDPOINTS[$endpoint]}
        echo "Testing endpoint: $endpoint ($method)"
        
        if [[ $spring_ok -eq 1 ]]; then
            if ! test_endpoint $SPRING_URL $endpoint $method "Spring Boot"; then
                echo -e "${RED}    Spring Boot $endpoint endpoint failed - will skip in benchmarks${NC}"
            fi
        fi
        
        if [[ $bun_ok -eq 1 ]]; then
            if ! test_endpoint $BUN_URL $endpoint $method "Bun+Hono"; then
                echo -e "${RED}    Bun+Hono $endpoint endpoint failed - will skip in benchmarks${NC}"
            fi
        fi
    done
    
    # Warmup services
    echo -e "\n${YELLOW}Warming up services...${NC}"
    if [[ $spring_ok -eq 1 ]]; then
        warmup_service $SPRING_URL "Spring Boot"
    fi
    if [[ $bun_ok -eq 1 ]]; then
        warmup_service $BUN_URL "Bun+Hono"
    fi
    
    # Initialize results file
    echo "Framework,Endpoint,Method,Target_TPS,Actual_RPS,Avg_Time_ms,P50_Time_ms,P95_Time_ms,P99_Time_ms,Failed_Requests,Completed_Requests" > benchmark_results.csv
    
    echo -e "\n${YELLOW}Starting benchmark tests...${NC}"
    echo "Duration: ${DURATION}s per test"
    echo "TPS Levels: ${TPS_LEVELS[*]}"
    
    # Run benchmarks - zsh syntax for associative arrays
    for tps in "${TPS_LEVELS[@]}"; do
        echo -e "\n${BLUE}Running ${tps}TPS tests:${NC}"
        
        for endpoint in "${(@k)ENDPOINTS}"; do
            method=${ENDPOINTS[$endpoint]}
            
            echo "  Endpoint: $endpoint ($method)"
            
            # Test Spring Boot
            if [[ $spring_ok -eq 1 ]]; then
                run_benchmark $SPRING_URL $endpoint $method $tps "SpringBoot"
                get_system_stats $SPRING_URL "SpringBoot"
                sleep 3  # Longer pause between tests
            fi
            
            # Test Bun+Hono
            if [[ $bun_ok -eq 1 ]]; then
                run_benchmark $BUN_URL $endpoint $method $tps "BunHono"
                get_system_stats $BUN_URL "BunHono"
                sleep 3  # Longer pause between tests
            fi
        done
        
        echo "Completed ${tps}TPS tests"
        echo "Pausing 10 seconds before next TPS level..."
        sleep 10
    done
    
    echo -e "\n${GREEN}Benchmark completed!${NC}"
    echo "Results saved to: benchmark_results.csv"
    echo "Run 'python3 analyze-results.py' to generate detailed analysis"
    
    # Show quick summary
    echo -e "\n${YELLOW}Quick Results Summary:${NC}"
    if [[ -f benchmark_results.csv ]]; then
        echo "Framework,Endpoint,Method,Target_TPS,Actual_RPS,Status"
        tail -n +2 benchmark_results.csv | while IFS=',' read framework endpoint method target_tps actual_rps avg_time p50 p95 p99 failed completed; do
            if [[ "$actual_rps" == "0" ]]; then
                status="${RED}FAILED${NC}"
            else
                status="${GREEN}OK${NC}"
            fi
            echo -e "$framework,$endpoint,$method,$target_tps,$actual_rps,$status"
        done
    fi
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up temporary files...${NC}"
    rm -f /tmp/*tps.txt /tmp/post_data.json /tmp/*_stats.json /tmp/health_check.txt /tmp/endpoint_test.txt /tmp/test_post_data.json
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"
