# SysML v2 → FMU → Python 仿真

这个仓库演示一个**最小可跑通**的端到端流程：

> **SysML v2（文本）** → 导出 `sim_input.json` → **Modelica** 导出 **FMU** → **Python/FMPy** 运行 **FMI** 仿真 → 输出指标（0–100 时间）与 pass/fail

---

## 输出结果

```json
{
  "vehicle_id": "vehicle_A",
  "t_0_100_s": 6.649052742008338,
  "limit_s": 10.0,
  "pass": true,
  "start_values": {
    "m": 1650.0,
    "Pmax": 140000.0,
    "CdA": 0.62,
    "Crr": 0.012,
    "v0": 0.0,
    "vTarget": 27.78,
    "tMax": 30.0
  }
}
```

- `t_0_100_s`：仿真算出来的 0–100 km/h 时间（这里目标速度用 27.78 m/s）
- `pass`：是否满足需求阈值（默认 limit_s = 10.0s）

## 文件结构

### 1) `car_inputs.sysml`（SysML v2 输入：系统工程侧“源数据”）
- **这是什么**：一份 SysML v2 风格的文本文件（`.sysml`）。
- **有什么作用**：作为本 demo 的“系统工程权威输入”。我们在其中约定一个 `package SimulationInputs`，集中存放仿真所需的参数、工况、需求阈值，便于导出。
- **关键内容**：
  - `vehicle_A`：质量、最大功率、风阻面积、滚阻等（例：`mass_kg`, `Pmax_W`, `CdA`, `Crr`）
  - `scenario_0_100`：工况（例：`v0_mps`, `vTarget_mps`, `tMax_s`）
  - `REQ_ACC_001`：需求阈值（例：`limit_s`）

> 说明：未来接 SysML v2 API 后，这份文件可以换成真实模型仓库中的元素查询，但下游 JSON 结构保持不变。

---

### 2) `export_sysml_to_json.py`（Exporter：把 SysML 输入导出为 `sim_input.json`）
- **这是什么**：一个 Python 脚本（离线导出器）。
- **有什么作用**：在没有 SysML v2 Model Server / API 的情况下，用脚本“模拟导出接口”这一步：
  - 从 `car_inputs.sysml` 中提取需要的参数/工况/需求
  - 生成标准化的仿真输入文件 `sim_input.json`
- **关键内容**：
  - 只解析 `package SimulationInputs` 下固定结构（PoC），不做完整 SysML 语义解析（如 redefine/variant 等）
  - 输出 JSON 的字段结构与 `sim_input_schema.md` 一致

---

### 3) `sim_input_schema.md`（输入契约说明：`sim_input.json` 应该长什么样）
- **这是什么**：一份 Markdown 文档（接口/协议说明）。
- **有什么作用**：把 `sim_input.json` 的结构固定下来，形成“上游（SysML 导出）与下游（仿真脚本）之间的稳定契约”：
  - 未来你可以把 exporter 换成真正的 SysML v2 API 导出器
  - 只要输出 JSON 符合这个 schema，下游 `run_fmu.py` 就不用改
- **关键内容**：`vehicle` / `scenario` / `requirements` 三段字段定义。

---

### 4) `LongitudinalVehicle.mo`（Modelica 源模型：可计算的物理/动态模型模板）
- **这是什么**：Modelica 模型源文件（`.mo`）。
- **有什么作用**：定义“仿真会算什么”：
  - 这里是一个极简整车纵向动力学模型，输出速度 `v(t)`
  - 定义 FMU 可接受哪些参数（`parameter`），这些参数会在导出 FMU 后成为可注入变量
- **关键内容**：
  - `parameter Real m, Pmax, CdA, Crr, v0, vTarget, tMax ...`
  - 动力学方程：滚阻、风阻、牵引力 → 加速度 `a` → `der(v) = a`

> 说明：`.mo` 中的参数赋值是“默认值/模板值”。实际仿真时我们会用 `sim_input.json` 注入覆盖这些默认值。

---

### 5) `export_fmu.mos`（OpenModelica 构建脚本：把 `.mo` 打包成 `.fmu`）
- **这是什么**：OpenModelica 的脚本文件（`.mos`）。
- **有什么作用**：把导出 FMU 变成可重复的一条命令：
  - 加载 `LongitudinalVehicle.mo`
  - 编译并导出 `LongitudinalVehicle.fmu`（FMI 2.0 Co-Simulation）
- **关键内容**：
  - `loadFile("LongitudinalVehicle.mo")`
  - `buildModelFMU(LongitudinalVehicle, version="2.0", fmuType="cs")`

---

