# Supported repair policy

An automatic repair is eligible only when all of the following are true:

1. The finding belongs to a published allow-list entry.
2. Component identity, value, footprint, pin-to-pad mapping and target nets are locked.
3. The exact current baseline is captured immediately before mutation.
4. The plan states every created or changed object and prohibits unrelated changes.
5. Partial failure has a complete compensation path.
6. No timeout or unknown state is blindly retried.
7. Independent readback verifies the change before and after save/close/reload.
8. A fresh review confirms the target finding improved and other findings did not worsen.

See [`docs/supported-repairs.md`](../../../docs/supported-repairs.md) for the alpha allow-list and status of each repair family.
