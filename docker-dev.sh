#!/bin/bash

# Docker Development Script for Solar Panel API
# Usage: ./docker-dev.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="solar-panel-api"
CONTAINER_NAME="solar-panel-api"
PROD_IMAGE_NAME="solar-panel-api-prod"

# Functions
print_help() {
    echo "🐳 Docker Development Script for Solar Panel API"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build      Build development Docker image"
    echo "  build-prod Build production Docker image"
    echo "  run        Start development container"
    echo "  stop       Stop and remove container"
    echo "  logs       Show container logs"
    echo "  shell      Open shell in running container"
    echo "  clean      Remove all Docker images and containers"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 run"
    echo "  $0 logs -f"
}

build_dev() {
    echo -e "${BLUE}🔨 Building development Docker image...${NC}"
    docker build -t ${IMAGE_NAME}:latest .
    echo -e "${GREEN}✅ Development image built successfully${NC}"
}

build_prod() {
    echo -e "${BLUE}🔨 Building production Docker image...${NC}"
    docker build -f Dockerfile.prod -t ${PROD_IMAGE_NAME}:latest .
    echo -e "${GREEN}✅ Production image built successfully${NC}"
}

run_dev() {
    echo -e "${BLUE}🚀 Starting development container...${NC}"

    # Check if container is already running
    if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
        echo -e "${YELLOW}⚠️  Container is already running. Stopping it first...${NC}"
        docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
        docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true
    fi

    # Run container
    docker run -d \
        --name ${CONTAINER_NAME} \
        -p 8000:8000 \
        --env-file .env \
        -v $(pwd):/app \
        ${IMAGE_NAME}:latest

    echo -e "${GREEN}✅ Container started successfully${NC}"
    echo -e "${BLUE}🌐 API available at: http://localhost:8000${NC}"
    echo -e "${BLUE}📚 API Docs at: http://localhost:8000/docs${NC}"
}

stop_container() {
    echo -e "${BLUE}🛑 Stopping container...${NC}"
    docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || echo -e "${YELLOW}⚠️  Container not running${NC}"
    docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || echo -e "${YELLOW}⚠️  Container not found${NC}"
    echo -e "${GREEN}✅ Container stopped and removed${NC}"
}

show_logs() {
    if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
        docker logs "$@" ${CONTAINER_NAME}
    else
        echo -e "${RED}❌ Container is not running${NC}"
        echo -e "${YELLOW}💡 Start the container first with: $0 run${NC}"
        exit 1
    fi
}

open_shell() {
    if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
        echo -e "${BLUE}🐚 Opening shell in container...${NC}"
        docker exec -it ${CONTAINER_NAME} /bin/bash
    else
        echo -e "${RED}❌ Container is not running${NC}"
        echo -e "${YELLOW}💡 Start the container first with: $0 run${NC}"
        exit 1
    fi
}

clean_all() {
    echo -e "${YELLOW}🧹 Cleaning up Docker images and containers...${NC}"

    # Stop and remove containers
    docker stop $(docker ps -aq -f name=${CONTAINER_NAME}) >/dev/null 2>&1 || true
    docker rm $(docker ps -aq -f name=${CONTAINER_NAME}) >/dev/null 2>&1 || true

    # Remove images
    docker rmi ${IMAGE_NAME}:latest >/dev/null 2>&1 || true
    docker rmi ${PROD_IMAGE_NAME}:latest >/dev/null 2>&1 || true

    # Remove dangling images
    docker image prune -f >/dev/null 2>&1 || true

    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Main script logic
case "${1:-help}" in
    build)
        build_dev
        ;;
    build-prod)
        build_prod
        ;;
    run)
        run_dev
        ;;
    stop)
        stop_container
        ;;
    logs)
        shift
        show_logs "$@"
        ;;
    shell)
        open_shell
        ;;
    clean)
        clean_all
        ;;
    help|--help|-h)
        print_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        print_help
        exit 1
        ;;
esac