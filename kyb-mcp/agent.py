"""
KYB Agent — Agentic ReAct Pattern
Uses Claude as the central intelligence. Claude autonomously:
- Decides which tools to call and in what order
- Reasons after each tool result
- Exits early when a decision is already clear
- Maintains full context across all tool calls
"""

import json
import os
import anthropic

from tools.verify_business import verify_business
from tools.get_directors import get_directors
from tools.sanctions_check import screen_sanctions
from tools.risk_score import calculate_risk_score
from tools.decision_engine import make_decision

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --- Tool definitions exposed to Claude ---
KYB_TOOLS = [
    {
        "name": "verify_business",
        "description": (
            "Verify a UK business by company registration number. "
            "Returns legal name, status (active/dissolved), incorporation date, "
            "SIC codes and registered address. Always call this first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "registration_number": {
                    "type": "string",
                    "description": "UK Companies House registration number e.g. 00445790"
                }
            },
            "required": ["registration_number"]
        }
    },
    {
        "name": "get_directors",
        "description": (
            "Retrieve active directors and persons with significant control (PSC/UBO) "
            "for a UK business. Only call this if the business is active."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "registration_number": {
                    "type": "string",
                    "description": "UK Companies House registration number"
                }
            },
            "required": ["registration_number"]
        }
    },
    {
        "name": "screen_sanctions",
        "description": (
            "Screen a business name and its directors against global sanctions lists "
            "(OFAC, UN, EU, HM Treasury). Call this after retrieving directors. "
            "If any hit is found, you should consider an immediate REJECT."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_name": {"type": "string"},
                "directors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of director full names"
                }
            },
            "required": ["business_name", "directors"]
        }
    },
    {
        "name": "calculate_risk_score",
        "description": (
            "Calculate a risk score (LOW/MEDIUM/HIGH) based on business, "
            "directors and sanctions data. Only call this if sanctions check is clear."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_data": {"type": "object"},
                "directors_data": {"type": "object"},
                "sanctions_data": {"type": "object"}
            },
            "required": ["business_data", "directors_data", "sanctions_data"]
        }
    },
    {
        "name": "make_decision",
        "description": (
            "Produce the final KYB decision (APPROVE/REFER/REJECT) with supporting "
            "details and next actions for human review. Call this as the final step."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_data": {"type": "object"},
                "directors_data": {"type": "object"},
                "sanctions_data": {"type": "object"},
                "risk_data": {"type": "object"}
            },
            "required": ["business_data", "directors_data", "sanctions_data", "risk_data"]
        }
    }
]

SYSTEM_PROMPT = """You are a KYB (Know Your Business) compliance agent for a UK digital onboarding platform.

Your job is to assess whether a business should be APPROVED, REFERRED for human review, or REJECTED.

Follow this reasoning approach at every step:
1. Always start by verifying the business.
2. If the business is dissolved or not found — REJECT immediately. Do not call further tools.
3. If the business is active — retrieve directors.
4. Screen the business and directors against sanctions lists.
5. If any sanctions hit is found — REJECT immediately. Do not call further tools.
6. If no sanctions hits — calculate the risk score.
7. Make the final decision.

Be efficient. Do not call tools you do not need based on what you already know.
Always call make_decision as your final action to produce the structured output."""


def _execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Routes Claude's tool calls to the actual tool implementations."""
    if tool_name == "verify_business":
        return verify_business(tool_input["registration_number"])
    elif tool_name == "get_directors":
        return get_directors(tool_input["registration_number"])
    elif tool_name == "screen_sanctions":
        return screen_sanctions(tool_input["business_name"], tool_input.get("directors", []))
    elif tool_name == "calculate_risk_score":
        return calculate_risk_score(
            tool_input["business_data"],
            tool_input["directors_data"],
            tool_input["sanctions_data"]
        )
    elif tool_name == "make_decision":
        return make_decision(
            tool_input["business_data"],
            tool_input["directors_data"],
            tool_input["sanctions_data"],
            tool_input["risk_data"]
        )
    return {"error": f"Unknown tool: {tool_name}"}


