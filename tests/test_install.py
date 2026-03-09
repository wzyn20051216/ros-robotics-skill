import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class InstallTests(unittest.TestCase):
    def setUp(self):
        script_path = Path(__file__).resolve().parents[1] / 'scripts' / 'install.py'
        self.module = load_module(script_path, 'install_script')

    def test_codex_path_resolution(self):
        home = Path('/tmp/home')
        path = self.module.codex_skill_dir(home, None)
        self.assertEqual(path.parts[-4:], ('tmp', 'home', '.codex', 'skills', 'ros-robotics')[-4:])
        self.assertEqual(path.name, 'ros-robotics')

    def test_detect_default_targets_falls_back_to_codex(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.assertEqual(self.module.detect_default_targets(home), ['codex'])


if __name__ == '__main__':
    unittest.main()
