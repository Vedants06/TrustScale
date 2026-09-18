# TrustScale

TrustScale is a distributed load balancer that doesn't blindly trust what nodes say about themselves. It predicts load ahead of time with an LSTM model, verifies every health report with cryptographic signatures, and cross-checks what a node claims against how it actually behaves. Nodes that lie about their load get flagged, lose trust, and eventually get quarantined.

The goal is to show that combining ML load prediction, cryptographic attestation, and behavioral trust scoring catches Byzantine (lying/compromised) nodes better than any of those approaches alone.

## The problem

Most load balancers just trust the numbers a node reports. If a node is compromised, buggy, or malicious, it can lie:

- Claim it's less busy than it actually is, so it gets flooded with traffic and becomes a bottleneck.
- Claim it's more busy than it actually is, so it starves itself of traffic and wastes capacity.
- Coordinate with other nodes to lie together, which is much harder to catch than a single bad actor.

Tools like nginx or HAProxy have no concept of this. Byzantine fault tolerance research (Raft, PBFT) solves a different problem (consensus, not real-time routing). Service meshes like Istio verify certificates, not behavior. Nothing off the shelf actually cross-checks whether a node's claimed load matches its observed behavior in real time.

## How it works

1. Every worker node sends a signed health report (JWT) to the load balancer every 5 seconds, reporting CPU, memory, active requests, and response time.
2. The load balancer verifies the signature, then compares the claimed load against the node's actual observed response times, using a per-node baseline built ahead of time.
3. If the claim and reality line up, trust goes up slightly. If they don't, trust drops, with the penalty getting steeper the bigger the lie.
4. Routing picks nodes based on a combination of predicted load and trust score, so a lying node naturally gets sidelined even before it's quarantined.
5. If a node's trust drops below 0.30, it gets quarantined. Repeat offenders get quarantined for longer each time (60s, then 5 minutes, then 30 minutes, then 24 hours, then it needs a manual admin restore), so a node can't just lie, sit out a short timeout, and lie again.
6. In parallel, an LSTM model forecasts where each node's load is heading over the next couple of minutes, so routing decisions aren't purely reactive.

New nodes don't start fully trusted either. They start at 0.5 and have to earn their way up with consistent honest reports before they get full routing weight.

## Architecture

```
                        ┌────────────────────┐
                        │   Traffic Generator │
                        │       (Locust)       │
                        └──────────┬───────────┘
                                   │ HTTP requests
                                   ▼
                        ┌────────────────────────────┐
                        │        Load Balancer         │
                        │  routing · trust · crypto     │
                        └───┬─────────────┬───────────┘
                            │             │
                    reads/writes     predictions
                            │             │
                            ▼             ▼
                  ┌──────────────┐  ┌──────────────┐
                  │     Redis     │  │  ML Service   │
                  │ trust scores  │  │ LSTM predictor│
                  │ predictions   │  │               │
                  │ quarantine    │  └──────────────┘
                  └──────────────┘
                            ▲
                            │ signed heartbeats (every 5s)
              ┌─────────────┴──────────────┐
              │        Worker Nodes          │
              │   (N instances, each with     │
              │   a configurable behavior:    │
              │   honest, lying, colluding)   │
              └─────────────────────────────┘

              ┌─────────────────────────────┐
              │      Attack Orchestrator      │
              │  drives Byzantine scenarios    │
              │  and coordinates colluders     │
              └─────────────────────────────┘

              ┌─────────────────────────────┐
              │    Prometheus + Grafana       │
              │  scrapes every service         │
              └─────────────────────────────┘

              ┌─────────────────────────────┐
              │      Next.js Dashboard        │
              │  live topology, trust graphs,  │
              │  booking-demo simulator        │
              └─────────────────────────────┘
```

## Repository layout

