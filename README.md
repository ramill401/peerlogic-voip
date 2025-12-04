# Peerlogic VoIP Admin

Universal VoIP administration system for Peerlogic.

## Overview

This system allows Peerlogic to manage VoIP phone systems (users, devices, call routing, etc.) through a universal interface that works with multiple providers:

- **NetSapiens** (Phase 1)
- RingCentral (Future)
- 8x8 (Future)
- Others...

## Architecture
```
Peerlogic Web App
       ↓
Peerlogic VoIP API (stable, never changes)
       ↓
Adapter Router (selects correct provider)
       ↓
Provider Adapter (NetSapiens, RingCentral, etc.)
       ↓
Provider API
```

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Docker (optional, recommended)

### Local Development

1. Clone the repo
2. Copy environment file:
```bash
   cp .env.example .env
```
3. Install Poetry (if not already installed):
```bash
   curl -sSL https://install.python-poetry.org | python3 -
   # Or: pip install poetry
```
4. Install dependencies:
```bash
   poetry install
```
5. Activate Poetry shell (optional):
```bash
   poetry shell
   # Or run commands with 'poetry run' prefix
```
6. Run migrations:
```bash
   poetry run python manage.py migrate
```
7. Start server:
```bash
   poetry run python manage.py runserver
```

**Note:** This project uses Poetry for dependency management. You can also use `pip install -r requirements.txt` if Poetry is not available, but Poetry is recommended.

## Project Structure
```
peerlogic-voip/
├── src/voip/
│   ├── adapters/        # Provider adapters
│   │   └── netsapiens/  # NetSapiens implementation
│   ├── api/             # REST API endpoints
│   ├── models/          # Django models
│   └── services/        # Business logic
├── tests/               # Test suite
└── docs/                # Documentation
```

## License

Proprietary - Peerlogic Inc.
```

5. Save the file

---

**Checkpoint:** Your project should now have these files in the root:
```
peerlogic-voip/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── docs/
├── src/
└── tests/