from pathlib import Path
import base64
import gzip
import hashlib
import importlib.util
import json
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('corpus_compression', ROOT/'scripts/corpus_compression.py')
compression = importlib.util.module_from_spec(spec); spec.loader.exec_module(compression)


class CorpusCompressionTests(unittest.TestCase):
    def test_all_published_payloads_and_hashes_are_preserved(self):
        assets = json.loads((ROOT/'science/corpus-embedded-assets.json').read_text())
        for asset in assets:
            original = base64.b64decode(asset['content_base64'])
            actual = compression.canonical_gzip(gzip.decompress(original))
            self.assertEqual(actual, original, asset['id'])
            self.assertEqual(hashlib.sha256(actual).hexdigest(), asset['sha256'])

    def test_stdlib_header_variants_produce_identical_published_format(self):
        native = gzip.compress
        data = 'Preservar o conteúdo científico, fórmulas e unidades: Ω, µm.'.encode()
        expected = compression.canonical_gzip(data)
        for marker in [0, 3, 255]:
            def varying_header(payload, *, compresslevel, mtime):
                self.assertEqual(compresslevel, 9)
                self.assertEqual(mtime, 0)
                result = native(payload, compresslevel=compresslevel, mtime=mtime)
                return result[:9] + bytes([marker]) + result[10:]
            with patch.object(compression.gzip, 'compress', side_effect=varying_header):
                self.assertEqual(compression.canonical_gzip(data), expected)

    def test_empty_and_binary_data_round_trip_without_timestamp(self):
        for payload in [b'', b'\x00\xff\x1f\x8b' * 500]:
            encoded = compression.canonical_gzip(payload)
            self.assertEqual(gzip.decompress(encoded), payload)
            self.assertEqual(encoded[4:8], b'\x00' * 4)
            self.assertEqual(encoded[9], 3)


if __name__ == '__main__':
    unittest.main()
