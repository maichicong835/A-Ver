"""Shared, machine-proven resolver primitives for A-Ver.

Acceptance and future production execution import these modules; they are not
allowed to maintain parallel resolver implementations.
"""

from .tmhunt import TMHuntResolver
from .trademarkia import TrademarkiaResolver

__all__ = ["TMHuntResolver", "TrademarkiaResolver"]
