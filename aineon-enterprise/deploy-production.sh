#!/bin/bash

#===============================================================================
# AINEON Flash Loan Engine - Production Deployment Script
# Enterprise Tier 0.001% | Profit Generation Mode
#===============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
CONTAINER_NAME="aineon-engine-prod"
IMAGE_NAME="aineon-flashloan:latest"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env"
LOG_DIR="./logs/deployment"

#===============================================================================
# Helper Functions
#===============================================================================

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}   $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}→${NC} $1"
}

log_step() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_DIR}/deployment.log"
}

#===============================================================================
# Pre-Flight Checks
#===============================================================================

check_prerequisites() {
    print_header "Pre-Flight Checks"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not installed"
        exit 1
    fi
    print_success "Docker installed: $(docker --version)"
    log_step "Docker available"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose not installed"
        exit 1
    fi
    print_success "Docker Compose installed: $(docker-compose --version)"
    log_step "Docker Compose available"
    
    # Check Python (for config validation)
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not installed"
        exit 1
    fi
    print_success "Python 3 installed: $(python3 --version)"
    log_step "Python 3 available"
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        print_error "curl not installed"
        exit 1
    fi
    print_success "curl installed"
    log_step "curl available"
    
    echo ""
}

check_environment() {
    print_header "Environment Configuration"
    
    # Check for .env file
    if [ ! -f "$ENV_FILE" ]; then
        print_error ".env file not found"
        print_info "Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example "$ENV_FILE"
            print_warning "EDIT .env WITH YOUR CREDENTIALS BEFORE DEPLOYING"
            cat "$ENV_FILE"
            exit 1
        else
            print_error ".env.example not found"
            exit 1
        fi
    fi
    
    print_success ".env file exists"
    
    # Source .env
    set -a
    source "$ENV_FILE"
    set +a
    
    # Validate required environment variables
    local required_vars=("ETH_RPC_URL" "WALLET_ADDRESS")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        else
            print_success "$var configured"
            log_step "$var configured"
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
    
    # Validate RPC connection
    print_info "Testing RPC connection..."
    python3 << PYEOF
import asyncio
from web3 import Web3
import sys
import os

eth_rpc = os.getenv('ETH_RPC_URL')
wallet = os.getenv('WALLET_ADDRESS')

try:
    w3 = Web3(Web3.HTTPProvider(eth_rpc))
    if w3.is_connected():
        print(f"✓ RPC connected (Chain ID: {w3.eth.chain_id})")
        print(f"✓ Wallet: {wallet[:10]}...{wallet[-8:]}")
        sys.exit(0)
    else:
        print("✗ RPC connection failed")
        sys.exit(1)
except Exception as e:
    print(f"✗ RPC error: {e}")
    sys.exit(1)
PYEOF
    
    if [ $? -ne 0 ]; then
        print_error "RPC validation failed"
        exit 1
    fi
    
    print_success "RPC connection validated"
    log_step "RPC connection validated"
    
    echo ""
}

#===============================================================================
# Docker Build
#===============================================================================

build_image() {
    print_header "Building Docker Image"
    
    print_info "Building: $IMAGE_NAME"
    log_step "Starting Docker build"
    
    if docker build -t "$IMAGE_NAME" \
        -f Dockerfile.production \
        --progress=plain \
        . ; then
        print_success "Docker image built successfully"
        log_step "Docker image built: $IMAGE_NAME"
    else
        print_error "Docker build failed"
        log_step "Docker build FAILED"
        exit 1
    fi
    
    echo ""
}

#===============================================================================
# Docker Deployment
#===============================================================================

deploy_containers() {
    print_header "Deploying Containers"
    
    # Stop existing containers
    print_info "Checking for existing containers..."
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_warning "Found existing container: $CONTAINER_NAME"
        print_info "Stopping and removing..."
        docker compose -f "$COMPOSE_FILE" down
        sleep 2
    fi
    
    # Start containers
    print_info "Starting Docker Compose services..."
    log_step "Starting Docker Compose"
    
    if docker compose -f "$COMPOSE_FILE" up -d ; then
        print_success "Docker Compose started"
        log_step "Docker Compose started successfully"
    else
        print_error "Docker Compose failed to start"
        log_step "Docker Compose FAILED"
        exit 1
    fi
    
    echo ""
}

#===============================================================================
# Health Checks
#===============================================================================

wait_for_health() {
    print_header "Waiting for System Health"
    
    local max_attempts=30
    local attempt=0
    local api_port=8081
    
    print_info "Waiting for API to respond (max 90 seconds)..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://localhost:${api_port}/health" > /dev/null 2>&1; then
            print_success "API Health Check: PASSED"
            log_step "API health check passed"
            
            # Get additional status
            print_info "Fetching system status..."
            local status=$(curl -s "http://localhost:${api_port}/status")
            echo "$status" | python3 -m json.tool 2>/dev/null || echo "$status"
            
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -ne "\r  Attempt $attempt/$max_attempts..."
        sleep 3
    done
    
    print_error "API Health Check: FAILED"
    print_info "Checking container logs..."
    docker logs "$CONTAINER_NAME" | tail -20
    
    log_step "API health check FAILED"
    return 1
}

