# 四门课程完整大纲来源（2026-11-01）

保留官方原始页面、完整学期安排和必要的结构化提取。当前目录与材料状态统一维护在 [COURSE_LAYOUT.json](../../COURSE_LAYOUT.json)，学习顺序见 [ROADMAP.zh-CN.md](../../ROADMAP.zh-CN.md)。官网允许后续调整；取得课表不代表其所有讲义、阅读或作业正文已经取得。

| 课程 | 官方原文 | 结构化大纲与课表 |
|---|---|---|
| CMU 11-768 | [首页](cmu/index.html)、[官方前端 JS](cmu/app.js) | [大纲与作业评分](cmu/syllabus.json)、[30 条日历记录](cmu/schedule.json) |
| Harvard CS2680 | [课表](harvard/index.html)、[作业计划](harvard/assignments.html)、[项目](harvard/project.html)、[政策](harvard/policy.html) | [28 条日历记录](harvard/schedule.json) |
| MIT MAS.S62 | [首页](mit/index.html)、[课表](mit/schedule.html)、[大纲 TXT](../../MAS.S62/site/syllabus/ai4ai-syllabus.txt)、[大纲 PDF](../../MAS.S62/site/syllabus/ai4ai-syllabus.pdf) | [14 条日历记录](mit/schedule.json) |
| Stanford CS329Z | [课表](../../329z/site/index.html)、[课程要求](../../329z/site/logistics.html)、[项目](../../329z/site/project.html) | [22 条日历记录](stanford/schedule.json)、[截止安排](stanford/deadlines.json) |

CMU 的课表与大纲从官方 JS 静态提取，保留原始字段，未执行远端代码。其余课程的结构化课表来自上表原文。合计 94 条日历记录，包含停课、项目与展示；Harvard 历史 others 占位记录在当前目录映射的 legacy_items 中。

MIT 大纲和 Stanford 三个页面复用课程目录中经逐字节确认相同的归档。下表的哈希固定本次大纲来源版本；今后刷新这些共享路径时，需按课程更新规则保存旧版本并更新此处指向。原始 HTML 的内部相对链接仍采用官网结构，未镜像的附件不算本地已取得资料。

## 来源与版本

下列响应均为 HTTP 200。时间保留实际取得时间，不因目录整理而改写。

| 本地原文 | 请求 URL | 最终 URL | 取得时间（UTC） | SHA-256 |
|---|---|---|---|---|
| [cmu/index.html](cmu/index.html) | https://www.cmu-agents.com/ | https://www.cmu-agents.com/ | 2026-11-01T06:25:54.339433+00:00 | `5ed69a97ada0dc08cc094c17f8099dc55d72acc01598a371c25cd3ebecf91833` |
| [cmu/app.js](cmu/app.js) | https://www.cmu-agents.com/assets/index-ZhsqTcOj.js | https://www.cmu-agents.com/assets/index-ZhsqTcOj.js | 2026-11-01T06:26:01.118874+00:00 | `1fd6f534bb85e3d4f2f868ed722ad254444c1f5ca026afe77ce0421fbda91eb8` |
| [harvard/index.html](harvard/index.html) | https://cs2680.com/index.html | https://cs2680.com/ | 2026-11-01T06:26:59.481Z | `43ab40fdefd3a290bb99f5e56c9219e9a66d5c025e0ba59aa87b39409f30169b` |
| [harvard/assignments.html](harvard/assignments.html) | https://cs2680.com/assignments/ | https://cs2680.com/assignments/ | 2026-11-01T06:26:54.193Z | `6600189575e590e17495e52a918c451170a46556da6c943971f94c40c3b107e8` |
| [harvard/project.html](harvard/project.html) | https://cs2680.com/project | https://cs2680.com/project | 2026-11-01T06:26:54.199Z | `daff7c72ffff591f73b4dc742777ccf58a9d4fda32f411b9a88091843ef1cd3a` |
| [harvard/policy.html](harvard/policy.html) | https://cs2680.com/policy | https://cs2680.com/policy | 2026-11-01T06:27:04.041Z | `aaf414dab224b911d81923a22631c2a4ce4ecd93df30a47aadc5227937a7c8d2` |
| [../../329z/site/index.html](../../329z/site/index.html) | https://cs329z.stanford.edu/index.html | https://cs329z.stanford.edu/index.html | 2026-11-01T06:27:05.809Z | `913a24331bbf0bd7198854e3c00e6e3fbcf84dd9af32510ceb5c9fbb8a460a2a` |
| [../../329z/site/logistics.html](../../329z/site/logistics.html) | https://cs329z.stanford.edu/logistics.html | https://cs329z.stanford.edu/logistics.html | 2026-11-01T06:27:05.689Z | `33626168e06a4ec8fd5439929100eab0df2bfbd37771746a5e508d33eee7d224` |
| [../../329z/site/project.html](../../329z/site/project.html) | https://cs329z.stanford.edu/project.html | https://cs329z.stanford.edu/project.html | 2026-11-01T06:27:06.256Z | `2b6d48a1f20829245886ee23cf5d7b2b513423f8c0b7dd27dc9c7617414b06d1` |
| [mit/index.html](mit/index.html) | https://mit-mi.github.io/how2ai-course/fall2026/ | https://mit-mi.github.io/how2ai-course/fall2026/ | 2026-11-01T06:27:10.792Z | `6e33dd8d7e50bca3de9e01fc0b7aa9e97c7bc9852e4785b6c037c54b1d245923` |
| [mit/schedule.html](mit/schedule.html) | https://mit-mi.github.io/how2ai-course/fall2026/schedule/ | https://mit-mi.github.io/how2ai-course/fall2026/schedule/ | 2026-11-01T06:27:10.712Z | `2bcc674248c7ebc8ca4f29312b0dc0c5bd73300bfd1a0c3710dbd58ffe82d7fc` |
| [../../MAS.S62/site/syllabus/ai4ai-syllabus.txt](../../MAS.S62/site/syllabus/ai4ai-syllabus.txt) | https://docs.google.com/document/d/1H1vs32fhWaxEuP6-nA2GP-a1aFuEmjOXNMcer2UyKpM/export?format=txt | https://doc-10-4k-docstext.googleusercontent.com/export/dr04igesal9pftlk9arelf1tq8/dei7cr6so7agm64mk2upqltijc/1793514435000/117925222914947718294/*/1H1vs32fhWaxEuP6-nA2GP-a1aFuEmjOXNMcer2UyKpM?format=txt | 2026-11-01T06:27:21.059Z | `62a0e9c97669b007ab74ccd9b440c92846b821445420965b0e0c602790a210ee` |
| [../../MAS.S62/site/syllabus/ai4ai-syllabus.pdf](../../MAS.S62/site/syllabus/ai4ai-syllabus.pdf) | https://docs.google.com/document/d/1H1vs32fhWaxEuP6-nA2GP-a1aFuEmjOXNMcer2UyKpM/export?format=pdf | https://doc-10-4k-docstext.googleusercontent.com/export/dr04igesal9pftlk9arelf1tq8/dei7cr6so7agm64mk2upqltijc/1793514435000/117925222914947718294/*/1H1vs32fhWaxEuP6-nA2GP-a1aFuEmjOXNMcer2UyKpM?format=pdf | 2026-11-01T06:27:22.260Z | `204f9edde27ed5ee5b2a4001df78ad07d41cd273c6ae3a6dd57e171b3badbdb9` |
