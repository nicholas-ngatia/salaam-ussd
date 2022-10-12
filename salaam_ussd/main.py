import redis
import utils
import ast
from flask import Flask, request

app = Flask(__name__)
r = redis.StrictRedis("localhost", 6379, charset="utf-8", decode_responses=True)


@app.post("/ussd")
def ussd():
    # try:
        session_id = request.values.get("sessionId", None)
        service_code = request.values.get("serviceCode", None)
        phone_number = request.values.get("phoneNumber", None)
        ussd_string = str(request.values.get("text", "default"))
        ussd_string = ussd_string.split("*")[-1]
        session = r.hgetall(session_id)
        current_screen = "main_menu"
        if session:
            sub_menu = session["sub_menu"] 
            current_screen = session["current_screen"]
        if ussd_string == "0":
            current_screen = session["previous_screen"]
            ussd_string = session["response"]
        if ussd_string == "00":
            current_screen = "main_menu"
        if current_screen == "main_menu":
            response = "CON Welcome to Salaam Microfinance Bank.\n1. Balance Enquiry\n2. Buy airtime for account\n3. Payments\n4. Send Money\n5. Withdraw Cash"
            current_screen = "main_menu_options"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": "None",
                    "previous_screen": "main_menu",
                    "response": response,
                },
            )
        elif current_screen == "main_menu_options":
            if ussd_string == "1":
                acc_no = utils.get_acc_no(phone_number)
                response = f"CON Please select the account you wish to check.\n1. {acc_no}"
                current_screen = "balance_enquiry"
            elif ussd_string == "2":
                response = "CON Please select who you wish to buy airtime for.\n1. Self\n2. Other"
                current_screen = "airtime_menu"
            elif ussd_string == "3":
                response = (
                    "CON Please select what to pay for.\n1. Paybill\n2. Buy goods"
                )
                current_screen = "payments"
            elif ussd_string == "4":
                response = "CON PLease select what to use.\n1. Account transfer\n2. Send to Mpesa"
                current_screen = "send_money"
            elif ussd_string == "5":
                response = "CON Please enter agent number:"
                current_screen = "withdraw"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "previous_screen": "main_menu",
                    "response": response,
                },
            )
        elif current_screen == "balance_enquiry":
            balance = utils.get_balance(phone_number)
            response = f"CON Your current balance is KES {balance}"
        elif current_screen == "airtime_menu":
            if ussd_string == "1" or sub_menu == "airtime_amount":
                response = "CON Please enter amount"
                sub_menu = "airtime_pin"
            elif ussd_string == "2":
                response = "CON Please enter number to send to"
                sub_menu = "airtime_amount"
            elif sub_menu == "airtime_pin":
                if int(ussd_string) < 5 or int(ussd_string) > 100000:
                    response = "CON Invalid amount input. Please try again"
                    sub_menu = "airtime_amount"
                else:
                    response = "CON Enter PIN"
                    sub_menu = "airtime_confirm"
            elif sub_menu == "airtime_confirm":
                response = (
                    "CON Request received. Kindly wait as we process the transaction."
                )
                sub_menu = "None"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": sub_menu,
                    "previous_screen": "main_menu",
                    "response": response,
                },
            )
        elif current_screen == "payments":
            if ussd_string == "1":
                response = "CON Please enter the paybill:"
                sub_menu = "paybill_number"
            elif ussd_string == "2":
                response = "CON Please enter buy goods number"
                sub_menu = "buy_goods_amount"
            elif sub_menu == "paybill_number":
                response = "CON Please enter the account number:"
                sub_menu = "buy_goods_amount"
            elif sub_menu == "buy_goods_amount":
                response = "CON Please enter the amount"
                sub_menu = "transaction_confirm"
            elif sub_menu == "transaction_confirm":
                response = "CON Please enter PIN"
                sub_menu = "transaction_success"
            elif sub_menu == "transaction_success":
                response = "CON Please wait as your transaction is processed."
                sub_menu = "None"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": sub_menu,
                    "previous_screen": "main_menu",
                    "response": response,
                },
            )
        elif current_screen == "send_money":
            if ussd_string == "1":
                response = "CON You will receive a text message with instructions"
                sub_menu = "None"
            elif ussd_string == "2":
                response = "CON Please enter the amount"
                sub_menu = "mpesa_send_money"
            elif sub_menu == "mpesa_send_money":
                response = "CON Please enter PIN:"
                sub_menu = "mpesa_send_confirm"
            elif sub_menu == "mpesa_send_confirm":
                response = "CON Please wait as your transaction is processed."
                sub_menu = "None"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": sub_menu,
                    "previous_screen": "main_menu",
                    "response": response,
                },
            )
        elif current_screen == "withdraw":
            if sub_menu == "None":
                response = "CON Please enter amount"
                sub_menu = "agent_pin"
            elif sub_menu == "agent_pin":
                response = "CON Please enter PIN:"
                sub_menu = "agent_confirm"
            elif sub_menu == "agent_confirm":
                response = "CON Please wait your transaction is processed."
                sub_menu = "None"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": sub_menu,
                    "previous_screen": "main_menu",
                    "response": response,
                },
            )
        if current_screen == "main_menu_options":
            return response
        else:
            return response + "\n\n0 Previous menu 00 Main menu"

    # except Exception as e:
    #     print(f"Shit's fucking {e}")
    #     return "END An error occurred, please try again later"


if __name__ == "__main__":
    app.run(debug=True)