#===============================================================================
# System Validation
#===============================================================================

validate_system() {
    print_header "System Validation"
    
    local api_port=8081
    
    # Check health endpoint
    print_info "Checking health endpoint..."
    if ! curl -s -f "http://localhost:${api_port}/health" > /dev/null; then
        print_error "Health endpoint unreachable"
        return 1
    fi
    print_success "Health endpoint: OK"
    log_step "Health endpoint OK"
    
    # Check status endpoint
    print_info "Checking status endpoint..."
    local status=$(curl -s "http://localhost:${api_port}/status")
    if echo "$status" | grep -q "ONLINE"; then
        print_success "Status endpoint: ONLINE"
        log_step "Status endpoint OK"
    else
        print_error "Status endpoint: OFFLINE"
        return 1
    fi
    
    # Check profit endpoint
    print_info "Checking profit endpoint..."
    local profit=$(curl -s "http://localhost:${api_port}/profit")
    if echo "$profit" | grep -q "accumulated_eth"; then
        print_success "Profit endpoint: OK"
        log_step "Profit endpoint OK"
    else
        print_error "Profit endpoint: FAILED"
        return 1
    fi
    
    # Check container status
    print_info "Checking container status..."
    if docker ps --format '{{.Names}}' | grep -q "^aineon"; then
        print_success "Container: RUNNING"
        log_step "Container running"
    else
        print_error "Container: NOT RUNNING"
        return 1
    fi
    
    echo ""
    return 0
}

#===============================================================================
# Information Display
#===============================================================================

show_deployment_info() {
    print_header "Deployment Summary"
    
    echo -e "${GREEN}✓ AINEON Flash Loan Engine Deployed Successfully${NC}\n"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "SYSTEM INFORMATION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    source "$ENV_FILE" 2>/dev/null
    
    echo "Container Name:     $CONTAINER_NAME"
    echo "Image:              $IMAGE_NAME"
    echo "Mode:               PRODUCTION (NO MOCK/SIM)"
    echo "Tier:               ENTERPRISE 0.001%"
    echo "Environment:        $(docker exec $CONTAINER_NAME printenv ENVIRONMENT 2>/dev/null || echo 'PRODUCTION')"
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "ENDPOINTS (LOCALHOST)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "API Server:         http://localhost:8081"
    echo "  ├─ Health:        http://localhost:8081/health"
    echo "  ├─ Status:        http://localhost:8081/status"
    echo "  ├─ Profit:        http://localhost:8081/profit"
    echo "  ├─ Opportunities: http://localhost:8081/opportunities"
    echo "  ├─ Audit:         http://localhost:8081/audit"
    echo "  └─ Report:        http://localhost:8081/audit/report"
    echo ""
    echo "Monitoring:         http://localhost:8082"
    echo "Dashboard:          http://localhost:8089"
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "PROFIT GENERATION CONFIGURATION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Mode:               $(docker exec $CONTAINER_NAME printenv PROFIT_MODE 2>/dev/null || echo 'ENTERPRISE_TIER_0.001%')"
    echo "Auto Transfer:      $(docker exec $CONTAINER_NAME printenv AUTO_TRANSFER_ENABLED 2>/dev/null || echo 'true')"
    echo "Profit Threshold:   $(docker exec $CONTAINER_NAME printenv PROFIT_THRESHOLD_ETH 2>/dev/null || echo '5.0') ETH"
    echo "Min Profit/Trade:   $(docker exec $CONTAINER_NAME printenv MIN_PROFIT_PER_TRADE 2>/dev/null || echo '0.5') ETH"
    echo "Max Slippage:       $(docker exec $CONTAINER_NAME printenv MAX_SLIPPAGE_PCT 2>/dev/null || echo '0.001')%"
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "USEFUL COMMANDS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "View logs:          docker logs -f $CONTAINER_NAME"
    echo "Check status:       curl http://localhost:8081/status"
    echo "View profit:        curl http://localhost:8081/profit"
    echo "Stop container:     docker compose -f $COMPOSE_FILE down"
    echo "Restart container:  docker compose -f $COMPOSE_FILE restart"
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "NEXT STEPS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "1. Monitor system:  curl http://localhost:8081/status"
    echo "2. View dashboard:  open http://localhost:8089"
    echo "3. Check profit:    curl http://localhost:8081/profit"
    echo "4. View logs:       docker logs -f $CONTAINER_NAME"
    echo ""
    
    log_step "Deployment completed successfully"
}

#===============================================================================
# Main Execution
#===============================================================================

main() {
    # Create log directory
    mkdir -p "$LOG_DIR"
    log_step "=== AINEON Production Deployment Started ==="
    
    # Run checks and deployment
    check_prerequisites
    check_environment
    build_image
    deploy_containers
    
    # Wait for health
    if wait_for_health; then
        if validate_system; then
            show_deployment_info
            exit 0
        else
            print_error "System validation failed"
            log_step "System validation FAILED"
            exit 1
        fi
    else
        print_error "System failed to become healthy"
        log_step "System health check FAILED"
        exit 1
    fi
}

# Run main function
main "$@"
