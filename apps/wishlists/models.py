# from oscar.apps.wishlists.models import *  # noqa isort:skip
from django.db import models

from oscar.apps.wishlists.abstract_models import (
    AbstractWishList,
    AbstractLine,
    AbstractWishListSharedEmail,
)


class WishList(AbstractWishList):
    pass


class Line(AbstractLine):
    is_wishlist = models.BooleanField(default=False)


class WishListSharedEmail(AbstractWishListSharedEmail):
    pass
