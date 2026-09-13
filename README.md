# Enterprise AI-Powered Real-Time EV Fleet Data Platform

A production-oriented, end-to-end EV Fleet Data Engineering platform demonstrating Senior/Lead Data Engineer capabilities across real-time ingestion, streaming, data quality, distributed processing, storage, analytics, machine learning, APIs, frontend delivery, containerization, Kubernetes, CI/CD, testing, security, observability, performance, scalability, and engineering documentation.

## Overview

The Enterprise AI-Powered Real-Time EV Fleet Data Platform is a complete EV data platform designed to demonstrate how a modern engineering team can ingest, stream, validate, persist, process, analyze, and expose real-time electric vehicle telemetry.

The platform connects the complete path from telemetry generation to an operational product:

```text
EV Telemetry
    |
    v
FastAPI Ingestion
    |
    v
Apache Kafka
    |
    v
Kafka Consumer
    |
    v
PostgreSQL
    |
    +-----------------------+
    |                       |
    v                       v
Apache Spark            AI / ML
Processing              Anomaly Detection
    |                       |
    +-----------+-----------+
                |
                v
            FastAPI APIs
                |
                v
              Nginx
                |
                v
          React Frontend
```

The project is intentionally built as a complete engineering platform rather than a small tutorial or isolated proof of concept.

## Project Objectives

The primary objectives are to demonstrate the ability to:

- Design an end-to-end data platform
- Build real-time EV telemetry ingestion
- Implement event-driven streaming with Apache Kafka
- Build reliable consumer processing
- Persist operational telemetry in PostgreSQL
- Manage database evolution with Alembic
- Process data with Apache Spark
- Orchestrate workflows with Apache Airflow
- Integrate genuine machine learning into a data platform
- Build production-style APIs with FastAPI
- Build a product interface with React and Vite
- Serve the frontend through Nginx
- Containerize services with Docker
- Deploy and validate services with Kubernetes
- Implement CI/CD with GitHub Actions
- Apply data-quality and reliability practices
- Implement security controls
- Perform performance and scalability validation
- Build automated regression and acceptance testing
- Produce professional engineering documentation

## End-to-End Platform Flow

### Stage 1 - Telemetry Generation

The platform includes an EV telemetry simulator capable of generating vehicle events for multiple vehicles.

Telemetry contains operational vehicle information such as:

- Vehicle identifier
- Battery level
- Temperature
- Speed
- Charging state
- Vehicle status
- Location
- Timestamp

The simulator produces continuous telemetry that enters the real application ingestion path.

### Stage 2 - FastAPI Ingestion

FastAPI provides the application ingestion boundary.

The telemetry API:

1. Receives an EV telemetry event.
2. Validates the incoming payload.
3. Normalizes relevant values.
4. Creates the application telemetry event.
5. Publishes the event to Kafka.
6. Returns the ingestion response.

This creates a clear separation between application/API responsibilities and streaming responsibilities.

### Stage 3 - Apache Kafka

Apache Kafka provides the event-streaming layer.

The telemetry topic is:

```text
ev.telemetry.v1
```

Kafka decouples the ingestion API from downstream persistence and processing.

The producer uses reliability-oriented configuration, including idempotent publishing and controlled in-flight requests.

### Stage 4 - Kafka Consumer

A dedicated Kafka consumer service processes telemetry events independently from FastAPI.

The consumer:

1. Reads events from Kafka.
2. Validates and normalizes telemetry.
3. Persists the event to PostgreSQL.
4. Executes telemetry-driven processing.
5. Commits the database transaction.
6. Commits the Kafka offset.

The resulting processing boundary is:

```text
Kafka
  |
  v
Consumer
  |
  v
PostgreSQL
```

### Stage 5 - PostgreSQL

PostgreSQL provides the operational persistence layer.

The database stores EV fleet telemetry and related application data.

The platform uses:

- PostgreSQL
- SQLAlchemy
- Alembic
- ORM models
- Database transactions
- Schema migrations
- Database validation
- Runtime schema compatibility checks

