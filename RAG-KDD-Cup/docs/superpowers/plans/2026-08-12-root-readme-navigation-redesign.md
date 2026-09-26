# 根 README 全仓库导航重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 将根 `README.md` 重构为覆盖全部研究资料、代码仓库、来源清单和项目文档的统一中文导航入口。

**架构：** README 使用“资产快照 → 快速导航 → 分项目完整索引 → 代码与复现矩阵 → 学习路线 → 仓库约定 → 设计文档”的分层结构。资产快照同时展示权威主工作区物理口径和根 Git 可移植口径：前者在固定绝对路径排除根 `.git` 与整个 `.worktrees` 后核验，后者由 `git ls-files`/`git archive` 核验。Meta CRAG 十篇论文作为子专题呈现，不再代表仓库总量。

**技术栈：** Markdown、Python 3、Git、SHA-256、`pdfinfo`、`pdftotext`、本地链接解析。

---

## 文件范围

- 修改：`README.md`——全仓库总导航。
- 创建：无。
- 只读参考：三个既有项目 README、十篇 CRAG README、十三份 manifest、两份既有归档计划和两份设计规格。
- 禁止修改：所有嵌套上游代码仓库及项目级/论文级 README。

### Task 1：建立资产与导航验收基线

**文件：**
- 只读：整个仓库
- 待修改：`README.md`

- [x] **Step 1：分别核验权威主工作区、根 Git 和独立 worktree 口径**

运行：

```bash
python3 - <<'PY'
from pathlib import Path
from collections import Counter
import hashlib
import subprocess

authority_root = Path('/Users/wangmingzhi/qg/code/RAGKK').resolve()
worktree_root = authority_root / '.worktrees/root-readme-navigation'

def included_under(root: Path, path: Path) -> bool:
    rel = path.relative_to(root)
    return bool(rel.parts) and rel.parts[0] not in {'.git', '.worktrees'}

pdfs = [p for p in authority_root.rglob('*.pdf') if included_under(authority_root, p)]
manifests = [
    p for p in authority_root.rglob('source-manifest.md')
    if included_under(authority_root, p)
]
repos = [
    p.parent for p in authority_root.rglob('.git')
    if included_under(authority_root, p)
]
hashes = {hashlib.sha256(p.read_bytes()).hexdigest() for p in pdfs}
papers = [p for p in pdfs if 'papers' in p.relative_to(authority_root).parts]

tracked = subprocess.run(
    ['git', '-C', str(worktree_root), 'ls-files', '-z'],
    check=True,
    capture_output=True,
).stdout.decode().split('\0')
tracked = [Path(p) for p in tracked if p]
tracked_pdfs = [p for p in tracked if p.suffix.lower() == '.pdf']
tracked_manifests = [p for p in tracked if p.name == 'source-manifest.md']
tracked_repos = [p for p in tracked if p.name == '.git' or '.git' in p.parts]

worktree_pdfs = [
    p for p in worktree_root.rglob('*.pdf')
    if included_under(worktree_root, p)
]
worktree_repos = [
    p.parent for p in worktree_root.rglob('.git')
    if included_under(worktree_root, p)
]

original = authority_root / 'EReL@MIR 2025/code/01-iLearn-MDR/report.pdf'
archived = authority_root / 'EReL@MIR 2025/papers/1st-iLearn-Technical-Report.pdf'
original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
archived_hash = hashlib.sha256(archived.read_bytes()).hexdigest()

print('authority_physical_pdfs', len(pdfs))
print('authority_papers_pdfs', len(papers))
print('authority_unique_pdf_contents', len(hashes))
print('authority_source_manifests', len(manifests))
print('authority_nested_repositories', len(repos))
print('authority_pdfs_by_top_level', dict(sorted(Counter(
    p.relative_to(authority_root).parts[0] for p in pdfs
).items())))
print('portable_tracked_pdfs', len(tracked_pdfs))
print('portable_source_manifests', len(tracked_manifests))
print('portable_nested_repositories', len(tracked_repos))
print('worktree_physical_pdfs', len(worktree_pdfs))
print('worktree_nested_repositories', len(worktree_repos))
print('erel_original_sha256', original_hash)
print('erel_archive_sha256', archived_hash)

assert (len(pdfs), len(papers), len(hashes), len(manifests), len(repos)) == (15, 14, 14, 13, 7)
assert (len(tracked_pdfs), len(tracked_manifests), len(tracked_repos)) == (14, 13, 0)
assert (len(worktree_pdfs), len(worktree_repos)) == (14, 0)
assert original_hash == archived_hash == '06c4b8ca4751dd502b9e49132570242ea101e0cf562dece329ac78274428474c'
PY
```

