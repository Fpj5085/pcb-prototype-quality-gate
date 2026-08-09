# M2 电源分配板 —— 端到端闭环公开示例

> **NOT FOR MANUFACTURING(不可直接制造)**

## 这个案例是什么

M2 是一块 5V/1A、一进二出的电源分配板:

- 6 个器件:J1 输入连接器、J2/J3 两个输出连接器(2.54mm 2×1 排针)、C1 大容量储能电容(10uF,靠近输入)、C2/C3 去耦电容(10uF,输出侧);
- 2 个网络:`+5V`、`GND`;
- 用途:把一路 5V/1A 直流输入分配给两路输出接口,板载储能与去耦,无 MCU 与通信逻辑。

它是本项目第一个真实跑通**完整闭环**的案例,因此被选作公开端到端演示。

## 真实闭环在哪一步做过

真实 M2 案例(在真实嘉立创 EDA 环境中)完整闭环如下,且**已真实发生并通过**:

1. 独立自动审核命中**且仅命中一个** blocker:`DECOUPLING_DISTANCE:J2:+5V` —— J2 输出口缺少足够近的旁路电容;距离 J2 最近的是 10uF 储能电容,不在 0.08–0.22uF 旁路容量范围内,评级为 `not_suitable_for_prototype`(当前不适合样板);
2. 白名单修正:计划 `ADD_LOCAL_BYPASS_CAP`,在 J2 附近新增一颗 100nF 旁路电容;
3. 在真实 EDA 中修改图纸 → 保存 → 重载 → 独立读回;
4. 复审:该 blocker 消失,评级提升为 `suitable_for_low_risk_prototype`(适合低风险样板)。

## 公开示例复现哪一段

本公开示例只复现上述闭环中**可离线运行**的一段链路:

> 中文需求 → 硬件规格(hardware-contract)→ 自动审核 → 评级

它**不**在此处自动画板、**不**执行任何 EDA 写入、**不**执行自动修正,也不伪造保存重载现场证据。真实闭环里的“EDA 画板/白名单修正/保存重载复验”一步已在真实环境完成,这里仅用清洗后的数据说明这一段链路长什么样、会产生什么结果。

## 如何运行

要求:Python 3.10+,零第三方依赖。

```powershell
python -B scripts/run-closed-loop-demo.py
```

加 `--now <ISO8601>` 可固定所有时间戳,使两次运行输出字节一致(可复现验证):

```powershell
python -B scripts/run-closed-loop-demo.py --now 2026-08-09T00:00:00+00:00
```

输出目录:`examples/m2-closed-loop/output/`

- `hardware-contract.json` —— 需求门禁产出的结构化硬件规格;
- `machine-review.json` / `prototype-review-report-zh.md` / `one-page-summary-zh.md` —— 审核结果(机器 JSON 与中文报告);
- `evidence-manifest.json` —— 输出文件的 SHA-256 清单;
- `demo-summary.zh.md` —— 一键汇总(需求→规格→审核→评级 + 真实闭环说明)。

退出码:全链路成功为 0;任一步失败为非 0,并在 stderr 打印错误。

## 预期输出

- 需求门禁状态:`requirements-incomplete`(fail-closed:缺失事实被记为未决项,不猜测;3 个组件、6 个信号、14 条未决项);
- 审核评级:`not_suitable_for_prototype`(当前不适合样板);
- blocker:**且仅一个** —— `DECOUPLING_DISTANCE:J2:+5V`(J2 输出口缺少合格旁路;最近电容为 C2 10uF,距 3.8mm,超 0.08–0.22uF 旁路范围);
- 附带 advisory(2,均为证据门,诚实标注离线范围):`EVIDENCE_INCOMPLETE:PERSISTENCE`(保存重载证据缺失)、`EVIDENCE_SCOPE:OFFLINE_FORECAST`(当前只是离线工程预测);
- pass(3):`TRACE_PASS:+5V`、`TRACE_PASS:GND`、`SCHEMATIC_TOPOLOGY`。

评级 `not_suitable_for_prototype` 由唯一的高置信度 blocker 决定——这与真实 M2 BEFORE 状态一致。

## 数据如何清洗

`examples/m2-closed-loop/` 下的两份输入数据为公开清洗/合成值,**不含任何私有 EDA 信息**:

- `requirements.zh.json`:中文需求的结构化表达(5V/1A 输入、一进二出、连接器、储能与去耦、接口与电压域、验收标准);省略了真实需求中未承诺的字段(如逐路额定电流、锁定器件型号/厂商/封装 UUID、MCU 管脚映射),以体现真实缺项并展示 fail-closed 的未决项记录;
- `design-data.json`:审核输入的归一化证据,坐标与网络为**合成值**(J1≈(-18.8,0)、J2≈(18.8,5)、J3≈(18.8,-5)、C1≈(-14,0)、C2/C3 输出侧),仅复现真实案例的**语义**——J2 附近最近的电容是 10uF 储能电容,不在旁路范围内,从而稳定命中唯一 blocker。

清洗边界:不包含真实 EDA UUID、primitive/library/device ID、审批 ID、token、截图路径、真实 receipts 或私有目录路径。全部数值均为合成/示例值,不代表任何私有设计。

## 声明

- NOT FOR MANUFACTURING;
- 本示例不构成打样放行、实物功能证明或 Manufacturing Release;
- 离线重放结果不代表当前真实 EDA 文档状态;真实闭环(含 EDA 画板、白名单修正、保存重载复验)只在真实环境中完成并通过,未在本示例内执行。
