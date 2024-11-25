from bannermanagement.models import VoucherSet
from oscar.core.loading import get_model
import logging
from DiscountManagement.models import ProxyClassForRange
from .models import CreditAmountUser

# from oscar.apps.partner.models import StockRecord


# StockRecord = get_model('partner','StockRecord')

# for i in StockRecord.objects.all():
#     if i.num_allocated > 0:
#         i.num_allocated = 0
#         i.save()

model_of_product = get_model("catalogue", "Product")
logger = logging.getLogger(__name__)
from itertools import chain


def create_voucher_data(basket):
    total_shipping_charge = None

    product_list = []
    total_list = []
    vouchers = basket.vouchers.all()
    total_product = basket.all_lines()
    print(f"{vouchers=}")
    total_amount_check = False
    total_product_dict = {}
    total_product_dict_quantity = {}
    for single_line in basket.lines.all():
        # print(single_line.__dict__)
        total_product_dict[single_line.product] = (
            single_line.price_incl_tax * single_line.quantity
        )
        total_product_dict_quantity[single_line.product] = single_line.quantity

        """
        TODO
        need to implement converting of all product into single categories

        """

    duplicate_total_product_dict = total_product_dict.copy()
    duplicate_total_product_dict1 = total_product_dict.copy()

    for single_voucher in vouchers:
        voucher_dict = {}

        # import pdb;pdb.set_trace()
        voucher_dict["code"] = single_voucher.code
        voucher_set_obj = single_voucher.voucher_set
        voucher_set_banner = VoucherSet.objects.get(voucher=voucher_set_obj)
        total_product_value_to_be_include_in_offer = 0
        total_offer = 0
        for offer_details in single_voucher.offers.all():

            try:
                if offer_details.benefit.range.back_range:
                    for single_product in total_product_dict:
                        proxy_obj = offer_details.benefit.range.back_range
                        if (
                            proxy_obj.all_product()
                            .filter(id=single_product.id)
                            .exists()
                        ):
                            total_product_value_to_be_include_in_offer = (
                                total_product_value_to_be_include_in_offer
                                + total_product_dict[single_product]
                            )
                            total_q_for_fixed = total_product_dict_quantity[single_product]
                            if voucher_set_banner.amount_type == "Percentage":
        
                                total_offer = (
                                    total_product_value_to_be_include_in_offer
                                    * (voucher_set_banner.voucher_amount / 100)
                                )
                                logger.debug(f"{total_offer=}")
                            elif voucher_set_banner.amount_type == "Absolute":
                                total_offer =  voucher_set_banner.voucher_amount 
                            else:
                                total_offer = voucher_set_banner.voucher_amount
                                logger.debug(f"{total_offer}")
                            total_product_value_to_be_include_in_offer = 0
                        logger.debug("exit")
                    continue
            except:
                import traceback

                f = traceback.format_exc()
                logger.debug(f"{f=}")
                pass

            if offer_details.benefit.range.includes_all_products:
                for single_product in total_product_dict:
                    the_parent = single_product.parent
                    total_product_value_to_be_include_in_offer = (
                        total_product_value_to_be_include_in_offer
                        + total_product_dict[single_product]
                    )
                    total_q_for_fixed = total_product_dict_quantity[single_product]
                    total_offer = voucher_set_banner.voucher_amount 
                    product_list.append(single_product.id)
                if voucher_set_banner.amount_type == "Percentage":
                    total_offer = total_product_value_to_be_include_in_offer * (
                        voucher_set_banner.voucher_amount / 100
                    )
                elif voucher_set_banner.amount_type == "Absolute":
                    total_offer = total_offer
                else:
                    total_offer = voucher_set_banner.voucher_amount
                total_product_value_to_be_include_in_offer = 0
                continue

            categories_included_in_the_offer = (
                offer_details.benefit.range.included_categories.all()
            )
            fixed_discount_offer = 0
            for single_categories in categories_included_in_the_offer:
                total_amount_check = False
                single_categories_all_cate = (
                    single_categories.get_descendants_and_self()
                )
                single_categories_id = [i.id for i in single_categories_all_cate]
                for single_product in total_product_dict:
                    the_parent = single_product.parent
                    if the_parent.categories.filter(
                        id__in=single_categories_id
                    ).exists():
                        total_amount_check = True
                        total_product_value_to_be_include_in_offer = (
                            total_product_value_to_be_include_in_offer
                            + total_product_dict[single_product]
                        )
                        total_q_for_fixed = total_product_dict_quantity[single_product]
                        fixed_discount_offer =  voucher_set_banner.voucher_amount
                        product_list.append(single_product.id)
                        del duplicate_total_product_dict[single_product]
                total_product_dict = duplicate_total_product_dict.copy()
            total_product_dict = duplicate_total_product_dict1.copy()
            duplicate_total_product_dict = duplicate_total_product_dict1.copy()
            if voucher_set_banner.amount_type == "Percentage":

                total_offer = total_product_value_to_be_include_in_offer * (
                    voucher_set_banner.voucher_amount / 100
                )
            elif voucher_set_banner.amount_type == "Absolute":
                total_offer = fixed_discount_offer
            else:
                if total_amount_check:
                    total_offer = voucher_set_banner.voucher_amount

            total_product_value_to_be_include_in_offer = 0
        logger.debug("reached next destination")
        logger.debug(f"{total_offer}")
        voucher_dict["offer"] = round(float(total_offer), 2)
        logger.debug(f"{voucher_dict['offer']=}")

        if voucher_set_banner.amount_type == "Percentage" or voucher_set_banner.amount_type == "Absolute":
            if voucher_set_banner.amount_type == "Percentage":
                voucher_con = voucher_set_banner.condition
                voucher_dict["max_amount"] = voucher_con.max_value
                voucher_dict["min_amount"] = voucher_con.min_value
            if voucher_set_banner.amount_type == "Absolute":
                voucher_con = voucher_set_banner.condition
                voucher_dict["max_amount"] = voucher_con.max_value
                voucher_dict["min_amount"] = voucher_con.min_value
                
                
                
                    
                
           
                

            voucher_dict["offer_type"] = "Coupon"
        else:
            voucher_dict["offer_type"] = "Voucher"

        voucher_dict["name"] = single_voucher.name
        voucher_obj = single_voucher.voucher_set
        voucher_set = VoucherSet.objects.get(voucher=voucher_obj)
        logger.debug(f"{voucher_set.voucher_type=}")
        voucher_dict["voucher_type"] = voucher_set.voucher_type
        voucher_dict["description"] = voucher_set.voucher.description
        voucher_dict["clubable"] = voucher_set.clubable
        voucher_dict["shipping_charge"] = voucher_set.is_ship_charge
        voucher_dict["shipping_incl"] = voucher_set.is_shipping_included

        try:
            if voucher_set.is_ship_charge:
                total_shipping_charge = (
                     int(voucher_set.shipping_charges)
                )

        except:
            total_shipping_charge = total_shipping_charge

        voucher_dict["product"] = product_list
        product_list = []
        if voucher_set.voucher_type == "shopping voucher":
            voucher_dict["voucher_gst_payable"] = (
                voucher_dict["voucher_gst"] + voucher_dict["voucher_gst"]
            )
        else:
            voucher_dict["voucher_gst_payable"] = 0

        total_list.append(voucher_dict)
    total_tax = 0
    total_price = 0

    for single_line in total_product:
        stock_rec = single_line.stockrecord
        total_price = float(total_price) + float(stock_rec.price) * float(
            single_line.quantity
        )
        total_tax = total_tax + float(stock_rec.calculate_gst_value()) * int(
            single_line.quantity
        )

    total_price = float(total_price)
    total_tax = float(total_tax)

    # total_discount = total_offer_amount if total_offer_amount < total_price else total_price

    # import pdb;pdb.set_trace()
    total_offer_amount = sum(map(lambda x: float(x["offer"]), total_list))

    total_payable = sum(
        map(
            lambda x: (
                float(x["offer"])
                if x["voucher_type"] == "Shopping Voucher - Exclusive"
                or x["voucher_type"] == "Gift Voucher - Exclusive"
                else 0
            ),
            total_list,
        )
    )
    gift_voucher_offer = sum(
        map(
            lambda x: (
                float(x["offer"])
                if x["voucher_type"] == "Gift Voucher - Inclusive"
                or x["voucher_type"] == "Shopping Voucher - Inclusive"
                else 0
            ),
            total_list,
        )
    )
    logger.debug(f"{total_payable=}")
    logger.debug(f"{gift_voucher_offer}")
    if gift_voucher_offer > 0:
        basic_amount_radeemable = float(total_price)
    else:
        basic_amount_radeemable = float(total_price) - float(total_tax)

    if total_payable > 0:
        if basic_amount_radeemable - total_offer_amount < 0:
            balance_payable = float(total_tax)
        else:
            balance_payable = float(total_price) - float(total_offer_amount)

        total_discount = float(total_price) - float(balance_payable)
    else:
        if total_price - gift_voucher_offer < 0:
            balance_payable = 0
        else:
            balance_payable = total_price - gift_voucher_offer
        total_discount = float(total_price) - float(balance_payable)

    logger.debug(
        f"{balance_payable=} {total_discount=} {total_tax} {basic_amount_radeemable}"
    )

    return (
        total_list,
        total_offer_amount,
        total_payable,
        basic_amount_radeemable,
        total_tax,
        total_discount,
        balance_payable,
        total_shipping_charge,
    )


