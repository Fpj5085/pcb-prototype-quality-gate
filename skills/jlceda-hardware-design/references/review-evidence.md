# Prototype review evidence

A Prototype conclusion should be reproducible from normalized evidence. At minimum, capture:

- exact component manufacturer part number where critical;
- symbol, package and pin-to-pad evidence;
- supply minimum/maximum, current assumptions and protection ratings;
- regulator loss/headroom and thermal calculations;
- copper weight, minimum trace width, vias and return-path observations;
- decoupling and bulk-capacitance value, voltage rating, nets and distance;
- interface voltage limits and divider calculations;
- schematic/ERC, PCB connectivity, containment and strict DRC results;
- save, close, reload and independent readback status.

Evidence provenance should use official URLs and document titles. Link to third-party data sheets rather than redistributing PDFs.

Confidence and severity are separate. A high-confidence blocker fails closed. Missing critical evidence should lower confidence and prevent an unconditional low-risk rating.

For the repository-level contracts and privacy-safe public fields, see [Evidence schema](../../../docs/evidence-schema.md).
