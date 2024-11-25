from apps.wishlists.models import WishList, Line
from apps.catalogue.models import Product


class WishListAddProduct:
    @classmethod
    def add_product(cls, wishlist_key, product_id, remove=False):
        try:
            wishlist = WishList.objects.get(key=wishlist_key)
            product = Product.objects.get(pk=product_id)

            line, created = Line.objects.get_or_create(
                wishlist=wishlist, product=product
            )

            if remove:
                line.delete()
            else:

                if not created:
                    line.quantity += 1
                    line.save()

            return {"success": True, "message": "Product operation successful."}

        except WishList.DoesNotExist:
            return {"success": False, "message": "Wishlist not found."}

        except Product.DoesNotExist:
            return {"success": False, "message": "Product not found."}

    @classmethod
    def remove_product(cls, wishlist_key, product_id):
        return cls.add_product(wishlist_key, product_id, remove=True)
