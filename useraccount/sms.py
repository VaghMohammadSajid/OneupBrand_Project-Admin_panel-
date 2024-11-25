import requests
import logging

logger = logging.getLogger(__name__)


class SmsOtpIntegration:

    @classmethod
    def send_otp_sms(cls, mobile_no, otp, username):
        # message = "".format()

        url = "https://api.technowizards.co.in/genericapi/QSGenericReceiver"
        params = {
            "version": "1.0",
            "header": "ONEUPB",
            "type": "PM",
            "accesskey": "sgmSm3ftbBFe",
            "dest": mobile_no,
            "msg": f"Dear customer, your OTP is  {otp} for OneUpBrands Customer Registration. Please do not share OTP with others.-OneUpBrands",
        }

        try:

            response = requests.get(url, params=params)
            print(response)

            if response.status_code == 200:

                print("Message sent successfully.")
                return True, "Message sent successfully."
            else:
                print(f"Failed to send message. Status code: {response.status_code}")
                print(response.text)
                return (
                    False,
                    f"Failed to send message. Status code: {response.status_code}",
                )

        except Exception as exc:
            print(exc)

    @classmethod
    def send_otp_sms_trackorder(cls, mobile_no, otp, username):
        url = "https://api.technowizards.co.in/genericapi/QSGenericReceiver"
        params = {
            "version": "1.0",
            "header": "ONEUPB",
            "type": "PM",
            "accesskey": "sgmSm3ftbBFe",
            "dest": mobile_no,
            "msg": f"Dear customer, your OTP is {otp}  for OneUpBrands Track you Order.Please do not share OTP with others.-OneUpBrands",
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                logger.debug(f"{response}")
                logger.debug("Custom SMS sent successfully.")
                return True, "Custom SMS sent successfully."
            else:
                logger.debug(
                    f"Failed to send custom SMS. Status code: {response.status_code}"
                )
                logger.debug(response.text)
                return (
                    False,
                    f"Failed to send custom SMS. Status code: {response.status_code}",
                )
        except Exception as exc:
            import traceback

            f = traceback.format_exc()
            logger.critical(f"{f}")
            logger.critical(f"Error occurred while sending custom SMS: {exc}")
            return False, f"Error occurred while sending custom SMS: {exc}"

    @classmethod
    def send_otp_sms_checkout(cls, mobile_no, username, ordernumber):
        print(username, "sms part")
        print(ordernumber, "sms part")
        print(mobile_no, "sms part")
        url = "https://api.technowizards.co.in/genericapi/QSGenericReceiver"
        params = {
            "version": "1.0",
            "header": "ONEUPB",
            "type": "PM",
            "accesskey": "sgmSm3ftbBFe",
            "dest": mobile_no,
            "msg": f"Hey {username} Your OneUpBrand order {ordernumber} has been placed successfully.  OneupBrand never contacts you for any promotions or contests, asking for any personal information or OTP. Please avoid such calls. OneUp",
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                print("Custom SMS sent successfully.")
                return True, "Custom SMS sent successfully."
            else:
                print(f"Failed to send custom SMS. Status code: {response.status_code}")
                print(response.text)
                return (
                    False,
                    f"Failed to send custom SMS. Status code: {response.status_code}",
                )
        except Exception as exc:
            print(f"Error occurred while sending custom SMS: {exc}")
            return False, f"Error occurred while sending custom SMS: {exc}"

    @classmethod
    def send_otp_for_credit_verification(
        cls, otp, mobile_no, username=None, amount=None
    ):

        url = "https://api.technowizards.co.in/genericapi/QSGenericReceiver"
        params = {
            "version": "1.0",
            "header": "ONEUPB",
            "type": "PM",
            "accesskey": "sgmSm3ftbBFe",
            "dest": mobile_no,
            "msg": f"Dear customer, your OTP is  {otp} for OneUpBrands Customer Registration. Please do not share OTP with others.-OneUpBrands",
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                print("Custom SMS sent successfully.")
                return True, "Custom SMS sent successfully."
            else:
                print(f"Failed to send custom SMS. Status code: {response.status_code}")
                print(response.text)
                return (
                    False,
                    f"Failed to send custom SMS. Status code: {response.status_code}",
                )
        except Exception as exc:
            print(f"Error occurred while sending custom SMS: {exc}")
            return False, f"Error occurred while sending custom SMS: {exc}"
