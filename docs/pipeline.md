# 端到端审计编排入口

本入口把“输入一个 Draft/现场读回适配器产出的归一化 JSON → 独立审核 → 可选生成唯一白名单修正预览”固定成一个可复现命令。

它是**编排入口**，不是 EDA 驱动器：不连接嘉立创 EDA，不申请审批，不执行 mutation，不保存、不关闭、不重载设计。

## 运行

在仓库根目录执行：

```powershell
python scripts/run-review-pipeline.py `
  --input tests/review/fixtures/synthetic-safe-input.json `
  --profiles src/review/component-profiles.json `
  --output out/pipeline-run
```

输出：

- `pipeline-run.json`：本次流程的边界、评级、输出位置和写入计数；
- `normalized-input.json`：脱敏后的归一化输入；
- `review/machine-review.json` 及用户报告：独立审核结果。

## 生成白名单修正预览

只有在已有审核结果和独立证据满足当前唯一白名单规则时，才可以额外生成不可变计划：

```powershell
python scripts/run-review-pipeline.py `
  --input <normalized-or-raw-design.json> `
  --profiles src/review/component-profiles.json `
  --output out/pipeline-before `
  --repair-evidence <current-readback-evidence.json> `
  --goal "在输出接口附近增加100nF本地旁路电容并重新复验"
```

输出 `repair-plan.json` 的状态是 `immutable-preview`，并明确：

- `approval=required-before-adapter-execution`；
- `execution=not-executed`；
- 当前修正类型仅为 `ADD_LOCAL_BYPASS_CAP`；
- 私有 EDA target ID 不进入公开计划。

## 适配器交接契约

仓库现在发布一个严格的只读证据包契约：

- Schema：`pcb-prototype-quality-gate-readonly-adapter/1.0`；
- JSON Schema：[readonly-adapter-envelope.schema.json](../schemas/readonly-adapter-envelope.schema.json)；
- 运行时检查：[readonly_adapter_contract.py](../src/review/readonly_adapter_contract.py)。

外部 Draft 生成器或 live EDA 适配器必须先独立读回当前状态，再交给入口。完整证据包必须提供：

1. 脱敏的目标身份指纹：工程、原理图页、PCB 页各一个 SHA-256；
2. 原理图状态哈希、PCB 状态哈希和归一化设计内容哈希；
3. `checks` 六项 Prototype 状态门；
4. 器件、网络、几何、规则计算和假设的显式字段；
5. `savedReloaded=true`、`independentReadback=true`、`targetStable=true`；
6. `readOnly=true`、`edaWrites=0`；
7. 失败、超时或状态未知时必须令 `capture=null`、`normalizedDesign=null`，并提供至少一个白名单分类错误；不得携带部分现场状态，也不得用生成器 ACK 代替读回。

入口通过 `--adapter-evidence <envelope.json>` 消费该证据包，并要求它的
`normalizedDesign` 与 `--input` **字节无关但结构完全相等**；哈希不一致、字段缺失、目标漂移或任何不完整状态都会 fail closed。适配器包只用于当前只读审核，不获得审批或写入权限。

适配器完成写入后，仍必须在入口之外执行受控的：

```text
用户查看 immutable ChangeSet
→ 一次性明确批准
→ 适配器按 target-bound 计划写入
→ 即时读回
→ 保存 / 关闭 / 重载
→ 独立二次读回
→ 重新运行本入口
```

任一阶段状态未知，都必须先读回确认，禁止盲目重试。

## 当前边界

- 入口可自动完成：规范化、独立审核、报告生成、唯一白名单计划预览；
- 入口不会自动完成：调用 EasyEDA Copilot、选择 EDA 窗口、真实 EDA 写入、审批、保存重载、制造输出；
- 真实 Gateway/Bridge 仍是独立环境集成，不得把它的 ACK 当作审计证据；
- `suitable_for_low_risk_prototype` 仍不代表实物验证、Manufacturing Release、上传、下单或支付。
