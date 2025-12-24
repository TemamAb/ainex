#!/bin/bash
# AINEON Production Deployment Script
# Deploys dashboards to ETH Mainnet with real-time profit monitoring

set -e

echo "🚀 AINEON Production Deployment - ETH Mainnet"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="aineon-production"
DOCKER_REGISTRY="aineon"
TAG=$(date +%Y%m%d_%H%M%S)

# Environment variables check
check_env_vars() {
    echo -e "${BLUE}Checking environment variables...${NC}"

    required_vars=(
        "ETHERSCAN_API_KEY"
        "INFURA_PROJECT_ID"
        "ETH_MAINNET_RPC_URL"
    )

    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Missing required environment variables:${NC}"
        printf '  - %s\n' "${missing_vars[@]}"
        echo -e "${YELLOW}Please set these in your .env.production file${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ All required environment variables are set${NC}"
}

# Docker build and push
build_and_push() {
    echo -e "${BLUE}Building Docker images...${NC}"

    # Build API image
    docker build -f Dockerfile.production -t ${DOCKER_REGISTRY}/aineon-api:${TAG} .
    docker tag ${DOCKER_REGISTRY}/aineon-api:${TAG} ${DOCKER_REGISTRY}/aineon-api:latest

    # Build dashboard images
    docker build -f Dockerfile.production -t ${DOCKER_REGISTRY}/aineon-profit-dashboard:${TAG} .
    docker tag ${DOCKER_REGISTRY}/aineon-profit-dashboard:${TAG} ${DOCKER_REGISTRY}/aineon-profit-dashboard:latest

    docker build -f Dockerfile.production -t ${DOCKER_REGISTRY}/aineon-monitoring-dashboard:${TAG} .
    docker tag ${DOCKER_REGISTRY}/aineon-monitoring-dashboard:${TAG} ${DOCKER_REGISTRY}/aineon-monitoring-dashboard:latest

    echo -e "${GREEN}✅ Docker images built successfully${NC}"

    # Push to registry (uncomment when you have a registry)
    # echo -e "${BLUE}Pushing to Docker registry...${NC}"
    # docker push ${DOCKER_REGISTRY}/aineon-api:${TAG}
    # docker push ${DOCKER_REGISTRY}/aineon-profit-dashboard:${TAG}
    # docker push ${DOCKER_REGISTRY}/aineon-monitoring-dashboard:${TAG}
    # echo -e "${GREEN}✅ Images pushed to registry${NC}"
}

# Deploy to Render
deploy_render() {
    echo -e "${BLUE}Deploying to Render...${NC}"

    # Check if Render CLI is installed
    if ! command -v render &> /dev/null; then
        echo -e "${YELLOW}⚠️  Render CLI not found. Installing...${NC}"
        npm install -g @render/cli
    fi

    # Deploy API
    echo -e "${BLUE}Deploying API service...${NC}"
    render services create \
        --name aineon-api-prod \
        --type web \
        --repo https://github.com/yourusername/aineon-enterprise \
        --branch main \
        --dockerfile Dockerfile.production \
        --env-file .env.production \
        --port 8000 \
        --health-check-path /api/profit

    # Deploy Profit Dashboard
    echo -e "${BLUE}Deploying Profit Dashboard...${NC}"
    render services create \
        --name aineon-profit-dashboard-prod \
        --type web \
        --repo https://github.com/yourusername/aineon-enterprise \
        --branch main \
        --dockerfile Dockerfile.production \
        --env-file .env.production \
        --port 8501 \
        --command "streamlit run production_profit_dashboard.py --server.port 8501 --server.address 0.0.0.0"

    # Deploy Monitoring Dashboard
    echo -e "${BLUE}Deploying Monitoring Dashboard...${NC}"
    render services create \
        --name aineon-monitoring-dashboard-prod \
        --type web \
        --repo https://github.com/yourusername/aineon-enterprise \
        --branch main \
        --dockerfile Dockerfile.production \
        --env-file .env.production \
        --port 8502 \
        --command "streamlit run dashboard/monitoring_dashboard.py --server.port 8502 --server.address 0.0.0.0"

    echo -e "${GREEN}✅ Render deployment initiated${NC}"
}

# Deploy to Vercel
deploy_vercel() {
    echo -e "${BLUE}Deploying to Vercel...${NC}"

    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        echo -e "${YELLOW}⚠️  Vercel CLI not found. Installing...${NC}"
        npm install -g vercel
    fi

    # Login to Vercel
    vercel login

    # Deploy dashboards
    echo -e "${BLUE}Deploying dashboards...${NC}"

    # Profit Dashboard
    cd dashboard
    vercel --prod --name aineon-profit-dashboard
    cd ..

    # Monitoring Dashboard
    vercel --prod --name aineon-monitoring-dashboard

    echo -e "${GREEN}✅ Vercel deployment completed${NC}"
}

# Deploy to AWS
deploy_aws() {
    echo -e "${BLUE}Deploying to AWS...${NC}"

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
        exit 1
    fi

    # Create ECS cluster
    aws ecs create-cluster --cluster-name aineon-production

    # Create task definitions
    aws ecs register-task-definition --cli-input-json file://infrastructure/aws/task-definition.json

    # Create services
    aws ecs create-service \
        --cluster aineon-production \
        --service-name aineon-api-service \
        --task-definition aineon-api \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration file://infrastructure/aws/network-config.json

    echo -e "${GREEN}✅ AWS deployment initiated${NC}"
}

# Health check
health_check() {
    echo -e "${BLUE}Running health checks...${NC}"

    # Wait for services to be ready
    sleep 30

    # Check API health
    if curl -f http://localhost:8000/api/profit > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is healthy${NC}"
    else
        echo -e "${RED}❌ API health check failed${NC}"
    fi

    # Check dashboards
    if curl -f http://localhost:8501 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Profit Dashboard is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  Profit Dashboard not yet ready${NC}"
    fi

    if curl -f http://localhost:8502 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Monitoring Dashboard is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  Monitoring Dashboard not yet ready${NC}"
    fi
}

# Main deployment flow
main() {
    echo -e "${BLUE}Starting AINEON production deployment...${NC}"

    # Load environment variables
    if [[ -f .env.production ]]; then
        export $(grep -v '^#' .env.production | xargs)
    fi

    check_env_vars

    case "${1:-render}" in
        "render")
            echo -e "${BLUE}Deploying to Render...${NC}"
            build_and_push
            deploy_render
            ;;
        "vercel")
            echo -e "${BLUE}Deploying to Vercel...${NC}"
            deploy_vercel
            ;;
        "aws")
            echo -e "${BLUE}Deploying to AWS...${NC}"
            build_and_push
            deploy_aws
            ;;
        "local")
            echo -e "${BLUE}Running locally with Docker Compose...${NC}"
            docker-compose -f docker-compose.production.yml up -d
            health_check
            ;;
        *)
            echo -e "${RED}Usage: $0 [render|vercel|aws|local]${NC}"
            exit 1
            ;;
    esac

    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${BLUE}Your AINEON dashboards are now live on ETH Mainnet${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Monitor the dashboards for real-time profit data"
    echo "2. Set up alerts for profit thresholds"
    echo "3. Configure automated withdrawals"
    echo "4. Monitor gas prices and network conditions"
}

# Run main function with all arguments
main "$@"