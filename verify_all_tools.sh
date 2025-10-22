#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  MCP-Kali-Server Tools Verification"
echo "========================================"
echo ""

# Set PATH
export PATH=$HOME/go/bin:$PATH

PASS=0
FAIL=0
WARN=0

# Function to test tool
test_tool() {
    local name=$1
    local command=$2
    local expected=$3
    
    echo -n "Testing $name... "
    
    if output=$($command 2>&1); then
        if echo "$output" | grep -q "$expected"; then
            echo -e "${GREEN}✓ PASS${NC}"
            ((PASS++))
            return 0
        else
            echo -e "${YELLOW}⚠ WARNING${NC} - Tool runs but unexpected output"
            ((WARN++))
            return 1
        fi
    else
        # Check exit code
        if echo "$output" | grep -q "$expected"; then
            echo -e "${GREEN}✓ PASS${NC}"
            ((PASS++))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC}"
            ((FAIL++))
            return 1
        fi
    fi
}

echo "=== Version Checks ==="
echo ""

# Test 1: Subzy
test_tool "Subzy" "$HOME/go/bin/subzy version" "v1.2.0"

# Test 2: 403bypasser
if [ -f "/usr/local/bin/403bypasser" ]; then
    echo -e "Testing 403bypasser... ${GREEN}✓ PASS${NC} (file exists)"
    ((PASS++))
else
    echo -e "Testing 403bypasser... ${RED}✗ FAIL${NC} (file not found)"
    ((FAIL++))
fi

# Test 3: Nuclei
test_tool "Nuclei" "nuclei -version" "v3.4"

# Test 4: HTTPx
test_tool "HTTPx" "$HOME/go/bin/httpx -version" "v1.7"

# Test 5: Assetfinder
if command -v $HOME/go/bin/assetfinder &> /dev/null; then
    echo -e "Testing Assetfinder... ${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "Testing Assetfinder... ${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 6: Waybackurls
if command -v $HOME/go/bin/waybackurls &> /dev/null; then
    echo -e "Testing Waybackurls... ${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "Testing Waybackurls... ${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 7: Shodan
test_tool "Shodan" "shodan version" "1.3"

echo ""
echo "=== Functional Tests ==="
echo ""

# Functional test 1: HTTPx
echo -n "HTTPx functional test... "
if echo "example.com" | timeout 15 $HOME/go/bin/httpx -silent 2>&1 | grep -q "example.com"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Functional test 2: Assetfinder
echo -n "Assetfinder functional test... "
if timeout 15 $HOME/go/bin/assetfinder --subs-only example.com 2>&1 | grep -q "example.com"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Functional test 3: Subzy
echo -n "Subzy functional test... "
if timeout 15 $HOME/go/bin/subzy -t test.example.com 2>&1 | grep -q "Loaded"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

echo ""
echo "=== Configuration Checks ==="
echo ""

# Check PATH
echo -n "Go binary path in PATH... "
if echo $PATH | grep -q "go/bin"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Check .bashrc
echo -n ".bashrc configuration... "
if grep -q "go/bin" ~/.bashrc; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

echo ""
echo "========================================"
echo "        Verification Summary"
echo "========================================"
echo -e "${GREEN}Passed:${NC}  $PASS"
echo -e "${YELLOW}Warnings:${NC} $WARN"
echo -e "${RED}Failed:${NC}  $FAIL"
echo ""

TOTAL=$((PASS + WARN + FAIL))
SUCCESS_RATE=$((PASS * 100 / TOTAL))

echo "Success Rate: $SUCCESS_RATE%"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}All critical tests passed! ✓${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Initialize Shodan: shodan init <YOUR_API_KEY>"
    echo "2. Update Nuclei templates: nuclei -update-templates"
    echo "3. Review documentation: cat ENHANCED_TOOLS_AUDIT_REPORT.md"
    exit 0
else
    echo -e "${RED}Some tests failed. Review output above.${NC}"
    exit 1
fi
