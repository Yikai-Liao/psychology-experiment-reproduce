---
name: psychology-experiment-reproduce
description: 用于复现给定心理学实现的实验数据对应的所有原始图片
---

## Description
A specialized skill for analyzing psychology research papers to extract experimental designs, generate flowcharts, and document visual stimuli parameters.

## Preparation

### Input Requirements
- Psychology research paper in markdown format
- Paper must contain detailed experimental methods sections
- Should include stimulus descriptions and experimental procedures

### Step 1: Experiment Identification
- Read the full content of the paper
- Identify and list all experiments described in the paper (Exp1, Exp2... or Exp1a, Exp1b, Exp2...)
- Number and name each experiment
- Extract research objectives and hypotheses for each Experiment
- 如果原始论文太大无法一次读完，请分多次读取

### Step 2: Detailed Flowchart Generation
For each experiment, generate following things into `exp_design.md`

#### Mermaid Flowchart
- Use standard Mermaid syntax
- Strictly avoid parentheses in node labels
- Clear node type labeling:
  - **Image Stimulus Nodes**: Visual stimulus presentation
  - **Text Stimulus Nodes**: Text information display
  - **Interaction Nodes**: User choice/reaction points
  - **Timing Nodes**: Time measurement points

#### Node Annotations (outside Mermaid)
**Text Stimulus Nodes:**
- Task instructions at experiment start
- Specific guidance text
- Feedback message descriptions

**Image Stimulus Nodes:**
- Detailed image composition description
- Visual element arrangement
- Color, shape, size visual features
- Examples: "Red circle at screen center, 5cm diameter, gray background"

**User Interaction Nodes:**
- Specific user actions (key press, mouse click, verbal response)
- Recorded data metrics:
  - Reaction time (milliseconds)
  - Accuracy rate (percentage)
  - Choice results (binary or multi-category)
  - Error types

#### Experiment Difference Explanation
- If experiments are similar, detail specific differences
- Variable control variations
- Stimulus material changes
- Measurement metric additions/modifications

### Step 3: Visual Stimulus Parameter Documentation

#### Image Enumeration
For each image node used in experiments:
- Image number and description
- Usage context in experiment

#### Detailed Parameter Specifications
首先，你需要找到论文原文中的描述，将原文中的描述通过markdown中 > 的形式插入到`exp_design.md`的对应章节中
其次，你需要使用能读取图片的MCP或者READ工具主动去读取论文中对于实验部分的所有示例图片，产生一个大概的认知，避免单纯通过文字描述来幻想原始刺激图片是什么样子的。
在这之后，你需要来确定这些刺激图片要还原的话需要哪些具体参数，以及这些刺激图片的示例出现在哪个论文插图中。
注意，论文插图会存放在一个单独的文件夹中，并且被论文的md文件引用。

**Geometric Parameters:**
- Position coordinates (X, Y)
- Shape type (circle, square, triangle, etc.)
- Size parameters (diameter, side length, radius, etc.)
- Rotation angle (degrees)

**Visual Parameters:**
- Color values (RGB/HEX)
- Transparency
- Border style and color
- Fill style

#### Parameter Importance

You need to specify which Parameter for an image in randomly decided in Experiment and which is important for results analyse(need to be recorded).

If the paramemter is random and not recorded, detail all the cases and corresponding possiblity.

If the paramemter should be recorded, also list all the cases, like 4 kinds of shape etc.

#### Pixel Conversion Specification
**Conversion Standards:**

You need to find the size and resolution of screen and watch distance in paper.

If you can't find it, use default settings:
- 17-inch CRT monitor, $1024 \times 768$ resolution.
- (Distance, $D$)：$50 \text{ cm}$.

**Conversion Examples:**
DPI 计算：
分辨率对角线像素：$\sqrt{1024^2 + 768^2} = 1280 \text{ px}$假设 17英寸 为显示区域对角线长度（标准 CRT 估算）：DPI $\approx 1280 / 17 \approx \mathbf{75.3 \text{ PPI}}

$换算公式：对于视觉角 $\theta$（度），屏幕物理尺寸 $S$（cm），像素 $P$（px）：

$$
S = 2 \times D \times \tan\left(\frac{\theta}{2}\right)$$

$$
P = S \times \frac{\text{DPI}}{2.54}
$$

### Output Example

