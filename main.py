# server.py
from typing import Literal, TypedDict
from fastmcp import FastMCP

mcp = FastMCP("Psychology Experiment Reproducer")


class MCPState(TypedDict):
    index: int
    experiments: list[str]
    exp_status: dict[str, Literal["impl", "exec", "done"]]
    done_report: bool


# Track which stage prompt to return on next_step
state: MCPState = {
    "index": -1,  # position within base stages (before per-experiment loop)
    "experiments": [],  # list of experiment ids, e.g., ["exp1a", "exp1b"]
    "exp_status": {},  # per-experiment phase: "impl", "exec", or "done"
    "done_report": False,
}

prompts = dict(
    overview="""
You are reconstructing the stimuli and flow of psychology experiments from a paper.
Process outline:
- Start with Preparation, then Step 1–4 in order; only move forward when each stage is done.
- Always cross-check the paper text and referenced figures; do not invent stimulus details.
- Every image stimulus node from the flowchart must have its own generated image (no bundling multiple stimuli into one picture). Do not add text/titles inside stimuli; if guidance text is needed, save per-trial .txt files instead.
- Canvas matters: set explicit resolution and background; use defaults only when unspecified.
- Prefer sympy/pyx for drawing; output SVG and matching JPG under output/<experiment-number>; add suffixes to filenames when you need to disambiguate (e.g., search).
- Use uv for env management (uv init, uv add, uv run). Avoid uv pip install.
- Work sequentially per experiment; add --limit and timeouts for quick checks; inspect JPGs and logs; iterate until visuals match the paper.
""",
    preparation="""
Preparation
- Inputs: markdown research paper with detailed methods; referenced figure files; any public data archives (zip/rar/tar.gz/xlsx/docx/etc.).
- Read the full paper (multiple passes if large).
- Enumerate all figures used as stimulus examples so you can reference them later; view them (use MCP/READ tools) to anchor parameters to real visuals.
""",
    step1_identification="""
Step 1: Experiment Identification
- List all experiments (Exp1, Exp1a, …) with numbering/names.
- Extract objectives and hypotheses for each.
- If the paper is large, read in passes but ensure full coverage.
""",
    step2_flowcharts="""
Step 2: Flowcharts to exp_design.md
- For each experiment, create a Mermaid graph with no parentheses in labels; label node types explicitly:
  * Image Stimulus, Text Stimulus, Interaction, Timing.
- Outside the graph, annotate nodes:
  * Text Stimulus: task instructions, guidance text, feedback.
  * Image Stimulus: composition/layout, elements, color/shape/size; cite figure examples.
  * User Interaction: exact actions (key/mouse/verbal) and recorded metrics (RT ms, accuracy %, choices, error types).
- If experiments are similar, list precise differences (variable controls, stimuli changes, metrics).
""",
    step3_visual_params="""
Step 3: Visual Stimulus Parameters (exp_design.md)
- For every image node: give number, description, and usage context.
- Insert paper quotes with blockquotes for parameter sources; map to corresponding figures.
- Inspect every example stimulus image (use tools) to ground details.
- Paper figures live in a separate folder referenced by the markdown; locate and view each linked figure.
- Specify required parameters to recreate stimuli: position (X,Y), shape, size, rotation, canvas resolution and background color (default white if unspecified), color values, transparency, border/fill.
- Mark which parameters are random vs. recorded/critical; for random-only, list all cases and probabilities; for recorded, list every case.
- 边框: 论文中是否要求具体的形状或者图形添加边框（默认无边框），如果需要请注明边框颜色和宽度
- 图形之间的关系，相对大小与相对位置: 如果论文中有提及图形之间的关系（例如大小比例，位置关系等），尤其对于多个图形组合的刺激，请务必注明这些关系，例如在一个圆形中抠出一个正方形，这个正方形的大小和圆形大小的关系，在圆形中的位置，朝向都需要注明。如果论文中语焉不详，请结合对应实验的参考图片进行推断。
- Visual angle → pixels: use paper’s screen size, resolution, viewing distance; if missing, default 17\" CRT, 1024x768, D=50cm, DPI≈75.3. Formulas:
  S = 2*D*tan(theta/2); P = S*DPI/2.54.

- Reference this sample outline (guide only) to ensure completeness:
```
# Psychology Experiment Analysis Report

## Step 1: Experiment Identification
- Experiment 1: Color Judgment Task
- Experiment 2: Shape Discrimination Task

## Step 2: Detailed Flowcharts

### Experiment 1 Flowchart
```mermaid
graph TD
    A[Start] --> B[Task Instructions]
    B --> C{Condition Check}
    C -->|Condition A| D[Stimulus A]
    C -->|Condition B| E[Stimulus B]
    D --> F[User Response A]
    E --> G[User Response B]
    F --> H[Data Recording]
    G --> H
    H --> I[End]
```

**Node Annotations:**
- Node B (Text Stimulus): "Please carefully observe the shapes on screen and judge their colors"
- Node D (Image Stimulus): "Red circle at screen center, diameter corresponds to 2 degrees visual angle"
- Node F (User Interaction): "Press F key for red, J key for blue, record reaction time and accuracy"

### Experiment 2 Flowchart
[Similar structure...]

**Experiment Difference Explanation:**
Experiment 2 reduced stimulus presentation time from 500ms to 250ms, increasing difficulty...

## Step 3: Visual Stimulus Parameters

### Image 1: Red Circle
- Usage Context: Color judgment task in Experiment 1
- Position: Screen center (X: 960, Y: 540)
- Shape: Circle
- Diameter: 2 degrees visual angle → 192 pixels
- Color: RGB(255, 0, 0)
- Rotation Angle: 0 degrees

### Image 2: Blue Square
[Detailed parameters...]
```

### Technical Specifications
- Mermaid syntax strictly compliant, avoiding compilation errors
- All size parameters dual-labeled (visual angle + pixels)
- Data metrics explicitly quantified
- Stimulus descriptions specific and reproducible
""",
    code_data_check="""
Code Generation - Step 1: Public Data Check
- Input requirements (use uv as env manager):
  * Paper in markdown format.
  * exp_design.md produced in Preparation.
  * Downloaded experiment public data (zip/rar/tar.gz/xlsx/docx/etc.); read ALL sheets/tables/files with Python scripts.
- Load all public data files with Python (read every tab/table in xlsx, every file in archives).
- Verify each expected parameter from preparation is recorded; adjust expectations pragmatically (document compromises or invented mappings).
- Cross-check design vs. data; re-read tagged figures to avoid misinterpretations (e.g., alignment, rotation).
- Add notes to exp_design.md: randomized vs. recorded vs. unused parameters, file-to-experiment mapping, actual column names and their parameter meanings. Do not delete earlier content.
- Stay in this verification loop until every experiment’s parameters are confirmed; only then proceed to coding.
""",
    code_guidelines='''
Code Generation Guidelines (applies to every experiment)
- Create experiment folder; run uv init there. Install deps via uv add; run via uv run.
- Prefer sympy and pyx for geometry-heavy stimuli; output SVG and JPG per image stimulus under output/<experiment-number>.
- Work one experiment at a time; add --limit for trial count; include debug logging of parameters per image.
- After coding an experiment, run quickly with timeout and small --limit to catch infinite loops; inspect JPGs and logs; iterate.
- Each image stimulus node → its own file (no multi-stimulus composites). Do not render text labels inside images; use filename suffixes if needed.
- Respect canvas size/background; match paper figures closely, not freeform guesses.
- 尤其是当出现多个图形的组合时，一定要注意回顾之前分析的参数，确保每个图形的位置，大小，朝向，相对大小位置关系都要正确。
- Extra requirements:
  * 对于 Preparation 阶段登记的每个图像刺激节点都要生成单独图片，保持画布大小和背景正确。
  * 不允许在图片里加文本 tag/title；若需注明 search job，把标识加到文件名。
  * 对于流程图中的文本刺激，引导语等，用 per-trial txt 保存，可用后缀区分。
- If you need a template for PyX drawing, adapt this example (adjust parameters instead of copying blindly):
```python
# uv add numpy scipy pyx
import numpy as np
from scipy.spatial.transform import Rotation as R
from pyx import canvas, path, color, style
import pyx.bitmap

# --------- 一点小几何封装（用 SciPy 做变换）---------

def rotate_points(points, angle_deg):
    """
    用 SciPy 把一组 2D 点绕原点旋转 angle_deg 角度。
    points: (N, 2) 数组
    """
    rot = R.from_euler("z", angle_deg, degrees=True)
    pts3d = np.column_stack([points, np.zeros(len(points))])  # 提升到 3D
    return rot.apply(pts3d)[:, :2]


# 以原点为中心的“+”号，由两条线段组成
def plus_shape(size):
    s = size
    segs = np.array([
        [[-s, 0], [s, 0]],   # 横线
        [[0, -s], [0, s]],   # 竖线
    ])
    return segs


# 用旋转得到 “X” 和 “/”
def x_shape(size):
    # 把 “+” 旋转 45° 就是 “X”
    return np.array([rotate_points(seg, 45) for seg in plus_shape(size)])


def slash_shape(size):
    # 取 “+” 中的横线，旋转 45°，得到斜杠 “/”
    base = plus_shape(size)[0]           # 只要横线那一段
    return rotate_points(base, 45)       # (2, 2)


# --------- 场景参数 ---------

ring_radius   = 3.0   # 圆环半径（决定八个小圆的位置）
circle_radius = 0.6   # 每个小圆半径
marker_size   = 0.35  # 圆里记号的线段长度

n_circles = 8
angles = np.linspace(0, 2*np.pi, n_circles, endpoint=False)
centers = np.stack([ring_radius*np.cos(angles),
                    ring_radius*np.sin(angles)], axis=1)

# SciPy 生成几何“记号”对象（都在局部坐标系，中心在原点）
plus_segments  = plus_shape(marker_size)
x_segments     = x_shape(marker_size)
slash_segment  = slash_shape(marker_size)

# 哪个圆是黄色，哪个圆里画 “/”
highlight_index = 4   # 左侧那个
slash_index     = 2   # 上方那个


# --------- 用 PyX 画图 ---------

c = canvas.canvas()
lw = style.linewidth(0.05)   # 线宽

# 中心 “+”
for seg in plus_segments:
    (x1, y1), (x2, y2) = seg
    c.stroke(path.line(x1, y1, x2, y2), [lw])

# 周围 8 个圆
for i, (cx, cy) in enumerate(centers):
    # 填充颜色：一个黄，其余灰
    fillcol = color.rgb(1, 1, 0) if i == highlight_index else color.rgb(0.85, 0.85, 0.85)
    circle_path = path.circle(cx, cy, circle_radius)
    c.fill(circle_path, [fillcol])
    c.stroke(circle_path, [lw])

    # 决定画 “X” 还是 “/”
    if i == slash_index:
        # 画一个斜杠
        (x1, y1), (x2, y2) = slash_segment + np.array([cx, cy])
        c.stroke(path.line(x1, y1, x2, y2), [lw])
    else:
        # 画一个 “X”（两条斜线）
        for seg in x_segments:
            (x1, y1), (x2, y2) = seg + np.array([cx, cy])
            c.stroke(path.line(x1, y1, x2, y2), [lw])

c.writeSVGfile("scipy_pyx_demo")
pyx.bitmap.render(c, "scipy_pyx_demo.jpg", dpi=300)
```
''',
    code_impl="""
Code Generation - Step 2: Implementation ({experiment})
- 按照“Code Generation Guidelines”逐条检查既有实现，确保不影响之前实验的复现代码。
- 请在不影响已完成的复现代码功能基础上，继续复现当前实验（{experiment}）记录的刺激，保持画布参数、输出目录和日志策略一致。
- 每完成一个实验，立即以小 --limit 运行并自查生成的 JPG 与调试日志。
""",
    code_exec="""
Code Execution - Step 3 ({experiment})
- Once a small batch passes, raise log level to reduce noise, remove timeout/limit, and generate all stimuli.
- Verify JPG count matches expectations for {experiment}. Read the JPGs to confirm fidelity.
- Do not move to the report stage until every experiment has completed full-size generation and validation.
""",
    report="""
Step 4: Report
- Write report.md summarizing coding difficulties, risks of deviation from original stimuli, and run instructions to reproduce images.
""",
)

