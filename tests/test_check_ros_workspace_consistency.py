import importlib.util
import sys
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        script_path = Path(__file__).resolve().parents[1] / 'scripts' / 'check_ros_workspace_consistency.py'
        self.module = load_module(script_path, 'check_ros_workspace_consistency')

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_reports_missing_dependency(self):
        package_dir = self.root / 'src' / 'demo_pkg'
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / 'package.xml').write_text(
            '<package><name>demo_pkg</name><buildtool_depend>catkin</buildtool_depend></package>',
            encoding='utf-8',
        )
        (package_dir / 'CMakeLists.txt').write_text(
            'find_package(catkin REQUIRED COMPONENTS roscpp std_msgs)',
            encoding='utf-8',
        )
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            issues = self.module.check_workspace(self.root)
        self.assertGreaterEqual(issues, 1)
        self.assertIn('package.xml 未声明', buffer.getvalue())

    def test_reports_missing_ros2_install_rule(self):
        package_dir = self.root / 'src' / 'demo_pkg'
        (package_dir / 'launch').mkdir(parents=True, exist_ok=True)
        (package_dir / 'package.xml').write_text(
            '<package><name>demo_pkg</name><buildtool_depend>ament_cmake</buildtool_depend></package>',
            encoding='utf-8',
        )
        (package_dir / 'CMakeLists.txt').write_text(
            'find_package(ament_cmake REQUIRED)\nament_package()',
            encoding='utf-8',
        )
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            issues = self.module.check_workspace(self.root)
        self.assertGreaterEqual(issues, 1)
        self.assertIn('install(DIRECTORY launch', buffer.getvalue())


if __name__ == '__main__':
    unittest.main()
