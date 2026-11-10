"""Exercise independent parsing, compression and exact version selection."""

import gzip
import lzma
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apt_index import download_index, exact_package

INDEX = b"""Package: demo
Version: 1.0-1
Architecture: amd64
Pre-Depends: init-tool (>= 1:3)
Depends: libone | libtwo,
 libthree
Description: Example
 ignore this continuation

Package: demo
Version: 2.0-1
Architecture: amd64
Depends: libfour
"""


class AptIndexTests(unittest.TestCase):
    def test_downloads_plain_gzip_and_xz(self):
        for suffix, payload in (
            ("", INDEX), (".gz", gzip.compress(INDEX)),
            (".xz", lzma.compress(INDEX)),
        ):
            with self.subTest(suffix=suffix):
                with patch("apt_index.urlopen", return_value=BytesIO(payload)):
                    url = "https://apt.test/Packages" + suffix
                    packages = download_index(url)
                first = exact_package(packages, "demo", "1.0-1")
                self.assertEqual(
                    list(first.direct_lines()),
                    ["Pre-Depends: init-tool (>= 1:3)",
                     "Depends: libone | libtwo, libthree"],
                )
                second = exact_package(packages, "demo", "2.0-1")
                self.assertEqual(second.depends, "libfour")
                with self.assertRaisesRegex(ValueError, "Доступные версии"):
                    exact_package(packages, "demo", "3.0")

    def test_index_size_limit(self):
        with patch("apt_index.MAX_INDEX_BYTES", 10):
            with patch("apt_index.urlopen", return_value=BytesIO(INDEX)):
                with self.assertRaisesRegex(ValueError, "64 МиБ"):
                    download_index("https://apt.test/Packages")
