# Project Charter — ServiceFlow

**Project Title:** ServiceFlow: An AI-Powered Internet Service Help-Desk Triage Agent

## Project Overview
Internet service customers frequently experience problems such as complete loss
of connectivity, slow internet speeds, intermittent connections, and router or
modem-related issues. When such problems occur, customers often need assistance
in determining the nature of the problem and whether it can be resolved through
basic troubleshooting or requires escalation to technical support.

ServiceFlow is a bounded AI-powered help-desk triage system designed to assist
internet service customers in reporting and troubleshooting service problems.
The system interprets a customer's problem description, classifies the issue,
retrieves relevant troubleshooting guidance from an approved knowledge base,
checks a simulated network or outage status, and determines an appropriate next
step. Where the problem cannot be resolved, the system may create and route a
simulated support ticket for human follow-up.

## Problem Statement
Internet service providers receive customer complaints including no internet
connection, slow connectivity, unstable connections and equipment-related
problems. Initial support requires identifying the issue, checking whether a
known outage exists, providing appropriate guidance and escalating unresolved
cases. These activities can be repetitive and time-consuming, while a
general-purpose AI chatbot may hallucinate service status or take actions
outside its authority. A controlled AI-assisted system is therefore needed to
triage problems using approved knowledge and explicit software tools while
maintaining clear operational limits.

## Target Users
Primary users are internet service customers experiencing connectivity or
service-related problems. A secondary user is the help-desk or technical
support officer who receives and follows up on escalated support tickets.

## Current Pain Points
- Customers may not know whether a problem is caused by their equipment or a wider outage.
- Common troubleshooting requests are repetitive for support staff.
- Customers may receive inconsistent or generic guidance.
- Customers may be uncertain whether a known service disruption exists.
- Escalated cases may contain incomplete information.
- Unresolved cases may experience delays before appropriate routing.

## Proposed AI-Native Solution
A customer describes an internet problem in natural language. The AI
interprets and classifies the issue, retrieves relevant guidance from an
approved knowledge base, and may request a simulated service-status check.
Based on retrieved evidence and approved tool results, the system may provide
troubleshooting guidance, ask for missing information, report a simulated
known outage, or create and route a simulated support ticket. The system
operates within predefined actions, permissions and limits rather than as an
unrestricted autonomous agent.

## Why AI is Appropriate
- Understanding differently worded natural-language service complaints.
- Classifying supported issue categories.
- Retrieving and synthesizing relevant troubleshooting information.
- Identifying missing information needed to continue a case.
- Selecting among approved next actions within a bounded workflow.
- Generating a clear case summary for escalation.

AI will not be responsible for authoritative service-status data, authorization
decisions or direct control of network infrastructure.

## Scope
The initial scope covers no internet connection, slow internet, intermittent
connectivity, router or modem-related problems, and known or simulated service
outages. The system will use a controlled knowledge base and approved tools
for checking simulated service/outage status and creating/routing simulated
support tickets. Data will consist of public service-help content where
appropriate and team-created or synthetic incidents, outage records and
support-ticket data.

## Out of Scope and Safety Boundaries
- Direct control of routers, network devices or infrastructure.
- Automatic service disconnection or reconnection.
- Network configuration changes.
- Arbitrary system command execution.
- Unauthorized access to confidential customer information.
- High-impact actions without human approval.
- Claims of outages without evidence from approved status data.

## Assumptions
- A controlled troubleshooting knowledge base can be created and maintained.
- Synthetic or simulated outage and service-status records will be available.
- Users provide a basic description of their problem.
- An approved foundation model is accessible.
- Simulated status and ticketing tools are available for testing.
- Human support staff remain responsible for escalated cases.

## Constraints
- Eight-week academic timeline.
- Limited access to real ISP infrastructure and customer data.
- Use of synthetic or public data instead of confidential information.
- Limited computing, API and model-access resources.
- Need for bounded, explainable AI behavior.
- Need for controlled evaluation and safety mechanisms.

## Success Criteria
1. Correctly interpret and classify common supported internet problems.
2. Retrieve relevant information from the approved troubleshooting knowledge base.
3. Provide grounded responses and handle unsupported questions appropriately.
4. Use the simulated service-status tool correctly when required.
5. Request missing information when necessary.
6. Create and route a simulated ticket when escalation conditions are satisfied.
7. Operate through a bounded multi-step workflow with approved tools and stop conditions.
8. Maintain explicit state for an active support case.
9. Implement one justified persistent-memory capability.
10. Prevent unauthorized and prohibited actions.
11. Produce useful workflow traces or logs.
12. Support evaluation using normal, edge, failure and adversarial scenarios.

## Minimum Proposal Statement
Our system helps internet service customers triage and report connectivity
problems through a guided, AI-assisted workflow. AI is used for understanding
and classifying user-reported issues, retrieving relevant troubleshooting
information from an approved knowledge base, and selecting among approved next
actions. Deterministic software remains responsible for data validation,
service-status retrieval, authorization, ticket creation and workflow limits.
The agent may use approved tools to search the troubleshooting knowledge base,
check simulated service or outage status, and create or route a support
ticket, but may not remotely control infrastructure or automatically
disconnect, reconnect or modify any service. We will build and evaluate the
system using public service-help content together with team-created or
synthetic service incidents, outage records and support-ticket data.

## Expected Outcome
By the end of the eight-week project, ServiceFlow is expected to demonstrate a
small but credible AI-native and agentic application that progresses from a
foundation-model capability to a grounded system using retrieval, approved
tools and a bounded multi-step workflow. Deterministic software and human
operators will retain control over service data, authorization and
higher-impact actions.