### Stage 6 - Spark Processing

Apache Spark provides distributed data-processing capability.

The Spark layer demonstrates:

- PySpark
- Spark DataFrames
- Transformations
- Structured data processing
- Parquet data handling
- Data integrity validation
- Scalable processing patterns

Spark is positioned as the distributed processing layer for workloads that benefit from large-scale data processing.

### Stage 7 - Airflow Orchestration

Apache Airflow provides workflow orchestration.

The project includes Airflow DAG definitions for scheduled and pipeline-oriented processing.

Airflow is responsible for orchestration rather than real-time event transport.

The separation is:

```text
Real-Time Events
      |
    Kafka
      |
      v
Streaming Processing

Scheduled Workflows
      |
   Airflow
      |
      v
     Spark
```

## Data Quality

Data quality is treated as a core engineering capability.

Validation and normalization are performed across the telemetry lifecycle.

Quality controls include:

- Required field validation
- Vehicle identifier validation
- Battery validation
- Temperature validation
- Speed validation
- Status normalization
- Timestamp handling
- API contract validation
- Database schema validation
- Persistence verification
- End-to-end data-flow validation

The acceptance process verifies that telemetry accepted by FastAPI is successfully published to Kafka and subsequently persisted by the consumer into PostgreSQL.

## Database Engineering

The PostgreSQL layer is managed through SQLAlchemy and Alembic.

Database engineering includes:

- ORM models
- Database transactions
- Schema migrations
- Migration history
- Runtime schema validation
- Application/database contract validation
- Persistence verification

Alembic is used to manage schema evolution and prevent application/database drift.

## AI / Machine Learning

The platform contains a genuine machine-learning anomaly detection pipeline.

The AI layer uses real EV telemetry persisted in PostgreSQL.

The machine-learning path is:

```text
Real EV Telemetry
       |
       v
PostgreSQL
       |
       v
Feature Engineering
       |
       v
IsolationForest
       |
       v
Persisted Model Artifact
       |
       v
FastAPI Inference
       |
       v
Vehicle Risk Result
       |
       v
React Product Layer
```

### Machine-Learning Algorithm

The current anomaly detection algorithm is:

```text
IsolationForest
```

Machine-learning library:

```text
scikit-learn
```

Current model features:

- Battery
- Temperature
- Speed

The model is trained using real telemetry from PostgreSQL rather than a hard-coded rule or static response.

### AI Training API

```text
POST /ai/train
```

The training endpoint:

1. Retrieves telemetry from PostgreSQL.
2. Selects the required model features.
3. Validates training data availability.
4. Trains the IsolationForest model.
5. Generates the persisted artifact.
6. Produces model metadata.
7. Calculates artifact integrity information.

### AI Status API

```text
GET /ai/status
```

The AI status endpoint exposes operational metadata such as:

- AI enabled state
- Artifact existence
- Configured model path
- Model version
- Algorithm
- Model ID
- Training timestamp
- Training row count
- Feature count
- Artifact size
- Artifact SHA-256

### AI Vehicle Inference API

```text
GET /ai/vehicle/{vehicle_id}/risk
```

The vehicle inference endpoint returns information including:

- Vehicle ID
- Telemetry timestamp
- Anomaly status
- Anomaly score
- Algorithm
- Model version
- Model ID
- Training timestamp
- Input features

Inference uses the persisted machine-learning model.

### AI Artifact Persistence

The model artifact is persisted independently from the application container lifecycle.

The project validates:

- Artifact existence
- Artifact size
- SHA-256 integrity
- Model metadata
- Model loading
- Model inference
- Artifact availability after pod replacement

This creates a separation between application runtime and model artifact storage.

## FastAPI Backend

FastAPI provides the primary backend application layer.

The backend integrates:

- Application configuration
- Authentication
- Telemetry ingestion
- Kafka publishing
- Database access
- Observability
- AI services
- API validation
- Health checks

The backend is containerized and deployed through Kubernetes.

## API Layer

The API layer provides capabilities for:

