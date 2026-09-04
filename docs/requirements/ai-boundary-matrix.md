# AI Boundary Matrix — ServiceFlow

| Activity | AI Responsibility | Deterministic Software | Human Responsibility | Boundary / Restriction |
| --- | --- | --- | --- | --- |
| Receive customer problem | Interpret natural-language description. | Validate required input and create active case. | None during normal intake. | AI does not alter the original report. |
| Classify internet problem | Identify likely supported issue category. | Validate classification against supported categories. | Review unusual cases. | Uncertain cases require clarification or safe escalation. |
| Ask for missing information | Identify missing details and generate questions. | Track collected information and prevent repetition. | Assist when needed. | Only case-relevant information may be requested. |
| Retrieve troubleshooting guidance | Select relevant queries and synthesize evidence. | Retrieve approved sources and enforce access boundaries. | Maintain and approve knowledge content. | No fabrication when supporting information is unavailable. |
| Provide troubleshooting steps | Generate clear, grounded guidance. | Apply safety and formatting checks. | Handle expert cases. | No unsafe or unauthorized infrastructure actions. |
| Check service/outage status | Decide when a check is relevant. | Call approved status tool and return results. | Maintain/review status information. | AI cannot invent or modify status information. |
| Select next action | Choose among approved actions. | Enforce action list, permissions, state and iteration limits. | Take over when hand-off is reached. | AI cannot invent new actions or tools. |
| Create ticket content | Summarize issue and evidence. | Validate fields and create simulated record. | Review and resolve case. | Ticketing remains within approved simulation. |
| Route ticket | Recommend routing category. | Apply routing rules. | Review or override if needed. | No independent high-impact decision-making. |
| Maintain active case state | Use available state for continuity. | Store and manage session/workflow state. | Access according to authorization. | State follows data-handling rules. |
| Persistent memory | Use approved retained information. | Enforce storage, retention, access and deletion. | Define/review memory policy. | Memory cannot silently make critical decisions. |
| Tool selection and use | Choose an appropriate approved tool. | Validate inputs and enforce allow-list. | Approve future tool expansion. | No arbitrary APIs, commands or unapproved tools. |
| Infrastructure control | None. | None in project scope. | Authorized personnel only. | AI must never control network infrastructure. |
| Disconnect/reconnect services | None. | None in project scope. | Authorized personnel only. | Automatic disconnection/reconnection is prohibited. |
| High-impact cases | Summarize evidence where appropriate. | Enforce hand-off and approval. | Make final decisions/actions. | AI cannot independently perform high-impact actions. |
| Stop workflow | Recognize completion, hand-off or inability to continue. | Enforce maximum iterations and stop conditions. | Continue after hand-off if necessary. | No uncontrolled or indefinite loops. |

## Explicitly Approved AI Actions
- Interpret customer-reported problems.
- Classify supported issue types.
- Ask relevant clarification questions.
- Retrieve and synthesize approved troubleshooting information.
- Decide when an approved status check is required.
- Interpret approved tool results.
- Select from predefined actions.
- Generate grounded guidance.
- Summarize unresolved cases for escalation.
- Recommend an approved routing category.
- Use justified case memory where permitted.

## Actions Reserved for Deterministic Software
- Input validation.
- Authorization and permission checks.
- Knowledge-base access controls.
- Calling the simulated service-status tool.
- Creating and storing simulated tickets.
- State management.
- Tool allow-list enforcement.
- Iteration and stop-limit enforcement.
- Retention/deletion rules.
- Logs and execution traces.
- Blocking prohibited actions.

## Actions Requiring Human Control
- Reviewing and resolving escalated cases.
- Actual infrastructure or service changes.
- Exceptional cases outside the workflow.
- Approval of high-impact actions.
- Knowledge-base governance.
- Memory and data-handling policy review.
- Overriding ticket routing where necessary.

## Prohibited Actions
- Direct infrastructure control.
- Arbitrary system or shell commands.
- Network configuration modification.
- Automatic disconnection or reconnection.
- Fabricating outage information.
- Modifying authoritative status records.
- Unauthorized data access.
- Use of tools outside the allow-list.
- Operation beyond iteration limits.
- High-impact actions without human approval.

## Boundary Principle
AI provides reasoning, interpretation, retrieval and bounded action selection.
Deterministic software provides validation, authorization, enforcement and
workflow control. Humans retain responsibility for high-impact decisions and
actions.