期望输出必须包含：

```text
authority_physical_pdfs 15
authority_papers_pdfs 14
authority_unique_pdf_contents 14
authority_source_manifests 13
authority_nested_repositories 7
authority_pdfs_by_top_level {'EReL@MIR 2025': 3, 'FinanceRAG Challenge 2024': 1, 'Meta KDD Cup CRAG': 10, 'WattBot Challenge 2025': 1}
portable_tracked_pdfs 14
portable_source_manifests 13
portable_nested_repositories 0
worktree_physical_pdfs 14
worktree_nested_repositories 0
erel_original_sha256 06c4b8ca4751dd502b9e49132570242ea101e0cf562dece329ac78274428474c
erel_archive_sha256 06c4b8ca4751dd502b9e49132570242ea101e0cf562dece329ac78274428474c
```

这里的 15/14/14/13/7 是固定绝对路径下的权威主工作区物理事实；14/13/0 是根 Git 可移植事实。不得在隔离 worktree 中用 `Path('.').rglob('.git')` 推导七个嵌套仓库是否存在。

- [x] **Step 2：运行旧 README 的失败验收**

运行：

```bash
python3 - <<'PY'
from pathlib import Path

text = Path('README.md').read_text()
required = [
    '当前用户主工作区物理资产',
    '15 个 PDF 文件',
    '14 份独立 PDF 内容',
    '13 份来源清单',
    '7 个本地官方代码仓库',
    '根 Git 可移植归档',
    '14 个 PDF 文件',
    '0 个嵌套本地仓库',
    '## 完整资料索引',
    '## 代码与复现状态',
    '## 设计与实施文档',
    'EReL 第一名技术报告保留了两个内容相同的文件',
]
missing = [item for item in required if item not in text]
assert not missing, f'缺少全仓库导航内容：{missing}'
PY
```

期望：失败，并列出旧 README 缺少的两种资产口径、完整索引、复现矩阵、文档导航和 EReL 重复说明。

### Task 2：重写根 README 的总览与完整索引

**文件：**
- 修改：`README.md`

- [x] **Step 1：写入仓库定位、目录和资产快照**

将 `README.md` 开头重构为以下层次，数字必须使用 Task 1 的现场结果，并明确限定统计边界：

```markdown
# RAG 竞赛论文、代码与工程分析仓库

本仓库按“论文、官方代码、来源核验、中文工程分析”组织 FinanceRAG、WattBot、EReL@MIR 和 Meta CRAG/CRAG-MM 资料。根 README 是全仓库导航；各项目和论文 README 承担详细技术分析。

## 目录

- [仓库资产快照](#仓库资产快照)
- [快速导航](#快速导航)
- [完整资料索引](#完整资料索引)
- [代码与复现状态](#代码与复现状态)
- [主题学习路线](#主题学习路线)
- [仓库约定与已知缺口](#仓库约定与已知缺口)
- [设计与实施文档](#设计与实施文档)

## 仓库资产快照

### 当前用户主工作区物理资产

以下统计以 `/Users/wangmingzhi/qg/code/RAGKK` 为权威主工作区，递归排除根 `.git/` 和整个 `.worktrees/`。这是当前机器上的物理资产事实，不代表新的 checkout 会自动携带被忽略的嵌套仓库。

| 资产 | 数量 | 口径 |
|---|---:|---|
| 比赛或年度专题 | 5 | FinanceRAG、WattBot、EReL、CRAG 2024、CRAG-MM 2025 |
| PDF 文件 | 15 | 权威主工作区物理文件数 |
| 独立 PDF 内容 | 14 | 按 SHA-256 去重 |
| `papers/` 归档 PDF | 14 | 项目维护的稳定论文入口 |
| 来源清单 | 13 | 三个既有项目加十个 CRAG 单元 |
| 本地官方代码仓库 | 7 | 当前主工作区中保留各自 `.git`、且被根 `.gitignore` 排除的上游仓库 |
| Meta CRAG 研究单元 | 10 | CRAG 2024 八篇、CRAG-MM 2025 两篇 |

EReL 第一名技术报告保留了两个内容相同的文件：上游代码仓库中的 `report.pdf` 与根 Git 追踪的 `papers/1st-iLearn-Technical-Report.pdf` 在权威主工作区核验得到相同 SHA-256。

### 根 Git 可移植归档

| 资产 | 数量 | 口径 |
|---|---:|---|
| PDF 文件 | 14 | `git ls-files`/`git archive` 可携带 |
| 来源清单 | 13 | `git ls-files`/`git archive` 可携带 |
| 嵌套本地仓库 | 0 | 七个上游仓库被根 `.gitignore` 排除 |

独立 worktree 的现场结果同样是 14 个 PDF 文件和 0 个嵌套本地仓库。新的 checkout、worktree 或根 Git 归档不会自动包含权威主工作区中的第 15 个 PDF 和七个嵌套仓库。
```

