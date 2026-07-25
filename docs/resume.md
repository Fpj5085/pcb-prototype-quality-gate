# Resume wording

These statements deliberately scope the benchmark to one evaluation fixture. They do not present `9/9` as general accuracy or recall.

## 中文（精简）

开发面向 Codex 与嘉立创EDA工作流的证据驱动 Prototype 质量门，覆盖电源、热、电流、封装、去耦、回流和 PCB 几何审核；在一个 28 器件 adversarial 评估 fixture 上命中 9/9 个预定义人工基准风险族，同时该 fixture 的 EDA DRC 为 0。输出可解释中文风险、整改条件和保存重载复验契约；该数字仅适用于此 fixture。

## 中文（项目说明）

将“AI 能画出原理图/PCB”和“设计值得打样”拆成两个独立门：第三方或环境适配器负责生成与读回，本项目负责 Draft/Prototype/Manufacturing Release 分级、证据归一化、确定性工程规则、评级和受限修正复验。在 28 器件小车控制器评估 fixture 上，审核引擎命中 9/9 个预置/人工基准风险族，包括 DRC=0 未覆盖的稳压余量、封装、电流保护、H 桥损耗、功率走线、去耦/储能、接口和回流问题。v0.1.0-alpha 不宣称通用自动修复或制造放行。

## English (concise)

Built an evidence-driven Prototype quality gate for Codex/JLCEDA workflows, covering power, thermal, current, footprint, decoupling, return-path, and PCB geometry checks. On one 28-component adversarial evaluation fixture whose EDA DRC reported zero findings, the engine detected all 9/9 predefined human-benchmark risk families. The metric is fixture-scoped, not a general accuracy claim.

## English (project description)

Separated “AI produced an editable schematic/PCB” from “the design is worth prototyping.” Third-party or environment adapters handle generation and readback, while this project provides Draft/Prototype/Manufacturing Release governance, normalized evidence, deterministic engineering rules, explainable ratings, and persistence-aware revalidation contracts. On a 28-component motor-controller evaluation fixture, the engine detected 9/9 seeded/manual benchmark risk families, including regulator headroom, package identity, protection current, H-bridge loss, power routing, decoupling/bulk storage, interface, and return-path risks not established by DRC. The alpha does not claim general autonomous repair or manufacturing release.

## Interview boundary

If asked what `9/9` means, answer: nine risk families were defined from the manual review of this one fixture, and the engine produced at least one matching finding in each family. It is a regression benchmark, not a population-level accuracy measurement.
