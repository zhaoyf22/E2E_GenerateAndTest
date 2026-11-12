# Kubernetes Pack Rules (stub)

- Batch 2 will add Chainsaw, Testkube TestWorkflow, Terratest, Toxiproxy, Tracetest, and Chaos Mesh templates.
- Use namespace isolation and cleanup; never run destructive tests against production.
- Assert resource state, events, logs, and OTel traces; not just `kubectl apply` success.
- Testkube is the orchestration layer; Chainsaw is the declarative E2E layer.
- Cap blast radius for chaos experiments; always define steady-state and rollback.
