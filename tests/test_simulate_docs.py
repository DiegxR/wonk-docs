import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".github" / "scripts"))

import simulate_docs as sd  # noqa: E402

PAGE = """---
titulo: Arquitectura
fuente_repo: DiegxR/wonk-pilot
rutas:
  - src/pilot/app.py
commit_verificado: abc1234
permalink_base: https://github.com/DiegxR/wonk-pilot/blob/abc1234
ultima_revision: 2026-10-18
estado: verificado
generado_por: manual
---
# Arquitectura
"""


def manifest(case, **kw):
    base = {"case": case, "sha": "d" * 40, "source_repo": "DiegxR/wonk-pilot",
            "reason": "x", "candidates": [], "uncovered": [], "documentable": []}
    base.update(kw)
    return base


class TestSimulacion(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "runtime" / "wonk-pilot").mkdir(parents=True)
        self.page = self.root / "runtime" / "wonk-pilot" / "arquitectura.md"
        self.page.write_text(PAGE, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_caso_a_no_toca_nada(self):
        actions = sd.simulate(manifest("A", reason="solo pruebas"), self.root)
        self.assertEqual(self.page.read_text(encoding="utf-8"), PAGE)
        self.assertIn("documentación al día", actions[0])

    def test_caso_b_sube_commit_verificado(self):
        actions = sd.simulate(
            manifest("B", candidates=["runtime/wonk-pilot/arquitectura.md"],
                     documentable=[{"path": "src/pilot/app.py", "status": "M"}]),
            self.root)
        text = self.page.read_text(encoding="utf-8")
        self.assertIn(f"commit_verificado: {'d' * 40}", text)
        self.assertIn("generado_por: simulacion", text)
        self.assertIn("Registro de simulación", text)
        self.assertTrue(any(a.startswith("se actualizó el archivo") for a in actions))

    def test_caso_c_marca_desactualizado(self):
        sd.simulate(
            manifest("C", candidates=["runtime/wonk-pilot/arquitectura.md"],
                     reason="refactor grande"),
            self.root)
        self.assertIn("estado: desactualizado", self.page.read_text(encoding="utf-8"))

    def test_caso_d_crea_stub(self):
        actions = sd.simulate(
            manifest("D", uncovered=[{"path": "src/pilot/nuevo_modulo.py", "status": "A"}]),
            self.root)
        stub = self.root / "runtime" / "wonk-pilot" / "nuevo-modulo.md"
        self.assertTrue(stub.exists())
        text = stub.read_text(encoding="utf-8")
        self.assertIn("commit_verificado: " + "d" * 40, text)
        self.assertIn("estado: borrador", text)
        self.assertIn("src/pilot/nuevo_modulo.py", text)
        self.assertTrue(any(a.startswith("se creó el archivo") for a in actions))

    def test_tope_de_paginas(self):
        cands = [f"runtime/wonk-pilot/p{i}.md" for i in range(15)]
        for c in cands:
            (self.root / c).write_text(PAGE, encoding="utf-8")
        actions = sd.simulate(manifest("B", candidates=cands), self.root)
        self.assertTrue(any("omitidas" in a for a in actions))
        self.assertEqual(
            sum(1 for a in actions if a.startswith("se actualizó")), sd.MAX_PAGES)

    def test_seNiegaFueraDe_runtime(self):
        fuera = self.root / "wiki" / "index.md"
        fuera.parent.mkdir(parents=True)
        fuera.write_text("# hola\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            sd.update_page(self.root, "wiki/index.md", "d" * 40, "B", "x")

    def test_main_escribe_actions_txt(self):
        out = self.root / "_run"
        out.mkdir()
        (out / "manifest.json").write_text(
            json.dumps(manifest("D", uncovered=[{"path": "src/pilot/mod.py", "status": "A"}])),
            encoding="utf-8")
        old = sys.argv
        sys.argv = ["simulate_docs.py", "--repo-root", str(self.root), "--out-dir", "_run"]
        try:
            code = sd.main()
        finally:
            sys.argv = old
        self.assertEqual(code, 0)
        actions = (out / "actions.txt").read_text(encoding="utf-8")
        self.assertIn("se creó el archivo", actions)


if __name__ == "__main__":
    unittest.main()
