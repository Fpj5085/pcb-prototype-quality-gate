# 预期输出示例

以下内容是展示层示例。机器真值以对应 fixture 的 `expected.json` 和实际运行生成的 `machine-review.json` 为准。

## M2 BEFORE（离线 fixture）

```text
最终评级：当前不适合样板
blocker：1
advisory：0

主要问题：J2 的 +5V/GND 本地回路没有同时满足容量、网络配对和距离要求的 80–220nF 电容。
修正条件：使用已锁定的 100nF X7R 电容，连接 +5V 与 GND，并在保存重载后重新计算距离。
边界：这是离线 fixture 审核，不是现场 EDA 修改。
```

目标 finding：`DECOUPLING_DISTANCE:J2:+5V`。

## M2 AFTER successor（离线预测）

```text
预测评级：适合低风险样板
预测 blocker：0
预测 advisory：0

目标变化：新增的 100nF X7R 电容满足值、网络和预测距离门，目标 blocker 关闭。
fixture 状态：离线 successor 重放；另有独立门禁生成的最小公开摘要记录真实保存重载、独立读回、DRC 与重新审核结论。
实物边界：仍需人工确认和 5V/1A 负载、压降与温升测试。
```

当前 manifest 已链接门禁生成的最小公开摘要；该摘要证明保存重载、独立读回、连通性、板框、DRC 和重新审核结论，但不把上述离线预测 fixture 本身改写成现场证据。

## 28 器件 adversarial fixture

```text
最终评级：当前不适合样板

尽管该 fixture 的板框包含和 EDA DRC 为 0，仍存在电源余量/封装、保护电流、H 桥损耗、功率走线、去耦/储能、接口和回流风险。
基准说明：审核命中本 fixture 预定义的 9/9 个人工基准风险族；该数字不外推到其他设计。
```

## 输出文件

一次 CLI 审核生成：

- `machine-review.json` — 机器稳定评级和 findings；
- `prototype-review-report-zh.md` — 完整中文报告；
- `one-page-summary-zh.md` — 面向普通用户的摘要；
- `firmware-pin-map.csv` — 已提供的固件引脚映射；
- `screenshot-index.json` — 只读采集截图索引，通常为空；
- `evidence-manifest.json` — 输出哈希、来源和 `edaWrites: 0`。
