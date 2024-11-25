from datetime import datetime
import secrets
import string
from oscar.core.loading import get_model
class Content:
    def __init__(self,end_date,clubable,tax,ship,voucher,amount) -> None:
        dt_obj = datetime.strptime(end_date, "%Y-%m-%dT%H:%M")
        end_date = dt_obj.strftime("%Y-%m-%d")
        self.VALIDITY = f"This voucher is Valid Upto 11:59:59 PM of {end_date}"
        if clubable:
            self.CLUBABLE_DES = f"This voucher is clubbable, i.e, more than one (clubbable)voucher can be applied on order value of up to Rs.{clubable} "
        else:
            self.CLUBABLE_DES = f"This voucher is not clubbable, i.e, only one voucher can be used per order."

        if tax:
            self.TAX = f"This voucher is not inclusive of taxes; GST is payable separately."
        else:
            self.TAX = f"This voucher is inclusive of GST."
        
        if voucher:
            if ship is False:
                self.SHIP = "Shipping charges are payable separately."

            elif ship == "Yes on With Charge":
                self.SHIP = "This voucher is fixed of Shipping Charges."

            else:
                self.SHIP = "Shipping is complimentary with this voucher."
        else:
            if ship is True:
                self.SHIP = "This voucher is inclusive of Shipping Charges."
            elif ship == "Yes on With Charge":
                self.SHIP = "This voucher is fixed of Shipping Charges."
            else:
                self.SHIP = "Shipping Charges are payable separately."

        self.arr = []
        self.arr.append(f"Value of this voucher is Rs {amount}")
        self.arr.append("This voucher cannot be redeemed for cash.")
        self.arr.append("This voucher cannot be redeemed in parts and has to be used in a single order; Any unutilised value will lapse.")
        self.arr.append("This voucher can be used to login for a maximum of 3 times. If a purchase is not made within these attempts, the voucher becomes inactive. ")
        self.arr.append("One Up Trade is not responsible for unauthorised use of lost/misplaced vouchers")

        

    @property
    def description(self):     
        self.arr.append(self.VALIDITY)
        self.arr.append(self.CLUBABLE_DES)
        self.arr.append(self.TAX)
        self.arr.append(self.SHIP)
        return self.arr





Offer = get_model("offer", "ConditionalOffer")
VoucherSet_Oscar = get_model("voucher", "VoucherSet")

def generate_unique_string():
    prefix = "OUB"
    characters =  string.ascii_uppercase + string.digits  
    length = 5
    i= 0
    while True:
        i= i + 1
        unique_string = ''.join(secrets.choice(characters) for _ in range(length))  
        final_string = prefix + unique_string
       
        if not Offer.objects.filter(name=final_string).exists() and not VoucherSet_Oscar.objects.filter(name=final_string).exists():
            return final_string
        if i > 100:
            length = length + 1