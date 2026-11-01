#!/usr/bin/env python3
"""Offline integrity/coverage checks; content review is recorded separately.

python3 329z/verify.py --require-notes --write-report
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from urllib.parse import unquote, urlparse

import fitz

from sync import ROOT, REPO, digest, inspect_download, material_target, parse_schedule

sys.path.insert(0, str(REPO/'tools'))
from verify_course_notes import targets, prose


def verify(require_notes=False):
    manifest = json.loads((ROOT/'manifest.json').read_text())
    errors, limitations = [], []
    lessons, events = parse_schedule((ROOT/'site/index.html').read_text())
    keys = ('number','week','date','title','folder','materials','readings')
    if [[l[k] for k in keys] for l in lessons] != [[l[k] for k in keys] for l in manifest['lessons']]:
        errors.append('Manifest differs from archived official timetable')
    if events != manifest['events']:
        errors.append('Non-teaching schedule events differ')
    allowed = {l['folder'] for l in lessons}|{'0.CourseInformation'}
    for folder in ROOT.iterdir():
        if folder.is_dir() and re.match(r'^\d+\.',folder.name) and folder.name not in allowed:
            errors.append('Unindexed teaching folder: '+folder.name)
    by_url, sources = {}, 0
    page_counts = {}
    for r in manifest['resources']:
        if r['url'] in by_url:
            errors.append('Duplicate resource URL: '+r['url'])
        by_url[r['url']]=r
        if r.get('sha256') and (ROOT/r['path']).is_file() and digest(ROOT/r['path'])!=r['sha256']:
            errors.append('Local source differs from trusted recorded checksum: '+r['path'])
        if r['status']!='saved':
            limitations.append(dict(url=r['url'],status=r['status'],reason=r.get('error','not acquired')))
            continue
        path = ROOT/r['path']
        if not path.is_file() or digest(path)!=r.get('sha256'):
            errors.append('Missing/changed archived source: '+r['path'])
            continue
        try:
            metadata = inspect_download(path)
            if path.suffix=='.pdf':
                page_counts[path.resolve()] = metadata['pages']
                if metadata['pages']!=r.get('pages'):
                    errors.append('Stale PDF metadata: '+r['path'])
        except (ValueError, RuntimeError) as exc:
            errors.append('Invalid saved body: '+r['path']+': '+str(exc))
        if r.get('reused_from'):
            origin = REPO/r['reused_from']
            if not origin.is_file() or digest(origin)!=r['sha256']:
                errors.append('Reused origin hash differs: '+r['path'])
        if r.get('kind')=='lecture' and r.get('review_required'):
            errors.append('Revised lecture still requires note review: '+r['path'])
        if r.get('acquisition_audit'):
            audit_path=ROOT/r['acquisition_audit']
            if not audit_path.is_file() or digest(audit_path)!=r.get('acquisition_audit_sha256'):
                errors.append('Range acquisition audit missing or changed: '+r['acquisition_audit'])
            else:
                audit=json.loads(audit_path.read_text())
                if audit['sha256']!=r['sha256'] or audit['total']!=r['bytes'] or audit['url']!=r['download_url']:
                    errors.append('Range acquisition audit refers to different source bytes: '+r['acquisition_audit'])
                cursor=0
                for chunk in audit['ranges']:
                    if chunk['start']!=cursor or chunk['end']-chunk['start']+1!=chunk['bytes'] or chunk['etag']!=audit['etag']:
                        errors.append('Mixed or incomplete byte ranges: '+r['acquisition_audit'])
                        break
                    cursor=chunk['end']+1
                if cursor!=r['bytes']:
                    errors.append('Byte ranges do not cover source length: '+r['acquisition_audit'])
        if r.get('refresh_status'):
            limitations.append(dict(url=r['url'],status=r['refresh_status']))
        if r.get('import_status'):
            limitations.append(dict(url=r['url'],status=r['import_status']))
        for old in r.get('history',[]):
            if not (ROOT/old['path']).is_file() or digest(ROOT/old['path'])!=old['sha256']:
                errors.append('Missing historical source version: '+old['path'])
        sources+=1
    notes, copies, refs, links, snapshots = [], 0, 0, 0, 0
    review_path = ROOT/'REVIEW.json'
    review = json.loads(review_path.read_text()) if review_path.exists() else {}
    reviews = {r['note']:r for r in review.get('documents',[])}
    for record in review.get('independent_review_reports',[]):
        report_path=ROOT/record['path']
        if not report_path.is_file() or digest(report_path)!=record['sha256']:
            errors.append('Independent review report missing or changed: '+record['path'])
    for l in lessons:
        folder = ROOT/l['folder']
        if not (folder/'SOURCES.md').is_file():
            errors.append('Missing lesson index: '+l['folder'])
        material_urls = [m['url'] for m in l['materials'] if m['label']=='Slides']+[r['url'] for r in l['readings']]
        expected = set()
        lectures = []
        for url in material_urls:
            r = by_url[url]
            if r['status']!='saved':
                continue
            target = material_target(r,l)
            expected.add(target.resolve())
            if not target.is_file() or digest(target)!=r['sha256']:
                errors.append('Classification missing/changed: '+str(target.relative_to(ROOT)))
            copies+=1
            if r['kind']=='lecture':
                lectures.append(r)
        for sub in ('slides','readings'):
            for p in (folder/sub).glob('*'):
                if p.is_file() and p.resolve() not in expected:
                    errors.append('Unindexed classified material: '+str(p.relative_to(ROOT)))
        note = folder/'notes.zh-CN.md'
        if require_notes and lectures and not note.is_file():
            errors.append('Missing complete Chinese guide: '+l['folder'])
        if note.is_file():
            text = note.read_text()
            notes.append(dict(lesson=l['number'],path=str(note.relative_to(ROOT)),characters=len(text),sha256=digest(note)))
            record = reviews.get(str(note.relative_to(REPO)))
            if require_notes and (not record or record.get('status')!='passed' or record.get('final_sha256')!=digest(note)):
                errors.append('Missing/stale content review: '+str(note.relative_to(ROOT)))
            if record:
                for lecture in lectures:
                    bound=str((ROOT/lecture['path']).relative_to(REPO))
                    classified=str(material_target(lecture,l).relative_to(REPO))
                    bindings=record.get('source_sha256',{})
                    if bindings.get(bound)!=lecture['sha256'] and bindings.get(classified)!=lecture['sha256']:
                        errors.append('Content review does not bind the actual main lecture: '+str(note.relative_to(ROOT)))
                for source, sha in record.get('source_sha256',{}).items():
                    if not (REPO/source).is_file() or digest(REPO/source)!=sha:
                        errors.append('Review source version changed: '+source)
        extra = folder/'REFERENCES.json'
        if extra.exists():
            for r in json.loads(extra.read_text()):
                if r['status']!='saved':
                    continue
                path = folder/r['path']
                if not path.is_file() or digest(path)!=r['sha256']:
                    errors.append('Supplemental source missing/changed: '+str(path.relative_to(ROOT)))
                refs+=1
    for p in ROOT.rglob('*.md'):
        if any(k in p.relative_to(ROOT).parts for k in ('site','readings','references','upstream')):
            continue
        text = p.read_text()
        if p.name=='notes.zh-CN.md':
            try:
                body = prose(text)
                if re.search(r'\\[\[\]\(\)]|\ue200(?:filecite|cite)|turn\d+(?:file|view|search)\d+',body):
                    errors.append('Unsupported math/citation marker: '+str(p.relative_to(ROOT)))
            except ValueError as exc:
                errors.append(str(p.relative_to(ROOT))+': '+str(exc))
        for target in targets(text):
            parsed=urlparse(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            local=p.parent/unquote(parsed.path)
            if not local.exists():
                errors.append('Broken local link in '+str(p.relative_to(ROOT))+': '+target)
                continue
            links+=1
            match=re.search(r'(?:^|&)page=(\d+)',parsed.fragment)
            if local.suffix=='.pdf' and match:
                if local.resolve() not in page_counts:
                    with fitz.open(local) as doc:
                        page_counts[local.resolve()]=len(doc)
                if not 1<=int(match[1])<=page_counts[local.resolve()]:
                    errors.append('PDF page outside source bounds in '+str(p.relative_to(ROOT))+': '+target)
    for snap in ROOT.rglob('SNAPSHOT.json'):
        data=json.loads(snap.read_text())
        if not re.fullmatch(r'[a-f0-9]{40}',data.get('commit','')):
            errors.append('Snapshot missing fixed commit: '+str(snap.relative_to(ROOT)))
        expected=set(data.get('files',{}))
        if not expected:
            errors.append('Snapshot missing file inventory: '+str(snap.relative_to(ROOT)))
        for relative,sha in data.get('files',{}).items():
            path=snap.parent/relative
            if not path.is_file() or digest(path)!=sha:
                errors.append('Snapshot file missing/changed: '+str(path.relative_to(ROOT)))
        upstream=snap.parent/'upstream'
        actual={str(f.relative_to(snap.parent)) for f in upstream.rglob('*') if f.is_file()}
        if actual!=expected:
            errors.append('Snapshot inventory incomplete or polluted: '+str(snap.relative_to(ROOT)))
        snapshots+=1
    example_runs=0
    for result_path in ROOT.glob('*/EXAMPLES.json'):
        result=json.loads(result_path.read_text())
        command=result['command']
        parts=shlex.split(command) if isinstance(command,str) else command
        script=REPO/parts[1]
        if not script.is_file() or digest(script)!=result['script_sha256']:
            errors.append('Teaching example differs from recorded run: '+str(result_path.relative_to(ROOT)))
        if result.get('exit_code')!=0:
            errors.append('Teaching example run failed: '+str(result_path.relative_to(ROOT)))
        example_runs+=1
    checks=ROOT/'CHECKSUMS.sha256'
    for line in checks.read_text().splitlines():
        sha,relative=line.split('  ',1)
        if not (ROOT/relative).is_file() or digest(ROOT/relative)!=sha:
            errors.append('CHECKSUMS mismatch: '+relative)
    return dict(course='329z',checked_at=__import__('sync').now(),scope='Offline structure, coverage, source versions, snapshot bytes and local PDF page bounds; semantic review separately in REVIEW.json; no model benchmark replication',
                lessons=len(lessons),saved_sources=sources,classifications=copies,guides=notes,
                supplementary_sources=refs,checked_local_links=links,code_snapshots=snapshots,
                published_lectures=sum(r['kind']=='lecture' and r['status']=='saved' for r in manifest['resources']),
                complete_guides=len(notes),verified_example_runs=example_runs,
                limitations=limitations,errors=errors)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-notes',action='store_true')
    parser.add_argument('--write-report',action='store_true')
    args=parser.parse_args()
    result=verify(args.require_notes)
    if args.write_report:
        from sync import write_json
        write_json(ROOT/'VERIFICATION.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(bool(result['errors']))


if __name__=='__main__':
    main()
