# KYB MCP — Architecture & Flow

---

## Agentic Model — Building Block View

```mermaid
C4Container
    title KYB MCP — Agentic Model Building Block View

    Person(customer, "Business Customer", "Applies for onboarding via the digital channel")
    Person(analyst, "KYB Analyst", "Reviews REFER and REJECT cases. Makes final manual decision.")

    System_Boundary(onboarding, "Digital Onboarding Platform") {
        Container(webApp, "Onboarding Web App", "Web Application", "Customer-facing channel. Collects business registration number and presents KYB outcome.")
        Container(apiGateway, "KYB API Gateway", "Python / Flask", "Exposes POST /kyb/check. Authenticates requests and hands off to KYB Agent.")

        Container(kybAgent, "KYB Agent", "Claude AI — ReAct Loop", "Central intelligence. Autonomously reasons at each step, decides which tools to call, in what order, and when to stop early. Maintains context across all tool calls.")

        System_Boundary(mcpServer, "KYB MCP Server — Tool Registry") {
            Container(verifyBusiness, "verify_business", "Tool", "Verifies legal name, status, incorporation date and registered address.")
            Container(getDirectors, "get_directors", "Tool", "Retrieves active directors, PSC and UBO structure.")
            Container(sanctionsCheck, "screen_sanctions", "Tool", "Screens business and directors against OFAC, UN, EU and HM Treasury lists.")
            Container(riskScore, "calculate_risk_score", "Tool", "Calculates risk score and LOW / MEDIUM / HIGH rating.")
            Container(decisionEngine, "make_decision", "Tool", "Produces APPROVE / REFER / REJECT with next actions.")
        }
    }

    System_Ext(companiesHouse, "Companies House API", "UK government registry. Source of business and director data.")
    System_Ext(sanctionsList, "Sanctions Lists", "OFAC, UN Security Council, EU Consolidated List, HM Treasury.")
    System_Ext(entraId, "Microsoft Entra ID", "Identity provider. Authenticates onboarding channel users via SSO.")

    Rel(customer, webApp, "Submits registration number", "HTTPS")
    Rel(analyst, apiGateway, "Reviews and actions REFER/REJECT cases", "HTTPS")
    Rel(webApp, apiGateway, "POST /kyb/check", "HTTPS / JSON")
    Rel(apiGateway, entraId, "Validates token", "OIDC")
    Rel(apiGateway, kybAgent, "Passes KYB request to agent", "Internal")

    Rel(kybAgent, verifyBusiness, "Agent decides to call — always first", "MCP")
    Rel(kybAgent, getDirectors, "Agent calls if business is active", "MCP")
    Rel(kybAgent, sanctionsCheck, "Agent calls if directors retrieved", "MCP")
    Rel(kybAgent, riskScore, "Agent calls if no critical sanctions hit", "MCP")
    Rel(kybAgent, decisionEngine, "Agent calls to produce final decision", "MCP")

    Rel(verifyBusiness, companiesHouse, "GET /company/{reg}", "HTTPS")
    Rel(getDirectors, companiesHouse, "GET /company/{reg}/officers", "HTTPS")
    Rel(sanctionsCheck, sanctionsList, "Screen name and directors", "HTTPS / API")
```

---

## Agentic ReAct Loop — How the Agent Thinks

```mermaid
flowchart TD
    A([KYB Request Received]) --> B

    B["🧠 REASON\nWhat do I know?\nWhat do I need next?"]
    B --> C["⚙️ ACT\nCall a KYB tool via MCP"]
    C --> D["👁️ OBSERVE\nRead the tool result"]
    D --> E{Enough to decide?}

    E -->|No — need more data| B
    E -->|Early exit condition met| F
    E -->|All checks complete| G

    F["⚠️ EARLY EXIT\nExamples:\n• Business dissolved → REJECT now\n• Sanctions hit found → REJECT now\n• Critical data missing → REFER now"]

    G["✅ FINAL DECISION\nCall decision engine\nAPPROVE / REFER / REJECT"]

    F --> H
    G --> H

    H{Requires human review?}
    H -->|APPROVE| I([Onboarding proceeds])
    H -->|REFER| J([Route to KYB Analyst])
    H -->|REJECT| K([Application declined])

    style B fill:#ede9fe,stroke:#7c3aed
    style C fill:#dcfce7,stroke:#16a34a
    style D fill:#dbeafe,stroke:#3b82f6
    style F fill:#fee2e2,stroke:#dc2626
    style G fill:#bbf7d0,stroke:#16a34a
    style I fill:#bbf7d0,stroke:#16a34a
    style J fill:#ffedd5,stroke:#ea580c
    style K fill:#fee2e2,stroke:#dc2626
```

---

## Pipeline vs Agentic — Key Difference

| | Pipeline Model (Before) | Agentic Model (Now) |
|--|--------------------------|----------------------|
| **Tool execution** | Fixed sequence, always all tools | Agent decides what to call and when |
| **Early exit** | No — always runs all steps | Yes — stops as soon as decision is clear |
| **Reasoning** | None — deterministic | Yes — reasons after every tool result |
| **Flexibility** | Rigid | Adapts based on intermediate results |
| **Example** | Dissolved company still runs sanctions check | Dissolved company → REJECT immediately, no further checks |

---

## Decision Outcomes

| Decision | Risk Rating | Meaning | Next Step |
|----------|-------------|---------|-----------|
| **APPROVE** | LOW | Business passed all KYB checks | Proceed with onboarding |
| **REFER** | MEDIUM | Needs further review | Route to KYB Analyst |
| **REJECT** | HIGH / Sanctions hit | Business fails KYB requirements | Block onboarding, notify customer |