from DiscountManagement.models import VoucherAllocationBYLine
from rest_framework import serializers


class VoucherLineSerializer(serializers.ModelSerializer):
    product_upc = serializers.ReadOnlyField(source="product.upc")
    order_no = serializers.ReadOnlyField(source="order.number")

    class Meta:
        model = VoucherAllocationBYLine
        fields = [
            "id", 
            "order_no",
            "product_upc", 
            "MRP",
            "listing_price",
            "voucher_value",
            "unit_price",
            "taxable_amount",
            "gst_value",
            "order_value",
            "quantity",
            "shipping",
        ]


def voucher_calculation(
    basket, total_offer_amount, basic_amount_radeemable, order, shipping
):
    vouchers = basket.vouchers.all()[0]

    voucher_set_banner = VoucherSet.objects.get(voucher=vouchers.voucher_set)
    voucher_type = voucher_set_banner.voucher_type
    voucher_allocation_dict = {}
    value_type = voucher_set_banner.amount_type

    for single_line in basket.lines.all():
        if voucher_type == "Gift Voucher - Inclusive":
            price = single_line.stockrecord.price
            tax_type = "Inclusive"
            logger.debug(f"inside Gift voucher{price=}")

        elif voucher_type == "Gift Voucher - Exclusive":
            price = single_line.stockrecord.get_base_price()
            tax_type = "Exclusive"
            logger.debug(f"inside exclusive {price=}")
        elif value_type == "Percentage":
            price = single_line.stockrecord.price
            logger.debug(f"inside discount {price=}")

        if basic_amount_radeemable < total_offer_amount:
            total_offer_amount = basic_amount_radeemable
        product = model_of_product.objects.get(upc=single_line.product.upc)
        line_total_price = float(price) * float(single_line.quantity)
        line_weight = float(line_total_price) / float(basic_amount_radeemable)
        amount_allocation = (
            float(line_weight) * float(total_offer_amount) / single_line.quantity
        )
        unit_price = float(price) - float(amount_allocation)

        VoucherAllocationBYLine.objects.create(
            order=order,
            product=product,
            MRP=float(single_line.stockrecord.mrp),
            listing_price=float(single_line.stockrecord.price),
            voucher_value=amount_allocation,
            unit_price=unit_price,
            stock=single_line.stockrecord,
            quantity=single_line.quantity,
            shipping=shipping,
            tax_type=tax_type,
        )

    voucher_allocation_query_set = VoucherAllocationBYLine.objects.filter(order=order)
    voucher_allocation_data = VoucherLineSerializer(
        voucher_allocation_query_set, many=True
    ).data
    return voucher_allocation_data


