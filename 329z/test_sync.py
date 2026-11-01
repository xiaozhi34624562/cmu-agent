"""Regression checks for schedule mapping and source preservation; no network."""
import importlib.util
from pathlib import Path
from unittest.mock import Mock

import fitz
import requests

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
