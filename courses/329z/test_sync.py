"""Regression checks for schedule mapping and source preservation; no network."""
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import fitz
import requests
import pytest
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('cs329z_sync',Path(__file__).with_name('sync.py'))
sync=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def make_pdf(text):
    with fitz.open() as doc:
        page=doc.new_page()
        page.insert_text((72,72),text)
        return doc.tobytes()


def test_official_timetable_separates_week_lesson_and_events():
    lessons,events=sync.parse_schedule((sync.ROOT/'site/index.html').read_text())
    assert len(lessons)==19
    assert (lessons[1]['number'],lessons[1]['week'],lessons[1]['date'])==(2,2,'2026-09-28')
    assert lessons[5]['title']=='Agent Design Patterns & Scaffolds'
    assert len(events)==3
    assert any('Final' in x['title'] for x in events)
    assert [x['role'] for x in lessons[5]['readings']]==['assigned']*3+['additional']*2


def test_invalid_pdf_refresh_preserves_verified_original(tmp_path,monkeypatch):
    monkeypatch.setattr(sync,'ROOT',tmp_path)
    original=tmp_path/'lecture.pdf'
    original.write_bytes(make_pdf('original source'))
    original_hash=sync.digest(original)
    response=Mock(content=b'<html>login</html>',url='https://example.org/login',headers={})
    monkeypatch.setattr(sync.requests,'get',Mock(return_value=response))
    item=sync.fetch(dict(url='https://example.org/lecture.pdf',path='lecture.pdf',status='saved',sha256=original_hash),refresh=True)
    assert item['status']=='saved'
    assert item['refresh_status']=='failed_retained_previous_version'
    assert sync.digest(original)==original_hash
    assert not list(tmp_path.glob('tmp*'))


def test_revised_pdf_keeps_old_bytes_and_requires_content_review(tmp_path,monkeypatch):
    monkeypatch.setattr(sync,'ROOT',tmp_path)
    original=tmp_path/'lecture.pdf'
    original.write_bytes(make_pdf('version one'))
    old_hash=sync.digest(original)
    response=Mock(content=make_pdf('version two'),url='https://example.org/lecture.pdf',headers={})
    monkeypatch.setattr(sync.requests,'get',Mock(return_value=response))
    item=sync.fetch(dict(url=response.url,path='lecture.pdf',status='saved',sha256=old_hash,
                         etag='old-etag',acquisition_audit='old-audit.json'),refresh=True)
    assert item['status']=='saved' and item['review_required']
    assert sync.digest(tmp_path/item['history'][0]['path'])==old_hash
    assert sync.digest(original)!=old_hash
    assert 'etag' not in item and 'acquisition_audit' not in item
    assert item['history'][0]['source_provenance']['etag']=='old-etag'


def test_failed_first_download_is_not_marked_saved(tmp_path,monkeypatch):
    monkeypatch.setattr(sync,'ROOT',tmp_path)
    monkeypatch.setattr(sync.requests,'get',Mock(side_effect=requests.Timeout('fixture timeout')))
    item=sync.fetch(dict(url='https://example.org/lecture.pdf',path='lecture.pdf'))
    assert item['status']=='unavailable'
    assert not (tmp_path/'lecture.pdf').exists()


def test_empty_or_unexpected_course_page_rejected():
    import pytest
    with pytest.raises(ValueError):
        sync.parse_schedule('<html><h1>Sign in</h1></html>')


def test_local_source_mutation_is_never_blessed_as_new_download(tmp_path,monkeypatch):
    monkeypatch.setattr(sync,'ROOT',tmp_path)
    source=tmp_path/'lecture.pdf'
    source.write_bytes(make_pdf('trusted source'))
    trusted_hash=sync.digest(source)
    source.write_bytes(make_pdf('changed locally'))
    network=Mock()
    monkeypatch.setattr(sync.requests,'get',network)
    item=sync.fetch(dict(url='https://example.org/source.pdf',path='lecture.pdf',status='saved',sha256=trusted_hash))
    assert item['status']=='unavailable'
    assert item['sha256']==trusted_hash
    assert 'recorded checksum' in item['error']
    network.assert_not_called()


def test_failed_course_page_batch_preserves_all_archived_pages(tmp_path,monkeypatch):
    original_home=(sync.ROOT/'site/index.html').read_bytes()
    monkeypatch.setattr(sync,'ROOT',tmp_path)
    site=tmp_path/'site'
    site.mkdir()
    prior=[]
    for name in ('index.html','logistics.html','project.html'):
        p=site/name
        p.write_bytes(b'old verified bytes '+name.encode())
        prior.append(dict(url=sync.BASE+name,path='site/'+name,status='saved',sha256=sync.digest(p)))
    response=Mock(content=original_home,url=sync.BASE+'index.html',headers={})
    monkeypatch.setattr(sync.requests,'get',Mock(side_effect=[response,requests.Timeout('second page timeout')]))
    import pytest
    with pytest.raises(requests.Timeout):
        sync.refresh_course_pages({'resources':prior})
    assert all(sync.digest(site/Path(item['path']).name)==item['sha256'] for item in prior)
    assert not (tmp_path/'versions').exists()


def test_title_change_retains_authored_lesson_folder():
    html = (sync.ROOT / 'site/index.html').read_text()
    previous, _ = sync.parse_schedule(html)
    changed = html.replace(previous[0]['title'], previous[0]['title'] + ' (Updated)')
    lessons, _ = sync.parse_schedule(changed, previous)
    assert lessons[0]['title'].endswith('(Updated)')
    assert [(l['number'], l['folder']) for l in lessons] == [(l['number'], l['folder']) for l in previous]


