# compreq

A library for dynamically computing Python requirements, to keep them up-to-date.

## Concepts

This library relies heavily on [packaging](https://packaging.pypa.io/en/stable/), and you should
understand that first.

The base types are the `Version`, `Specifier`, `SpecifierSet` and `Requirement` in `packaging` and
 `Release` and `ReleaseSet` added by this library.

For all of the base types this library adds lazy versions - which both allows reuse, but also allows
some values to be fetched from the context, instead of specified explicitly.

To resolve a lazy object into a concrete value use a `CompReq.resolve_...` method.

Finally this library adds wrappers around `pyproject.toml` and `requirements.txt` files, for getting
and setting the requirments in them.

## Example:

```python
import compreq as cr

with cr.PyprojectFile.open() as pyproject:
    prev_python_specifier = cr.get_bounds(
        pyproject.get_requirements()["python"].specifier
    ).lower_specifier_set()
    comp_req = cr.CompReq(python_specifier=prev_python_specifier)

    default_range = cr.version(
        ">=",
        cr.floor_ver(
            cr.REL_MINOR,
            cr.minimum_ver(
                cr.max_ver(cr.min_age(years=1)),
                cr.min_ver(cr.count(cr.MINOR, 3)),
            ),
        ),
    ) & cr.version("<", cr.ceil_ver(cr.REL_MAJOR, cr.max_ver()))

    dev_range = cr.version(">=", cr.floor_ver(cr.REL_MINOR, cr.max_ver())) & cr.version(
        "<", cr.ceil_ver(cr.REL_MINOR, cr.max_ver())
    )

    pyproject.set_requirements(
        comp_req,
        [
            cr.pkg("beautifulsoup4") & default_range,
            cr.pkg("packaging") & default_range,
            cr.pkg("pip") & default_range,
            cr.pkg("python") & default_range,
            cr.pkg("python-dateutil") & default_range,
            cr.pkg("requests") & default_range,
            cr.pkg("tomlkit") & default_range,
            cr.pkg("typing-extensions") & default_range,
        ],
    )
    pyproject.set_requirements(
        comp_req,
        [
            cr.pkg("black") & dev_range,
            cr.pkg("isort") & dev_range,
            cr.pkg("mypy") & dev_range,
            cr.pkg("pylint") & dev_range,
            cr.pkg("pytest") & dev_range,
            cr.pkg("taskipy") & dev_range,
            cr.pkg("types-beautifulsoup4") & default_range,
            cr.pkg("types-python-dateutil") & default_range,
            cr.pkg("types-requests") & default_range,
        ],
        "dev",
    )
```

Or see [requirements.py](https://github.com/jesnie/compreq/blob/main/requirements.py).


# References:

https://peps.python.org/pep-0440/
https://packaging.pypa.io/en/stable