```
trustscale/
├── services/
│   ├── load_balancer/       Routing, trust engine, crypto verification, API (port 8000)
│   ├── node/                 Worker node: monitoring agent, signer, behavior modes
│   ├── ml_service/           LSTM load prediction service (port 8100)
│   ├── attack_orchestrator/  Runs Byzantine attack scenarios (port 8200)
│   └── traffic_generator/    Locust traffic patterns (port 8089 UI)
├── shared/
│   ├── contracts/            Pydantic data contracts shared across services
│   ├── crypto/                Shared signing/verification utilities
│   ├── models/                 Shared data models
│   └── utils/
├── dashboard/                Next.js 15 + React 19 dashboard (port 3000)
├── config/
│   ├── attack_scenarios/     YAML Byzantine attack scenario definitions
│   ├── traffic_patterns/     YAML traffic pattern definitions
│   └── deployment/
├── infrastructure/
│   ├── prometheus/, grafana/, redis/, nginx/, kubernetes/
├── scripts/
│   ├── ml/                    Model training scripts
│   ├── data/                  Training data generation
│   └── baseline_profiler.py  Builds the per-node latency baseline used for cross-validation
├── research/                 Paper drafts, experiment data, analysis notebooks
├── tests/
│   ├── unit/, integration/, load/, scenarios/
├── docker-compose.yml               Single-machine local cluster
├── docker-compose.distributed.yml   Multi-machine / LAN deployment
└── pyproject.toml            Poetry project definition (Python 3.13)
```

## Services

| Service | Port | Stack | What it does |
|---|---|---|---|
| Load Balancer | 8000 | FastAPI + asyncio | Routes requests, verifies signed heartbeats, runs cross-validation, owns trust scoring and quarantine, exposes Prometheus metrics and a `/ws/live` WebSocket |
| Worker Node | 8001 to 8008 | FastAPI + asyncio | Handles forwarded requests, collects local metrics, signs heartbeats, supports pluggable `BEHAVIOR_MODE` for simulating honest or lying nodes |
| ML Service | 8100 | FastAPI + PyTorch | Trains and serves an LSTM that predicts each node's load a couple minutes ahead, with simpler baselines for comparison |
| Attack Orchestrator | 8200 | FastAPI + asyncio | Loads YAML attack scenarios, coordinates Byzantine node behavior including collusion, runs repeated experiments, collects results |
| Traffic Generator | 8089 (Locust UI) | Locust | Generates configurable traffic patterns (steady state, ramps, spikes) |
| Redis | 6379 | Redis 7 | Stores trust scores, predictions, and quarantine state; all trust updates are atomic via WATCH/MULTI |
| Prometheus | 9090 | Prometheus | Scrapes all services every 5 seconds |
| Grafana | via infrastructure/grafana | Grafana | Dashboards for overview, trust, predictions, attacks, routing |
| Dashboard | 3000 | Next.js 15 + React 19 + Tailwind | Live topology view, per-node trust graphs, activity feed, booking simulator demo |

## Trust scoring, briefly

Trust is a float between 0 and 1, updated on every heartbeat:

- New nodes start at 0.5, not 1.0, and stay capped until they've sent 20 consecutive honest reports.
- Small discrepancies between claimed and observed metrics cost a small penalty; large ones cost an exponentially bigger one.
- An invalid signature or a stale timestamp is penalized on its own, independent of the metric comparison.
- Dropping below 0.30 triggers quarantine, with the duration escalating on repeat offenses.
- Every 30 seconds, the system checks for correlated lying across nodes to catch collusion, and quarantines colluders together.

The comparison between "claimed load" and "expected behavior" relies on a per-node latency baseline built with `scripts/baseline_profiler.py`, since different nodes handle the same CPU load differently.

## Byzantine attack modes

Each worker node can run in one of several behavior modes, set via `BEHAVIOR_MODE`:

- `honest`, reports truthfully.
- `under_reporter`, claims lower load than it actually has.
- `over_reporter`, claims higher load than it actually has.
- `intermittent_liar`, only lies some of the time, which is harder to catch.
- `colluder`, coordinates lying with other nodes through the Attack Orchestrator over Redis pub/sub.

Pre-built scenarios live in `config/attack_scenarios/`: a solo under-reporter, a 20% Byzantine cluster, and a 3-node collusion attack, each with a "no defense" version for comparison.

## Tech stack

| Layer | Technology |
|---|---|
| Language / runtime | Python 3.13, asyncio |
| Web framework | FastAPI + uvicorn |
| ML | PyTorch (LSTM), scikit-learn (baselines), pandas/numpy |
| Cryptography | `cryptography` + PyJWT (RSA/ECDSA-signed JWTs) |
| Cache / coordination | Redis 7 (WATCH/MULTI, pub/sub) |
| Load testing | Locust |
| Observability | Prometheus, Grafana, structlog |
| Orchestration | Docker Compose locally, Kubernetes/Minikube for the final demo |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, Recharts |
| Dependency management | Poetry (backend), npm (dashboard) |
| Testing / linting | pytest, mypy, ruff |

