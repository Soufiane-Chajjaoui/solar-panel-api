"""
Module des routes de l'application.
Exporte tous les routeurs pour faciliter l'importation.
"""

from . import auth_routes
from . import panel_routes
from . import cleaning_routes
from . import user_routes

__all__ = ["auth_routes", "panel_routes", "cleaning_routes", "user_routes"]

