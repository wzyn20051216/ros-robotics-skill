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


class DetectWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        script_path = Path(__file__).resolve().parents[1] / 'scripts' / 'detect_ros_workspace.py'
        self.module = load_module(script_path, 'detect_ros_workspace')

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_ros1_workspace(self):
        (self.root / 'src').mkdir(parents=True, exist_ok=True)
        (self.root / 'src' / 'CMakeLists.txt').write_text('# ws', encoding='utf-8')
        package_dir = self.root / 'src' / 'demo_pkg'
        package_dir.mkdir()
        (package_dir / 'package.xml').write_text(
            '<package><name>demo_pkg</name><buildtool_depend>catkin</buildtool_depend></package>',
            encoding='utf-8',
        )
        (package_dir / 'CMakeLists.txt').write_text('find_package(catkin REQUIRED)', encoding='utf-8')

    def write_ros2_workspace(self):
        package_dir = self.root / 'src' / 'demo_pkg'
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / 'package.xml').write_text(
            '<package><name>demo_pkg</name><buildtool_depend>ament_cmake</buildtool_depend></package>',
            encoding='utf-8',
        )
        (package_dir / 'CMakeLists.txt').write_text('find_package(ament_cmake REQUIRED)\nament_package()', encoding='utf-8')

    def test_detects_ros1_catkin_workspace(self):
        self.write_ros1_workspace()
        result = self.module.detect_workspace(self.root)
        self.assertEqual(result.workspace_type, 'ros1-catkin')
        self.assertEqual(result.ros1_packages, 1)

    def test_detects_ros2_colcon_workspace(self):
        self.write_ros2_workspace()
        result = self.module.detect_workspace(self.root)
        self.assertEqual(result.workspace_type, 'ros2-colcon')
        self.assertEqual(result.ros2_packages, 1)

    def test_handles_broken_package_xml(self):
        package_dir = self.root / 'src' / 'broken_pkg'
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / 'package.xml').write_text('<package><name>broken_pkg</name>', encoding='utf-8')
        (package_dir / 'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.8)', encoding='utf-8')
        result = self.module.detect_workspace(self.root)
        self.assertEqual(result.unknown_packages, 1)


if __name__ == '__main__':
    unittest.main()
