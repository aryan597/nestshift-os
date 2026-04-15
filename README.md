# NestShift OS

## 🎯 Complete Edge AI Operating System for Home Energy Optimization

**NestShift OS** is a comprehensive, autonomous edge AI operating system designed specifically for intelligent home energy management. Built across 6 development phases, this production-ready system provides real-time energy optimization, predictive modeling, adaptive automation, and comprehensive safety controls - all running entirely on-device without any cloud dependency.

### ✨ Key Features
- **🏠 Autonomous Energy Optimization** - AI agents learn and optimize energy usage patterns
- **🔒 Safety-First Design** - Immutable hardware safety constraints prevent dangerous operations
- **📊 Real-Time Monitoring** - Comprehensive telemetry with drift detection and system health
- **🔐 Enterprise Security** - JWT authentication, TLS-encrypted MQTT, secure API endpoints
- **🧪 Full Test Suite** - 14 integration tests covering all critical safety and functionality
- **🚀 Production Ready** - Complete CI/CD pipeline, OS build scripts, and deployment automation
- **📱 Multi-Platform** - Web dashboard, mobile client, and hardware interfaces
- **⚡ Edge-First Architecture** - All AI processing happens locally, ensuring privacy and speed

## 🏗️ Complete System Architecture

### Core Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │     API         │    │     MQTT        │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Mosquitto)   │
│   WebSocket     │    │   JWT Auth      │    │   TLS 8883      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Energy Agent  │    │ Automation Agent│    │ System Agent   │
│   (LightGBM)    │    │   (Behaviour)   │    │  (Monitoring)   │
│  Forecasting    │    │   Learning      │    │  Drift Detect   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐    ┌─────────────────┐
                    │     InfluxDB    │    │     SQLite      │
                    │   (Telemetry)   │    │   (Config)      │
                    └─────────────────┘    └─────────────────┘
```

### Hardware Integration Layer
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GPIO Service  │    │   Zigbee2MQTT  │    │   Brain Service │
│   (RPi.GPIO)    │    │   (Devices)     │    │  (Orchestrator) │
│   Relays/Sensors│    │   Smart Home    │    │   Coordination │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Mobile & External Interfaces
```
┌─────────────────┐    ┌─────────────────┐
│   Flutter Client│    │   Node-RED      │
│   (Mobile App)  │    │   (Workflows)   │
│   MQTT + REST   │    │   Automation    │
└─────────────────┘    └─────────────────┘
```

## 🚀 How to Run NestShift OS

### Method 1: 🐳 Docker Development (Fastest - RECOMMENDED)
**Perfect for development, testing, and evaluation**

```bash
cd "/home/aryan597/os image/"

# 1. Start the complete development stack
docker-compose -f dev/docker-compose.dev.yml up -d --build

# 2. Check services are running
docker-compose -f dev/docker-compose.dev.yml ps

# 3. Run integration tests
docker-compose -f dev/docker-compose.dev.yml exec nestshift-api pytest /app/tests/ -v

# 4. Access the dashboard
open http://localhost:3000

# 5. API endpoints available at
curl http://localhost:8000/health
curl http://localhost:8000/agents/status
```

**Services started:**
- API (port 8000) - REST API with JWT auth
- MQTT (ports 1883, 9001, 8883) - Message broker with TLS
- InfluxDB (port 8086) - Time series database
- Dashboard (port 3000) - Web interface
- All 6 AI agents (Energy, Automation, System, GPIO, Brain, Zigbee)
- Node-RED (port 1880) - Workflow automation

### Method 2: 🏠 Production OS Image (Full System)
**For Raspberry Pi deployment with custom OS**

```bash
cd "/home/aryan597/os image/"

# 1. Build custom Raspberry Pi OS image
cd os/
git clone https://github.com/RPi-Distro/pi-gen.git
cd pi-gen && git checkout arm64
cp -r ../stage-nestshift stage-nestshift
sudo ./build.sh -c config  # Takes ~45 minutes

# 2. Flash the generated image to SD card
cd deploy/
ls *.img  # Find the generated image
../scripts/flash.sh /dev/sdX  # Replace /dev/sdX

# 3. Boot Raspberry Pi with flashed SD card
# First boot takes 2-3 minutes, system auto-configures

# 4. Access via:
# Dashboard: http://nestshift.local:3000
# SSH: ssh nestshift@nestshift.local
# API: http://nestshift.local:8000
```

### Method 3: 🧪 Manual Service Development
**Run individual services for development/debugging**

```bash
cd "/home/aryan597/os image/"

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies for each service
pip install -r services/api/requirements.txt
pip install -r services/system-agent/requirements.txt
pip install -r services/automation-agent/requirements.txt
pip install -r services/energy-agent/requirements.txt

