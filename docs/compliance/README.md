# Compliance and Broker Readiness

This directory tracks requirements that affect ModelX design. It is not legal advice; broker/exchange implementation requirements must be verified with the chosen broker before live deployment.

## Current baseline

SEBI's retail algorithmic-trading framework is applicable to stock brokers from 1 April 2026. ModelX therefore must not be designed around bypassing broker controls.

Key design considerations:

- use the broker's supported API and authentication flow;
- preserve traceability of API-originated orders;
- do not expose an open/unrestricted trading API to the public internet;
- keep credentials/tokens out of source control;
- retain an audit trail for signals, approvals, orders and execution outcomes;
- confirm current broker requirements for retail algos, static IP/API access, authentication, algo identification/registration and rate/order limits;
- use only broker-supported functionality for automated exits and order management.

## Status

- [ ] Select broker and confirm current retail-algo onboarding requirements.
- [ ] Confirm whether this personal algo crosses any applicable registration/order-rate threshold.
- [ ] Confirm API authentication and static-IP requirements.
- [ ] Confirm order tagging/algo identifier requirements.
- [ ] Confirm allowed order types and automated exit mechanisms.
- [ ] Confirm current operational limits and kill-switch procedures.
- [ ] Complete paper-trading validation.
- [ ] Complete security review.
- [ ] Enable live execution only after all checks are satisfied.
