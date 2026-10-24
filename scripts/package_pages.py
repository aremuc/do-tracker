"""Validate and stage only the public website for GitHub Pages."""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tracker.core import PUBLIC_JOB_FIELDS


def package(root=ROOT):
    root = Path(root)
    source = (root/'index.html').read_text(encoding='utf-8')
    if any(marker in source for marker in ('__JOBS__','__DISCOVERED__','__TODAY__','__UPDATED__')):
        raise ValueError('Unrendered website placeholders')
    match = re.search(r'<script id="data" type="application/json">(.*?)</script>',source,re.S)
    if not match:
        raise ValueError('Missing public listing payload')
    jobs = json.loads(match[1])
    if not isinstance(jobs,list):
        raise ValueError('Listing payload must be a list')
    for job in jobs:
        if not isinstance(job,dict) or set(job)-PUBLIC_JOB_FIELDS:
            raise ValueError('Unexpected or private listing fields')
        if not {'id','title','company','url','status'}.issubset(job):
            raise ValueError('Incomplete job metadata')
        if not re.match(r'^https?://',job['url'],re.I):
            raise ValueError('Unsafe application link')
    output = root/'_site'
    if output.is_symlink():
        raise ValueError('Site output must not be a symlink')
    if output.exists():
        for child in output.iterdir():
            if child.is_symlink() or child.is_file():
                child.unlink()
            else:
                shutil.rmtree(child)
    else:
        output.mkdir()
    (output/'index.html').write_text(source,encoding='utf-8')
    (output/'.nojekyll').write_text('')
    return len(jobs)


if __name__=='__main__':
    print(f'Packaged {package()} public listings; only index.html and .nojekyll included.')
