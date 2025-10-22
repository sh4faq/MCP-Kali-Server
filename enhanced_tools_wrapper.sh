#!/bin/bash
# Enhanced Tools Wrapper for MCP-Kali-Server
# Provides easy access to all reconnaissance tools

export PATH=$HOME/go/bin:$PATH
export GOPATH=$HOME/go

echo "==================================="
echo "MCP-Kali-Server Enhanced Tools"
echo "==================================="
echo ""

show_help() {
    echo "Available tools:"
    echo ""
    echo "  1. subzy          - Subdomain takeover detection"
    echo "  2. 403bypasser    - Bypass 403 Forbidden responses"
    echo "  3. nuclei         - Vulnerability scanner"
    echo "  4. httpx          - HTTP toolkit (Project Discovery)"
    echo "  5. assetfinder    - Subdomain discovery"
    echo "  6. waybackurls    - Historical URL discovery via Wayback Machine"
    echo "  7. shodan         - Internet-connected device search"
    echo ""
    echo "Usage examples:"
    echo "  ./enhanced_tools_wrapper.sh subzy -t example.com"
    echo "  ./enhanced_tools_wrapper.sh httpx -l domains.txt -status-code"
    echo "  ./enhanced_tools_wrapper.sh nuclei -u https://example.com -severity critical"
    echo "  ./enhanced_tools_wrapper.sh assetfinder --subs-only example.com"
    echo "  ./enhanced_tools_wrapper.sh waybackurls example.com"
    echo ""
}

if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

TOOL=$1
shift

case "$TOOL" in
    subzy)
        $HOME/go/bin/subzy "$@"
        ;;
    403bypasser|bypass403)
        python3 /usr/local/bin/403bypasser "$@"
        ;;
    nuclei)
        nuclei "$@"
        ;;
    httpx)
        $HOME/go/bin/httpx "$@"
        ;;
    assetfinder)
        $HOME/go/bin/assetfinder "$@"
        ;;
    waybackurls)
        $HOME/go/bin/waybackurls "$@"
        ;;
    shodan)
        shodan "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown tool: $TOOL"
        echo ""
        show_help
        exit 1
        ;;
esac