Voucher = get_model("voucher", "Voucher")


def add_voucher_details(array_prod, code_list):
    print(f"{array_prod=}")

    product_query_set = None
    for single_code in code_list:
        single_voucher = Voucher.objects.get(code=single_code)
        offer = single_voucher.offers.all()[0]
        try:
            all_product = offer.benefit.range.back_range.all_product()

        except:
            all_product = offer.benefit.range.all_products()
        if product_query_set == None:
            product_query_set = all_product
        else:
            all_product = product_query_set.intersection(all_product)
    product_with_only_id = [x.id for x in product_query_set]
    logger.debug(product_with_only_id)
    for i in array_prod:
        if i["id"] in product_with_only_id:
            i["voucher_status"] = True
        else:
            i["voucher_status"] = False
    return array_prod


def voucher_calc_in_cart(cart, basic_amount_radeemable, offer_amount, stock, quantity):
    vouchers = cart.vouchers.all()[0]
    logger.debug("voucher found")
    logger.debug(f"{vouchers.__dict__}")
    voucher_set_banner = VoucherSet.objects.get(voucher=vouchers.voucher_set)
    voucher_type = voucher_set_banner.voucher_type
    value_type = voucher_set_banner.amount_type
    if voucher_type == "Gift Voucher - Exclusive":
        price = stock.get_base_price()
        tax_type = "Exclusive"
        logger.debug(f"inside exclusive {price=}")
    elif voucher_type == "Gift Voucher - Inclusive":
        price = stock.price
    else:
        raise Exception("raised by other voucher")
    logger.debug(f"{basic_amount_radeemable=} {offer_amount=}")
    if basic_amount_radeemable < offer_amount:
        offer_amount = basic_amount_radeemable
    line_total_price = float(price) * float(quantity)
    line_weight = float(line_total_price) / float(basic_amount_radeemable)
    amount_allocation = float(line_weight) * float(offer_amount) / quantity
    amount_allocation_by_line = amount_allocation * quantity
    taxable_amount = float(price) - float(amount_allocation)
    if voucher_type == "Gift Voucher - Exclusive":
        tax_amount = (stock.gst_rate.gst_rate.rate / 100) * taxable_amount
        product_price = tax_amount + taxable_amount
    elif voucher_type == "Gift Voucher - Inclusive":
        product_price = taxable_amount
        taxable_amount = product_price / (1 + float(stock.gst_rate.gst_rate.rate) / 100)
        tax_amount = product_price - taxable_amount

    return product_price, tax_amount, taxable_amount, amount_allocation_by_line


def check_voucher(basket):
    vouchers = basket.vouchers.all()
    for single_voucher in vouchers:
        print(single_voucher)
        all_offers = single_voucher.offers.all()
        for single_offer in all_offers:
            print(single_offer)
        # import pdb;pdb.set_trace()


def CreateCreditForCart(user,cart):
    try:
        amount = CreditAmountUser.objects.get(user=user,cart=cart).amount
    except :
        return None
    return amount