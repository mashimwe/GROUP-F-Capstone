# ServiceFlow — AI-Powered Internet Service Help-Desk Triage Agent

**Course:** BSE4104 — Emerging Trends in Software Engineering (AI-Native & Agentic Engineering Capstone)
**Institution:** Makerere University, College of Computing and Information Sciences, Department of Networks
**Academic Year:** 2026/2027

## Team

| Name | Role | GitHub handle |
| --- | --- | --- |
| Andimashimwe Rhoda | Project/Requirements Lead | @mashimwe |
| Priscillah Aruho | Application/Integration Lead | @aruhoPriscillah |
| Bahati Brenda Kizito | AI Engineering Lead | @Bahati-bk |
| Samuel Buyinza | Quality/Security Lead | @buyinzasamuel |
| Dennise Nuwahereza | DevOps/Documentation Lead | @Dennise-Nuwahereza |

## Problem Statement

ServiceFlow is a bounded AI-powered help-desk triage system for internet service
customers. It interprets a customer's reported problem, classifies the issue,
retrieves troubleshooting guidance from an approved knowledge base, checks a
simulated network/outage status, and determines an appropriate next step —
creating and routing a simulated support ticket when the issue cannot be
resolved through guidance alone.

> Our system helps internet service customers triage and report connectivity
> problems through a guided, AI-assisted workflow. AI is used for understanding
> and classifying user-reported issues, retrieving relevant troubleshooting
> information from an approved knowledge base, and selecting among approved
> next actions. Deterministic software remains responsible for data validation,
> service-status retrieval, authorization, ticket creation and workflow limits.
> The agent may use approved tools to search the troubleshooting knowledge base,
> check simulated service or outage status, and create or route a support
> ticket, but may not remotely control infrastructure or automatically
> disconnect, reconnect or modify any service. We will build and evaluate the
> system using public service-help content together with team-created or
> synthetic service incidents, outage records and support-ticket data.

## Repository Structure

```
README.md
docs/
  requirements/       # Project Charter, user stories, AI Boundary Matrix
  architecture/        # Architecture/context diagrams
  weekly-reports/      # One report per week (1-2 pages each)
  evaluation/           # Evaluation datasets, results, failure catalogues
prompts/               # Versioned prompt specifications
knowledge/              # Corpus metadata/provenance (not restricted data)
src/                    # Application source code
tests/                  # Automated tests
evidence/
  traces/               # Agent/RAG execution traces
  screenshots/          # UI and tool-run screenshots
  demo/                 # Demo recordings/assets
.env.example            # Template for required env vars — never commit real secrets
```

## Status

Week 1 complete — Project Charter, user stories, AI Boundary Matrix and initial
architecture diagram are in `docs/requirements/` and `docs/architecture/`. Week
1 progress report to be completed in `docs/weekly-reports/`.

## Setup / Run Instructions

_(To be completed as the application is built — from Week 2 onward.)_

## Links

- ClickUp board: [link]
- Latest weekly report: `docs/weekly-reports/`
