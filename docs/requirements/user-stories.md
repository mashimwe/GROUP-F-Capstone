# User Stories and Acceptance Criteria — ServiceFlow

## User Story 1: Report an Internet Service Problem
As an internet service customer, I want to describe my internet problem in my
own words, so that the system can begin assisting me.

**Acceptance Criteria**
- The system shall allow a natural-language problem description.
- The system shall validate that a description has been provided.
- If the description is missing or insufficient, the system shall request additional information.
- The description shall be associated with the active support case.

## User Story 2: Classify the Reported Problem
As an internet service customer, I want the system to identify the type of
problem I am experiencing, so that I can receive relevant assistance.

**Acceptance Criteria**
- The system shall classify supported problems such as no connection, slow connection, intermittent connection, router/modem problem or possible outage.
- If classification is uncertain, the system shall ask for clarification or provide a safe escalation path.
- The system shall not invent a service status or technical cause without supporting information.

## User Story 3: Retrieve Relevant Troubleshooting Guidance
As an internet service customer, I want relevant troubleshooting guidance, so
that I can attempt safe and appropriate steps before escalation.

**Acceptance Criteria**
- The system shall retrieve relevant information from the approved knowledge base.
- Responses shall be based on retrieved information when relevant evidence exists.
- The system shall handle missing knowledge without fabricating an answer.
- The system shall not provide unsafe or unauthorized infrastructure-control instructions.

## User Story 4: Check Service or Outage Status
As an internet service customer, I want the system to check whether there is a
known service disruption, so that I can determine whether my problem may be
related to a wider outage.

**Acceptance Criteria**
- The system shall use an approved service-status tool when required.
- The system shall distinguish tool results from AI-generated explanations.
- The system shall not claim an outage exists without tool evidence.
- If the tool is unavailable, the system shall handle the failure safely.

## User Story 5: Ask for Missing Information
As an internet service customer, I want the system to ask for relevant missing
information, so that my problem can be accurately assessed.

**Acceptance Criteria**
- The system shall identify information required to continue triage.
- It may request relevant details such as duration, connection type or basic equipment status.
- It shall not repeatedly ask for information already recorded.
- Collected information shall update workflow state.

## User Story 6: Receive an Appropriate Next Action
As an internet service customer, I want the system to determine an appropriate
next step, so that I know what should happen next.

**Acceptance Criteria**
- The system shall select only from approved actions.
- Actions may include guidance, clarification, outage information or ticket escalation.
- The workflow shall have defined limits and stop conditions.
- The system shall stop or hand over when no further approved action is appropriate.

## User Story 7: Create a Support Ticket
As an internet service customer, I want my unresolved problem recorded as a
support ticket, so that a human support officer can follow up.

**Acceptance Criteria**
- A simulated ticket shall be created only when escalation conditions are satisfied.
- The ticket shall include the issue summary, category and relevant troubleshooting/status results.
- Required information shall be validated.
- The ticket shall indicate that human follow-up is required.
- No infrastructure changes shall occur after ticket creation.

## User Story 8: Track the Active Support Case
As an internet service customer, I want the system to maintain progress of my
current support case, so that I do not repeatedly provide the same information.

**Acceptance Criteria**
- The system shall maintain explicit case state.
- State may include the issue, category, collected information, guidance, status result, workflow stage and ticket status.
- Stored state shall support continuation of the current case.
- The system shall distinguish session state from persistent memory.

## User Story 9: Remember Justified Case Information
As a returning internet service customer, I want relevant approved information
from a previous support case retained, so that ongoing problems can be handled
more efficiently.

**Acceptance Criteria**
- Only justified information shall be retained.
- The purpose of retained information shall be documented.
- Access shall follow authorization rules.
- Retention and deletion rules shall be supported.
- Memory shall not independently make critical decisions.

## User Story 10: Maintain Safe and Controlled Operation
As a system owner or support officer, I want the AI agent to operate within
clearly defined boundaries, so that it cannot perform unauthorized or
high-impact actions.

**Acceptance Criteria**
- The agent shall use only explicitly approved tools.
- Maximum workflow iterations shall be enforced.
- Tool inputs and outputs shall be validated.
- Unauthorized requests shall be rejected safely.
- The system shall not execute arbitrary commands or control network infrastructure.
- Higher-impact actions shall require human approval.
- Useful workflow logs or traces shall be generated.
