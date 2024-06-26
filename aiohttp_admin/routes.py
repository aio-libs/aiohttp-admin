"""Setup routes for admin app."""

import copy
from pathlib import Path

from aiohttp import web

from . import views
from .backends.abc import AbstractAdminResource
from .types import Schema, _ResourceState, data, resources_key, state_key


def setup_resources(admin: web.Application, schema: Schema) -> None:
    resources: dict[str, AbstractAdminResource[tuple[object, ...]]] = {}
    for r in schema["resources"]:
        m = r["model"]
        resources[m.name] = m
        admin.router.add_routes(m.routes)

        try:
            omit_fields = m.fields.keys() - r["display"]
        except KeyError:
            omit_fields = m.omit_fields
        else:
            if not all(f in m.fields for f in r["display"]):
                raise ValueError(f"Display includes non-existent field {r['display']}")
        # TODO: Use label: https://github.com/marmelab/react-admin/issues/9587
        omit_fields = tuple(m.fields[f]["props"].get("source") for f in omit_fields)

        repr_field = r.get("repr", data(m.primary_key[0]))
        if repr_field.removeprefix("data.") not in m.fields:
            raise ValueError(f"repr not a valid field name: {repr_field}")

        # Don't modify the resource.
        fields = copy.deepcopy(m.fields)
        inputs = copy.deepcopy(m.inputs)

        validators = r.get("validators", {})
        input_props = r.get("input_props", {})
        for k, v in inputs.items():
            k = k.removeprefix("data.")
            if k not in omit_fields:
                v["props"]["alwaysOn"] = "alwaysOn"  # Always display filter
            if k in validators:
                v["props"]["validate"] = (tuple(v["props"].get("validate", ()))
                                          + tuple(validators[k]))
            v["props"].update(input_props.get(k, {}))

        for name, props in r.get("field_props", {}).items():
            fields[name]["props"].update(props)

        state: _ResourceState = {
            "fields": fields, "inputs": inputs, "list_omit": tuple(omit_fields),
            "repr": repr_field, "label": r.get("label"), "icon": r.get("icon"),
            "bulk_update": r.get("bulk_update", {}), "urls": {},
            "show_actions": r.get("show_actions", ())}
        admin[state_key]["resources"][m.name] = state
    admin[resources_key] = resources


def setup_routes(admin: web.Application) -> None:
    """Add routes to the admin application."""
    admin.router.add_get("", views.index, name="index")
    admin.router.add_post("/token", views.token, name="token")
    admin.router.add_delete("/logout", views.logout, name="logout")
    admin.router.add_static("/static", path=Path(__file__).with_name("static"), name="static")
