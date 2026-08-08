"""Model registry — importing this package registers all ORM models.

Each model module only imports SQLAlchemy + db.session at runtime (no runtime
cross-imports), so importing the package in order registers every class with
SQLAlchemy's registry, making string-based relationship() targets resolvable.
"""

from models.bazi_chart import BaziChart
from models.session import RefreshSession
from models.user import User

__all__ = ["User", "RefreshSession", "BaziChart"]
