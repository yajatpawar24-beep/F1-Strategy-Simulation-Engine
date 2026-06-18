#!/bin/bash

# F1 Strategy Engine - Docker Deployment Script
# Usage: ./deploy.sh [build|start|stop|restart|logs|health|clean]

set -e

PROJECT_NAME="f1-strategy-engine"
IMAGE_NAME="f1-strategy-engine"
CONTAINER_NAME="f1-strategy-engine"
PORT="8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "${BLUE}🏎️  F1 Strategy Engine - Docker Deployment${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

function check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is installed${NC}"
}

function check_models() {
    if [ ! -f "data/registry/m1_pipeline.pkl" ]; then
        echo -e "${RED}❌ Model files not found in data/registry/${NC}"
        echo -e "${YELLOW}   Make sure all 5 .pkl files exist:${NC}"
        echo "   - m1_pipeline.pkl"
        echo "   - m2_pipeline.pkl"
        echo "   - m3_pipeline.pkl"
        echo "   - m4_pipeline.pkl"
        echo "   - m5_pipeline.pkl"
        exit 1
    fi
    echo -e "${GREEN}✓ Model files found${NC}"
}

function build() {
    print_header
    echo -e "${BLUE}Building Docker image...${NC}"
    check_docker
    check_models

    docker build -t $IMAGE_NAME . || {
        echo -e "${RED}❌ Build failed${NC}"
        exit 1
    }

    echo -e "${GREEN}✅ Build successful!${NC}"
    docker images | grep $IMAGE_NAME
}

function start() {
    print_header
    echo -e "${BLUE}Starting container...${NC}"
    check_docker

    # Check if container already exists
    if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        echo -e "${YELLOW}⚠️  Container already exists. Removing...${NC}"
        docker rm -f $CONTAINER_NAME
    fi

    # Run container
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:$PORT \
        -e PYTHONUNBUFFERED=1 \
        --restart unless-stopped \
        $IMAGE_NAME || {
        echo -e "${RED}❌ Failed to start container${NC}"
        exit 1
    }

    echo -e "${GREEN}✅ Container started successfully!${NC}"
    echo ""
    echo -e "${BLUE}Waiting for application to be ready...${NC}"
    sleep 5

    # Check health
    if curl -sf http://localhost:$PORT/health > /dev/null; then
        echo -e "${GREEN}✅ Application is healthy!${NC}"
        echo ""
        echo -e "${GREEN}🎉 F1 Strategy Engine is running!${NC}"
        echo ""
        echo -e "${YELLOW}Access the application:${NC}"
        echo -e "  Frontend: ${BLUE}http://localhost:$PORT/frontend/index_v3.html${NC}"
        echo -e "  API Docs: ${BLUE}http://localhost:$PORT/docs${NC}"
        echo -e "  Health:   ${BLUE}http://localhost:$PORT/health${NC}"
    else
        echo -e "${YELLOW}⚠️  Application started but health check failed${NC}"
        echo -e "${YELLOW}   Check logs with: ./deploy.sh logs${NC}"
    fi
}

function stop() {
    print_header
    echo -e "${BLUE}Stopping container...${NC}"

    if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        docker stop $CONTAINER_NAME
        echo -e "${GREEN}✅ Container stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Container is not running${NC}"
    fi
}

function restart() {
    print_header
    echo -e "${BLUE}Restarting container...${NC}"
    stop
    sleep 2
    start
}

function logs() {
    print_header
    echo -e "${BLUE}Showing logs (Ctrl+C to exit)...${NC}"
    docker logs -f $CONTAINER_NAME
}

function health() {
    print_header
    echo -e "${BLUE}Checking health...${NC}"

    if [ ! "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        echo -e "${RED}❌ Container is not running${NC}"
        exit 1
    fi

    echo -e "${BLUE}Docker container status:${NC}"
    docker ps -f name=$CONTAINER_NAME
    echo ""

    echo -e "${BLUE}Health check:${NC}"
    if curl -sf http://localhost:$PORT/health | python3 -m json.tool; then
        echo -e "${GREEN}✅ Application is healthy!${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
        exit 1
    fi
}

function clean() {
    print_header
    echo -e "${BLUE}Cleaning up...${NC}"

    # Stop and remove container
    if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        docker rm -f $CONTAINER_NAME
        echo -e "${GREEN}✓ Container removed${NC}"
    fi

    # Remove image
    if [ "$(docker images -q $IMAGE_NAME)" ]; then
        docker rmi -f $IMAGE_NAME
        echo -e "${GREEN}✓ Image removed${NC}"
    fi

    # Remove dangling images
    docker image prune -f

    echo -e "${GREEN}✅ Cleanup complete!${NC}"
}

function compose_up() {
    print_header
    echo -e "${BLUE}Starting with Docker Compose...${NC}"
    check_docker
    check_models

    docker-compose up --build -d

    echo -e "${GREEN}✅ Docker Compose stack started!${NC}"
    echo ""
    echo -e "${YELLOW}Access the application:${NC}"
    echo -e "  Frontend: ${BLUE}http://localhost:$PORT/frontend/index_v3.html${NC}"
    echo -e "  API Docs: ${BLUE}http://localhost:$PORT/docs${NC}"
}

function compose_down() {
    print_header
    echo -e "${BLUE}Stopping Docker Compose stack...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Stack stopped${NC}"
}

function usage() {
    echo -e "${YELLOW}Usage:${NC} ./deploy.sh [command]"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo "  build              Build Docker image"
    echo "  start              Start container"
    echo "  stop               Stop container"
    echo "  restart            Restart container"
    echo "  logs               View container logs"
    echo "  health             Check application health"
    echo "  clean              Remove container and image"
    echo "  compose-up         Start with Docker Compose"
    echo "  compose-down       Stop Docker Compose stack"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  ./deploy.sh build && ./deploy.sh start"
    echo "  ./deploy.sh restart"
    echo "  ./deploy.sh logs"
}

# Main script
case "$1" in
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    health)
        health
        ;;
    clean)
        clean
        ;;
    compose-up)
        compose_up
        ;;
    compose-down)
        compose_down
        ;;
    *)
        usage
        exit 1
        ;;
esac
