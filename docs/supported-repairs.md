# Supported repairs

Statuses are deliberately conservative.

| Repair ID | Finding family | Allowed mutation | Required preconditions | Persistence/review gates | Status |
| --- | --- | --- | --- | --- | --- |
| `ADD_LOCAL_BYPASS_CAP` | Local decoupling | Addition-only capacitor and its validated schematic/PCB connections | Locked MPN/value/dielectric/voltage/package/pin-to-pad/nets; exact baseline; safe cross-document compensation; distance threshold | Immediate readback, save/close/reload, identity/net/distance check, ERC/connectivity/containment/DRC, fresh review | Public fail-closed plan CLI plus `live-evidence-gate-verified` scoped M2 execution; live adapter not bundled |
| `ADD_LOCAL_BULK_CAP` | Motor/load bulk storage | Addition-only polarized or non-polarized bulk capacitor and validated local loop | Locked electrical ratings/polarity/package/pads/nets; surge assumptions; exact baseline and compensation | Same as above plus voltage rating, polarity and loop-distance evidence | `planned-experimental` |
| `REPORT_ONLY_REGULATOR_REPLACEMENT` | Headroom/thermal/package | No automatic mutation | Full regulator and peripheral design must be frozen | Re-review only | `review-only` |
| `REPORT_ONLY_HBRIDGE_REPLACEMENT` | Driver loss/current/thermal | No automatic mutation | Motor continuous/peak/stall data and exact driver design required | Re-review only | `review-only` |
| `REPORT_ONLY_FUSE_SIZING` | Protection | No automatic mutation | Load curves, temperature derating and time-current evidence required | Re-review only | `review-only` |
| `REPORT_ONLY_POWER_REROUTE` | Trace/via/return path | No automatic mutation | Current loops, copper, geometry and compensation must be proven | Re-review only | `review-only` |
| `REPORT_ONLY_CONNECTOR_REMAP` | Interface/debug | No automatic mutation | Connector variant and pin sequence must be locked | Re-review only | `review-only` |

`live-evidence-gate-verified` is limited to the scoped, sanitized M2 bypass-cap case represented by the minimal public summary. It does not mean the public repository bundles the EDA mutation runtime, and the alpha does not claim general component replacement or whole-board automatic repair.

The portable planner is `scripts/plan-local-bypass.py`. It accepts an explicit machine review, its normalized evidence and an ordinary-language goal. It emits a deterministic `ADD_LOCAL_BYPASS_CAP` plan only when the decoupling blocker is the sole unresolved finding, all Prototype gates are explicit and passing, the target/net/distance requirement is unambiguous and no qualifying bypass already exists. Private project IDs and execution approvals are intentionally deferred to the separately audited environment adapter.
