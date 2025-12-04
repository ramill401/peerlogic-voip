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
3. Create virtual environment:
```bash
   python -m venv venv
   source venv/bin/activate  # On Mac/Linux
```
4. Install dependencies:
```bash
   pip install -r requirements.txt
```
5. Run migrations:
```bash
   python manage.py migrate
```
6. Start server:
```bash
   python manage.py runserver
```

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