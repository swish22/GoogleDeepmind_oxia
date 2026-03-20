"""
Oxia — Metabolic Intelligence OS (modular monolith, Phase 1 Clean Architecture).

Layers:
  domain/        — core concepts, errors (no I/O)
  application/ — use-case orchestration, pure mappers
  infrastructure/ — FastAPI, DB, LLM providers, external APIs

See docs/ARCHITECTURE.md for the full roadmap (agents, vector memory, MCP, etc.).
"""

__version__ = "2.0.0-phase1"
