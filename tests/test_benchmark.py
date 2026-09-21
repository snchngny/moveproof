import tempfile
import unittest
from pathlib import Path

from benchmarks.benchmark_fingerprint import _write_benchmark_file


class BenchmarkFileTests(unittest.TestCase):
    def test_writes_random_content_instead_of_truncating(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "benchmark.bin"
            _write_benchmark_file(path, size_mib=1)
            self.assertEqual(path.stat().st_size, 1024 * 1024)
            self.assertNotEqual(path.read_bytes(), bytes(1024 * 1024))


if __name__ == "__main__":
    unittest.main()
