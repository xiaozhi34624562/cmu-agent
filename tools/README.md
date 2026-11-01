# 资料命名与校验

论文 PDF 使用正文标题，阅读网页使用页面标题，文件名中的空白和不安全标点替换为下划线。保留完整标题，不使用 arXiv 编号、方法简称、URL 摘要或截断标题作为文件名。`τ`、`#` 分别写为 `tau`、`Sharp`，避免丢失论文身份。

- [MATERIAL_RENAMES.json](MATERIAL_RENAMES.json)：同步与整理使用的命名映射，记录旧路径、当前路径、标题、来源 URL 与内容 SHA-256。同一论文的不同归档副本分别记录。
- [material_names.py](material_names.py)：MAS.S62 和 CS2680 同步、整理共用的命名函数；通过来源 URL 解析课表中的方法简称，同时保留课表原始标签。
- [verify_material_names.py](verify_material_names.py)：检查文件名、原始字节、旧路径是否被重新生成，以及同步脚本的离线路径解析。
- [verify_assignment3_archive.py](verify_assignment3_archive.py)：核对 CMU 作业 3 固定提交的原始文件哈希、Python 语法、本地文件链接和数据集结构；公开测试的环境及失败范围保留在作业目录的 `BASELINE_TESTS.json`。
- [verify_course_notes.py](verify_course_notes.py)：检查 CMU 与 Harvard 的讲解覆盖、当前审核版本、本地引用、PDF 页码和资料完整性。
- [Stanford CS329Z](../courses/329z/README.md)：第四门课程按教学课次组织，课程自己的 `sync.py` 与 `verify.py` 维护来源版本、分类副本、主讲义绑定、固定代码快照和逐课完整讲解；复核记录见 `courses/329z/REVIEW.json`。

新增材料时先核对 PDF 标题页、版本及本课来源索引。课表仅提供简称时，在清单中登记完整标题与来源 URL，再运行同步或整理。不要只根据 PDF 元数据自动命名：元数据可能缺失、截断或保留投稿模板标题。清单中的历史改名条目保留原始哈希；上游更新版本时单独记录版本与新哈希，避免将正文修订混入改名验证。

课程讲义和教程保留官方原名，上游代码快照保留原始结构。例如代码快照内的 `report.pdf` 不改名，学习入口中的论文副本使用完整标题。

整理和校验：

```bash
python3 courses/MAS.S62/sync.py --organize-only
python3 courses/2680/organize.py
python3 tools/verify_material_names.py
python3 tools/verify_course_notes.py
python3 tools/verify_assignment3_archive.py
python3 courses/MAS.S62/verify.py --require-notes
python3 courses/329z/sync.py --organize-only
python3 courses/329z/verify.py --require-notes
```

检查结果默认输出到终端。确需保留时，使用支持的 `--output /tmp/course-check.json`，或将标准输出重定向到临时目录；仓库只维护当前状态和可重跑的校验脚本。

这些检查验证路径、校验值和引用结构，不代替论文精读或模型实验。各课程 `REVIEW.json` 保留当前笔记哈希、最近内容审核的版本、来源范围、复读结论和限制；知识正文修改后须重新内容审核，仅路径或维护链接调整则记录对应版本关系。
