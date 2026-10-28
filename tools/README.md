# 资料命名与校验

论文 PDF 使用正文标题，阅读网页使用页面标题，文件名中的空白和不安全标点替换为下划线。保留完整标题，不使用 arXiv 编号、方法简称、URL 摘要或截断标题作为文件名。`τ`、`#` 分别写为 `tau`、`Sharp`，避免丢失论文身份。

- [MATERIAL_RENAMES.json](MATERIAL_RENAMES.json)：2026-10-27 改名清单，逐文件保留旧路径、当前路径、标题、来源 URL 和未改变的 SHA-256。同一论文的不同归档副本分别记录。
- [material_names.py](material_names.py)：MAS.S62 和 CS2680 同步、整理共用的命名函数；通过来源 URL 解析课表中的方法简称，同时保留课表原始标签。
- [verify_material_names.py](verify_material_names.py)：检查文件名、原始字节、旧路径是否被重新生成，以及同步脚本的离线路径解析。
- [MATERIAL_NAMES_VERIFICATION.json](MATERIAL_NAMES_VERIFICATION.json)：本次实际验证结果。
- [verify_assignment3_archive.py](verify_assignment3_archive.py)：核对 CMU 作业 3 固定提交的原始文件哈希、Python 语法、本地文件链接和数据集结构；结果写入作业目录的 `VERIFICATION.json`，公开测试另记于 `BASELINE_TESTS.json`。
- [三门课程学习质量复核](reviews/2026-10-28-full/README.md)：面向有 Java 经验的 LLM Developer，逐篇检查问题链、前置知识、机制推导、案例和自测；清单与复读记录绑定最终讲解的校验值。

新增材料时先核对 PDF 标题页、版本及本课来源索引。课表仅提供简称时，在清单中登记完整标题与来源 URL，再运行同步或整理。不要只根据 PDF 元数据自动命名：元数据可能缺失、截断或保留投稿模板标题。清单中的历史改名条目保留原始哈希；上游更新版本时单独记录版本与新哈希，避免将正文修订混入改名验证。

课程讲义和教程保留官方原名，上游代码快照保留原始结构。例如代码快照内的 `report.pdf` 不改名，学习入口中的论文副本使用完整标题。

整理和校验：

```bash
python3 MAS.S62/sync.py --organize-only
python3 2680/organize.py
python3 tools/verify_material_names.py --write-report
python3 tools/verify_course_notes.py --write-report
python3 tools/verify_assignment3_archive.py --write-report
python3 MAS.S62/verify.py --require-notes > MAS.S62/VERIFICATION.json
```

这些检查验证路径、校验值和引用结构，不代替论文精读，不表示重新复现了模型实验。各课程 `REVIEW.json` 的本轮路径维护记录保留了改名前的讲解哈希和既有内容审核历史。