不得省略“当前用户主工作区物理资产”和“根 Git 可移植归档”两个限定标题，也不得把 15/7 写成新 checkout 的自包含资产承诺。

- [x] **Step 2：写入五个专题的快速导航表**

快速导航表使用以下列：

```markdown
| 专题 | 独立论文内容 | 本地官方仓库 | 技术分析 | 论文 | 代码 | 来源 |
```

五行分别对应 FinanceRAG、WattBot、EReL、CRAG 2024、CRAG-MM 2025。FinanceRAG、WattBot 直接链接单篇 PDF；EReL 直接链接两份独立 PDF；两个 CRAG 年度链接年度导航和论文目录，不用“十篇”代表整个仓库。

- [x] **Step 3：写入 FinanceRAG、WattBot、EReL 完整索引**

使用三个三级标题，每个链接必须直接指向实际文件或仓库：

```markdown
### FinanceRAG Challenge 2024

- [中文技术分析](./FinanceRAG%20Challenge%202024/README.md)
- [Multi-Reranker PDF](./FinanceRAG%20Challenge%202024/papers/Multi-Reranker.pdf)
- [FinanceRAG 官方代码](./FinanceRAG%20Challenge%202024/code/FinanceRAG/)
- [来源清单](./FinanceRAG%20Challenge%202024/resources/source-manifest.md)

### WattBot Challenge 2025

- [中文技术分析](./WattBot%20Challenge%202025/README.md)
- [KohakuRAG PDF](./WattBot%20Challenge%202025/papers/KohakuRAG.pdf)
- [KohakuRAG 官方代码](./WattBot%20Challenge%202025/code/KohakuRAG/)
- [来源清单](./WattBot%20Challenge%202025/resources/source-manifest.md)
```

EReL 必须单独列出挑战综述、第一名技术报告归档副本、代码仓库中的原始报告、三支获奖团队代码和 manifest，并在相邻文本中说明两个报告 SHA-256 相同。

- [x] **Step 4：写入十个 Meta CRAG 单元的统一表格**

分别在 `Meta CRAG 2024` 和 `Meta CRAG-MM 2025` 三级标题下使用以下列：

```markdown
| 论文 | 技术分析 | PDF | 代码 | 来源 | 名次口径 | 复现状态 |
```

每行必须直接链接：论文 README、PDF、官方仓库或 `code/README.md`、manifest。名次必须区分类别名次、作者报告、human evaluation 和存在冲突的来源；复现状态必须区分本地官方 clone、上游 503 和未发布代码。

- [x] **Step 5：运行完整索引覆盖检查**

运行：

