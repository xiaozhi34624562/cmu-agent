#!/usr/bin/env python3
"""Archive Stanford CS329Z Fall 2026. Preserve original bytes and authored notes.

python3 329z/sync.py                      # refresh official pages, fetch new links
python3 329z/sync.py --organize-only      # rebuild local indexes, no network
python3 329z/sync.py --refresh-materials  # explicitly check revised source bodies
Requires requests, beautifulsoup4, pymupdf.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlparse, urlunparse
from zoneinfo import ZoneInfo

import fitz
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO / 'tools'))
from material_names import material_filename, registered_material, url_key

BASE = 'https://cs329z.stanford.edu/'
SEMESTER = 'Fall 2026'


def now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def normalized(url):
    p = urlparse(urljoin(BASE, url))
    return urlunparse((p.scheme, p.netloc.lower(), p.path, '', p.query, ''))


def local_link(path, parent=ROOT):
    return quote(os.path.relpath(path, parent), safe='/._-')


def inspect_download(path):
    path = Path(path)
    data = path.read_bytes()
    if not data:
        raise ValueError('Empty response')
    if path.suffix.lower() == '.pdf':
        if not data.startswith(b'%PDF-'):
            raise ValueError('Expected PDF bytes, received another body')
        with fitz.open(path) as doc:
            if not len(doc) or doc.is_encrypted:
                raise ValueError('Empty or encrypted PDF')
            cover = ' '.join(doc[0].get_text().split())
            metadata = dict(pages=len(doc), cover=cover)
            version = re.search(r'arXiv:(\d{4}\.\d{4,5}v\d+)', doc[0].get_text())
            if version:
                metadata['pdf_version'] = version[1]
            return metadata
    if path.suffix.lower() == '.html':
        soup = BeautifulSoup(data, 'html.parser')
        title = soup.title.get_text(' ', strip=True) if soup.title else ''
        body = soup.get_text(' ', strip=True)
        blocked = ('just a moment', 'verifying your browser', 'access denied',
                   'sign in - google', 'page not found', 'security checkpoint')
        if any(t in title.lower() for t in blocked) or len(body) < 150:
            raise ValueError('Not a verified reading body: ' + title)
        return dict(html_title=title)
    return {}


def fetch(item, refresh=False):
    target = ROOT / item['path']
    old = dict(item)
    temporary = None
    try:
        if target.is_file() and item.get('sha256') and digest(target)!=item['sha256']:
            raise ValueError('Local archive differs from recorded checksum; refusing to bless or overwrite changed source bytes')
        if target.is_file() and not refresh:
            item.update(inspect_download(target), status='saved', sha256=digest(target), bytes=target.stat().st_size)
            return item
        response = requests.get(item.get('download_url', item['url']), timeout=45,
                                headers={'User-Agent': 'CS329Z-public-study-archive/1.0'})
        response.raise_for_status()
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=target.suffix, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(response.content)
        metadata = inspect_download(temporary)
        incoming_hash = digest(temporary)
        if target.exists() and digest(target) != incoming_hash:
            previous_hash = digest(target)
            version = ROOT / 'versions' / previous_hash / target.relative_to(ROOT)
            version.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, version)
            item.setdefault('history', []).append(dict(path=str(version.relative_to(ROOT)),
                sha256=previous_hash, replaced_at=now(), retrieved_at=old.get('retrieved_at'),
                source_provenance={k:old[k] for k in ('acquisition_audit','etag','pdf_version','reused_from','final_url') if k in old}))
            item['review_required'] = True
        os.replace(temporary, target)
        for key in ('pages','cover','pdf_version','html_title','acquisition_audit','acquisition_audit_sha256','etag'):
            item.pop(key,None)
        item.update(metadata, status='saved', sha256=incoming_hash, bytes=target.stat().st_size,
                    retrieved_at=now(), final_url=response.url,
                    content_type=response.headers.get('Content-Type', ''),
                    content_disposition=response.headers.get('Content-Disposition',''),
                    transport='Python requests; original response bytes validated')
        item.pop('error', None)
        item.pop('refresh_status', None)
        item.pop('import_status', None)
        for key in ('reused_from','reused_at','provenance_note','retrieved_at_basis','response_metadata_note'):
            item.pop(key, None)
    except (requests.RequestException, OSError, ValueError, RuntimeError) as exc:
        item.update(checked_at=now(), error=str(exc)[:500])
        if target.exists() and old.get('sha256') == digest(target):
            item.update(status='saved', refresh_status='failed_retained_previous_version')
        else:
            item['status'] = 'unavailable'
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return item


def refresh_course_pages(previous):
    """Validate the entire page batch before replacing any archived page.

    A failed later HTTP response must not leave index.html newer than its
    recorded manifest while claiming that the previous snapshot was preserved.
    """
    old={r['url']:r for r in previous.get('resources',[])}
    staged=[]
    with tempfile.TemporaryDirectory(prefix='cs329z-site-') as temporary:
        for name in ('index.html','logistics.html','project.html'):
            url=BASE+name
            target=ROOT/'site'/name
            prior=old.get(url,{})
            if target.exists() and prior.get('sha256') and digest(target)!=prior['sha256']:
                raise ValueError('Local course page changed: '+str(target))
            response=requests.get(url,timeout=45,headers={'User-Agent':'CS329Z-public-study-archive/1.0'})
            response.raise_for_status()
            incoming=Path(temporary)/name
            incoming.write_bytes(response.content)
            metadata=inspect_download(incoming)
            text=BeautifulSoup(response.content,'html.parser').get_text(' ',strip=True)
            if not re.search(r'CS\s*329Z',text) or not re.search(r'Fall\s+2026',text):
                raise ValueError('Course identity or semester differs: '+url)
            if name=='index.html':
                parse_schedule(response.content)
            staged.append((incoming,target,dict(prior,title='Course '+name,url=url,kind='site',
                path='site/'+name,status='saved',sha256=digest(incoming),bytes=incoming.stat().st_size,
                retrieved_at=now(),final_url=response.url,content_type=response.headers.get('Content-Type',''),
                transport='Python requests; complete course-page batch validated',**metadata)))
        for incoming,target,item in staged:
            prior=old.get(item['url'],{})
            if target.exists() and digest(target)!=item['sha256']:
                sha=digest(target)
                backup=ROOT/'versions'/sha/item['path']
                backup.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(target,backup)
                item['history']=list(prior.get('history',[]))+[dict(path=str(backup.relative_to(ROOT)),sha256=sha,
                    retrieved_at=prior.get('retrieved_at'),replaced_at=now())]
            target.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent,suffix='.html',delete=False) as stream:
                stream.write(incoming.read_bytes())
                atomic=Path(stream.name)
            os.replace(atomic,target)
            for key in ('error','refresh_status','retrieved_at_basis','response_metadata_note'):
                item.pop(key,None)
            old[item['url']]=item
    previous['resources']=list(old.values())
    return previous


def parse_schedule(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = next((t for t in soup.find_all('table')
                  if 'Lecture' in t.get_text() and 'Week' in t.get_text()), None)
    if table is None:
        raise ValueError('Official schedule table absent; refusing to replace manifest')
    lessons, events = [], []
    for row in table.find_all('tr'):
        cells = row.find_all('td', recursive=False)
        if len(cells) != 4:
            continue
        week, date_text, lecture, reading = cells
        title_node = lecture.select_one('.lec-title') or lecture.find('strong') or lecture.find('b')
        title = title_node.get_text(' ', strip=True) if title_node else lecture.get_text(' ', strip=True)
        title = re.sub(r'^[📺\s]+', '', title)
        date_label = date_text.get_text(' ', strip=True)
        if not week.get_text(strip=True).isdigit() or not re.search(r'\b(?:Sep|Oct|Nov|Dec)\s+\d+', date_label):
            events.append(dict(week=week.get_text(' ', strip=True), date_label=date_label, title=title))
            continue
        month_day = re.search(r'\b(Sep|Oct|Nov|Dec)\s+(\d+)', date_label)
        month = {'Sep':9,'Oct':10,'Nov':11,'Dec':12}[month_day[1]]
        date = f"2026-{month:02d}-{int(month_day[2]):02d}"
        if 'No Class' in lecture.get_text() or 'Thanksgiving' in lecture.get_text():
            events.append(dict(week=week.get_text(' ', strip=True), date=date, date_label=date_label, title=title))
            continue
        number = len(lessons) + 1
        clean = re.sub(r'[^A-Za-z0-9]+', ' ', title)
        folder = str(number) + '.' + ''.join(w[0].upper() + w[1:] for w in clean.split())
        materials = [dict(label=a.get_text(' ', strip=True), url=normalized(a['href']))
                     for a in lecture.select('a[href]') if a.get_text(' ', strip=True) in ('Slides', 'Code')]
        readings = []
        for a in reading.select('a[href]'):
            preceding = a.find_previous(string=re.compile('Additional readings'))
            additional = bool(preceding and preceding.find_parent('td') == reading)
            readings.append(dict(label=a.get_text(' ', strip=True), url=normalized(a['href']),
                                 role='additional' if additional else 'assigned'))
        lessons.append(dict(number=number, week=int(week.get_text(strip=True)), date=date,
                            title=title, folder=folder, description=lecture.get_text(' ', strip=True),
                            materials=materials, readings=readings))
    if not lessons or len({x['date'] for x in lessons}) != len(lessons):
        raise ValueError('Empty or ambiguous course schedule')
    return lessons, events


def reading_title(label, url):
    registered = registered_material(url)
    if registered:
        return registered['title']
    quoted = re.search(r'["“](.+?)["”]', label)
    return quoted[1].rstrip('.') if quoted else re.sub(r'\s*\((?:19|20)\d\d\)\.?$', '', label).strip().rstrip('.')


def build_resources(lessons, previous):
    old = {r['url']: r for r in previous.get('resources', [])}
    resources = {}
    def add(title, url, kind, path, lesson=None, download_url=None):
        url = normalized(url)
        if url not in resources:
            resources[url] = {**old.get(url, {}), 'title':title, 'url':url, 'kind':kind,
                'path':path, 'download_url':download_url or url, 'lessons':[]}
            resources[url].setdefault('status', 'pending')
            prior=old.get(url,{})
            if prior.get('path') and prior['path']!=path:
                resources[url]['landing_snapshot']={k:prior[k] for k in ('path','sha256','retrieved_at') if k in prior}
                resources[url]['status']='pending'
                for key in ('sha256','bytes','pages','cover','html_title','retrieved_at'):
                    resources[url].pop(key,None)
        if lesson is not None and lesson not in resources[url]['lessons']:
            resources[url]['lessons'].append(lesson)
        if kind=='lecture':
            source_name=unquote(Path(urlparse(url).path).name)
            resources[url]['original_filename']=source_name
            match=re.search(r'lecture(\d+)',source_name,re.I)
            if match:
                resources[url]['official_filename_number']=int(match[1])
    for name in ('index.html', 'logistics.html', 'project.html'):
        add('Course ' + name, BASE + name, 'site', 'site/' + name)
    for name in ('index.html','logistics.html','project.html'):
        page = ROOT/'site'/name
        if not page.exists():
            continue
        soup=BeautifulSoup(page.read_bytes(),'html.parser')
        for tag in soup.select('img[src], script[src], link[href]'):
            href=tag.get('src') or tag.get('href')
            url=normalized(href)
            parsed=urlparse(url)
            if parsed.netloc==urlparse(BASE).netloc and parsed.path.startswith('/static/'):
                add(Path(parsed.path).name,url,'asset','site/'+parsed.path.lstrip('/'))
    add('Paper Video handout', 'https://web.stanford.edu/class/cs329z/assignments/paper_video.pdf',
        'handout','site/assignments/paper_video.pdf')
    for lesson in lessons:
        for m in lesson['materials']:
            if m['label'] == 'Slides':
                name = unquote(Path(urlparse(m['url']).path).name)
                add(lesson['title'], m['url'], 'lecture', 'site/slides/' + name, lesson['number'])
        for reading in lesson['readings']:
            title, url = reading_title(reading['label'], reading['url']), reading['url']
            match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', url)
            acl = re.match(r'https://aclanthology\.org/([^/]+)/?$',url)
            openreview = url.startswith('https://openreview.net/forum?id=')
            extension = '.pdf' if match or acl or openreview or urlparse(url).path.endswith('.pdf') else '.html'
            name = material_filename(title, url, extension)
            download_url = ('https://arxiv.org/pdf/' + match[1] if match else
                            'https://aclanthology.org/' + acl[1] + '.pdf' if acl else
                            url.replace('/forum?', '/pdf?') if openreview else url)
            add(title, url, 'reading', 'readings/' + ('papers/' if extension == '.pdf' else 'web/') + name,
                lesson['number'], download_url)
    return list(resources.values())


def reuse_existing(item):
    """Reuse exact archived versions, retaining their actual provenance."""
    if (ROOT/item['path']).exists() or item.get('kind') != 'reading':
        return False
    candidates = []
    registered = registered_material(item['url'])
    if registered:
        candidates.append(REPO / registered['path'])
    for manifest_path in (REPO/'MAS.S62/manifest.json',):
        if manifest_path.exists():
            for r in json.loads(manifest_path.read_text()).get('resources', []):
                if url_key(r['url']) == url_key(item['url']) and r.get('status') == 'saved':
                    candidates.append(manifest_path.parent/r['path'])
    for source in candidates:
        if not source.is_file() or source.suffix != Path(item['path']).suffix:
            continue
        try:
            metadata = inspect_download(source)
        except (ValueError, RuntimeError):
            continue
        # Explicitly versioned arXiv links may not silently reuse another version.
        version = re.search(r'(\d{4}\.\d{4,5}v\d+)', item['url'])
        if version and metadata.get('pdf_version') != version[1]:
            continue
        target = ROOT/item['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        item.update(metadata, status='saved', sha256=digest(target), bytes=target.stat().st_size,
                    reused_from=str(source.relative_to(REPO)), reused_at=now(),
                    provenance_note='Existing repository archive; not a new download or latest-version claim')
        return True
    return False


def material_target(item, lesson):
    return ROOT/lesson['folder']/('slides' if item['kind']=='lecture' else 'readings')/Path(item['path']).name


def organize(manifest):
    by_url = {r['url']:r for r in manifest['resources']}
    lecture_links = []
    for lesson in manifest['lessons']:
        folder = ROOT/lesson['folder']
        folder.mkdir(parents=True, exist_ok=True)
        lines = [f"# {lesson['number']}. {lesson['title']}", '',
            f"- 官网 Week：{lesson['week']}；日期：{lesson['date']}；本地编号按教学课次连续排列。",
            f"- 来源：{BASE}index.html#schedule", '', '## Lecture / code', '']
        for material in lesson['materials']:
            if material['label']=='Code':
                lines.extend([f"- [官方课堂代码]({material['url']})；固定快照见课程代码索引。"])
                continue
            item = by_url[material['url']]
            if item['status']=='saved':
                source, target = ROOT/item['path'], material_target(item, lesson)
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists() or digest(target)!=digest(source):
                    shutil.copy2(source, target)
                lines.extend([f"- [{target.name}]({local_link(target, folder)}) — {item.get('pages','?')} 页；SHA-256：`{item['sha256']}`",
                              f"  - Source: {item['url']}"])
                if item.get('official_filename_number'):
                    lines.append(f"  - 官方文件名编号：{item['official_filename_number']}；实际 PDF 页序从 1 开始，与 Week / 本地课次分别记录。")
                with fitz.open(source) as doc:
                    for page_no, page in enumerate(doc, 1):
                        for link in page.get_links():
                            if link.get('uri'):
                                lecture_links.append(dict(lesson=lesson['number'], pdf=str(target.relative_to(ROOT)),
                                                          page=page_no, url=link['uri']))
            else:
                lines.append(f"- {item['title']}：{item['status']}；{item['url']}")
        if not lesson['materials']:
            lines.append('- 官网尚未提供讲义/代码链接；不能推断为已经取得材料。')
        for role, heading in [('assigned','Assigned readings'),('additional','Additional readings')]:
            lines += ['', '## ' + heading, '']
            for reading in lesson['readings']:
                if reading['role'] != role:
                    continue
                item = by_url[reading['url']]
                if item['status']=='saved':
                    source, target = ROOT/item['path'], material_target(item, lesson)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists() or digest(target)!=digest(source):
                        shutil.copy2(source, target)
                    lines.extend([f"- [{item['title']}]({local_link(target, folder)})",
                                  f"  - Source: {item['url']}", f"  - SHA-256: `{item['sha256']}`"])
                    if item.get('pdf_version'):
                        lines.append(f"  - 实际归档版本：{item['pdf_version']}；不将官网的会议/期刊年份视为该 PDF 已是最终发表版。")
                    if item.get('html_title'):
                        lines.append(f"  - 实际归档页面标题：{item['html_title']}；官网阅读标签仍原样保留在 manifest 的课表记录中。")
                    if item.get('reused_from'):
                        lines.append(f"  - 复用既有归档：`{item['reused_from']}`；不表示本次新下载或当前最新版本。")
                else:
                    lines.append(f"- [{item['title']}]({item['url']}) — {item['status']}；尚未取得有效正文。")
        # Retire a classified landing-page copy only when the manifest records
        # the exact bytes; retain the original landing snapshot in readings/.
        for reading in lesson['readings']:
            item=by_url[reading['url']]
            landing=item.get('landing_snapshot',{})
            if landing.get('path') and landing.get('sha256'):
                stale=folder/'readings'/Path(landing['path']).name
                if stale.exists():
                    if digest(stale)!=landing['sha256']:
                        raise ValueError('Authored/changed classified landing copy requires manual reconciliation: '+str(stale))
                    stale.unlink()
        lines += ['', '## 中文讲解与补充参考', '']
        note = folder/'notes.zh-CN.md'
        lines.append('- [完整中文讲解](notes.zh-CN.md)' if note.exists() else '- 待取得并核实讲义后编写完整讲解。')
        references = folder/'REFERENCES.json'
        if references.exists():
            for r in json.loads(references.read_text()):
                lines.append(f"- [{r['title']}]({quote(r['path'],safe='/._-')}) — {r['status']}；{r['url']}")
                if r.get('version_note'):
                    lines.append('  - 版本边界：'+r['version_note'])
                if r.get('reused_from'):
                    lines.append('  - 复用已有归档：'+r['reused_from']+'；不记为本次新下载。')
        (folder/'SOURCES.md').write_text('\n'.join(lines)+'\n')
    info = ROOT/'0.CourseInformation'
    info.mkdir(exist_ok=True)
    (info/'SOURCES.md').write_text('# Stanford CS329Z — Engineering AI Agents\n\n'
        f'- 学期：{SEMESTER}\n- [官网原始页面](../site/index.html)\n'
        '- [课程安排与作业评分](../site/logistics.html)\n- [课程总入口](../README.md)\n'
        '- 录像需登录 Canvas；仅登记入口，不标记为公开归档。\n')
    table = ['| 课次 / Week / 日期 | 官网原题 | 讲义 | 中文讲解 |','|---|---|---|---|']
    for l in manifest['lessons']:
        slides = [by_url[m['url']] for m in l['materials'] if m['label']=='Slides']
        state = ', '.join(f"{r.get('pages','?')} 页" if r['status']=='saved' else r['status'] for r in slides) or '尚未公开'
        note = ROOT/l['folder']/'notes.zh-CN.md'
        table.append(f"| {l['number']} / {l['week']} / {l['date'][5:]} | [{l['title']}]({l['folder']}/SOURCES.md) | {state} | "
                     +(f"[完整讲解]({l['folder']}/notes.zh-CN.md)" if note.exists() else '待讲义公开/核实')+' |')
    saved_lectures = sum(r['kind']=='lecture' and r['status']=='saved' for r in manifest['resources'])
    read = [r for r in manifest['resources'] if r['kind']=='reading']
    readme = f'''# Stanford CS329Z：Engineering AI Agents

{SEMESTER}。按官网日期逐次编号，Week、课次、PDF Lecture 编号分别保留。官网可能调整课表，原始页面和来源版本均可追溯。

本轮索引日期：{manifest['snapshot_date']}。已核实归档 {saved_lectures} 份讲义；{len(read)} 个去重阅读入口中 {sum(r['status']=='saved' for r in read)} 个有有效正文。材料的复用来源和获取限制见 [SOURCES.md](SOURCES.md) 与 [manifest.json](manifest.json)。

[官网]({BASE}) · [课程信息](0.CourseInformation/SOURCES.md) · [作业](assignment/SOURCES.md) · [项目](project/SOURCES.md) · [课堂代码](code/SOURCES.md)

## 课程目录

'''+ '\n'.join(table)+'''

## 学习和证据边界

逐课 notes.zh-CN.md 以讲义的问题链为主线，指定阅读补机制与实验，Additional readings 和 references/ 补背景与实现。PDF 页码为从 1 开始的实际页序。正文区分来源结论、教学推导和工程建议；未运行的模型/API/GPU 实验明确说明。

site/ 和 readings/ 保留原始字节；各课 slides/、readings/ 为按课次分类的副本。论文和网页按完整标题命名，讲义和上游代码保留官方名称及结构。相同 URL 的修订需显式刷新，旧版保存在 versions/ 并标记 review_required，避免笔记继续引用旧页码。

## 同步与验证

```bash
python3 329z/sync.py
python3 329z/sync.py --organize-only
python3 329z/verify.py --require-notes --write-report
```

依赖 requests、beautifulsoup4、pymupdf。同步不覆盖中文讲解、补充参考及复核记录；失败重试保留已验证旧版并单独记录刷新失败。上游代码快照使用固定提交，见各 SNAPSHOT.json；学生待实现内容保留原貌。

Python HTTP 不可用时，可选用 `node 329z/download.mjs /tmp/cs329z-downloads` 获取待下载原始响应，再运行 `python3 329z/sync.py --import-downloads /tmp/cs329z-downloads` 验证导入。该传输脚本逐请求保存来源日志；大文件的分段下载只接受连续范围、强 ETag 和完整字节长度，审计记录随来源一起校验，不将摘要页或验证页冒充论文正文。

[CHECKSUMS.sha256](CHECKSUMS.sha256) · [讲义内嵌链接及 PDF 页码](LECTURE_LINKS.json) · [内容复核记录](REVIEW.json) · [结构与完整性验证](VERIFICATION.json)
'''
    (ROOT/'README.md').write_text(readme)
    lines = ['# CS329Z 全部来源', '', f"- 学期：{SEMESTER}；索引日期：{manifest['snapshot_date']}",
             '- saved 表示已检查正文；reused_from 表示复用旧归档，不是本次新下载。',
             '- 未公开、登录限制、下载失败分别保留；页面 HTTP 200 不足以证明有正文。','',
             '| 类型 | 标题 | 本地文件 / 状态 | 来源 |','|---|---|---|---|']
    for r in manifest['resources']:
        state = f"[{r['status']}]({quote(r['path'],safe='/._-')})" if r['status']=='saved' else r['status']
        lines.append(f"| {r['kind']} | {r['title'].replace('|','/')} | {state} | {r['url']} |")
    lines += ['', '## 非教学事件', '']
    lines.extend('- '+e['date_label']+'：'+e['title'] for e in manifest['events'])
    lines += ['', '## 其他来源与限制', '', '- [作业来源](assignment/SOURCES.md)；[项目来源](project/SOURCES.md)；[课堂代码](code/SOURCES.md)。',
              '- Canvas 录像需课程权限；本次未取得录像正文。', '- HW2 以官网当前实际链接为准，不通过猜测 URL 宣称已获取。']
    (ROOT/'SOURCES.md').write_text('\n'.join(lines)+'\n')
    write_json(ROOT/'LECTURE_LINKS.json', lecture_links)
    checks = {r['path']:r['sha256'] for r in manifest['resources'] if r['status']=='saved'}
    for r in manifest['resources']:
        if r.get('acquisition_audit'):
            audit=ROOT/r['acquisition_audit']
            if not audit.is_file():
                raise ValueError('Missing original range acquisition audit: '+r['acquisition_audit'])
            r.setdefault('acquisition_audit_sha256',digest(audit))
            if r['acquisition_audit_sha256']!=digest(audit):
                raise ValueError('Changed range acquisition audit: '+r['acquisition_audit'])
            checks[r['acquisition_audit']]=r['acquisition_audit_sha256']
        for saved in [r.get('landing_snapshot',{})]+r.get('history',[]):
            if saved.get('path') and saved.get('sha256'):
                checks[saved['path']]=saved['sha256']
    for l in manifest['lessons']:
        refs = ROOT/l['folder']/'REFERENCES.json'
        if refs.exists():
            for r in json.loads(refs.read_text()):
                if r['status']=='saved':
                    checks[l['folder']+'/'+r['path']] = r['sha256']
    for snap in ROOT.rglob('SNAPSHOT.json'):
        snapshot = json.loads(snap.read_text())
        for relative, sha in snapshot.get('files', {}).items():
            checks[str((snap.parent/relative).relative_to(ROOT))] = sha
    (ROOT/'CHECKSUMS.sha256').write_text(''.join(f'{sha}  {path}\n' for path,sha in sorted(checks.items())))
    write_json(ROOT/'manifest.json',manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--organize-only', action='store_true')
    parser.add_argument('--refresh-materials', action='store_true')
    parser.add_argument('--plan-only', action='store_true', help='Prepare manifest/download plan from already archived home page')
    parser.add_argument('--import-downloads', type=Path, help='Validate original bytes from download.mjs staging and import their provenance')
    parser.add_argument('--import-ranges', type=Path, help='Validate completed ETag/byte-range PDF downloads')
    args = parser.parse_args()
    manifest_path = ROOT/'manifest.json'
    old = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if args.import_ranges:
        staging=args.import_ranges.resolve()
        for item in old['resources']:
            candidate=staging/Path(item['path']).name
            audit_path=candidate.with_name(candidate.name+'.acquisition.json')
            if not candidate.exists() or not audit_path.exists():
                continue
            audit=json.loads(audit_path.read_text())
            if audit['url']!=item['download_url'] or digest(candidate)!=audit['sha256'] or candidate.stat().st_size!=audit['total']:
                raise ValueError('Completed range download provenance mismatch')
            metadata=inspect_download(candidate)
            cursor=0
            for r in audit['ranges']:
                if r['start']!=cursor or r['end']-r['start']+1!=r['bytes'] or r['etag']!=audit['etag']:
                    raise ValueError('Incomplete/mixed-version byte range audit')
                cursor=r['end']+1
            if cursor!=audit['total']:
                raise ValueError('Byte ranges do not cover original length')
            target=ROOT/item['path']
            if target.exists() and item.get('status')=='saved' and digest(target)!=audit['sha256']:
                raise ValueError('Range import cannot silently replace verified old version')
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(candidate,target)
            provenance=ROOT/'acquisition'/audit_path.name
            provenance.parent.mkdir(exist_ok=True)
            shutil.copy2(audit_path,provenance)
            item.update(metadata,status='saved',sha256=audit['sha256'],bytes=audit['total'],
                        retrieved_at=audit['completed_at'],final_url=audit['ranges'][0]['final_url'],
                        etag=audit['etag'],acquisition_audit=str(provenance.relative_to(ROOT)),
                        acquisition_audit_sha256=digest(provenance),
                        transport='Validated original HTTP byte ranges; no content conversion')
            item.pop('error',None)
        write_json(manifest_path,old)
        organize(old)
        print('Imported complete, validated range downloads')
        return
    if args.import_downloads:
        staging = args.import_downloads.resolve()
        records = {r['url']:r for r in json.loads((staging/'download-log.json').read_text())}
        for item in old['resources']:
            record = records.get(item['url'])
            if not record:
                continue
            if record['transport_status']!='downloaded_unvalidated':
                if item.get('status')!='saved':
                    item.update(status='unavailable',error=record.get('error','Download failed'),checked_at=record['attempted_at'])
                continue
            path = (staging/record['path']).resolve()
            if not path.is_relative_to(staging) or record['path']!=item['path']:
                raise ValueError('Unsafe or inconsistent imported path')
            try:
                metadata = inspect_download(path)
                if digest(path)!=record['sha256']:
                    raise ValueError('Imported transport checksum differs')
                target=ROOT/item['path']
                if target.exists() and item.get('status')=='saved' and digest(target)!=record['sha256']:
                    raise ValueError('Import cannot silently replace a verified old version; use explicit refresh')
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(path,target)
                item.update(metadata,status='saved',sha256=record['sha256'],bytes=record['bytes'],
                            retrieved_at=record['retrieved_at'],final_url=record['final_url'],
                            content_type=record['content_type'],content_disposition=record.get('content_disposition'),
                            transport='Node fetch; validated by sync.py')
                if record.get('retrieved_at_basis'):
                    item['retrieved_at_basis']=record['retrieved_at_basis']
                    item['final_url']=None
                    item['response_metadata_note']='Response headers and final redirect URL not recovered after transport interruption; download_url records requested source.'
                item.pop('error',None)
                item.pop('import_status',None)
            except (ValueError, RuntimeError) as exc:
                target=ROOT/item['path']
                if item.get('status')=='saved' and target.exists() and digest(target)==item.get('sha256'):
                    item.update(import_status='failed_retained_previous_version',error=str(exc),checked_at=now())
                else:
                    item.update(status='unavailable',error=str(exc),checked_at=now())
        write_json(manifest_path,old)
        organize(old)
        print(json.dumps({r['url']:r['status'] for r in old['resources']},ensure_ascii=False,indent=2))
        return
    if args.organize_only:
        if not old:
            parser.error('No manifest; run the initial sync first')
        organize(old)
        return
    if not args.plan_only:
        try:
            old=refresh_course_pages(old)
        except (requests.RequestException,OSError,ValueError,RuntimeError) as exc:
            raise SystemExit('Cannot verify complete current course-page batch; archived pages and manifest preserved: '+str(exc))
    lessons, events = parse_schedule((ROOT/'site/index.html').read_text())
    resources = build_resources(lessons, old)
    manifest = dict(course='Stanford CS329Z — Engineering AI Agents', semester=SEMESTER,
                    snapshot_date=now()[:10], base_url=BASE, lessons=lessons, events=events, resources=resources)
    for item in resources:
        reuse_existing(item)
    if not args.plan_only:
        with ThreadPoolExecutor(max_workers=4) as pool:
            resources[:] = list(pool.map(lambda r:fetch(r, refresh=args.refresh_materials and r['kind']!='site'), resources))
    write_json(manifest_path, manifest)
    organize(manifest)
    print(json.dumps(dict(lessons=len(lessons), saved=sum(r['status']=='saved' for r in resources),
                          unavailable=[r['url'] for r in resources if r['status']!='saved']),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
