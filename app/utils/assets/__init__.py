"""
Asset helpers for the garden RPG theme.

Every image reference goes through here — the page always renders
something clean whether real art exists, partial art exists, or zero art exists.
"""
import os
from flask import current_app


def asset_exists(relative_static_path):
    """Check if an image file exists on disk."""
    full_path = os.path.join(current_app.static_folder, relative_static_path)
    return os.path.exists(full_path)


def region_art(region_key, tier):
    """Return path + existence flag for a region tier image."""
    rel_path = f"img/regions/{region_key}-tier{tier}.png"
    return {"path": rel_path, "exists": asset_exists(rel_path)}


def hero_bg():
    """Return path + existence flag for the default garden world background."""
    rel_path = "img/garden-hero-default.jpg"
    return {"path": rel_path, "exists": asset_exists(rel_path)}


def health_overlay(state):
    """Return path + existence flag for the garden health mood overlay."""
    filename = {
        "FLOURISHING": "garden-health-flourishing.png",
        "STABLE": "garden-health-stable.png",
        "NEGLECTED": "garden-health-neglected.png",
    }[state]
    rel_path = f"img/{filename}"
    return {"path": rel_path, "exists": asset_exists(rel_path)}
