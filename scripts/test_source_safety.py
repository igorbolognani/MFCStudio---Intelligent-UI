import base64,gzip,importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('source_safety',Path(__file__).with_name('source_safety.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SourceSafetyTests(unittest.TestCase):
 def test_publisher_runtime_removed_science_preserved(self):
  key=('AI'+'za'+'X'*35)
  s='<article><h1>Article</h1><p>Conductivity 4 S/m</p><math>x</math><a href="license">CC BY</a></article><script>var mapKey="'+key+'"</script>'
  clean=m.sanitize_html(s)
  self.assertNotIn(key,clean);self.assertNotIn('<script',clean);self.assertIn('Conductivity 4 S/m',clean);self.assertIn('<math>x</math>',clean);self.assertIn('CC BY',clean)
 def test_math_script_preserved_without_executable_script(self):
  self.assertIn('x &lt; y',m.sanitize_html('<script type="math/tex">x < y</script>'))
 def test_embedded_gzip_is_checked_not_only_visible_json(self):
  key=b'AI'+b'za'+b'X'*35;v=json.dumps([{'content_base64':base64.b64encode(gzip.compress(key)).decode()}]).encode()
  hits=m.inspect_bytes(v,'assets.json');self.assertTrue(hits);self.assertIn('gzip',hits[0]['path'])
 def test_current_source_has_no_key(self):self.assertEqual(m.scan_current(),[])
if __name__=='__main__':unittest.main()