def run_kyb_agent(registration_number: str) -> dict:
    """
    Runs the KYB agent using Claude's ReAct loop.
    Claude autonomously decides which tools to call and when to stop.
    """
    if not ANTHROPIC_API_KEY:
        return _run_mock_agent(registration_number)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = [
        {
            "role": "user",
            "content": f"Run a full KYB check for UK company registration number: {registration_number}"
        }
    ]

    # ReAct loop — continues until Claude stops calling tools
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=KYB_TOOLS,
            messages=messages
        )

        # Add Claude's response to message history
        messages.append({"role": "assistant", "content": response.content})

        # If Claude has finished (no more tool calls) — extract final answer
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    try:
                        return json.loads(block.text)
                    except Exception:
                        return {"kyb_decision": "REFER", "message": block.text, "requires_human_review": True}

        # Process tool calls and feed results back to Claude
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = _execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

                # If make_decision was called — this is the final result
                if block.name == "make_decision":
                    return result

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return {"error": "Agent did not produce a decision", "requires_human_review": True}


def _run_mock_agent(registration_number: str) -> dict:
    """
    Mock agentic run for testing without an Anthropic API key.
    Simulates the ReAct reasoning logic locally.
    """
    reasoning_log = []

    # Step 1 — REASON: I need to verify the business first
    reasoning_log.append("REASON: Starting KYB. Must verify business first.")
    business = verify_business(registration_number)
    reasoning_log.append(f"OBSERVE: Business status = {business.get('status')}")

    # Early exit — dissolved
    if business.get("status") != "active":
        reasoning_log.append("REASON: Business is not active. Early REJECT — no further checks needed.")
        directors = {"directors": [], "persons_with_significant_control": []}
        sanctions = {"hit_count": 0, "clear": True, "hits": [], "lists_checked": []}
        risk = {"rating": "HIGH", "score": 100, "factors": [{"factor": "Business is not active", "severity": "HIGH", "weight": 100}]}
        result = make_decision(business, directors, sanctions, risk)
        result["reasoning_log"] = reasoning_log
        return result

    # Step 2 — REASON: Business is active, get directors
    reasoning_log.append("REASON: Business is active. Retrieving directors.")
    directors = get_directors(registration_number)
    director_names = [d["name"] for d in directors.get("directors", [])]
    reasoning_log.append(f"OBSERVE: Found {len(director_names)} director(s).")

    # Step 3 — REASON: Screen sanctions
    reasoning_log.append("REASON: Screening business and directors against sanctions lists.")
    sanctions = screen_sanctions(business.get("name", ""), director_names)
    reasoning_log.append(f"OBSERVE: Sanctions hits = {sanctions.get('hit_count')}")

    # Early exit — sanctions hit
    if not sanctions.get("clear"):
        reasoning_log.append("REASON: Sanctions hit found. Early REJECT — no further checks needed.")
        risk = {"rating": "HIGH", "score": 100, "factors": [{"factor": "Sanctions hit detected", "severity": "CRITICAL", "weight": 100}]}
        result = make_decision(business, directors, sanctions, risk)
        result["reasoning_log"] = reasoning_log
        return result

    # Step 4 — REASON: No sanctions hits, calculate risk
    reasoning_log.append("REASON: Sanctions clear. Calculating risk score.")
    risk = calculate_risk_score(business, directors, sanctions)
    reasoning_log.append(f"OBSERVE: Risk rating = {risk.get('rating')}, score = {risk.get('score')}")

    # Step 5 — Final decision
    reasoning_log.append("REASON: All checks complete. Making final decision.")
    result = make_decision(business, directors, sanctions, risk)
    result["reasoning_log"] = reasoning_log
    return result
