# Dependency-Aware Workflow Recovery

A Python implementation of dependency-aware recovery for autonomous fulfillment workflows.

## Problem

A fulfillment workflow can experience failures and uncertain external operations while its underlying data changes.

Restarting the entire workflow can repeat completed work, invalidate useful results, or duplicate external side effects.

The challenge is to recover safely without assuming that every previously completed operation is still valid.

## Solution

This project implements a dependency-aware recovery engine that distinguishes between:

- **Execution status:** Whether an operation completed, failed, or has an uncertain outcome.
- **Result validity:** Whether its output is still valid against the current workflow state.
- **External side effects:** Operations that may have succeeded externally and require reconciliation or compensation.

### Key Features

- Workflow and execution-state tracking.
- Dependency traversal using Breadth-First Search (BFS).
- Downstream result invalidation.
- Idempotent external reservation simulation.
- Reconciliation of uncertain reservation outcomes.
- Inventory version-change detection.
- Reservation compatibility checks against the current fulfillment plan.
- Reservation release and compensation for incompatible reservations.
- Protection against downstream execution when dependencies are invalid or unresolved.
- Automated unit and integration tests.

## Workflow

The fulfillment workflow consists of five dependent steps:

1. Retrieve inventory.
2. Calculate fulfillment plan.
3. Reserve inventory.
4. Generate shipping label.
5. Notify customer.

## Reservation Recovery Scenario

The project handles a scenario where:

1. An external inventory reservation succeeds, but its response times out.
2. The inventory version changes during recovery.
3. The recovery engine reconciles the uncertain reservation.
4. The confirmed reservation is checked against the newly calculated fulfillment plan.
5. If compatible, the reservation is retained.
6. If incompatible, the reservation is released and its outcome is verified before recovery continues.

Downstream steps remain blocked while reservation validity or compensation is unresolved.

## Technology

- Python 3.13
- unittest
- Git and GitHub
- GitHub Actions

## Running the Tests

Run the complete test suite:

```bash
python -m unittest discover -s tests -v
```

## Assumptions and Limitations

- The external reservation provider supports idempotency keys.
- The provider supports reservation-status lookups.
- The external reservation service is simulated in memory.
- Reservation release and compensation are simulated rather than integrated with a real provider.
- Workflow state and execution history are not persisted in a database.
- The project does not implement production-grade distributed transactions, durable retry policies, or automated recovery workers.
- Operations with unresolved outcomes remain blocked until they can be reconciled.

## CI

GitHub Actions runs the automated test suite on pushes and pull requests targeting the configured branches.

## Project Goal

Demonstrate how an autonomous fulfillment workflow can recover from failures and changing data while preserving valid completed work, reconciling external side effects, and preventing unsafe downstream execution.