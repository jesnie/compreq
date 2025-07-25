import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import compreq as cr

TEXT_REQUIREMENTS = """dist1!=1.2.5,<2.0.0,>=1.2.3
dist2<=1.9.0,>1.2.3
dist3==1.2.5
dist4~=1.2
dist5<2.0.0,>=1.2.3
dist6<0.2.0,>=0.1.0
distextra[extra1,extra2]<2.0.0,>=1.2.3
distgit@ git+https://github.com/dist6/dist6
distmarker>=1.2.3; platform_system != "Darwin" or platform_machine != "arm64"
distpath@ file:///home/compreq
disturl@ http://www.test.com/test/dist7-1.2.3.tar.gz
"""

REQUIREMENTS = cr.get_requirement_set(
    [
        "dist1!=1.2.5,<2.0.0,>=1.2.3",
        "dist2<=1.9.0,>1.2.3",
        "dist3==1.2.5",
        "dist4~=1.2",
        "dist5<2.0.0,>=1.2.3",
        "dist6<0.2.0,>=0.1.0",
        "distextra[extra1, extra2]<2.0.0,>=1.2.3",
        "distgit@git+https://github.com/dist6/dist6",
        "distmarker>=1.2.3; platform_system != 'Darwin' or platform_machine != 'arm64'",
        "distpath@file:///home/compreq",
        "disturl@http://www.test.com/test/dist7-1.2.3.tar.gz",
    ],
)


def test_text_requirements_file__get_requirements(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text(TEXT_REQUIREMENTS)

    with cr.TextRequirementsFile.open(requirements_path) as requirements:
        assert requirements.get_requirements() == REQUIREMENTS


def test_text_requirements_file__set_requirements(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text(
        """

  # A comment

foo<2.0.0,>=1.2.3
""",
    )

    with cr.TextRequirementsFile.open(requirements_path) as requirements:
        compreq = MagicMock(cr.CompReq)
        compreq.context = MagicMock(cr.Context)
        compreq.resolve_requirement_set.side_effect = lambda r: asyncio.run(
            cr.get_lazy_requirement_set(r).resolve(compreq.context),
        )

        requirements.set_requirements(compreq, REQUIREMENTS)

    assert requirements_path.read_text() == TEXT_REQUIREMENTS
