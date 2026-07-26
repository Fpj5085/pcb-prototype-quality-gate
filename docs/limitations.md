# Limitations

- The intended product loop is ordinary-language need → real editable schematic/PCB → independent automated review → allow-listed correction → save/reload re-verification → plain-language prototype rating. This alpha independently runs the offline review portion; it does not bundle or certify every live step.
- Draft generation is an adapter boundary and may be replaced. No generator acknowledgement is treated as proof of editable EDA state, engineering correctness or persistence.
- Evaluation cases are synthetic or sanitized fixtures and do not establish universal accuracy.
- Rules provide conservative engineering screening, not certification or professional sign-off.
- Physical load, motor stall current, cable drop, ambient, airflow and duty cycle may be unknown and must be measured.
- No SI/PI, EMC, safety-category, creepage/clearance certification, environmental test, thermal-chamber test, assembly fit or lifetime proof is included.
- Manufacturer data, component identity and procurement availability can change.
- EDA APIs may acknowledge an operation before it appears in current readback or persists to storage.
- Save/close/reload is required but still does not prove physical behavior.
- Cross-document transactions on non-empty designs require exact recovery. Without a complete compensation boundary, mutation should not start.
- ERC, DRC, connectivity and containment are necessary but insufficient.
- Manufacturing files, upload, ordering, payment and manufacture are outside this alpha.
- The repository does not bundle or license third-party draft generators, EDA extensions, data sheets or supplier catalogs.
- The public plugin declares no live MCP server, workstation wrapper or EDA application integration; offline review is the independently runnable surface.
- The M2 BEFORE/AFTER pair remains pending. The AFTER successor is an offline forecast until a real EDA run provides complete, sanitized immediate-readback, save/close/reload, independent-readback, DRC and fresh Prototype-review evidence.

The adversarial fixture's `9/9` benchmark is scoped to nine seeded/manual risk families on that fixture only. It is not an accuracy, recall or certification claim for arbitrary boards.
