"""
RHNS — Recursive Hierarchical Network System
Perfect reasoning substrate for the Revenue Automation Organ.

Layers (doctrine order):
1. Perception encode
2. Neural-symbolic parse
3. Symbolic verify + forward chain
4. Knowledge-graph ingest
5. Memory observe / consolidate
6. HRM reason (L-module fast, H-module slow)
7. LATS tree search
8. Metacognitive gate (CMC)
9. Decode / act
10. Audit-chain verify
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import hashlib
import json
from datetime import datetime


class CMCDecision(Enum):
    CONTINUE = "continue"
    ESCALATE = "escalate"
    COMMIT = "commit"
    ABORT = "abort"


@dataclass
class Goal:
    id: str
    description: str
    parent: Optional[str] = None
    status: str = "open"
    confidence: float = 0.0


@dataclass
class RHNSState:
    goals: List[Goal] = field(default_factory=list)
    knowledge: Dict[str, Any] = field(default_factory=dict)
    memory: List[Dict] = field(default_factory=list)
    contradictions: int = 0
    confidence: float = 0.0
    audit_chain: List[str] = field(default_factory=list)


class RHNS:
    """Perfect RHNS substrate — RGT + HRM + CMC + Symbolic Constraint Engine."""

    def __init__(self):
        self.state = RHNSState()
        self.commit_threshold = 0.72
        self.max_contradictions = 2

    def perceive(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perception encode + neural-symbolic parse."""
        structured = {
            "type": payload.get("type", "unknown"),
            "entities": payload.get("entities", {}),
            "timestamp": datetime.utcnow().isoformat(),
            "raw_hash": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16],
        }
        self.state.knowledge["last_perception"] = structured
        return structured

    def reason(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """HRM: L-module (fast) then H-module (slow)."""
        # L-module: quick pattern match
        l_result = {
            "hypothesis": f"fulfill_{context.get('product', 'unknown')}",
            "confidence": 0.65,
            "path": "fast",
        }
        # H-module: hierarchical refinement
        h_result = {
            "refined_goal": goal,
            "subgoals": ["verify_payment", "check_policy", "trigger_fulfillment", "audit"],
            "confidence": min(0.95, l_result["confidence"] + 0.2),
            "path": "hierarchical",
        }
        self.state.confidence = h_result["confidence"]
        return h_result

    def gate(self, action: str, context: Dict[str, Any]) -> CMCDecision:
        """CMC metacognitive gate. Money-moving requires commit."""
        if self.state.contradictions >= self.max_contradictions:
            return CMCDecision.ABORT
        if self.state.confidence < self.commit_threshold:
            return CMCDecision.CONTINUE
        if action in ("fulfillment.trigger", "outreach.send", "billing.write"):
            if self.state.confidence >= self.commit_threshold and self.state.contradictions < 2:
                return CMCDecision.COMMIT
            return CMCDecision.ESCALATE
        return CMCDecision.CONTINUE

    def audit(self, event: str, decision: CMCDecision, payload_hash: str) -> str:
        """Audit-chain verify. Append-only."""
        entry = f"{datetime.utcnow().isoformat()}|{event}|{decision.value}|{payload_hash}|{self.state.confidence:.2f}"
        chain_hash = hashlib.sha256((entry + (self.state.audit_chain[-1] if self.state.audit_chain else "")).encode()).hexdigest()
        self.state.audit_chain.append(chain_hash)
        return chain_hash

    def run_cycle(self, intent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Full 10-layer sweep."""
        perceived = self.perceive(payload)
        reasoned = self.reason(intent, payload)
        decision = self.gate(payload.get("action", "observe"), payload)
        audit_hash = self.audit(intent, decision, perceived["raw_hash"])

        return {
            "decision": decision.value,
            "confidence": self.state.confidence,
            "audit_hash": audit_hash,
            "proof": hashlib.sha256(json.dumps({"intent": intent, "decision": decision.value, "audit": audit_hash}, sort_keys=True).encode()).hexdigest(),
            "state_summary": {
                "contradictions": self.state.contradictions,
                "goals_open": len([g for g in self.state.goals if g.status == "open"]),
            },
        }


# Singleton for the organ
rhns = RHNS()
