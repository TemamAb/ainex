#!/bin/bash

# AINEON Enterprise - Phase 4 Deployment Script
# Chief Architect Approved - Enterprise Grade Deployment

set -e  # Exit on error

echo "================================================"
echo "AINEON ENTERPRISE - PHASE 4 DEPLOYMENT"
echo "Enterprise Scaling & High Availability"
echo "================================================"
echo "í»¡ï¸  CHIEF ARCHITECT AUTHORIZATION: ENTERPRISE DEPLOYMENT"
echo "í¾¯ TARGET: 99.99% Uptime | 10,000 RPS | Bank-Grade Security"
echo "â±ï¸  DEPLOYMENT TIMELINE: 8-12 Weeks"
echo "================================================"

# Configuration
ENVIRONMENT=${1:-"production"}
REGION=${2:-"us-east-1"}
CLUSTER_NAME="aineon-enterprise-${ENVIRONMENT}"
VERSION="1.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check kubectl if deploying to Kubernetes
    if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "staging" ]; then
        if ! command -v kubectl &> /dev/null; then
            log_error "kubectl is not installed"
            exit 1
        fi
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker image
build_docker_image() {
    log_info "Building Docker image..."
    
    docker build -t aineon/enterprise-dashboard:$VERSION \
                 -t aineon/enterprise-dashboard:latest \
                 -f infrastructure/docker/Dockerfile .
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Run security scan
run_security_scan() {
    log_info "Running security scan..."
    
    # Check for known vulnerabilities
    if command -v trivy &> /dev/null; then
        trivy image aineon/enterprise-dashboard:$VERSION
    else
        log_warning "Trivy not installed, skipping security scan"
    fi
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying to Kubernetes cluster: $CLUSTER_NAME"
    
    # Apply namespace
    kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: $ENVIRONMENT
