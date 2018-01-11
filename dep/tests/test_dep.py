"""Test deps.

Testing adds more requirements, as we use Pytest. That is not needed for running though.

"""
import json
import os
import sys
import pytest

import dep
from dep import Line, Brew, Version, MissingDependencyError, ConMan, HostOSVersion

here = os.path.dirname(os.path.realpath(__file__))


def test_simple_brew():
    """End-to-end test of a simple brew dependency."""
    dep.parse_dependencies(['./tests/Dependencies0'])


def test_main():
    """End-to-end test of larger dependency file."""
    sys.argv = ['/bin/deps', 'verify', './tests/Dependencies1']
    with pytest.raises(dep.MalformedDependency):
        dep.main()


def test_brew_cmake_requirement(mocker):
    """Detailed check of a brew cmake dependency."""
    line = Line("foo.c", 10, "brew cmake <= 3.10.0", "test")

    b = Brew(line, "brew")
    b.parse()
    assert b.operator == "<="
    assert b.command == "brew"
    assert b.package == "cmake"
    assert b.version_text == "3.10.0"
    mocker.patch('dep.brew_cmd')
    dep.brew_cmd.return_value = json.load(open(here + '/assets/brew_cmake_installed.json'))
    b.verify_and_act()
    assert dep.brew_cmd.called


def test_brew_ninja_not_installed_requirement(mocker):
    """Detailed check of a unmatched brew requirement."""
    line = Line("foo.c", 11, "brew ninja <= 1.8.2", "We use ninja as clang's build system.")

    b = Brew(line, "brew")
    b.parse()
    assert b.operator == "<="
    assert b.command == "brew"
    assert b.package == "ninja"
    assert b.version_text == "1.8.2"
    mocker.patch('dep.brew_cmd')
    dep.brew_cmd.return_value = json.load(open(here + '/assets/brew_ninja_not_installed.json'))
    # The package is not installed
    with pytest.raises(MissingDependencyError) as exception_info:
        b.verify_and_act()

    assert "missing dependency: brew ninja v1.8.2, found nothing installed" in str(exception_info)
    assert dep.brew_cmd.called


def test_versions():
    """Unittests for the version comparison objects."""
    v1 = Version("3.2.1")
    v2 = Version("3.3.1")
    v3 = Version("3.2")
    v4 = Version("3.2")

    # Check the values are parsed correctly.
    assert v1.text == "3.2.1"
    assert v1.numeric == [3, 2, 1]
    assert v3.text == "3.2"
    assert v3.numeric == [3, 2]

    # Check the operators work correctly.
    assert v2 > v1
    assert v1 < v2
    assert v2 >= v1
    assert v1 <= v2
    assert v3 == v4

    # Check that versions with different number of digits compare correctly.
    assert v2 > v3
    assert v3 < v2

    # TODO fix different digit comparisons.
    # assert v4 == v1
    assert v3 >= v4


def test_self_version_requirement():
    """Unittest of the self version check."""
    line = Line("foo.c", 10, "config_manager <= 0.1", "test")

    b = ConMan(line, "config_manager")
    b.parse()
    assert b.operator == "<="
    assert b.command == "config_manager"
    assert b.version_text == "0.1"

    b.verify_and_act()

    line = Line("foo.c", 10, "config_manager <= 0.0.1", "test")
    bad = ConMan(line, "config_manager")
    bad.parse()
    with pytest.raises(MissingDependencyError):
        bad.verify_and_act()
    line = Line("foo.c", 10, "config_manager == " + dep.VERSION, "test")
    good = ConMan(line, "config_manager")
    good.parse()
    good.verify_and_act()


def test_host_os_version_requirement(mocker):
    """Unittest of the host os version check."""
    line = Line("foo.c", 11, "os_version == 10.13.2", "test")
    mocker.patch('dep.platform.mac_ver')
    dep.platform.mac_ver.return_value = ('10.13.2', "", "")
    b = HostOSVersion(line, "os_version")
    b.parse()
    assert b.operator == "=="
    assert b.command == "os_version"
    assert b.version_text == "10.13.2"

    b.verify_and_act()

    line = Line("foo.c", 10, "os_version == 10.13.1", "test")
    bad = HostOSVersion(line, "os_version")
    bad.parse()
    with pytest.raises(MissingDependencyError):
        bad.verify_and_act()