```bash
python3 - <<'PY'
from pathlib import Path
from urllib.parse import quote
import subprocess

authority_root = Path('/Users/wangmingzhi/qg/code/RAGKK').resolve()
text = Path('README.md').read_text()
tracked = subprocess.run(
    ['git', 'ls-files', '-z', '*.pdf'],
    check=True,
    capture_output=True,
).stdout.decode().split('\0')
papers = [Path(p) for p in tracked if p and 'papers' in Path(p).parts]
repo_paths = [
    Path('FinanceRAG Challenge 2024/code/FinanceRAG'),
    Path('WattBot Challenge 2025/code/KohakuRAG'),
    Path('EReL@MIR 2025/code/01-iLearn-MDR'),
    Path('EReL@MIR 2025/code/02-LLMHunter-MMDocRetrievalChallenge'),
    Path('EReL@MIR 2025/code/03-GPU-is-all-you-need-MultiModal_InformationRetrieval'),
    Path('Meta KDD Cup CRAG/CRAG 2024/02-Revisiting-CRAG/code/CRAG-in-KDD-Cup2024'),
    Path('Meta KDD Cup CRAG/CRAG-MM 2025/09-Winning-Task-2/code/crag-mm'),
]

missing_pdfs = [str(p) for p in papers if quote(str(p), safe='/') not in text]
missing_repo_links = [str(p) for p in repo_paths if quote(str(p), safe='/') not in text]
missing_authority_repos = [
    str(authority_root / p) for p in repo_paths
    if not (authority_root / p / '.git').exists()
]
assert len(papers) == 14, len(papers)
assert not missing_pdfs, missing_pdfs
assert not missing_repo_links, missing_repo_links
assert not missing_authority_repos, missing_authority_repos
print('PASS：14 个 tracked papers PDF 有直接入口')
print('PASS：7 个嵌套仓库路径有 README 入口，并已在权威主工作区核验物理存在性')
PY
```

期望输出上述两个 `PASS`。隔离 worktree 只负责检查 14 个根 Git 追踪的 `papers/` PDF 和七个仓库路径字符串是否被 README 覆盖；七个嵌套仓库的物理存在性必须通过 `authority_root` 在主工作区外部核验，不得要求它们存在于隔离 worktree。

### Task 3：补齐复现矩阵、学习路线和项目文档

**文件：**
- 修改：`README.md`

- [x] **Step 1：写入代码与复现状态矩阵**

矩阵至少使用以下状态：

- 本地官方仓库：7 个，固定 commit，完成静态审计
- 官方仓库上游不可访问：2024 db3、Hybrid RAG、2025 db3
- 未发现作者代码：Simple RAG、KG Self-Verification、Honest AI、TCAF、MARAGS
- 外部依赖：受限数据、模型权重、API、凭据、GPU

不得把“代码已下载”写成“系统已复现”，也不得把 503 写成“未发布代码”。

- [x] **Step 2：将学习路线改为可点击的全仓库路线**

创建八条路线：检索与重排、层级文档与引用、金融表格与结构化计算、验证与拒答、Agent 与复杂推理、多模态检索、多轮视觉 RAG、生产评估与复现。每条路线中的项目或论文名称必须是本地 Markdown 链接。

- [x] **Step 3：写入仓库约定与已知缺口**

明确目录职责、官方代码认定、nested Git、PDF 去重、下载边界、静态审计与榜单复现的区别，以及三份 AIcrowd GitLab 官方仓库在核验日期的 503 状态。

- [x] **Step 4：写入设计与实施文档导航**

直接链接：

```markdown
- [Kaggle RAG 研究归档实施计划](./docs/superpowers/plans/2026-08-11-kaggle-rag-research-archive.md)
- [Meta CRAG 研究归档设计](./docs/superpowers/specs/2026-08-12-meta-crag-research-archive-design.md)
- [Meta CRAG 研究归档实施计划](./docs/superpowers/plans/2026-08-12-meta-crag-research-archive.md)
- [根 README 全仓库导航重构设计](./docs/superpowers/specs/2026-08-12-root-readme-navigation-redesign.md)
- [根 README 全仓库导航重构实施计划](./docs/superpowers/plans/2026-08-12-root-readme-navigation-redesign.md)
```

### Task 4：最终验收与提交

**文件：**
- 修改：`README.md`
- 修改：`docs/superpowers/plans/2026-08-12-root-readme-navigation-redesign.md`（完成复选框）

- [x] **Step 1：运行本项目维护 Markdown 的本地链接检查**

在隔离 worktree 中运行；一般链接相对当前 Markdown 文件解析，七个被忽略的嵌套仓库链接改到权威主工作区核验物理存在性：

