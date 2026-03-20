# Data handling & compliance notes

## Not HIPAA-ready by default

Oxia as shipped in this repo is an **educational / hackathon-style** stack. It is **not** a HIPAA-compliant product unless you implement a full security program and sign **Business Associate Agreements (BAAs)** with all subprocessors (cloud LLM vendors, hosts, DB providers).

## What you should do before real PHI

1. **No PHI in prompts** to third-party LLMs without a BAA and enterprise configuration.
2. **Encrypt data at rest** (database, backups) and **in transit** (TLS only).
3. **Access control**: strong auth, session hygiene, audit logs for data access.
4. **Minimum necessary**: store only what you need; define retention and deletion.
5. **User consent** for wearables and any cross-device sync.

## This codebase (Phase 1)

- SQLite + JWT: suitable for **local dev / demos** only for sensitive data.
- CORS `allow_origins=["*"]`: **not** production-safe — restrict to your frontend origin.

## Roadmap alignment

Planned **FHIR** and **MCP** integrations must be designed with the above constraints and a security review.
