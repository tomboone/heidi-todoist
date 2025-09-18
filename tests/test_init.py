"""Test cases for the heidi_todoist package __init__.py file."""

import heidi_todoist


def test_package_imports():
    """Test that the package can be imported successfully."""
    # The __init__.py file is empty, so we just verify the package imports
    assert heidi_todoist is not None


def test_package_has_name():
    """Test that the package has a __name__ attribute."""
    assert hasattr(heidi_todoist, '__name__')
    assert heidi_todoist.__name__ == 'heidi_todoist'


def test_package_has_path():
    """Test that the package has a __path__ attribute."""
    assert hasattr(heidi_todoist, '__path__')
    assert heidi_todoist.__path__ is not None