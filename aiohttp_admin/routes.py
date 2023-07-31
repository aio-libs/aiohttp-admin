"""Setup routes for admin app."""

import copy
from pathlib import Path

from aiohttp import web

from . import views
from .types import Schema


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
            omit_fields = m.omit_fields
        else:
            if not all(f in m.fields for f in r["display"]):
                raise ValueError(f"Display includes non-existent field {r['display']}")

        repr_field = r.get("repr", m.primary_key)
        if repr_field not in m.fields:
            raise ValueError(f"repr not a valid field name: {repr_field}")

        # Don't modify the resource.
        fields = copy.deepcopy(m.fields)
        inputs = copy.deepcopy(m.inputs)

        validators = r.get("validators", {})
        input_props = r.get("input_props", {})
        for k, v in inputs.items():
            if k not in omit_fields:
                v["props"]["alwaysOn"] = "alwaysOn"  # Always display filter
            if k in validators:
                v["props"]["validate"] = (tuple(v["props"].get("validate", ()))
                                          + tuple(validators[k]))
            v["props"].update(input_props.get(k, {}))

        for name, props in r.get("field_props", {}).items():
            fields[name]["props"].update(props)

        state = {"fields": fields, "inputs": inputs, "list_omit": tuple(omit_fields),
                 "repr": repr_field, "label": r.get("label"), "icon": r.get("icon"),
                 "bulk_update": r.get("bulk_update", {}),
                 "show_actions": r.get("show_actions", ())}
        admin["state"]["resources"][m.name] = state


def setup_routes(admin: web.Application) -> None:
    """Add routes to the admin application."""
    admin.router.add_get("", views.index, name="index")
    admin.router.add_post("/token", views.token, name="token")
    admin.router.add_delete("/logout", views.logout, name="logout")
    admin.router.add_static("/static", path=Path(__file__).with_name("static"), name="static")
