import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('package_pages',Path(__file__).resolve().parents[1]/'scripts/package_pages.py')
pages=importlib.util.module_from_spec(spec);spec.loader.exec_module(pages)


class PagesTests(unittest.TestCase):
    def test_package_contains_website_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            root.joinpath('index.html').write_text('<script id="data" type="application/json">[]</script>')
            root.joinpath('private.txt').write_text('NOT_FOR_WEBSITE')
            root.joinpath('_site').mkdir();root.joinpath('_site/old.txt').write_text('OLD')
            self.assertEqual(pages.package(root),0)
            self.assertEqual({p.name for p in root.joinpath('_site').iterdir()},{'index.html','.nojekyll'})

    def test_private_fields_and_unsafe_links_rejected(self):
        base={'id':'a','title':'Role','company':'Example','url':'https://example.org/1','status':'Unverified'}
        for job in [{**base,'notes':'PRIVATE'},{**base,'url':'javascript:alert(1)'}]:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);root.joinpath('index.html').write_text('<script id="data" type="application/json">'+json.dumps([job])+'</script>')
                with self.assertRaises(ValueError):pages.package(root)

    def test_unrendered_site_is_not_published(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.joinpath('index.html').write_text('__DISCOVERED__')
            with self.assertRaises(ValueError):pages.package(root)
