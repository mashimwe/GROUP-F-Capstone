# AI Boundary Matrix

Defines what AI may do autonomously, what must remain deterministic/rule-based, and what requires explicit human approval.

| Decision / Action | AI may do | Deterministic software controls | Requires human approval |
| --- | --- | --- | --- |
| e.g. Answer grounded FAQ question | Retrieve + draft answer | Access control on which documents are retrievable | — |
| e.g. Create support ticket | Draft ticket content | Validate required fields, assign ticket ID | Yes — before ticket is routed |
| e.g. [financial/disciplinary/etc. action] | — | Full control | Always, no autonomous action |

Add one row per meaningful decision point in your workflow.