- Health
- Authentication
- Telemetry ingestion
- Observability
- AI training
- AI model status
- Vehicle anomaly inference

Important AI endpoints include:

```text
POST /ai/train
GET  /ai/status
GET  /ai/vehicle/{vehicle_id}/risk
```

The API layer provides the contract between the backend platform and the product/frontend layer.

## React Product Layer

The frontend is built using React and Vite.

The product layer provides an operational fleet interface and AI insights.

The frontend consumes backend APIs through Nginx.

The product integration path is:

```text
React
  |
  v
Nginx
  |
  v
FastAPI
  |
  +------> PostgreSQL
  |
  +------> AI / ML
```

The frontend is compiled into a production bundle and served through Nginx.

## Nginx

Nginx provides the frontend web-serving and reverse-proxy layer.

Responsibilities include:

- Serving the React production build
- SPA routing
- Frontend health endpoint
- API reverse proxy
- Forwarding requests to FastAPI
- Production-style HTTP handling

The resulting browser path is:

```text
Browser
   |
   v
Nginx
   |
   +----> React Application
   |
   +----> FastAPI APIs
```

## Docker

The platform is containerized using Docker.

Docker provides:

- Reproducible environments
- Dependency isolation
- Consistent builds
- Service packaging
- Runtime consistency
- Production-style container images

The backend uses Python 3.12.

The frontend is built as a production React application and served using Nginx.

## Kubernetes

Kubernetes provides the runtime orchestration layer.

The project has been validated using Docker Desktop Kubernetes.

The Kubernetes layer includes:

- Backend deployment
- Kafka consumer deployment
- Frontend deployment
- Services
- Health probes
- Runtime configuration
- RBAC
- AI model persistence

The canonical Kubernetes directory is:

```text
k8s/
```

Structure:

```text
k8s/
+-- ai/
-   +-- model-persistence.yaml
+-- frontend/
    +-- deployment.yaml
```

## CI/CD

GitHub Actions provides automated engineering validation.

CI/CD covers:

- Backend quality
- Frontend quality
- Container validation
- Kubernetes validation
- Security validation
- Dependency auditing
- Contract tests
- Release validation

The workflows use least-privilege permissions where applicable.

Container releases support immutable commit-based image tags.

## Testing Strategy

Testing is performed across multiple engineering layers.

### Backend Testing

- Unit tests
- API tests
- Contract tests
- AI tests
- Data validation
- Integration validation

### Streaming Testing

- Kafka publication
- Consumer processing
- Database persistence
- Offset handling

### AI Testing

- Model training
- Model artifact creation
- Artifact integrity
- Model loading
- Model inference
- Anomaly detection behavior
- Model metadata

### Frontend Testing

- Production build
- Application asset validation
- Nginx health
- API integration

### Kubernetes Testing

- Manifest validation
- Deployment validation
- Pod readiness
- Service availability
- RBAC validation
- Persistent model storage

## End-to-End Product Acceptance

Area 29 completed full end-to-end product acceptance.

The validated path is:

```text
Real EV Telemetry
       |
       v
FastAPI
       |
       v
Apache Kafka
       |
       v
Kafka Consumer
       |
       v
PostgreSQL
       |
       v
Real AI Training
       |
       v
AI Inference
       |
       v
Nginx
       |
       v
React
```

Area 29 acceptance validated:

- Backend runtime
- PostgreSQL connectivity
- Kafka consumer
- Real telemetry ingestion
- Kafka publication
- Consumer persistence
- Real AI training
- AI artifact
- AI status
- Real AI inference
- React production application
- Nginx health
- Nginx to FastAPI integration
- Kubernetes runtime
- Production frontend image

## Performance and Scalability

Performance engineering is treated as a dedicated concern.

The project includes:

- API benchmarking
- Request latency measurement
- Mean latency
- P50 latency
- P95 latency
- Maximum latency
- Concurrency validation
- PostgreSQL scalability testing

Performance artifacts are maintained under:

```text
performance/
```

