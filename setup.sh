#!/bin/bash

# 🚀 Portfolio Backend - Universal Setup Script
# Działa na Ubuntu/Debian, EC2, i lokalnych maszynach

set -e  # Exit on error

echo "🚀 Portfolio Backend - Universal Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_warning "Ten skrypt nie powinien być uruchamiany jako root"
   print_info "Uruchom jako normalny użytkownik z sudo"
   exit 1
fi

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [[ -f /etc/debian_version ]]; then
        OS="debian"
        print_info "Wykryto: Debian/Ubuntu"
    elif [[ -f /etc/redhat-release ]]; then
        OS="redhat"
        print_info "Wykryto: RedHat/CentOS/Amazon Linux"
    else
        OS="linux"
        print_info "Wykryto: Linux (nieznana dystrybucja)"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    print_info "Wykryto: macOS"
else
    OS="unknown"
    print_warning "Nieznany system operacyjny: $OSTYPE"
fi

# Check if we're on EC2
if curl -s --max-time 3 http://169.254.169.254/latest/meta-data/instance-id >/dev/null 2>&1; then
    print_info "🌩️  Wykryto instancję AWS EC2"
    IS_EC2=true
else
    IS_EC2=false
fi

# Function to install Docker
install_docker() {
    print_info "🐳 Instalowanie Docker..."
    
    if command -v docker &> /dev/null; then
        print_status "Docker już jest zainstalowany"
        return
    fi
    
    case $OS in
        "debian")
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y ca-certificates curl gnupg lsb-release
            
            # Add Docker's official GPG key
            sudo mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            
            # Set up repository
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
              $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Install Docker Engine
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        "redhat")
            # Amazon Linux/CentOS
            sudo yum update -y
            sudo yum install -y docker
            sudo systemctl start docker
            sudo systemctl enable docker
            ;;
        "macos")
            print_warning "Na macOS zainstaluj Docker Desktop ręcznie z https://www.docker.com/products/docker-desktop"
            exit 1
            ;;
        *)
            print_error "Nieobsługiwany system operacyjny dla automatycznej instalacji Docker"
            exit 1
            ;;
    esac
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    print_status "Docker zainstalowany pomyślnie"
    print_warning "Musisz się wylogować i zalogować ponownie aby docker działał bez sudo"
}

# Function to install Git
install_git() {
    if command -v git &> /dev/null; then
        print_status "Git już jest zainstalowany"
        return
    fi
    
    print_info "📦 Instalowanie Git..."
    case $OS in
        "debian")
            sudo apt-get update
            sudo apt-get install -y git
            ;;
        "redhat")
            sudo yum install -y git
            ;;
        "macos")
            # Git comes with Xcode command line tools
            xcode-select --install
            ;;
    esac
    print_status "Git zainstalowany"
}

# Function to clean database and migrations for fresh start
clean_for_fresh_start() {
    print_info "🧹 Przygotowywanie środowiska do czystego startu..."
    
    # Stop any running containers
    cd backend
    if [[ -f docker-compose.yml ]]; then
        # Detect docker compose command
        if command -v docker-compose &> /dev/null; then
            DOCKER_COMPOSE="docker-compose"
        elif docker compose version &> /dev/null; then
            DOCKER_COMPOSE="docker compose"
        else
            print_warning "Docker compose nie jest dostępny, pomijam czyszczenie kontenerów"
            cd ..
            return
        fi
        
        print_info "🛑 Zatrzymywanie kontenerów..."
        $DOCKER_COMPOSE down -v 2>/dev/null || true
        
        # Remove specific volumes
        docker volume rm backend_postgres_data 2>/dev/null || true
        docker volume rm portfolio-backend_postgres_data 2>/dev/null || true
    fi
    cd ..
    
    # Clean old migration files for fresh start
    if [[ -d backend/alembic/versions ]]; then
        print_info "🗑️  Usuwanie starych migracji..."
        rm -f backend/alembic/versions/*.py
        rm -rf backend/alembic/versions/__pycache__
        print_status "Stare migracje usunięte"
    fi
    
    print_status "Środowisko przygotowane do czystego startu"
}

# Function to create .env file
create_env_file() {
    print_info "📝 Tworzenie pliku .env..."
    
    if [[ -f backend/.env ]]; then
        print_warning "Plik .env już istnieje, tworzę backup..."
        cp backend/.env backend/.env.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Generate random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    
    cat > backend/.env << EOL
# Database Configuration
DATABASE_URL=postgresql://postgres:password@db:5432/portfolio
POSTGRES_DB=portfolio
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Application Configuration
SECRET_KEY=$SECRET_KEY
ENVIRONMENT=development
DEBUG=True

# Admin Configuration (automatyczne tworzenie podczas inicjalizacji)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@kgr33n.com
ADMIN_PASSWORD=admin123
ADMIN_FULL_NAME=KGR33N Administrator

# Frontend Configuration
FRONTEND_URL=http://localhost:4321
PRODUCTION_FRONTEND=https://your-domain.com

# Email Configuration (opcjonalne)
RESEND_API_KEY=your-resend-api-key-here
FROM_EMAIL=noreply@your-domain.com
FROM_NAME=Portfolio
EOL

    print_status "Plik .env utworzony z domyślną konfiguracją"
}

# Function to setup firewall for EC2
setup_ec2_firewall() {
    if [[ "$IS_EC2" == true ]]; then
        print_info "🔥 Konfigurowanie iptables dla EC2..."
        
        # Allow HTTP and HTTPS
        sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
        sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
        sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
        
        # Save iptables rules
        if command -v iptables-save &> /dev/null; then
            sudo iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
        fi
        
        print_status "Porty 80, 443, 8000 otwarte"
        print_warning "Pamiętaj o skonfigurowaniu Security Group w AWS Console"
    fi
}

# Main installation
main() {
    print_info "Rozpoczynanie instalacji..."
    
    # Install prerequisites
    install_git
    install_docker
    
    # Check if we're in the right directory
    if [[ ! -f "backend/docker-compose.yml" ]]; then
        print_error "Nie znaleziono backend/docker-compose.yml"
        print_info "Upewnij się, że jesteś w głównym katalogu repozytorium Portfolio-Backend"
        exit 1
    fi
    
    # Clean for fresh start
    clean_for_fresh_start
    
    # Create .env file
    create_env_file
    
    # Setup firewall for EC2
    setup_ec2_firewall
    
    # Make scripts executable
    chmod +x backend/start-fresh.sh
    chmod +x backend/start-with-migrations.sh
    chmod +x backend/app/create_admin.py
    
    print_status "Setup zakończony pomyślnie!"
    echo
    print_info "🚀 Aby uruchomić aplikację:"
    echo "   cd backend"
    echo "   ./start-fresh.sh"
    echo
    print_info "🌐 Aplikacja będzie dostępna pod:"
    echo "   - Frontend: http://localhost:4321"
    echo "   - Backend API: http://localhost:8000"
    echo "   - API Docs: http://localhost:8000/api/docs"
    echo
    
    if [[ "$IS_EC2" == true ]]; then
        # Get EC2 public IP
        PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "your-ec2-ip")
        print_info "🌩️  Na EC2 aplikacja będzie dostępna pod:"
        echo "   - http://$PUBLIC_IP:8000"
        echo "   - http://$PUBLIC_IP:8000/api/docs"
    fi
    
    if ! groups $USER | grep -q docker; then
        print_warning "🔄 Wyloguj się i zaloguj ponownie aby docker działał bez sudo"
    fi
}

# Run main function
main "$@"
