"""
Full-stack Revenue Automation Organ runtime
Integrates Stripe webhook + RHNS substrate + fulfillment.
"""
import os
import json
import hmac
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify
from rhns import rhns, CMCDecision
from fulfillment import fulfill_order

app = Flask(__name__)

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
PRODUCT_MAP = {
    os.getenv("STRIPE_PRICE_ULTRA_LOW_LATENCY", ""): "ultra_low_latency",
    os.getenv("STRIPE_PRICE_ARCHITECT_MASTER", ""): "architect_master",
}


def verify_signature(payload: bytes, sig_header: str) -> bool:
    if not STRIPE_WEBHOOK_SECRET or not sig_header:
        return False
    try:
        parts = sig_header.split(",")
        timestamp = parts[0].split("=")[1]
        signatures = [p.split("=")[1] for p in parts[1:]]
        signed = f"{timestamp}.{payload.decode()}"
        expected = hmac.new(STRIPE_WEBHOOK_SECRET.encode(), signed.encode(), hashlib.sha256).hexdigest()
        return any(hmac.compare_digest(expected, s) for s in signatures)
    except Exception:
        return False


@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature", "")

    if not verify_signature(payload, sig):
        return jsonify({"error": "invalid signature"}), 400

    event = json.loads(payload)
    if event.get("type") != "checkout.session.completed":
        return jsonify({"status": "ignored"}), 200

    session = event["data"]["object"]
    email = session.get("customer_details", {}).get("email")
    amount = session.get("amount_total", 0) / 100
    price_id = (session.get("metadata") or {}).get("price_id") or "unknown"
    product = PRODUCT_MAP.get(price_id, "unknown")

    # RHNS full cycle before any side effect
    cycle = rhns.run_cycle(
        intent="fulfill_paid_order",
        payload={
            "action": "fulfillment.trigger",
            "product": product,
            "email": email,
            "amount": amount,
            "session_id": session.get("id"),
            "type": "stripe.checkout.completed",
        },
    )

    if cycle["decision"] != CMCDecision.COMMIT.value:
        return jsonify({
            "status": "gated",
            "rhns": cycle,
            "message": "CMC did not commit — no fulfillment side effects",
        }), 202

    # Commit path: fulfill
    result = fulfill_order({
        "product": product,
        "email": email,
        "amount": amount,
        "session_id": session.get("id"),
        "rhns_proof": cycle["proof"],
        "audit_hash": cycle["audit_hash"],
        "timestamp": datetime.utcnow().isoformat(),
    })

    return jsonify({
        "status": "fulfilled",
        "rhns": cycle,
        "fulfillment": result,
    }), 200


@app.route("/rhns/status", methods=["GET"])
def rhns_status():
    return jsonify({
        "confidence": rhns.state.confidence,
        "contradictions": rhns.state.contradictions,
        "audit_chain_len": len(rhns.state.audit_chain),
        "last_audit": rhns.state.audit_chain[-1] if rhns.state.audit_chain else None,
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "organ": "revenue-automation", "rhns": "active"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