The objective is to demonstrate measurable engineering behavior rather than only functional correctness.

## Reliability Engineering

Reliability is treated as a first-class engineering standard.

The platform includes:

- Kafka producer reliability configuration
- Idempotent event publishing
- Consumer processing controls
- Database transaction management
- Kafka offset handling
- Health checks
- Kubernetes probes
- Migration validation
- End-to-end persistence checks
- AI artifact integrity validation
- Regression testing
- Runtime acceptance validation

## Observability

Observability is incorporated across application and infrastructure layers.

The project includes visibility into:

- Application health
- Backend service status
- AI model status
- Kubernetes pod state
- Container health
- Kafka consumer behavior
- Database persistence
- End-to-end acceptance diagnostics

The goal is to make failures diagnosable across service boundaries.

## Security

Security is incorporated throughout the platform.

Security controls include:

- Environment-based configuration
- Secret exclusion from Git
- Hardened `.gitignore`
- Hardened `.dockerignore`
- JWT authentication foundation
- Dependency auditing
- CI security validation
- Least-privilege CI permissions
- Kubernetes RBAC
- Container validation

Real credentials and local environment files are intentionally excluded from the repository.

## Configuration Management

Configuration is separated from application source code.

Templates include:

```text
.env.example
backend/.env.example
```

Local environment files are ignored by Git.

Real credentials must never be committed to the repository.

## Repository Structure

```text
.
+-- .github/
-   +-- workflows/
-       +-- ci.yml
-       +-- cd.yml
-
+-- airflow/
-   +-- dags/
-
+-- backend/
-   +-- alembic/
-   +-- app/
-   +-- models/
-   +-- simulator/
-   +-- tests/
-   +-- Dockerfile
-   +-- requirements.txt
-
+-- frontend/
-   +-- src/
-   +-- Dockerfile
-   +-- nginx.conf
-   +-- package.json
-   +-- package-lock.json
-
+-- hadoop/
-
+-- k8s/
-   +-- ai/
-   -   +-- model-persistence.yaml
-   +-- frontend/
-       +-- deployment.yaml
-
+-- kafka_config/
-
+-- performance/
-
+-- spark/
-
+-- data_lake/
-
+-- docs/
-
+-- alembic.ini
+-- docker-compose.yml
+-- docker-compose.override.yml
+-- .dockerignore
+-- .gitignore
+-- .env.example
+-- Makefile
+-- LICENSE
+-- README.md
```

## Documentation

The `docs/` directory contains engineering documentation covering:

- Requirements
- Project planning
- Architecture
- Business analysis
- Database design
- Backend engineering
- Data engineering
- Big data and streaming
- Security
- Testing
- CI/CD
- Engineering decisions
- Portfolio documentation

Documentation is treated as part of the engineering deliverable.

## Local Development

### Prerequisites

Recommended local environment:

- Docker Desktop
- Docker Compose
- Docker Desktop Kubernetes
- Python 3.12
- Node.js 22+

### Configuration

Use the following files as local configuration templates:

```text
.env.example
backend/.env.example
```

Never commit real credentials or secrets.

### Start the Platform

```powershell
docker compose up -d
```

Check running services:

```powershell
docker compose ps
```

View service logs:

```powershell
docker compose logs --tail=200
```

### Makefile Commands

Common commands include:

```text
make help
make up
make down
make restart
make ps
make logs
make backend-test
make frontend-test
make test
make lint
```

## Engineering Standards

The project emphasizes:

- Production-oriented architecture
- Clear service boundaries
- Separation of responsibilities
- Reproducible builds
- Configuration externalization
- Data quality
- Reliability
- Security
- Observability
- Performance
- Scalability
- Testability
- Maintainability
- Documentation
- Operational readiness

## Architecture Principles

The platform follows these engineering principles:

### Separation of Concerns

API ingestion, streaming, persistence, processing, AI, and product presentation have clearly defined responsibilities.

### Event-Driven Processing

Kafka provides asynchronous event transport between ingestion and downstream processing.

### Data Integrity

