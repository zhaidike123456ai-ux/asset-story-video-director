# Asset Story Video Director V1 实施方案

## 环境扫描结论

- 项目仓库初始为空，无旧架构冲突。
- 可用运行时：Python 3.14、Node 26、Deno、uv、jq、ffmpeg。
- V1 选用 Python 标准库，不引入安装成本。
- 未发现 `jimeng` / `dreamina` / `seedance` 可执行 CLI、相关 Python/Node 包、或可直接调用的 MCP/API Provider。
- 因此 V1 提供稳定 Provider 接口、Mock Provider 和可配置的 Jimeng CLI Adapter；不冒充真实接通。

## 架构

```text
User Assets / Reference Video
            |
      Asset Analyzer ---- Reference Story DNA
            |                    |
            +---- Asset Bible ---+
                       |
                  Story Router
                       |
                  Story Engine
                       |
             Feasibility Checker
                       |
                Story Development
                       |
                 Director Engine
                       |
                 Prompt Compiler
                       |
             Video Provider Interface
                 /              \
          Mock Provider     Jimeng CLI Adapter
                 \              /
                    Job Store
```

Story/Director 只依赖中立数据结构。Prompt Compiler 读取 Provider capability 后再进行分段。Provider 负责提交、查询、下载与可选取消，不参与故事创作。

## 文件树

```text
asset-story-video-director/
├── SKILL.md
├── agents/openai.yaml
├── scripts/
│   ├── asvd.py
│   └── asvd/
│       ├── project.py
│       ├── assets.py
│       ├── stories.py
│       ├── director.py
│       ├── compiler.py
│       ├── jobs.py
│       └── providers/
│           ├── base.py
│           ├── mock.py
│           └── jimeng_cli.py
├── assets/
│   ├── story_types/
│   ├── schemas/
│   └── providers/
├── references/
└── tests/
```

用户项目在指定的 `projects/<project_id>/` 中生成，包含 `project.json`、`assets/asset_bible.json`、`references/`、`stories/`、`director/`、`prompts/`、`jobs/`、`outputs/`。

## 核心模块与数据模型

- Asset Analyzer：稳定 ID、7 类资产、A/B/C 级、视觉身份与行为/故事功能。
- Reference Analyzer：保存 Story DNA，输出抽象母型，禁止复制具体事件。
- Story Type Library：每类型一个 JSON；V1 内置 TYPE_01/TYPE_02，新类型不修改引擎。
- Story Router：结合资产、情绪、时长、可执行动作和复杂度评分。
- Story Generator：默认 5–8 个不同变化轴的候选，附生产风险。
- Story Development：只深化已保存的选中故事。
- Director Engine：类型感知节奏、动态镜头、时长守恒。
- Prompt Compiler：依 capability 分段，输出动作时序、镜头、一致性、声音和 negative constraints。
- Job Store：每 generation unit 一个 job，独立失败/重试。

字段约束见 `references/schemas.md` 与 `assets/schemas/*.schema.json`。

## Provider Interface

```python
get_capabilities() -> dict
submit_generation(prompt, assets, parameters) -> task_id
get_task_status(task_id) -> status
download_result(task_id, output_path) -> path
cancel_task(task_id) -> bool  # optional
```

Capability 至少包含 `max_duration`、`supported_ratios`、`supported_resolutions`、`text_to_video`、`image_to_video`、`first_frame`、`last_frame`、`multi_image`、`audio_support`。

## Jimeng Adapter 方案

Jimeng adapter 不假设非官方 CLI 名称。它从 JSON 配置读取 executable、capability、参数模板和响应字段，使用不经 shell 的参数数组执行，并在不可用时返回可诊断错误。Token/Cookie 只能由 CLI 自身的登录机制或环境变量提供。真实接入前需核对官方或第三方接口的稳定性、授权方式、费用与响应 schema。

## 状态保存

- `project.json` 保存项目阶段、当前选中故事、显示顺序、目标参数和最近产物路径。
- 所有 JSON 原子写入，防止中断留下半文件。
- 聊天中的序号通过 `story_order` 解析为稳定 `story_id`。
- 后续阶段读取既有产物，不隐式重新生成。

## 测试方案

`unittest` 覆盖 Asset Bible、Router、候选差异性、TYPE_01、TYPE_02 的超额回报、Story Development、Director 时长守恒、Provider capability、Prompt Compiler 按 capability 分段、Provider 不可用时的优雅降级，以及 job 独立重试语义。

## V1 不做什么

- 不在无稳定授权接口时伪造即梦成功。
- 不内置通用视觉大模调用；由 Codex 检视资产后把结构化描述交给 CLI。
- 不做剪辑合片、字幕烧录、TTS、BGM 版权处理。
- 不保证爆款，不自动扣费，不保存密钥。
- 不在引擎中写死单一模型时长、分辨率或画幅。
