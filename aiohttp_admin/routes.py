"""Setup routes for admin app."""

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
            display_fields = r["display"]
        except KeyError:
            display_fields = list(m.fields.keys())
        else:
            if not all(f in m.fields for f in display_fields):
                raise ValueError(f"Display includes non-existent field {display_fields}")

        repr_field = r.get("repr", m.repr_field)

        for k, v in m.inputs.items():
            if k in display_fields:
                v["props"]["alwaysOn"] = "alwaysOn"  # Always display filter

        state = {"fields": m.fields, "inputs": m.inputs, "display": display_fields,
                 "repr": repr_field}
        admin["state"]["resources"][m.name] = state


def setup_routes(admin: web.Application) -> None:
    """Add routes to the admin application."""
    admin.router.add_get("", views.index, name="index")
    admin.router.add_post("/token", views.token, name="token")
    admin.router.add_delete("/logout", views.logout, name="logout")
    admin.router.add_static("/static", path=Path(__file__).with_name("static"), name="static")