base_keys = [
    "overview",
    "preparation",
    "step1_identification",
    "step2_flowcharts",
    "step3_visual_params",
    "code_data_check",
    "code_guidelines",
]


@mcp.tool
def init() -> str:
    """Return the overall task prompt and reset stage index."""
    global state
    state.update(
        {
            "index": 0,
            "experiments": [],
            "exp_status": {},
            "done_report": False,
        }
    )
    return prompts["overview"].strip()


@mcp.tool
def set_experiments(experiments: list[str]) -> str:
    """
    Set the ordered experiment identifiers, e.g., ["exp1a", "exp1b"].
    Resets per-experiment loop state.
    """
    state["experiments"] = experiments
    state["exp_status"] = {exp: "impl" for exp in experiments}
    state["done_report"] = False
    return f"Experiments registered: {', '.join(experiments) if experiments else 'none provided'}"


@mcp.tool
def experiment_step(experiment: str) -> str:
    """
    Request the next instruction (implementation or execution) for a specific experiment.
    Enforces experiment order defined in set_experiments.
    """
    if state["index"] + 1 < len(base_keys):
        return "Complete the base steps via next_step() before running experiment-specific prompts."

    if not state["experiments"]:
        return "No experiments registered. Call set_experiments([...]) first."

    if experiment not in state["exp_status"]:
        return (
            f"Experiment '{experiment}' is not in the registered list: {state['experiments']}. "
            "Call set_experiments again if you need to adjust the list."
        )

    # Enforce sequential order: only the first unfinished experiment is allowed
    pending = [exp for exp in state["experiments"] if state["exp_status"].get(exp) != "done"]
    if not pending:
        return "All experiments are already marked done. Use next_step() to proceed to the report."
    if experiment != pending[0]:
        return f"Next experiment in sequence is '{pending[0]}'. Finish it before moving to '{experiment}'."

    phase = state["exp_status"][experiment]
    if phase == "impl":
        state["exp_status"][experiment] = "exec"
        return prompts["code_impl"].strip().format(experiment=experiment)
    if phase == "exec":
        state["exp_status"][experiment] = "done"
        return prompts["code_exec"].strip().format(experiment=experiment)
    return f"Experiment '{experiment}' already completed. Pending experiments: {pending[1:] if len(pending) > 1 else 'none'}."


@mcp.tool
def next_step() -> str:
    """Return the next stage prompt in sequence."""
    # Base (non-looping) stages
    idx = state["index"] + 1
    if idx < len(base_keys):
        state["index"] = idx
        key = base_keys[idx]
        return prompts[key].strip()

    # After base stages, ensure experiments defined and completed
    if not state["experiments"]:
        return (
            "Set experiments first via set_experiments([...]), e.g., set_experiments(['exp1a', 'exp1b']). "
            "Then call experiment_step('<experiment>') to receive implementation/execution prompts."
        )

    pending = [exp for exp, phase in state["exp_status"].items() if phase != "done"]
    if pending:
        return (
            "Finish per-experiment prompts before the report. "
            f"Pending experiments (in order): {', '.join(pending)}. "
            "Use experiment_step('<experiment-name>') to continue."
        )

    # After all experiments completed, deliver report prompt once
    if state.get("done_report"):
        return "All prompts have been delivered."
    state["done_report"] = True
    return prompts["report"].strip()


if __name__ == "__main__":
    mcp.run()
