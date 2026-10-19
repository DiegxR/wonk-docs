import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".github" / "scripts"))

import build_manifest as bm  # noqa: E402

ARQUITECTURA = """---
titulo: Arquitectura
fuente_repo: GetWonk/wonk-pilot
rutas:
  - src/pilot/app.py
  - src/pilot/__init__.py
commit_verificado: abc1234
estado: verificado
---
# Arquitectura
"""

CONTRATOS = """---
titulo: Contratos
fuente_repo: GetWonk/wonk-pilot
rutas:
  - src/pilot/calculo.py#L1-L30
commit_verificado: abc1234
estado: verificado
---
# Contratos
"""

COMO_PROBAR = """---
titulo: Como probar
fuente_repo: GetWonk/wonk-pilot
rutas:
  - tests/test_calculo.py
commit_verificado: abc1234
estado: verificado
---
# Como probar
"""


def payload(files, diff=""):
    return {"source_repo": "GetWonk/wonk-pilot", "sha": "d" * 40, "before": "a" * 40,
            "files": files, "diff": diff, "source_docs": {}}


def f(status, path, old=None):
    return {"status": status, "path": path, "old_path": old}


class TestFrontmatter(unittest.TestCase):
    def test_parse_rutas_en_lista(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "page.md"
            p.write_text(ARQUITECTURA, encoding="utf-8")
            data = bm.parse_frontmatter(p)
        self.assertEqual(data["fuente_repo"], "GetWonk/wonk-pilot")
        self.assertEqual(data["rutas"], ["src/pilot/app.py", "src/pilot/__init__.py"])
        self.assertEqual(data["commit_verificado"], "abc1234")

    def test_load_pages_filtra_por_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "runtime" / "wonk-pilot").mkdir(parents=True)
            (root / "runtime" / "wonk-pilot" / "arquitectura.md").write_text(
                ARQUITECTURA, encoding="utf-8")
            (root / "runtime" / "wonk-pilot" / "contratos.md").write_text(
                CONTRATOS.replace("wonk-pilot", "otro-repo"), encoding="utf-8")
            pages = bm.load_pages(root, "GetWonk/wonk-pilot")
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["page"], "runtime/wonk-pilot/arquitectura.md")


class TestClasificacion(unittest.TestCase):
    def setUp(self):
        self.pages = [
            {"page": "runtime/wonk-pilot/arquitectura.md", "fuente_repo": "GetWonk/wonk-pilot",
             "commit_verificado": "abc1234", "estado": "verificado", "titulo": "Arquitectura",
             "rutas": ["src/pilot/app.py", "src/pilot/__init__.py"]},
            {"page": "runtime/wonk-pilot/contratos.md", "fuente_repo": "GetWonk/wonk-pilot",
             "commit_verificado": "abc1234", "estado": "verificado", "titulo": "Contratos",
             "rutas": ["src/pilot/calculo.py#L1-L30"]},
            {"page": "runtime/wonk-pilot/como-probar.md", "fuente_repo": "GetWonk/wonk-pilot",
             "commit_verificado": "abc1234", "estado": "verificado", "titulo": "Como probar",
             "rutas": ["tests/test_calculo.py"]},
        ]

    def test_caso_a_solo_pruebas(self):
        p = payload([f("M", "tests/test_calculo.py")])
        v = bm.classify(p, self.pages)
        self.assertEqual(v["case"], "A")

    def test_caso_a_excluidos(self):
        p = payload([f("M", "pytest-run.log"), f("M", "coverage.xml"),
                     f("M", "insumos/ontologia.ttl")])
        v = bm.classify(p, self.pages)
        self.assertEqual(v["case"], "A")

    def test_caso_a_diff_solo_comentarios(self):
        diff = "--- a/src/pilot/app.py\n+++ b/src/pilot/app.py\n@@ -1,3 +1,4 @@\n+ # comentario nuevo\n  x = 1"
        p = payload([f("M", "src/pilot/app.py")], diff=diff)
        v = bm.classify(p, self.pages)
        self.assertEqual(v["case"], "A")
        self.assertIn("comentarios", v["reason"])

    def test_caso_b_ruta_cubierta(self):
        diff = "--- a/src/pilot/app.py\n+++ b/src/pilot/app.py\n@@ -1 +1 @@\n-ANTES\n+DESPUES = 2"
        p = payload([f("M", "src/pilot/app.py")], diff=diff)
        v = bm.classify(p, self.pages)
        self.assertEqual(v["case"], "B")
        self.assertIn("runtime/wonk-pilot/arquitectura.md", v["candidates"])

    def test_caso_b_con_ruta_hash(self):
        diff = "--- a/src/pilot/calculo.py\n+++ b/src/pilot/calculo.py\n@@ -1 +1 @@\n-a\n+b"
        p = payload([f("M", "src/pilot/calculo.py")], diff=diff)
        v = bm.classify(p, self.pages)
        self.assertEqual(v["case"], "B")
        self.assertIn("runtime/wonk-pilot/contratos.md", v["candidates"])

    def test_caso_d_ruta_sin_pagina(self):
        p = payload([f("A", "src/pilot/nuevo_modulo.py")])
        v = bm.classify(p, self.pages)
        self.assertEqual(v["case"], "D")
        self.assertEqual(v["uncovered"][0]["path"], "src/pilot/nuevo_modulo.py")

    def test_caso_c_borrado_de_ruta_del_frontmatter(self):
        p = payload([f("D", "src/pilot/calculo.py")])
        v = bm.classify(p, self.pages)
        self.assertEqual(v["case"], "C")
        self.assertIn("dejan de existir", v["reason"])

    def test_caso_c_renames_masivos(self):
        files = [f("R", f"src/pilot/mod{i}.py", f"src/pilot/viejo{i}.py") for i in range(5)]
        p = payload(files)
        v = bm.classify(p, self.pages)
        self.assertEqual(v["case"], "C")

    def test_caso_b_gana_sobre_d_cuando_todo_esta_cubierto(self):
        diff = "--- a/src/pilot/app.py\n+++ b/src/pilot/app.py\n@@ -1 +1 @@\n-x\n+y"
        p = payload([f("M", "src/pilot/app.py"), f("M", "src/pilot/__init__.py")], diff=diff)
        v = bm.classify(p, self.pages)
        self.assertEqual(v["case"], "B")

    def test_sin_archivos_es_caso_a(self):
        v = bm.classify(payload([]), self.pages)
        self.assertEqual(v["case"], "A")


class TestManifiesto(unittest.TestCase):
    def test_render_markdown_incluye_secciones(self):
        p = payload([f("M", "src/pilot/app.py")], diff="+DESPUES = 2")
        p.update({"pusher": "diego", "commit_message": "feat: cambio",
                  "compare_url": "https://example/compare", "run_url": "https://example/run",
                  "source_docs": {"README.md": "# piloto"}})
        v = bm.classify(p, [])
        md = bm.render_markdown(p, v, [])
        for bloque in ("# Manifiesto de sincronización", "## Archivos cambiados",
                       "## Páginas candidatas", "## Diff", "## Documentación existente",
                       "## Contrato del agente"):
            self.assertIn(bloque, md)

    def test_diff_solo_comentarios(self):
        self.assertTrue(bm.diff_solo_comentarios("+ # un comentario\n- # otro"))
        self.assertFalse(bm.diff_solo_comentarios("+ valor = 1"))


if __name__ == "__main__":
    unittest.main()