Kafka, Consul/etcd, a full service mesh, RL-based routing, and a blockchain trust ledger were all considered and deliberately left out for this scale of system, since they'd add complexity without matching benefit for a cluster this size.

## Getting started

### Prerequisites

- Docker and Docker Compose
- Python 3.13 and Poetry, for local (non-Docker) development
- Node.js 18+ and npm, for the dashboard

### 1. Clone and configure

```bash
git clone <repo-url>
cd trustscale
cp .env.example .env
```

Adjust `.env` as needed (ports, quarantine thresholds, traffic patterns).

### 2. Run the full cluster with Docker Compose

```bash
docker-compose up --build
```

This starts Redis, the load balancer, 8 worker nodes, the ML service, the attack orchestrator, the traffic generator, and Prometheus.

| Component | URL |
|---|---|
| Load Balancer API | http://localhost:8000 |
| Load Balancer docs | http://localhost:8000/docs |
| Worker nodes | http://localhost:8001 to 8008 |
| ML Service | http://localhost:8100 |
| Attack Orchestrator | http://localhost:8200 |
| Locust UI | http://localhost:8089 |
| Prometheus | http://localhost:9090 |

### 3. Run the dashboard (optional, separate terminal)

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:3000.

### 4. Local backend development without Docker

```bash
poetry install
poetry run uvicorn services.load_balancer.main:app --reload --port 8000
```

Run other services the same way, pointing each at the ports and URLs set in `.env`.

## Configuration

Everything is configured through environment variables, see `.env.example` for the full list. The important ones:

| Variable | Default | Meaning |
|---|---|---|
| `TRUST_STRATEGY` | `trust_aware` | Routing strategy, combines prediction and trust |
| `QUARANTINE_THRESHOLD` | `0.30` | Trust score below which a node is quarantined |
| `QUARANTINE_INITIAL_DURATION` | `60` | Seconds for the first quarantine, escalates on repeat offenses |
| `BOOTSTRAP_MAX_INITIAL` | `0.5` | Starting trust score for newly registered nodes |
| `BEHAVIOR_MODE` | `honest` | Per-node behavior for simulating attacks |
| `REPORT_INTERVAL_SECONDS` | `5` | How often nodes send signed heartbeats |
| `RETRAIN_INTERVAL_MINUTES` | `30` | ML model retraining cadence |
| `TRAFFIC_PATTERN` | `steady_state` | Locust traffic shape |

## Dashboard

The dashboard (Next.js 15 + React 19, in `dashboard/`) shows:

- A live topology view of the load balancer and its nodes, with animated traffic particles showing routing decisions as they happen.
- Per-node trust sparklines and a detail modal for drilling into a specific node's history.
- A status banner and activity feed streaming trust and quarantine events.
- A booking simulator demo, an IRCTC-style booking load test used to visualize round-robin routing, quarantine, and lie detection under bursty traffic.

## Running experiments

Attack scenarios are YAML files in `config/attack_scenarios/`, run by the Attack Orchestrator on port 8200. It loads a scenario, switches the configured nodes into the right behavior mode (coordinating colluders over Redis pub/sub if needed), drives traffic through the system for the scenario duration, and records detection time, false positives, quarantine events, and success rate. Each scenario also has a "no defense" variant so you can compare with TrustScale turned off.

Model training scripts live in `scripts/ml/`, and the per-node latency baseline used for cross-validation is built with `scripts/baseline_profiler.py`.

## Testing

```bash
poetry run pytest tests/unit          # per-service unit tests
poetry run pytest tests/integration   # cross-service integration tests
poetry run locust -f tests/load/locustfile_baseline.py
poetry run ruff check .
poetry run mypy .
```

## Observability

Prometheus scrapes every service every 5 seconds, and Grafana dashboards cover system overview, trust scores, predictions, live attacks, and routing decisions. All services log structured JSON via structlog. The load balancer also exposes a `/ws/live` WebSocket that the dashboard uses for real-time updates.

## Distributed / multi-machine deployment

To run the cluster across multiple physical machines instead of one, use `docker-compose.distributed.yml`, which supports LAN IP registration so worker nodes on separate hosts can register with a centrally hosted load balancer.

## License

MIT License, see `LICENSE`.
