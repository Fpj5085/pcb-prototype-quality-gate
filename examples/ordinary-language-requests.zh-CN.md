# 普通中文请求示例

用户不需要提供项目 UUID、内部审批 ID、ChangeSet 或适配器命令。若输入是离线文件，只需指出仓库相对路径。

## 1. 审核一个安全合成 fixture

> 请按 Prototype 模式审核 `evals/synthetic-safe/input.json`。先告诉我是否值得打 2–5 块低风险样板，再列 blocker、advisory、关键假设和仍需做的实物测试。不要操作 EDA。

预期行为：运行只读离线审核，评级应与 fixture 的 `expected.json` 一致；仍明确说明软件审核不等于实物功能证明。

## 2. 查看 5V/1A 电源分配板 BEFORE

> 这是一个 NOT FOR MANUFACTURING 的 5V/1A 一进二出电源分配板。请审核 BEFORE 证据，重点检查输出附近的本地去耦；不要因为 DRC=0 就直接说能打样。

预期行为：报告唯一目标 blocker `DECOUPLING_DISTANCE:J2:+5V`，并说明需要同时满足容量、网络和几何距离。

## 3. 比较 BEFORE 与 AFTER successor

> 比较电源分配板 BEFORE 和 AFTER。确认 AFTER 只新增了合格的 100nF X7R 旁路电容，目标问题是否消失，其他风险有没有变差。没有真实保存重载证据时请明确写成离线预测。

预期行为：显示 blocker 预测从 1 变 0，但把执行状态保留为 pending/offline forecast；不宣称真实 EDA 修改已发生。

## 4. 审核 adversarial 小车控制器

> 这块双电机控制器的原理图和 PCB 可编辑，板框包含和 DRC 都通过。请判断是否值得打样，并解释 DRC 没覆盖的电源、热、电流、去耦、线宽、接口和回流风险。

预期行为：当前评级为 `not_suitable_for_prototype`。可以引用“本 fixture 命中 9/9 个预定义人工基准风险族”，同时明确这不是普遍准确率。

## 5. 请求受限修正计划

> 如果问题属于已经证明的白名单，请给出不可变修正计划、写前快照、失败补偿、保存关闭重载和重新审核条件；如果还没有真实验证，就只做计划，不执行通用自动修复。

预期行为：查阅支持状态，只对已满足前置条件的条目形成计划。`prepared-not-live-verified` 不等于可在任意非空设计上执行。
