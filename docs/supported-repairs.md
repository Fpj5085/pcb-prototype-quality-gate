# Supported repairs

Statuses are deliberately conservative.

| Repair ID | Finding family | Allowed mutation | Required preconditions | Persistence/review gates | Status |
| --- | --- | --- | --- | --- | --- |
| `ADD_LOCAL_BYPASS_CAP` | Local decoupling | Addition-only capacitor and its validated schematic/PCB connections | Locked MPN/value/dielectric/voltage/package/pin-to-pad/nets; exact baseline; safe cross-document compensation; distance threshold | Immediate readback, save/close/reload, identity/net/distance check, ERC/connectivity/containment/DRC, fresh review | `prepared-not-live-verified` in the public M2 successor eval |
| `ADD_LOCAL_BULK_CAP` | Motor/load bulk storage | Addition-only polarized or non-polarized bulk capacitor and validated local loop | Locked electrical ratings/polarity/package/pads/nets; surge assumptions; exact baseline and compensation | Same as above plus voltage rating, polarity and loop-distance evidence | `planned-experimental` |
| `REPORT_ONLY_REGULATOR_REPLACEMENT` | Headroom/thermal/package | No automatic mutation | Full regulator and peripheral design must be frozen | Re-review only | `review-only` |
| `REPORT_ONLY_HBRIDGE_REPLACEMENT` | Driver loss/current/thermal | No automatic mutation | Motor continuous/peak/stall data and exact driver design required | Re-review only | `review-only` |
| `REPORT_ONLY_FUSE_SIZING` | Protection | No automatic mutation | Load curves, temperature derating and time-current evidence required | Re-review only | `review-only` |
| `REPORT_ONLY_POWER_REROUTE` | Trace/via/return path | No automatic mutation | Current loops, copper, geometry and compensation must be proven | Re-review only | `review-only` |
| `REPORT_ONLY_CONNECTOR_REMAP` | Interface/debug | No automatic mutation | Connector variant and pin sequence must be locked | Re-review only | `review-only` |

`prepared-not-live-verified` means that an immutable synthetic successor and acceptance contract exist, not that a live EDA save/reload repair has been demonstrated. The public alpha does not claim general component replacement or whole-board automatic repair.
