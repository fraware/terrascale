# Planet-Scale Social Network Architecture

## Overview

This document describes the architecture for a hypothetical social network designed to support 1 billion active users globally. The system is designed with the following goals:

- **Global Availability:** Deploying services in multiple cloud regions with global load balancing and CDNs.
- **Scalability:** Using sharding, replication, and caching to handle millions of requests per second.
- **Resilience:** Multi-region disaster recovery and automated failover.
- **Event-Driven Data Flow:** Employing a streaming data pipeline for real-time updates.

## Implementation in this repository

The **full architecture below is aspirational**. What you can run from this repo today is a **narrow slice** that illustrates patterns (API service, relational data, cache-aside, migrations, observability hooks):

| Aspect | In this repo now | Full vision (documented below) |
|--------|------------------|----------------------------------|
| Services | **User Service** only | Post, Feed, Notification, and others |
| Runtime | **FastAPI**, sync **SQLAlchemy 2** + **psycopg2**, **Redis**, **Alembic** | Same language family possible; async drivers and more services at scale |
| Data stores | Single **PostgreSQL** instance, single **Redis** | Sharded PostgreSQL, NoSQL for graph/posts, replicated caches |
| Messaging | Not in **docker-compose.yml** | **Kafka** (or managed streaming) between services |
| Deploy | **Docker Compose** for local dev | **Kubernetes** in cloud regions, global LB, CDN |
| Observability | **structlog**, optional **OpenTelemetry** OTLP HTTP export | Prometheus/Grafana, centralized logs (ELK/EFK), full tracing mesh |

**Code layout:** the runnable User Service lives under `services/user-service/` (`src/user_service/`, `alembic/`, `Dockerfile`, `tests/`). Root [README.md](README.md) explains how to start the stack and where CI runs.

When you add cross-service events, reintroduce a broker (for example Kafka in **KRaft** mode or a managed equivalent) via a separate Compose override or deployment chart rather than coupling it to the minimal local stack.

## High-Level Architecture

### Components

1. **Global Front-End & CDN:**

   - **DNS & Global Load Balancing:** Use anycast DNS and cloud load balancers to direct users to the nearest region.
   - **CDN:** Cache static assets worldwide (e.g., via Cloudflare or AWS CloudFront).

2. **API Gateway:**

   - Acts as the single entry point for all API calls. It routes requests to appropriate microservices.
   - Implements rate limiting, authentication, and monitoring.

3. **Microservices:**

   - **User Service:** Manages user profiles, authentication, and social graph. (Implemented in this repo as a sample **FastAPI** application with PostgreSQL and Redis.)
   - **Post Service:** Manages creation, storage, and retrieval of posts.
   - **Feed Service:** Aggregates posts for user timelines.
   - **Notification Service:** Delivers real-time notifications.

4. **Data Storage:**

   - **Transactional Data:** Sharded SQL databases (e.g., PostgreSQL clusters) for user data.
   - **Social Graph & Posts:** NoSQL solutions (e.g., Cassandra, DynamoDB) to handle large, flexible datasets.
   - **Caching:** In-memory caches (e.g., Redis) for frequently accessed data.
   - **Event Streaming:** Kafka (or managed alternatives) for handling asynchronous events across services.

5. **Observability & Monitoring:**

   - **Metrics:** Prometheus and Grafana for real-time monitoring.
   - **Logging:** ELK/EFK stack (Elasticsearch, Fluentd/Logstash, Kibana) for centralized logging.
   - **Tracing:** OpenTelemetry/Jaeger for distributed tracing.

6. **Backup & Disaster Recovery:**
   - Data is replicated across regions.
   - Regular backups and a defined RTO/RPO are in place.
   - Failover strategies include active-active and active-passive configurations.

## Data Flow

1. **User Request:**

   - A user’s request is directed by DNS to the nearest region.
   - The API Gateway receives the request and routes it to the appropriate microservice.

2. **Service Interaction:**

   - The User Service handles login and profile management, reading/writing from the sharded PostgreSQL.
   - When a user posts an update, the Post Service stores it (using a NoSQL store for scalability) and publishes an event to Kafka.
   - The Feed Service subscribes to Kafka, processes the event, and updates user timelines.
   - Caching layers (Redis) are used to serve high-read endpoints.

3. **Monitoring & Recovery:**
   - Services report metrics and logs to the central observability stack.
   - In the event of a regional failure, traffic is automatically rerouted to healthy regions.

## Technology Choices

- **Cloud & Multi-Region:** AWS, GCP, or Azure – with Kubernetes (EKS, GKE, or AKS) as the orchestration layer.
- **API Gateway:** NGINX or a cloud-native solution.
- **Microservices:** Python/FastAPI for the User Service (sample implementation in `services/user-service/`); other services can use similar stacks.
- **Databases:** PostgreSQL (transactional, sharded) and Cassandra/DynamoDB (for social graph/posts).
- **Caching:** Redis.
- **Event Streaming:** Apache Kafka.
- **Observability:** Prometheus, Grafana, ELK/EFK, Jaeger; the sample service additionally supports OTLP HTTP export when configured.

## Comparison & Inspirations

- **Facebook/Twitter:** Use similar ideas (sharding, caching, CDNs) to handle millions of users.
- **AWS IoT:** For global data ingestion and processing, similar techniques (multi-region replication, stream processing) are employed.
- **Google SRE Practices:** Emphasize observability, automation, and blameless postmortems.

## Future Considerations

- Expand the design to include other microservices (e.g., Recommendation Engine, Analytics Service).
- Implement rigorous load testing and chaos engineering (e.g., using Chaos Monkey) to simulate real-world failures.
- Explore serverless functions and edge computing for further latency reduction.