# Run services individually (in separate terminals)
python3 services/api/main.py              # API on port 8000
python3 services/system-agent/main.py     # System monitoring
python3 services/automation-agent/main.py # Behavior learning
python3 services/energy-agent/main.py     # Energy forecasting
python3 services/gpio/main.py            # Hardware interface
python3 services/brain/main.py           # Orchestration

# Start MQTT broker separately (using Docker)
docker run -d -p 1883:1883 -p 8883:8883 eclipse-mosquitto:2.0

# Start InfluxDB separately
docker run -d -p 8086:8086 influxdb:2.7
```

### Method 4: 🔧 Development Scripts (Testing)
**Use included scripts for testing and setup**

```bash
cd "/home/aryan597/os image/"

# Run first-run setup (creates database, certs, etc.)
./scripts/first-run.sh

# Test shell scripts syntax
bash -n scripts/*.sh && echo "All scripts OK"

# Check Docker configuration
docker-compose -f dev/docker-compose.dev.yml config --quiet

# Run tests manually
pip install -r tests/requirements.txt
pytest tests/ -v
```

## 📊 Complete Service Map

### Core Services
| Service | Port | Responsibilities | Technology | Status |
|---------|------|------------------|------------|---------|
| **API** | 8000 | REST endpoints, JWT auth, safety filtering | FastAPI, SQLite, Pydantic | ✅ Complete |
| **MQTT** | 1883/8883 | Message broker, TLS encryption, device coordination | Mosquitto, certificates | ✅ Complete |
| **Dashboard** | 3000 | Web interface, real-time telemetry, controls | React, WebSocket, Tailwind | ✅ Complete |
| **InfluxDB** | 8086 | Time series storage, sensor data, analytics | InfluxDB 2.x | ✅ Complete |

### AI Agent Services
| Service | Port | Responsibilities | Technology | AI Features |
|---------|------|------------------|------------|-------------|
| **Energy Agent** | MQTT | Demand forecasting, tariff optimization, Octopus API | LightGBM, Pandas, httpx | ✅ LightGBM models, real-time forecasting |
| **Automation Agent** | MQTT | Behavior learning, rule engine, pattern recognition | NumPy, Pandas, scikit-learn | ✅ Behavior patterns, confidence scoring |
| **System Agent** | MQTT | Resource monitoring, drift detection, health checks | psutil, APScheduler | ✅ Drift detection, model freshness |
| **Brain Service** | 8001 | Orchestration, coordination, decision making | FastAPI, custom logic | ✅ Multi-agent coordination |

### Hardware & Integration Services
| Service | Port | Responsibilities | Technology | Hardware |
|---------|------|------------------|------------|-----------|
| **GPIO Service** | MQTT | Relay control, sensor reading, hardware interface | RPi.GPIO, lgpio | ✅ Raspberry Pi GPIO |
| **Zigbee2MQTT** | 8080 | Smart home device integration, Zigbee protocol | zigbee2mqtt, MQTT | ✅ Zigbee devices |
| **Node-RED** | 1880 | Workflow automation, custom integrations | Node-RED | ✅ Visual programming |

### Mobile & External Interfaces
| Component | Platform | Features | Technology |
|-----------|----------|----------|------------|
| **Flutter Client** | Mobile (iOS/Android) | MQTT client, controls, monitoring | Dart, MQTT, REST API | ✅ Complete client library |
| **Systemd Services** | Linux | Auto-start, monitoring, logging | systemd | ✅ Service definitions |

## 🔒 Security Features

### Authentication & Authorization
- **JWT Token System**: Bearer token authentication for sensitive endpoints
- **Password Security**: bcrypt hashing with configurable salt rounds
- **First-Run Setup**: Automatic admin user creation with forced password change
- **Token Expiration**: 24-hour token validity with refresh mechanism

### Transport Security
- **MQTT TLS**: Certificate-based authentication on port 8883
- **Self-Signed CA**: Local certificate authority for development/production
- **Client Certificates**: Agent authentication via client certificates
- **Secure MQTT**: require_certificate and use_identity_as_username enabled

### Safety & Constraints
- **Πsafe Filter**: Immutable hardware safety constraints
- **Temperature Limits**: HVAC capped at 16-26°C regardless of user input
- **Power Limits**: Maximum 3 simultaneous high-power devices (>1000W)
- **Device Limits**: Individual devices capped at 3000W maximum
- **Safety Violations**: Automatic blocking with detailed logging

## 🧪 Testing & Quality Assurance

### Integration Tests (14 total)
```bash
# Run complete test suite
pytest tests/ -v

# Individual test suites
pytest tests/test_safety_filter.py -v    # 6 tests - safety constraints
pytest tests/test_drift_detector.py -v   # 4 tests - model monitoring
pytest tests/test_behaviour_model.py -v  # 4 tests - learning algorithms
```

### Safety Filter Tests
- ✅ HVAC temperature clamping (above/below limits)
- ✅ Maximum device wattage enforcement
- ✅ High-power device simultaneous limits
- ✅ Valid temperature passthrough
- ✅ Normal device operation allowance

### CI/CD Pipeline
- **GitHub Actions**: Automated testing on push/PR
- **Multi-Service Testing**: API, agents, linting, building
- **Docker Validation**: Compose configuration checking
- **Shell Script Testing**: Syntax validation for all scripts
- **Dashboard Building**: Automated React build verification

### Code Quality
- **Flake8**: Python linting with 100-character line limits
- **Import Testing**: All modules load without missing dependencies
- **Syntax Validation**: All shell scripts pass bash -n checks

## 🧪 Testing & Validation

### Complete Test Suite
All tests use actual service code (no mocks) and validate real functionality:

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run complete test suite (14 tests)
pytest tests/ -v --tb=short

# Run specific test suites
pytest tests/test_safety_filter.py -v    # Safety constraints validation
pytest tests/test_drift_detector.py -v   # Model drift detection
pytest tests/test_behaviour_model.py -v  # Behavior learning algorithms

# Run with coverage
pytest tests/ --cov=services/api --cov-report=html
```

### Test Coverage
- **Safety Filter**: 6 tests covering all safety constraints
- **Drift Detection**: 4 tests validating model monitoring
- **Behavior Learning**: 4 tests covering pattern recognition
- **Safety Validation**: All tests must pass for production deployment

### Manual Testing
```bash
# Verify safety filter manually
python3 -c "
import sys
sys.path.insert(0, 'services/api')
from safety_filter import validate_action, SAFETY_RULES
action = {'action': 'set_temperature', 'params': {'temperature': 35}}
result = validate_action(action, {})
print('Safety filter working - clamped to:', result['params']['temperature'])
"

# Check service imports
python3 -c "
import sys
sys.path.insert(0, 'services/api')
from main import app
print('API service imports successfully')
"
```

## 📁 Complete Project Structure

```
nestshift-os/
├── 📊 README.md                    # Comprehensive documentation (this file)
├── 🔧 .env.example                 # Environment variables template
├── 🐳 docker-compose.dev.yml       # Development stack orchestration
├── ⚙️ .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD pipeline
├── 🔐 config/                      # Configuration files
│   ├── gpio/                      # GPIO pin configurations
│   └── nodered/                   # Node-RED flow templates
├── 🌐 dashboard/                   # React web dashboard
│   ├── src/
│   │   ├── main.jsx               # React entry point
│   │   ├── App.jsx                # Main application
│   │   ├── pages/                 # Dashboard pages (Home, Energy, Devices, Settings)
│   │   ├── services/              # API client services
│   │   ├── store/                 # State management (Zustand)
│   │   └── design-system/         # UI components (Glass morphism, tokens)
│   ├── package.json               # Node.js dependencies
│   ├── vite.config.js            # Build configuration
│   ├── tailwind.config.js        # CSS framework config
│   ├── nginx.conf                # Production web server config
│   └── Dockerfile                # Dashboard container
├── 🗄️ database/                   # Data persistence
│   ├── schema.sql                # SQLite database schema
│   ├── migrations/               # Database migration scripts
│   └── README.md
├── 🐳 dev/                        # Development environment
│   ├── docker-compose.dev.yml    # Full development stack with health checks
│   ├── docker-compose.sim.yml    # Simulation environment
│   └── README.md
├── 📱 mobile/                     # Flutter mobile client
│   ├── lib/
│   │   └── nestshift_client/     # Complete Dart client library
│   │       ├── nestshift_client.dart    # Main client
│   │       ├── nestshift_mqtt.dart      # MQTT client
│   │       ├── nestshift_exception.dart # Custom exceptions
│   │       ├── models/                  # Data models
│   │       └── index.dart              # Library exports
│   └── README.md
├── 🏗️ os/                         # OS build pipeline
│   ├── BUILD.md                  # OS build instructions
│   └── stage-nestshift/          # pi-gen custom stage
│       ├── STAGE.md             # Stage configuration
│       └── 01-sys-tweaks/       # System optimizations & packages
│           └── files/           # Configuration files
├── 📜 scripts/                    # Installation & utility scripts
│   ├── install.sh                # Production installation script
│   ├── first-run.sh              # First-run setup & initialization
│   └── flash.sh                  # SD card flashing utility
├── 🔧 services/                   # All microservices (9 total)
│   ├── api/                      # REST API service (FastAPI)
│   │   ├── main.py               # API application with JWT auth
│   │   ├── safety_filter.py      # Πsafe hardware safety constraints
│   │   ├── requirements.txt      # Python dependencies
│   │   └── Dockerfile
│   ├── automation-agent/         # Behavior learning agent
│   │   ├── main.py               # BehaviorModel & RuleEngine
│   │   ├── config.yaml           # Agent configuration
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── brain/                    # Orchestration service
│   │   ├── main.py               # Multi-agent coordination
│   │   ├── training_data/        # Training datasets
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── energy-agent/             # Forecasting agent
│   │   ├── main.py               # LightGBM demand forecasting
│   │   ├── config.yaml
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── gpio/                     # Hardware interface
│   │   ├── main.py               # Raspberry Pi GPIO control
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── influxdb/                 # Time series database config
│   │   ├── influxdb.conf         # InfluxDB configuration
│   │   ├── init.sh               # Database initialization
│   │   └── README.md
│   ├── mqtt/                     # MQTT broker configuration
│   │   ├── mosquitto.conf        # Broker config with TLS
│   │   ├── generate-certs.sh     # Certificate generation script
│   │   └── README.md
│   ├── system-agent/             # Monitoring agent
│   │   ├── main.py               # DriftDetector & ResourceMonitor
│   │   ├── config.yaml
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── zigbee/                   # Smart home integration
│       ├── configuration.yaml    # Zigbee2MQTT config
│       └── README.md
├── 🔧 systemd/                    # System service definitions
├── 🧪 tests/                      # Complete test suite
│   ├── test_safety_filter.py     # Safety constraint tests (6 tests)
│   ├── test_drift_detector.py    # Drift detection tests (4 tests)
│   ├── test_behaviour_model.py   # Behavior learning tests (4 tests)
│   ├── conftest.py               # Test fixtures
│   └── requirements.txt          # Test dependencies
└── 📋 .gitignore                  # Git ignore patterns
```

## 📈 Development Status & Roadmap

### ✅ Completed Features (Parts 1-6)

#### Part 1: Monorepo Scaffold ✅
- Complete project structure with all directories
- Docker Compose development environment
- Service contracts and communication patterns
- Database schemas and migration system

#### Part 2: React Dashboard & API ✅
- Full React dashboard with real-time telemetry
- FastAPI backend with comprehensive endpoints
- WebSocket integration for live updates
- Mobile Flutter client library
- State management and UI components

#### Part 3: AI Agents Intelligence ✅
- **Energy Agent**: LightGBM forecasting with Octopus API integration
- **Automation Agent**: Behavior pattern learning with confidence scoring
- **System Agent**: Resource monitoring with drift detection
- Real data pipelines and time series storage

#### Part 4: OS Image Build ✅
- pi-gen custom stage for Raspberry Pi OS
- Automated installation scripts
- First-run setup and initialization
- SD card flashing utilities

#### Part 5: Security Hardening ✅
- JWT authentication system with password hashing
- TLS-encrypted MQTT with certificate management
- Πsafe safety filter with immutable constraints
- Protected API endpoints with proper authorization

#### Part 6: Integration Tests & CI/CD ✅
- 14 comprehensive integration tests
- GitHub Actions CI/CD pipeline
- Docker health checks and monitoring
- Automated testing and validation

### 🎯 System Capabilities

#### Energy Optimization
- **Real-time Forecasting**: LightGBM models predict energy demand
- **Tariff Optimization**: Dynamic pricing integration (Octopus API)
- **Behavioral Learning**: Pattern recognition for usage optimization
- **Safety Constraints**: Hardware protection (16-26°C, 3kW limits)

#### System Monitoring
- **Resource Tracking**: CPU, RAM, disk, temperature monitoring
- **Model Drift Detection**: Automatic AI model validation
- **Health Checks**: Service availability and performance monitoring
- **Logging**: Comprehensive system and service logs

#### Hardware Integration
- **GPIO Control**: Relay switching and sensor reading
- **Zigbee Support**: Smart home device integration
- **Multi-protocol**: MQTT, REST API, WebSocket support
- **Raspberry Pi Optimized**: Hardware-specific optimizations

## 🔧 API Documentation

### Authentication Endpoints
```bash
POST /auth/token          # JWT token generation
POST /auth/change-password # Password update (protected)
GET  /auth/status         # Authentication status (protected)
```

### Core Endpoints
```bash
GET  /health              # System health check
GET  /devices             # Device inventory
GET  /energy/usage        # Energy consumption data
GET  /energy/tariff/current # Current electricity pricing
GET  /agents/status       # AI agent health status
GET  /system/version      # System version information
```

### Protected Endpoints (Require JWT)
```bash
POST /preferences/comfort-bias    # User comfort settings
POST /agents/{agent}/toggle       # Agent enable/disable
POST /devices/{id}/control        # Device control commands
```

### Safety-Filtered Operations
All device control operations pass through the Πsafe filter:
- Temperature settings clamped to safe ranges
- Power consumption limits enforced
- Simultaneous high-power device restrictions
- Automatic safety violation logging

## 🚨 Troubleshooting

### Docker Issues
```bash
# Clean up failed containers
docker-compose -f dev/docker-compose.dev.yml down -v --remove-orphans

# Rebuild all services
docker-compose -f dev/docker-compose.dev.yml up -d --build

# Check service logs
docker-compose -f dev/docker-compose.dev.yml logs [service-name]

# Validate configuration
docker-compose -f dev/docker-compose.dev.yml config --quiet
```

### Service Connection Issues
```bash
# Check MQTT connectivity
mosquitto_pub -h localhost -t "test" -m "hello"

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/agents/status

# Check InfluxDB
curl http://localhost:8086/ping
```

### Common Errors

**"ContainerConfig" Error**: Clean up Docker volumes and restart
```bash
docker system prune -a --volumes
```

**Port Conflicts**: Change ports in docker-compose.dev.yml if needed

**Certificate Issues**: Regenerate MQTT certificates
```bash
cd services/mqtt && ./generate-certs.sh
```

**Permission Issues**: Ensure scripts are executable
```bash
chmod +x scripts/*.sh
```

### Development Debugging
```bash
# Run services individually for debugging
python3 services/api/main.py              # Debug API
python3 services/system-agent/main.py     # Debug monitoring
python3 services/automation-agent/main.py # Debug learning

# Check MQTT messages
mosquitto_sub -h localhost -t "nestshift/#" -v

# Monitor system logs
journalctl -f -u nestshift-*
```

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/new-feature`)
3. **Develop** with tests (`pytest tests/ -v`)
4. **Commit** with clear messages (`git commit -m "Add: new feature"`)
5. **Push** and create pull request

### Branch Naming Conventions
- `feature/feature-name` - New features and enhancements
- `bugfix/bug-description` - Bug fixes and patches
- `hotfix/critical-fix` - Critical production fixes
- `docs/update-documentation` - Documentation updates

### Pull Request Requirements
- ✅ All tests pass (`pytest tests/ -v`)
- ✅ Code follows style guidelines (flake8 max-line-length=100)
- ✅ Shell scripts pass syntax check (`bash -n scripts/*.sh`)
- ✅ Dashboard builds successfully (`npm run build`)
- ✅ Docker Compose configuration validates
- ✅ Security scan passes (no hardcoded secrets)
- ✅ Documentation updated for new features

### Code Quality Standards
- **Python**: PEP 8 compliant, type hints encouraged
- **JavaScript/React**: ESLint compliant, functional components preferred
- **Shell Scripts**: Portable bash, error handling included
- **Docker**: Multi-stage builds, minimal images
- **Security**: No hardcoded credentials, secure defaults

## 📄 License

**MIT License** - Full license text available in LICENSE file

### Permissions
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

### Limitations
- ❌ No liability
- ❌ No warranty

### Conditions
- 🔄 License and copyright notice must be included

---

## 🎉 Summary

**NestShift OS** is a complete, production-ready edge AI operating system for autonomous home energy optimization. Built across 6 comprehensive development phases, it provides:

- **9 Microservices** with specialized AI agents
- **Enterprise Security** with JWT auth and TLS encryption
- **Safety-First Design** with immutable hardware constraints
- **Complete Test Suite** with 14 integration tests
- **Multi-Platform Support** (Web, Mobile, Hardware)
- **Production Deployment** ready for Raspberry Pi
- **CI/CD Pipeline** with automated validation

**Ready to deploy and optimize home energy usage autonomously!** 🚀

---

*Built with ❤️ for sustainable, intelligent home automation*