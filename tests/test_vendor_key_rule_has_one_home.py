"""The vendor key rule lives in one module, and nothing carries a copy of it.

Paul's decision of 2026-11-13. `seed_client_vendors.py` and
`regenerate_vendor_codes.py` each carried their own `NOISE_WORDS`,
`LOCATION_WORDS`, `DEFAULT_ALIASES`, `normalise_description()` and
`extract_vendor_key()`, "embedded from engine.py to avoid openai import". Both
had fallen behind the engine. The seed script's copy never had the rule that
keeps the first word of a name of three or more, so 91 of the 101 keys in the
recovery CSV are keys the engine never computes. The regenerate script's copy
lacked the four articles added in `b61f055`.

**The rule now lives in `worker\\categorisation\\normalise.py`**, which imports
nothing but `re`. `engine.py` imports the five names from it, so every existing
`from worker.categorisation.engine import NOISE_WORDS` still gets the same
object. The two scripts import from it too, which is what lets them stop
carrying a copy without importing the engine. Importing the engine brings
`config`, and `config` creates folders under the practice root at import.
`regenerate_vendor_codes.py` is a pure CSV transform that never imported
`config`, and it must not start to.
"""

import ast
import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

import live_paths
from worker.categorisation import engine

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = ("seed_client_vendors.py", "regenerate_vendor_codes.py")
THE_RULE = ("NOISE_WORDS", "LOCATION_WORDS", "DEFAULT_ALIASES",
            "normalise_description", "extract_vendor_key")
MODULE = "worker.categorisation.normalise"

#: Names whose keys the two old copies got wrong, one per fault. The first is
#: three words, which the seed copy kept whole; the second starts with an
#: article, which the regenerate copy kept.
NAMES = ("Gatwick Drop Off Crawley Gb", "LA BELLA RESTAURANT",
         "IMO CAR WASH MERTON LONDON SW19 GB", "Apcoa Parking", "O2")


def module_level_definitions(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def imports(path):
    """Every module a file imports, at any depth, as dotted names."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def load_script(filename):
    spec = importlib.util.spec_from_file_location(
        filename[:-3] + "_under_test", REPO / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def modules_loaded_by_importing(name):
    """Import `name` in a fresh interpreter and return what it loaded.

    **The environment is the redirected one**, read from `live_paths`, so a
    script that imports `config` creates its folders under the session temp
    root and never under the live practice root. Asserted before the launch
    rather than trusted."""
    env = dict(os.environ)
    for var, root in ((live_paths.PRACTICE_VAR, live_paths.TEMP_PRACTICE_ROOT),
                      (live_paths.UNSYNCED_VAR, live_paths.TEMP_UNSYNCED_ROOT)):
        assert env.get(var) == str(root), f"{var} is not redirected"
    code = (f"import sys, importlib; importlib.import_module({name!r}); "
            "print('\\n'.join(sorted(sys.modules)))")
    done = subprocess.run([sys.executable, "-c", code], cwd=REPO, env=env,
                          capture_output=True, text=True, timeout=120)
    if done.returncode:
        raise AssertionError(f"importing {name} failed:\n{done.stderr}")
    return set(done.stdout.split())


class TheModuleTest(unittest.TestCase):

    def test_it_defines_the_rule(self):
        from worker.categorisation import normalise
        for name in THE_RULE:
            with self.subTest(name=name):
                self.assertIn(name, vars(normalise))

    def test_the_engine_uses_the_same_objects(self):
        """Re-exported, not copied, so a word added in one place is added
        everywhere and existing imports from the engine keep working."""
        from worker.categorisation import normalise
        for name in THE_RULE:
            with self.subTest(name=name):
                self.assertIs(getattr(engine, name), getattr(normalise, name))

    def test_the_engine_defines_none_of_it(self):
        defined = module_level_definitions(
            REPO / "worker" / "categorisation" / "engine.py")
        self.assertEqual(defined & set(THE_RULE), set())

    def test_importing_it_loads_neither_openai_nor_config(self):
        loaded = modules_loaded_by_importing(MODULE)
        self.assertNotIn("openai", loaded)
        self.assertNotIn("config", loaded)
        self.assertNotIn("worker.categorisation.engine", loaded)


class TheScriptsTest(unittest.TestCase):

    def test_neither_script_carries_a_copy(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                self.assertEqual(
                    module_level_definitions(REPO / script) & set(THE_RULE),
                    set())

    def test_both_import_the_rule_from_the_module(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                self.assertIn(MODULE, imports(REPO / script))

    def test_neither_imports_the_engine_or_openai(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                found = imports(REPO / script)
                self.assertNotIn("worker.categorisation.engine", found)
                self.assertFalse(any(m.split(".")[0] == "openai" for m in found))

    def test_regenerate_still_does_not_import_config(self):
        """It never did, and it is a pure CSV transform. Importing the engine
        to get the rule would have made it run `config`'s mkdir block."""
        self.assertNotIn("config", imports(REPO / "regenerate_vendor_codes.py"))
        loaded = modules_loaded_by_importing("regenerate_vendor_codes")
        self.assertNotIn("config", loaded)
        self.assertNotIn("openai", loaded)

    def test_seed_does_not_load_openai(self):
        """The reason the copies existed. The seed script imports `config` and
        the repository by design; it must not reach the classifier's client."""
        self.assertNotIn("openai", modules_loaded_by_importing("seed_client_vendors"))

    def test_each_script_computes_the_engines_key(self):
        rule = engine.CategorisationEngine()
        for script in SCRIPTS:
            module = load_script(script)
            for name in NAMES:
                with self.subTest(script=script, name=name):
                    self.assertEqual(
                        module.extract_vendor_key(
                            module.normalise_description(name)),
                        rule.vendor_key_for(name))


if __name__ == "__main__":
    unittest.main()