Telemetry is validated before persistence and end-to-end acceptance verifies actual data flow.

### Reproducibility

Docker, dependency pinning, CI/CD, and infrastructure definitions support repeatable environments.

### Operational Visibility

Health checks, status APIs, Kubernetes validation, and acceptance tests provide operational visibility.

### Security by Default

Secrets are externalized and excluded from version control.

### Testability

The system is validated at unit, contract, integration, runtime, performance, and end-to-end levels.

## Project Status

### Areas 1-28

**Status: COMPLETE**

The foundational, backend, data engineering, streaming, database, reliability, security, testing, CI/CD, and performance engineering areas were completed before the final product integration stage.

### Area 29 - Complete Product / Demo Layer

**Status: COMPLETE / GREEN**

Area 29 integrated the platform into a complete demonstrable product.

Validated path:

```text
FastAPI
   |
   v
Kafka
   |
   v
Consumer
   |
   v
PostgreSQL
   |
   v
AI
   |
   v
Nginx
   |
   v
React
```

All Area 29 acceptance gates were completed successfully.

### Area 30 - Final Acceptance + Portfolio Engineering

**Status: IN PROGRESS**

Area 30 is the final area of the locked Project 01 roadmap.

Area 30 covers:

- Final project clearance
- Final acceptance
- Repository finalization
- GitHub portfolio presentation
- GitHub profile presentation
- Professional portfolio website
- Final documentation
- Portfolio readiness

There is no Area 31 in the Project 01 roadmap.

## Production Readiness Position

The platform has been validated locally using Docker and Kubernetes, including real end-to-end runtime flows.

This repository does not claim that the current environment is a publicly deployed cloud production system.

The architecture provides a strong foundation for deployment to managed cloud infrastructure with appropriate production services and controls.

A future cloud deployment would require appropriate:

- Managed databases
- Managed streaming infrastructure
- Object storage
- Kubernetes infrastructure
- Networking
- Secrets management
- Monitoring
- Logging
- Alerting
- High availability
- Disaster recovery
- Security controls

Cloud deployment is therefore not represented as an already completed public-cloud production deployment.

## Project Outcomes

The project demonstrates a complete data platform capable of connecting:

```text
Operational Telemetry
        |
        v
Real-Time Streaming
        |
        v
Reliable Persistence
        |
        v
Distributed Processing
        |
        v
Machine Learning
        |
        v
API Products
        |
        v
Frontend Product
        |
        v
Containerized Runtime
        |
        v
Kubernetes Platform
        |
        v
Automated Engineering Validation
```

This demonstrates ownership of the complete lifecycle from data generation through operational intelligence.

## Portfolio Positioning

This project is designed as a flagship Data Engineering portfolio project.

It demonstrates engineering across:

- Data Engineering
- Real-Time Streaming
- Distributed Processing
- Databases
- Machine Learning
- Backend Engineering
- API Engineering
- Frontend Integration
- Docker
- Kubernetes
- CI/CD
- Security
- Observability
- Reliability
- Performance
- Scalability
- Testing
- Documentation

The project is intended to demonstrate Senior/Lead Data Engineer-level engineering breadth through a complete, integrated platform.

## Final Engineering Statement

The primary engineering achievement of this project is not any single technology.

It is the integration of multiple engineering layers into one validated platform:

```text
Real EV Telemetry
        |
        v
FastAPI
        |
        v
Apache Kafka
        |
        v
Kafka Consumer
        |
        v
PostgreSQL
        |
        +-------------------+
        |                   |
        v                   v
     Spark              AI / ML
        |                   |
        +---------+---------+
                  |
                  v
              FastAPI
                  |
                  v
                Nginx
                  |
                  v
                React
```

The platform has been built with a focus on correctness, reliability, security, testability, performance, maintainability, and operational readiness.

## Author

**Sandeep Reddy**

Data Engineer | Real-Time Data Platforms | Data Engineering | AI/ML Data Systems

## License

MIT License

Copyright (c) 2026 Sandeep Reddy

This project is licensed under the MIT License.