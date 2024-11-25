from django.urls import path


from .views import (
    CategoryTreeView,
    CategoryWisedProduct,
    BasketView,
    DeleteCartProduct,
    DeleteProductFromWishlist,
    GetProductDetailIdWise,
    UpdateQuantityOfProduct,
    CartCountOfUser,
    VoucherList,
    AddressCreateAPIView,
    AddressListAPIView,
    AddressUpdateAPIView,
    WishListView,
    WishListCreateView,
    WishListRemoveProductAPIView,
    AddressDeleteAPIView,
    SearchApiView,
    GetVouchersView,
    ListWithFilter,
    ProductAttributeListView,
    BestSellerProductListView,
    FeaturedProductListView,
    GetRecommendedProduct,
    WishlistDeatailView,
    AddProductWishlistView,
    GetCountOfWishlist,
    ShopByBrandAPIView,
    redirect_to_dashboard,
    VoucherCodeAlreadyExists,
)

urlpatterns = [
    # path('',redirect_to_dashboard),
    # path('<path:path>/',redirect_to_dashboard),
    path("CategoryTreeView/", CategoryTreeView.as_view(), name="CategoryTreeView"),
    path(
        "CategoryWisedProduct/<int:id>/",
        CategoryWisedProduct.as_view(),
        name="CategoryWisedProduct",
    ),
    path("BasketView", BasketView.as_view(), name="BasketView"),
    path(
        "DeleteCartProduct/<int:productid>/<int:basketid>",
        DeleteCartProduct.as_view(),
        name="DeleteCartProduct",
    ),
    path(
        "GetProductDetailIdWise/<int:id>",
        GetProductDetailIdWise.as_view(),
        name="GetProductDetailIdWise",
    ),
    path(
        "UpdateQuantityOfProduct",
        UpdateQuantityOfProduct.as_view(),
        name="UpdateQuantityOfProduct",
    ),
    path("CartCountOfUser", CartCountOfUser.as_view(), name="CartCountOfUser"),
    path("GetVouchersView", GetVouchersView.as_view(), name="GetVouchersView"),
    path("vouchers/", VoucherList.as_view(), name="voucher-list"),
    path("address/create/", AddressCreateAPIView.as_view(), name="address-create-api"),
    path("address/list/", AddressListAPIView.as_view(), name="address-list-api"),
    path(
        "address/<int:pk>/update/",
        AddressUpdateAPIView.as_view(),
        name="address-update-api",
    ),
    path("address/<int:id>/", AddressDeleteAPIView.as_view(), name="address-delete"),
    path("wishlists/", WishListView.as_view(), name="wishlist-list"),
    path("wishlists/create/", WishListCreateView.as_view(), name="wishlist-create"),
    path(
        "wishlist/remove-product/<str:key>/<int:product_id>/",
        WishListRemoveProductAPIView.as_view(),
        name="wishlist-remove-product",
    ),
    path("search/", SearchApiView.as_view(), name="search-api"),
    path(
        "search/<str:search_words>", SearchApiView.as_view(), name="search_words_by_api"
    ),
    path(
        "GetRecommendedProduct/<int:id>/",
        GetRecommendedProduct.as_view(),
        name="GetRecommendedProduct",
    ),
    path(
        "add-wishlist-view/", AddProductWishlistView.as_view(), name="add-wishlist-view"
    ),
    path("wishlist-deatail/", WishlistDeatailView.as_view(), name="wishlist-details"),
    path("GetCountOfWishlist", GetCountOfWishlist.as_view(), name="GetCountOfWishlist"),
    path("attr/<int:id>/", ListWithFilter.as_view(), name="filter-list"),
    path(
        "product-attributes/<int:category_id>/",
        ProductAttributeListView.as_view(),
        name="product-attributes-list",
    ),
    path(
        "DeleteProductFromWishlist/<int:id>/",
        DeleteProductFromWishlist.as_view(),
        name="DeleteProductFromWishlist",
    ),
    path(
        "shop_by_brand/<str:brand_name>/",
        ShopByBrandAPIView.as_view(),
        name="shop_by_brand_api",
    ),
    path("shop_by_brand/", ShopByBrandAPIView.as_view(), name="brand-list"),
    path("best-sellers/", BestSellerProductListView.as_view(), name="best-sellers"),
    path(
        "featured-products/",
        FeaturedProductListView.as_view(),
        name="featured-products",
    ),
    path(
        "already-used-voucher-code/",
        VoucherCodeAlreadyExists.as_view(),
        name="already-used-voucher-code",
    ),
]
