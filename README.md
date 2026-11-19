# Dependency-Aware Workflow Recovery

A Python implementation of dependency-aware recovery for autonomous fulfillment workflows.

## Problem

A workflow can experience failures and uncertain external operations while its underlying data changes.

Restarting everything can repeat completed work or duplicate external side effects.

## Solution

This project implements:

- Workflow and execution state tracking.
- Dependency traversal using BFS.
- Downstream invalidation.
- Idempotent reservation simulation.
- Reconciliation of uncertain external operations.
- Inventory version-change detection.
- Recovery decisions based on dependency validity.

## Workflow

1. Retrieve inventory.
2. Calculate fulfillment plan.
3. Reserve inventory.
4. Generate shipping label.
5. Notify customer.

## Technology

- Python 3.13
- unittest
- Git
- GitHub Actions

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Assumptions and limitations

- The external reservation provider supports idempotency keys.
- The provider supports reservation-status lookups.
- The external service is simulated in memory.
- The project does not implement distributed persistence,
  automatic compensation, or production retry policies.
- Uncertain operations that cannot be reconciled remain blocked.

## CI

GitHub Actions runs the automated test suite on pushes
and pull requests targeting main and develop.