```bash
python3 - <<'PY'
from pathlib import Path
from urllib.parse import unquote, urlparse
import re
import subprocess

worktree_root = Path.cwd().resolve()
authority_root = Path('/Users/wangmingzhi/qg/code/RAGKK').resolve()
nested_roots = tuple(Path(p) for p in [
    'FinanceRAG Challenge 2024/code/FinanceRAG',
    'WattBot Challenge 2025/code/KohakuRAG',
    'EReL@MIR 2025/code/01-iLearn-MDR',
    'EReL@MIR 2025/code/02-LLMHunter-MMDocRetrievalChallenge',
    'EReL@MIR 2025/code/03-GPU-is-all-you-need-MultiModal_InformationRetrieval',
    'Meta KDD Cup CRAG/CRAG 2024/02-Revisiting-CRAG/code/CRAG-in-KDD-Cup2024',
    'Meta KDD Cup CRAG/CRAG-MM 2025/09-Winning-Task-2/code/crag-mm',
])
markdown = subprocess.run(
    ['git', 'ls-files', '-z', '*.md'],
    check=True,
    capture_output=True,
).stdout.decode().split('\0')
missing = []
for name in filter(None, markdown):
    source = Path(name)
    for href in re.findall(r'!?\[[^]]*\]\(([^)]+)\)', source.read_text()):
        href = href.strip().strip('<>')
        parsed = urlparse(href)
        if parsed.scheme in {'http', 'https', 'mailto'} or href.startswith('#'):
            continue
        decoded = Path(unquote(parsed.path))
        candidate = (source.parent / decoded).resolve()
        if candidate.exists():
            continue
        try:
            relative = candidate.relative_to(worktree_root)
        except ValueError:
            missing.append((name, href))
            continue
        in_nested_repo = any(relative == root or root in relative.parents for root in nested_roots)
        if in_nested_repo and (authority_root / relative).exists():
            continue
        missing.append((name, href))
assert not missing, missing
print('PASS：本项目维护 Markdown 本地链接缺失 0')
PY
```

期望：`PASS：本项目维护 Markdown 本地链接缺失 0`。

- [x] **Step 2：重新运行资产、PDF 与重复内容检查**

重新从两种边界核验，不能以隔离 worktree 的物理扫描替代主工作区统计：

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib
import subprocess

authority_root = Path('/Users/wangmingzhi/qg/code/RAGKK').resolve()
worktree_root = Path.cwd().resolve()

def included_under(root: Path, path: Path) -> bool:
    rel = path.relative_to(root)
    return bool(rel.parts) and rel.parts[0] not in {'.git', '.worktrees'}

pdfs = [p for p in authority_root.rglob('*.pdf') if included_under(authority_root, p)]
papers = [p for p in pdfs if 'papers' in p.relative_to(authority_root).parts]
manifests = [p for p in authority_root.rglob('source-manifest.md') if included_under(authority_root, p)]
repos = [p.parent for p in authority_root.rglob('.git') if included_under(authority_root, p)]
hashes = {hashlib.sha256(p.read_bytes()).hexdigest() for p in pdfs}

tracked = subprocess.run(
    ['git', 'ls-files', '-z'],
    check=True,
    capture_output=True,
).stdout.decode().split('\0')
tracked = [Path(p) for p in tracked if p]
tracked_pdfs = [p for p in tracked if p.suffix.lower() == '.pdf']
tracked_manifests = [p for p in tracked if p.name == 'source-manifest.md']
tracked_repos = [p for p in tracked if p.name == '.git' or '.git' in p.parts]
worktree_pdfs = [p for p in worktree_root.rglob('*.pdf') if included_under(worktree_root, p)]
worktree_repos = [p.parent for p in worktree_root.rglob('.git') if included_under(worktree_root, p)]

original = authority_root / 'EReL@MIR 2025/code/01-iLearn-MDR/report.pdf'
archived = authority_root / 'EReL@MIR 2025/papers/1st-iLearn-Technical-Report.pdf'
original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
archived_hash = hashlib.sha256(archived.read_bytes()).hexdigest()