```markdown
# Psychology Experiment Analysis Report

## Step 1: Experiment Identification
- Experiment 1: Color Judgment Task
- Experiment 2: Shape Discrimination Task

## Step 2: Detailed Flowcharts

### Experiment 1 Flowchart
\```mermaid
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
\```

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

## Code Generation

### Input requirements

(Use uv as python env management)

- Paper in markdown formats
- The generated markdown in preparse stage
- Downloaded Experiment Public Data of the paper (The data could be in zip, rar, tar.gz, xlsx, docx, etc. You need to read these data using python scripts, especially for xlsx, make sure you have read all the tab and table in the file, not just the first one)

### Step 1: Check Public Data

You need to load the public exp data using python scripts and check for each experiment that if all the parameter you expected in prepare stage are recorded.

你需要逐步下调你的预期，来做到尽可能精确还原原始实验数据。例如，试验中，如果有一个图像前后颜色可能发生改变，最精确的结果是实验数据记录了前后的颜色分别是什么，但是如果没有记录的话，你要降低要求，记录了前后颜色是否发生改变也可以，你只需要在给定的颜色列表中按照是否改变颜色随机选择就可以了（因为可能对于实验分析而言，具体是什么颜色不重要，是否改变很重要）。同样的，如果遇到了有形状编号，但是没有编号和形状对应里关系的情况，你也可以直接自己写一个对应关系（因为对应关系在试验中可能也是不重要的）。类似的情况还有一个干扰形状，我们可能只关系他是否会出现，颜色是否与之前的某个图形一致，具体的位置如果没有记录我们都可以随机处理。

在这一步中，你一定要仔细去原始论文中核对实验设计，确保你没有对原始论文产生误解，比如将垂直理解成水平，或者误用了某些旋转角度等等。并且，你在这一步中一定要重新阅读在Prepare阶段标注出来的图片，确保你对图片的理解与论文中的示意图一致。

并且，请你一定确认你真的看了所有下载下来的实验数据，几乎不会出现单独某个实验的实验数据没有公开而其他实验数据存在的情况。如果你感觉你遇到了这种情况，请一定要重新确认是否有遗漏的数据文件没有查看。

当你核对完成后，你需要在 `exp_design.md`中，进一步补充实际复现中，哪些参数被你随机了，哪里是精确的记录的参数，哪些参数你没有用到，以及记录的实验数据中的文件和实验对应关系，数据实际列名和你在文档中提到的参数的对应关系。
请注意，这里我说的是进一步补充，所以请注意，你不能删除在Prepare阶段创建的内容，只能新增。而且，请时刻注意，你没有处理完所有实验，在处理完所有实验的图片参数核对之前，不要进入代码实现阶段。

### Step 2: 代码实现。

在上一步彻底理解了图像参数的基础只上，开始创建代码来还原实验中的原始图片刺激。

创建一个`experiment`文件夹，cd 进去，使用uv init 来创建python环境。你可以使用uv add 来安装依赖，使用uv run 来运行程序，禁止使用uv pip install，这不会更改依赖。

因为实验中可能会涉及到大量的图形绘制，我建议你采取sympy + pyx 进行几何绘图，将结果输出到`output/实验编号`路径下。我建议绘制svg图像,并同时保存一个同名pdf文件作为备份，并且逐个实验推进，不要一次写完所有实验的代码，并且添加 --limit 入参，限制处理的trial数量（或者说实验数据中的行数），添加debug log 输出每个图像对应的实验记录参数。请每写完一个实验的代码后立即运行，先使用 timeout 机制 加 limit 小样本运行，确保没有死循环的产生，并阅读生成的svg与对应的log出来的debug参数，看看，是否符合要求。如果不符合要求需要修改代码，直到符合要求。

下面是一个使用scipy 和 pyx绘图的简单示例代码：
```python
# uv add numpy scipy pyx
import numpy as np
from scipy.spatial.transform import Rotation as R
from pyx import canvas, path, color, style


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

# 输出 PDF（也可以改成 writeEPSfile / writeSVGfile）
c.writeSVGfile("scipy_pyx_demo")
c.writePDFfile("scipy_pyx_demo")
```

### Step 3: 代码执行

测试小批次符合要求后，修改log等级，不输出debug内容，进行无timeout，无limit上限运行，生成所有实验数据的对应图片刺激，并最后确认最后生成的图像数量符合预期。

注意，当你执行并确认完一个实验之后，不要着急进入Step4撰写报告，而是需要检查确认是否完成了所有实验的原始刺激图像生成。如果没有，回到Step 2继续处理下一个实验。

### Step 4: 报告撰写

编写 `report.md`，详细描述你在编码中遇到的困那，生成的图像可能的风险（也就是可能有什么和离线的原始刺激图像不一致的地方），如何调用你写的脚本来复现这些图像。