"""
KYB API Gateway
Entry point for the Digital Onboarding Channel.
Delegates all KYB logic to the agentic runner (agent.py).
Claude autonomously reasons and decides which tools to call.

POST /kyb/check  → runs agentic KYB and returns decision to onboarding channel
GET  /kyb/health → health check
"""

from flask import Flask, request, jsonify
from agent import run_kyb_agent

app = Flask(__name__)


@app.route("/kyb/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "kyb-mcp-gateway"})


@app.route("/kyb/check", methods=["POST"])
def kyb_check():
    """
    Called by the Digital Onboarding Channel.
    Expected request body:
    {
        "registration_number": "00445790"
    }
    """
    body = request.get_json()

    if not body or "registration_number" not in body:
        return jsonify({"error": "registration_number is required"}), 400

    reg = body["registration_number"].strip()

    # Delegate entirely to the KYB Agent — it decides what to do
    decision = run_kyb_agent(reg)

    if "error" in decision:
        return jsonify(decision), 502

    return jsonify(_format_onboarding_response(decision))


def _format_onboarding_response(decision: dict) -> dict:
    """
    Formats the KYB agent decision for the Digital Onboarding Channel.
    """
    kyb_decision = decision.get("kyb_decision", "REFER")

    if kyb_decision == "APPROVE":
        onboarding_status = "PROCEED"
        message = "KYB checks passed. You may proceed with the onboarding journey."
    elif kyb_decision == "REFER":
        onboarding_status = "ON_HOLD"
        message = "Your application is under review. A member of our team will be in touch."
    else:
        onboarding_status = "DECLINED"
        message = "We are unable to proceed with your application at this time."

    return {
        "onboarding_status": onboarding_status,
        "message": message,
        "kyb_decision": kyb_decision,
        "risk_rating": decision.get("risk_rating"),
        "business_name": decision.get("business", {}).get("name"),
        "registration_number": decision.get("business", {}).get("registration_number"),
        "requires_human_review": decision.get("requires_human_review", False),
        "next_actions": decision.get("next_actions", []),
        "reasoning_log": decision.get("reasoning_log", []),
        "timestamp": decision.get("timestamp")
    }


if __name__ == "__main__":
    app.run(debug=True, port=5001)
