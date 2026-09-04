# Initial Architecture / Context Diagram — ServiceFlow

```
                         ┌──────────────────────┐
                         │   Internet Service   │
                         │      Customer        │
                         └──────────┬───────────┘
                                    │
                           Reports an internet
                              service problem
                                    │
                                    ▼
                     ┌──────────────────────────┐
                     │       SERVICEFLOW        │
                     │    Web/Application UI    │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                ┌────────────────────────────────┐
                │  APPLICATION / ORCHESTRATION   │
                │ • Input validation             │
                │ • Workflow state               │
                │ • Authorization                │
                │ • Action/tool allow-list       │
                │ • Iteration & stop limits      │
                └───────────────┬────────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
                 ▼                             ▼
       ┌───────────────────┐        ┌─────────────────────┐
       │   AI COMPONENT    │        │ DETERMINISTIC       │
       │ • Understand issue│        │ COMPONENTS          │
       │ • Classify issue  │        │ • Validation        │
       │ • Ask questions   │        │ • Authorization     │
       │ • Select approved │        │ • Workflow control  │
       │   next action     │        │ • State management  │
       └─────────┬─────────┘        └─────────────────────┘
                 │
        ┌────────┼───────────┬─────────────────┐
        │        │           │                 │
        ▼        ▼           ▼                 ▼
 ┌───────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐
 │ Foundation│ │Knowledge │ │ Service/     │ │ Ticketing    │
 │ Model     │ │ Base/RAG │ │ Outage Tool  │ │ Tool         │
 │           │ │          │ │ (Simulated)  │ │ (Simulated)  │
 └───────────┘ └──────────┘ └──────────────┘ └──────┬───────┘
                                                     │
                                                     ▼
                                           ┌─────────────────┐
                                           │ Human Support   │
                                           │ Officer         │
                                           │ Reviews and     │
                                           │ resolves case   │
                                           └─────────────────┘
```

## Component Responsibilities

| Component | Responsibility |
| --- | --- |
| Internet Service Customer | Reports connectivity or service problems and provides clarification when requested. |
| ServiceFlow Application UI | Provides the interface through which the customer interacts with the system. |
| Application/Orchestration Layer | Controls workflow, validates inputs, manages state, enforces permissions, tool restrictions and stopping conditions. |
| Foundation Model | Understands natural language, classifies issues, generates clarification questions and selects among approved actions. |
| Knowledge Base/RAG | Provides controlled troubleshooting information and service guidance. |
| Service/Outage Tool | Returns authoritative simulated information about service availability or known outages. |
| Ticketing Tool | Creates and stores a simulated support ticket when escalation conditions are met. |
| Human Support Officer | Reviews escalated tickets and handles actions outside the AI agent's authority. |

## Architecture Boundary
The AI model does not directly control tools or network infrastructure without
the application's control layer. The workflow follows: AI proposes or selects
an approved action → the orchestration layer validates it → an authorized tool
executes → the result returns to the workflow → the AI interprets the result →
the workflow stops or continues within defined limits.
