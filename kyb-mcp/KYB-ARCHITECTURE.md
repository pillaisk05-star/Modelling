# KYB MCP — Architecture & Flow

## Building Block View

```mermaid
C4Container
    title KYB MCP — Building Block View

    Person(customer, "Business Customer", "Applies for onboarding via the digital channel")
    Person(analyst, "KYB Analyst", "Reviews REFER and REJECT cases. Makes final manual decision.")

    System_Boundary(onboarding, "Digital Onboarding Platform") {
        Container(webApp, "Onboarding Web App", "Web Application", "Customer-facing channel. Collects business registration number and presents KYB outcome.")
        Container(apiGateway, "KYB API Gateway", "Python / Flask", "Exposes POST /kyb/check. Authenticates requests and orchestrates the KYB process.")
        Container(kybAgent, "KYB Agent", "Claude AI", "Reasons over KYB results. Interprets risk and routes to appropriate outcome.")

        System_Boundary(mcpServer, "KYB MCP Server") {
            Container(verifyBusiness, "Business Verification", "Python", "Verifies legal name, status, incorporation date and registered address.")
            Container(getDirectors, "Directors & Ownership", "Python", "Retrieves active directors, PSC and UBO structure.")
            Container(sanctionsCheck, "Sanctions Screening", "Python", "Screens business and directors against OFAC, UN, EU and HM Treasury lists.")
            Container(riskScore, "Risk Scoring Engine", "Python", "Calculates a risk score and LOW / MEDIUM / HIGH rating from all KYB data.")
            Container(decisionEngine, "Decision Engine", "Python", "Produces APPROVE / REFER / REJECT decision with next actions for human review.")
        }
    }

    System_Ext(companiesHouse, "Companies House API", "UK government registry. Source of business and director data.")
    System_Ext(sanctionsList, "Sanctions Lists", "OFAC, UN Security Council, EU Consolidated List, HM Treasury.")
    System_Ext(entraId, "Microsoft Entra ID", "Identity provider. Authenticates onboarding channel users via SSO.")

    Rel(customer, webApp, "Submits registration number", "HTTPS")
    Rel(analyst, apiGateway, "Reviews and actions REFER/REJECT cases", "HTTPS")

    Rel(webApp, apiGateway, "POST /kyb/check", "HTTPS / JSON")
    Rel(apiGateway, entraId, "Validates token", "OIDC")
    Rel(apiGateway, kybAgent, "Triggers KYB check")

    Rel(kybAgent, verifyBusiness, "Calls tool", "MCP")
    Rel(kybAgent, getDirectors, "Calls tool", "MCP")
    Rel(kybAgent, sanctionsCheck, "Calls tool", "MCP")
    Rel(kybAgent, riskScore, "Calls tool", "MCP")
    Rel(kybAgent, decisionEngine, "Calls tool", "MCP")

    Rel(verifyBusiness, companiesHouse, "GET /company/{reg}", "HTTPS")
    Rel(getDirectors, companiesHouse, "GET /company/{reg}/officers", "HTTPS")
    Rel(sanctionsCheck, sanctionsList, "Screen name and directors", "HTTPS / API")
```

---

## Text Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  DIGITAL ONBOARDING CHANNEL                     │
│            (Web App — Business Customer facing)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │  ① Submits KYB request
                             │  (registration number, business name)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KYB API GATEWAY                              │
│              (Flask REST API — POST /kyb/check)                 │
│         Accepts request, authenticates, triggers agent          │
└────────────────────────────┬────────────────────────────────────┘
                             │  ② Triggers KYB Agent
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      KYB AGENT (Claude)                         │
│   Orchestrates the KYB flow, calls MCP tools in sequence,       │
│   interprets results and determines referral path               │
└────────────────────────────┬────────────────────────────────────┘
                             │  ③ Calls run_full_kyb tool
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     KYB MCP SERVER                              │
│                                                                 │
│   ④ verify_business ──────► Companies House API (UK)            │
│          │                  Returns: name, status, address      │
│          ▼                                                      │
│   ⑤ get_directors ────────► Companies House API (UK)            │
│          │                  Returns: directors, PSC/UBO         │
│          ▼                                                      │
│   ⑥ screen_sanctions ─────► OFAC / UN / EU / HM Treasury       │
│          │                  Returns: hits, clear flag           │
│          ▼                                                      │
│   ⑦ calculate_risk_score   (Internal scoring engine)            │
│          │                  Returns: score, LOW/MEDIUM/HIGH     │
│          ▼                                                      │
│   ⑧ decision_engine        (Internal logic)                     │
│                             Returns: APPROVE / REFER / REJECT   │
└────────────────────────────┬────────────────────────────────────┘
                             │  ⑨ Returns KYB decision + details
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      KYB AGENT (Claude)                         │
│      Receives structured decision, formats response             │
└──────────┬──────────────────────────────────────────┬──────────┘
           │                                          │
    ⑩ APPROVE                              ⑩ REFER or REJECT
           │                                          │
           ▼                                          ▼
┌──────────────────────┐              ┌───────────────────────────┐
│  ONBOARDING CHANNEL  │              │     HUMAN REVIEWER        │
│  Proceeds with       │              │  KYB Analyst reviews case │
│  onboarding journey  │              │  Takes manual decision    │
└──────────────────────┘              │  Approves / Rejects       │
                                      └───────────────────────────┘
```

---

## Step-by-Step Flow

| Step | Who | What Happens |
|------|-----|-------------|
| ① | Business Customer | Fills in registration number on Digital Onboarding Channel |
| ② | Onboarding Channel | Sends POST /kyb/check to KYB API Gateway |
| ③ | KYB API Gateway | Authenticates request, triggers KYB Agent |
| ④ | KYB Agent | Calls `run_full_kyb` on MCP Server |
| ⑤ | MCP Server | Calls Companies House — verifies business status and details |
| ⑥ | MCP Server | Calls Companies House — retrieves directors and PSC/UBO |
| ⑦ | MCP Server | Screens business and directors against sanctions lists |
| ⑧ | MCP Server | Calculates risk score from all gathered data |
| ⑨ | MCP Server | Decision engine produces APPROVE / REFER / REJECT + next actions |
| ⑩ | KYB Agent | Returns structured decision back to API Gateway |
| ⑪ | API Gateway | Returns result to Onboarding Channel |
| ⑫a | Onboarding Channel | If APPROVE → continues onboarding journey |
| ⑫b | Onboarding Channel | If REFER/REJECT → notifies customer, routes case to KYB Analyst |
| ⑬ | Human Reviewer | Reviews REFER/REJECT cases, takes final decision |

---

## Decision Outcomes

| Decision | Risk Rating | Meaning | Next Step |
|----------|-------------|---------|-----------|
| **APPROVE** | LOW | Business passed all KYB checks | Proceed with onboarding |
| **REFER** | MEDIUM | Needs further review | Route to KYB Analyst |
| **REJECT** | HIGH / Sanctions hit | Business fails KYB requirements | Block onboarding, notify customer |