### 6) `LongitudinalVehicle.fmu`（导出产物：可运行的标准模型包）
- **这是什么**：FMU 文件（`.fmu`，本质是一个 zip 包）。
- **有什么作用**：作为“可交付、可跨工具运行”的仿真组件：
  - Python/FMPy 不直接跑 `.mo`，而是加载这个 `.fmu`
  - FMU 内含二进制代码（Windows 下是 `.dll`）+ `modelDescription.xml`
- **关键内容（FMU 内部）**：
  - `modelDescription.xml`：变量名、参数/输入/输出、单位、FMI 版本等
  - `binaries/win64/*.dll`：执行模型计算的二进制

> 说明：FMU 通常与平台相关（Windows 导出的 FMU 建议在 Windows 上运行）。

---

### 7) `mapping.yaml`（字段映射表：SysML/JSON 字段 ↔ FMU 变量名）
- **这是什么**：YAML 配置文件（映射表）。
- **有什么作用**：解决“系统工程命名”和“仿真模型变量命名”不一致的问题：
  - 左侧：`sim_input.json` 的字段路径（如 `vehicle.mass_kg`）
  - 右侧：FMU 暴露的变量名（如 `m`）
- **关键内容**：例如：
  - `vehicle.mass_kg: m`
  - `scenario.vTarget_mps: vTarget`

> 如何知道 FMU 变量名：运行 `python -m fmpy dump LongitudinalVehicle.fmu` 查看。

---

### 8) `sim_input.json`（仿真输入：由 exporter 生成的“本次仿真配置快照”）
- **这是什么**：JSON 文件（仿真输入快照）。
- **有什么作用**：承载“本次仿真要用的参数/工况/阈值”，是从 SysML 导出的中间产物：
  - 可版本管理、可留档、可追溯
  - 也便于未来做批量仿真（多组 JSON）
- **关键内容**：三块结构 `vehicle` / `scenario` / `requirements`

---

### 9) `run_fmu.py`（FMI runtime 执行器：加载 FMU、注入参数、跑仿真、算指标）
- **这是什么**：Python 脚本（仿真运行器）。
- **有什么作用**：真正执行仿真（数值求解），并输出可复现结果摘要：
  1) 读取 `sim_input.json`（本次输入）
  2) 读取 `mapping.yaml`（映射）
  3) 形成 `start_values` 注入 FMU
  4) 调用 FMPy `simulate_fmu` 运行仿真，取出 `time` 与 `v(t)`
  5) 从 `v(t)` 计算 0–100 时间 `t_0_100_s`
  6) 与阈值比较得到 pass/fail
- **关键内容**：
  - 输出 JSON 摘要（终端打印）
  - 写 `result.json`（结果留档）

---

### 10) `result.json`（仿真结果摘要：可追溯输出）
- **这是什么**：JSON 文件（仿真结果摘要）。
- **有什么作用**：作为验证证据链的一部分，便于：
  - 回写 SysML v2（把 `t_0_100_s` 与 pass/fail 作为 evidence）
  - 做回归测试（不同参数对比）
- **关键内容**：
  - `t_0_100_s`、`pass`、`limit_s`
  - `start_values`（本次注入的参数快照）

---

## 环境要求（Windows）

- Windows 10/11
- Python 3.10+（建议）
- OpenModelica（用于导出 FMU）
- Python 依赖：
  - `fmpy`
  - `pyyaml`
  - `numpy`

> FMU 通常与平台相关：Windows 导出的 FMU（包含 .dll）应在 Windows 上运行。

---

## 一键跑通

在仓库根目录执行以下命令：

### Step 1：从 SysML v2 导出仿真输入 JSON

```bash
python .\export_sysml_to_json.py .\car_inputs.sysml
```

会生成：`sim_input.json`

可查看：

```bash
type .\sim_input.json
```

### Step 2：导出 FMU（Modelica → FMU）

```bash
omc .\export_fmu.mos
```

会生成：`LongitudinalVehicle.fmu`

（可选）查看 FMU 暴露的变量名：

```bash
python -m fmpy dump .\LongitudinalVehicle.fmu
```

### Step 3：运行仿真（FMU → 结果）

```bash
python .\run_fmu.py
```

会生成：`result.json`，并在终端打印仿真结果摘要。

---

## 如何验证"真的是 SysML 在驱动仿真"

修改 `car_inputs.sysml` 中的参数，然后重复 Step 1 + Step 3：

### 示例：让车更重（加速变慢）

把：

```sysml
attribute mass_kg = 1650;
```

改成：

```sysml
attribute mass_kg = 2200;
```

然后运行：

```bash
python .\export_sysml_to_json.py .\car_inputs.sysml
python .\run_fmu.py
```

你会看到 `t_0_100_s` 变大，可能 `pass` 变为 `false`。
