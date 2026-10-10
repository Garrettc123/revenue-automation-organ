# Full-stack Revenue Automation Organ
# Perfect RHNS substrate embedded

## Architecture
```
Stripe webhook → RHNS 10-layer cycle → CMC gate → (commit only) → fulfillment
                     ↑
              RGT + HRM + Symbolic + Audit chain
```

## Perfect RHNS binding
- Perception encode + neural-symbolic parse
- HRM (L-module fast + H-module hierarchical)
- CMC gate: commit only if confidence ≥ 0.72 and contradictions < 2
- Money-moving hops (fulfillment.trigger) require explicit CMC commit
- Append-only audit chain on every decision
- Detach retains audit ledger

## Run
```bash
pip install -r requirements.txt
export STRIPE_WEBHOOK_SECRET=whsec_...
python src/app.py
```

## Endpoints
- POST /webhook — Stripe events (RHNS-gated)
- GET /rhns/status — live RHNS state
- GET /health — organ liveness

## Certification gates (BioForge)
- [x] Contract declared (bioforge-organ.yaml)
- [x] RHNS ports bound (rhns.py)
- [x] CMC commit required for side effects
- [x] Detach path defined
- [x] Audit ledger retained
- [ ] Live Stripe paid=true fulfillment (host-keyed)