assert (len(pdfs), len(papers), len(hashes), len(manifests), len(repos)) == (15, 14, 14, 13, 7)
assert (len(tracked_pdfs), len(tracked_manifests), len(tracked_repos)) == (14, 13, 0)
assert (len(worktree_pdfs), len(worktree_repos)) == (14, 0)
assert original_hash == archived_hash == '06c4b8ca4751dd502b9e49132570242ea101e0cf562dece329ac78274428474c'
print('PASS：主工作区 15/14/14/13/7；根 Git 14/13/0；独立 worktree 14/0；EReL SHA-256 相同')
PY
```

期望：输出上述 `PASS`。EReL 两个文件均从权威主工作区绝对路径读取。

- [x] **Step 3：运行 README 内容契约检查**

运行以下检查，验证双口径措辞、14 个根 Git 追踪论文入口和七个嵌套仓库路径入口；此步骤不要求七个仓库存在于隔离 worktree：

```bash
python3 - <<'PY'
from pathlib import Path
from urllib.parse import quote
import subprocess

text = Path('README.md').read_text()
required = [
    '## 仓库资产快照', '## 快速导航', '## 完整资料索引',
    '## 代码与复现状态', '## 主题学习路线',
    '## 仓库约定与已知缺口', '## 设计与实施文档',
    '当前用户主工作区物理资产', '15 个 PDF 文件',
    '14 份独立 PDF 内容', '7 个本地官方代码仓库',
    '根 Git 可移植归档', '14 个 PDF 文件', '0 个嵌套本地仓库',
    'EReL 第一名技术报告保留了两个内容相同的文件',
    'FinanceRAG Challenge 2024', 'WattBot Challenge 2025', 'EReL@MIR 2025',
    'Meta KDD Cup CRAG 2024', 'Meta KDD Cup CRAG-MM 2025',
]
missing_required = [item for item in required if item not in text]
tracked = subprocess.run(
    ['git', 'ls-files', '-z', '*.pdf'],
    check=True,
    capture_output=True,
).stdout.decode().split('\0')
papers = [Path(p) for p in tracked if p and 'papers' in Path(p).parts]
repo_paths = [Path(p) for p in [
    'FinanceRAG Challenge 2024/code/FinanceRAG',
    'WattBot Challenge 2025/code/KohakuRAG',
    'EReL@MIR 2025/code/01-iLearn-MDR',
    'EReL@MIR 2025/code/02-LLMHunter-MMDocRetrievalChallenge',
    'EReL@MIR 2025/code/03-GPU-is-all-you-need-MultiModal_InformationRetrieval',
    'Meta KDD Cup CRAG/CRAG 2024/02-Revisiting-CRAG/code/CRAG-in-KDD-Cup2024',
    'Meta KDD Cup CRAG/CRAG-MM 2025/09-Winning-Task-2/code/crag-mm',
]]
docs = [Path(p) for p in [
    'docs/superpowers/plans/2026-08-11-kaggle-rag-research-archive.md',
    'docs/superpowers/specs/2026-08-12-meta-crag-research-archive-design.md',
    'docs/superpowers/plans/2026-08-12-meta-crag-research-archive.md',
    'docs/superpowers/specs/2026-08-12-root-readme-navigation-redesign.md',
    'docs/superpowers/plans/2026-08-12-root-readme-navigation-redesign.md',
]]
missing_paths = [
    str(p) for p in papers + repo_paths + docs
    if quote(str(p), safe='/') not in text
]
assert len(papers) == 14, len(papers)
assert not missing_required, missing_required
assert not missing_paths, missing_paths
print('PASS：README 双口径、14 个 tracked papers、7 个仓库路径和 5 份项目文档覆盖完整')
PY
```

期望：输出上述 `PASS`。十个 CRAG 单元仍需逐行人工核对技术分析、PDF、代码状态、来源和复现口径五类信息。

- [x] **Step 4：运行 Git 检查**

```bash
git diff --check
git status --short
```

期望：只有 `README.md` 和本实施计划存在预期改动；无嵌套仓库、PDF、manifest 或项目级 README 改动。

- [x] **Step 5：勾选计划并提交**

```bash
git add README.md docs/superpowers/plans/2026-08-12-root-readme-navigation-redesign.md
git commit -m "docs: rebuild full repository navigation"
```

- [x] **Step 6：提交后复验**

重新运行 Steps 1–4，确认工作区干净，并报告最终提交哈希。
