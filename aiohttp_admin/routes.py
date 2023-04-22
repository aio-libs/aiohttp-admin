"""Setup routes for admin app."""

from pathlib import Path

from aiohttp import web

from . import views
from .types import Schema

_VALIDATORS = ("email", "maxLength", "maxValue", "minLength", "minValue", "regex", "required")


def setup_resources(admin: web.Application, schema: Schema) -> None:
    admin["resources"] = []
    admin["state"]["resources"] = {}

    for r in schema["resources"]:
        m = r["model"]
        admin["resources"].append(m)
        admin.router.add_routes(m.routes)

        try:
            omit_fields = m.fields.keys() - r["display"]
        except KeyError:
            omit_fields = ()
        else:
            if not all(f in m.fields for f in r["display"]):
                raise ValueError(f"Display includes non-existent field {r['display']}")

        repr_field = r.get("repr", m.primary_key)

        for k, v in m.inputs.items():
            if k not in omit_fields:
                v["props"]["alwaysOn"] = "alwaysOn"  # Always display filter

        inputs = m.inputs.copy()  # Don't modify the resource.
        for name, validators in r.get("validators", {}).items():
            if not all(v[0] in _VALIDATORS for v in validators):
                raise ValueError(f"First value in validators must be one of {_VALIDATORS}")
            inputs[name] = inputs[name].copy()
            inputs[name]["validators"] = tuple(inputs[name]["validators"]) + tuple(validators)

        state = {"fields": m.fields, "inputs": inputs, "list_omit": tuple(omit_fields),
                 "repr": repr_field, "label": r.get("label"), "icon": r.get("icon"),
                 "bulk_update": r.get("bulk_update", {})}
        admin["state"]["resources"][m.name] = state


def setup_routes(admin: web.Application) -> None:
    """Add routes to the admin application."""
    admin.router.add_get("", views.index, name="index")
    admin.router.add_post("/token", views.token, name="token")
    admin.router.add_delete("/logout", views.logout, name="logout")
    admin.router.add_static("/static", path=Path(__file__).with_name("static"), name="static")
