from unittest.mock import MagicMock

from compreq import CompReq, get_lazy_release_set, set_python_classifiers
from tests.utils import fake_release_set


def test_set_python_classifiers() -> None:
    cr = MagicMock(CompReq)
    python_releases = fake_release_set(
        distribution="python",
        releases=[
            # NOT sorted:
            "2.6.1",
            "3.1.1",
            "3.0.0",
            "2.7.2",
            "3.0.1",
            "2.7.0",
            "2.7.1",
            "3.1.2",
        ],
    )
    lazy_python_releases = get_lazy_release_set(python_releases)
    cr.resolve_release_set.return_value = python_releases

    assert set_python_classifiers(
        [
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Typing :: Typed",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
        ],
        cr,
        lazy_python_releases,
    ) == [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Typing :: Typed",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
    ]
    cr.resolve_release_set.assert_called_once_with("python", lazy_python_releases)
