# Excluded files and source classes

These classes are outside the v0.1.0-alpha public candidate and must not be copied into the Git repository or release archive.

## Third-party software and documents

- EasyEDA Copilot source, distribution files, extension packages, caches or reverse-engineered output;
- JLCEDA/EasyEDA application code, gateways, binaries, SDK source or supplier catalog databases;
- manufacturer data-sheet PDFs, copied figures, full tables or archives;
- vendored dependency directories such as `node_modules` or a Python virtual environment.

## Private operating evidence

- live EDA project files and raw object dumps;
- screenshots, desktop recordings and image metadata;
- full machine/session logs, historical conversations and process dumps;
- workstation configuration, service state, ports, PIDs and local task state;
- credentials, cookies, tokens, authorization headers, passwords and private keys;
- project/page/object/library/device identifiers;
- approval, receipt, checkpoint, nonce, bundle and transaction values.

## Private implementation surfaces

- live Bridge/Gateway/wrapper implementations and configuration;
- delivery, approval, recovery, supervisor, daemon and watchdog code;
- local patched third-party components;
- one-off artifact builders that embed private paths or internal identities.

## Generated and large artifacts

- `.tmp-*`, `out/`, `__pycache__/`, `*.pyc`, `*.pyo`, logs and crash dumps;
- PDFs, images, EDA extension packages, executable/binary files and archives inside the repository;
- unexplained files larger than 1 MiB;
- the local `.git/` directory in the distributable ZIP.

## Evaluation-specific exclusions

- raw M2 working artifacts and approval/ChangeSet bindings;
- raw car-controller snapshots, screenshots and private evidence manifests;
- any claim that converts offline/pending M2 evidence into live save/reload proof.

Public evaluations contain only synthetic or sanitized inputs, expected outputs, status declarations and manifest templates. Official data-sheet facts are represented as link-only metadata.