def test_inserted_lesson_gets_new_number_without_moving_existing_folders():
    html = (sync.ROOT / 'site/index.html').read_text()
    previous, _ = sync.parse_schedule(html)
    soup = BeautifulSoup(html, 'html.parser')
    table = next(t for t in soup.find_all('table') if 'Lecture' in t.get_text() and 'Week' in t.get_text())
    row = BeautifulSoup('<tr><td>1</td><td>Sep 24</td><td><b>Added workshop</b></td><td></td></tr>', 'html.parser').tr
    table.find_all('tr')[1].insert_after(row)
    lessons, _ = sync.parse_schedule(str(soup), previous)
    assert lessons[1]['number'] == 20
    assert lessons[1]['folder'] == '20.AddedWorkshop'
    assert [(l['number'], l['folder']) for l in lessons if l['number'] != 20] == [(l['number'], l['folder']) for l in previous]


def test_reschedule_retains_identity_and_removal_requires_explicit_mapping():
    html = (sync.ROOT / 'site/index.html').read_text()
    previous, _ = sync.parse_schedule(html)
    lessons, _ = sync.parse_schedule(html.replace('Sep 23', 'Sep 24'), previous)
    assert lessons[0]['date'] == '2026-09-24'
    assert lessons[0]['folder'] == previous[0]['folder']
    with pytest.raises(ValueError, match='explicit mapping'):
        sync.preserve_lesson_identity(lessons[1:], previous)


def prepare_page_refresh(tmp_path, monkeypatch):
    pages = {name: (sync.ROOT / 'site' / name).read_bytes()
             for name in ('index.html', 'logistics.html', 'project.html')}
    lessons, events = sync.parse_schedule(pages['index.html'])
    monkeypatch.setattr(sync, 'ROOT', tmp_path)
    (tmp_path / 'site').mkdir()
    resources = []
    originals = {}
    for name, content in pages.items():
        path = tmp_path / 'site' / name
        path.write_bytes(content)
        originals['site/' + name] = content
        resources.append(dict(url=sync.BASE + name, path='site/' + name, status='saved', sha256=sync.digest(path)))
    previous = dict(lessons=lessons, events=events, resources=resources)
    originals['manifest.json'] = json.dumps(previous).encode()
    (tmp_path / 'manifest.json').write_bytes(originals['manifest.json'])
    # Every page is visibly different; the home-page rename must retain identity.
    pages = {name: content + b'\n<!-- refreshed -->' for name, content in pages.items()}
    pages['index.html'] = pages['index.html'].replace(lessons[0]['title'].encode(), (lessons[0]['title'] + ' (Updated)').encode())
    responses = {sync.BASE + name: Mock(content=content, url=sync.BASE + name, headers={}) for name, content in pages.items()}
    monkeypatch.setattr(sync.requests, 'get', lambda url, **kwargs: responses[url])
    return previous, originals, pages


@pytest.mark.parametrize('failed_path', ['site/logistics.html', 'manifest.json'])
def test_page_or_manifest_commit_failure_rolls_back_and_can_retry(tmp_path, monkeypatch, failed_path):
    previous, originals, pages = prepare_page_refresh(tmp_path, monkeypatch)
    replace = sync.os.replace
    failed = False

    def fail_once(source, destination):
        nonlocal failed
        if Path(destination) == tmp_path / failed_path and not failed:
            failed = True
            raise OSError('simulated commit failure')
        return replace(source, destination)

    monkeypatch.setattr(sync.os, 'replace', fail_once)
    with pytest.raises(OSError, match='simulated commit failure'):
        sync.refresh_course_pages(previous)
    assert failed
    assert all((tmp_path / path).read_bytes() == content for path, content in originals.items())
    assert not (tmp_path / '.page-refresh').exists()
    updated = sync.refresh_course_pages(previous)
    assert json.loads((tmp_path / 'manifest.json').read_text()) == updated
    assert all((tmp_path / 'site' / name).read_bytes() == content for name, content in pages.items())
    assert updated['lessons'][0]['folder'] == previous['lessons'][0]['folder']
    assert all(sync.digest(tmp_path / item['path']) == item['sha256'] for item in updated['resources'] if item['kind'] == 'site')


@pytest.mark.parametrize('committed', [False, True])
def test_interrupted_page_commit_recovers_on_next_start(tmp_path, monkeypatch, committed):
    monkeypatch.setattr(sync, 'ROOT', tmp_path)
    recovery = tmp_path / '.page-refresh'
    recovery.mkdir()
    originals = {'site/index.html': b'old page', 'manifest.json': b'old manifest'}
    journal = []
    for index, (path, content) in enumerate(originals.items()):
        (recovery / str(index)).write_bytes(content)
        journal.append(dict(path=path, backup=str(index)))
        (tmp_path / path).parent.mkdir(exist_ok=True)
        (tmp_path / path).write_bytes(b'new bytes')
    (recovery / 'journal.json').write_text(json.dumps(journal))
    if committed:
        (recovery / 'committed').write_bytes(b'complete')
    sync.recover_page_refresh()
    assert all((tmp_path / path).read_bytes() == (b'new bytes' if committed else content) for path, content in originals.items())
    assert not recovery.exists()
