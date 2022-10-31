import redis
import utils
import json
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
        print(phone_number, ussd_string, session_id)
        session = r.hgetall(session_id)
        if not utils.whitelist_check(phone_number):
            response = "END Coming soon!"
            return response
        current_screen = "password"
        if session:
            sub_menu = session["sub_menu"] 
            current_screen = session["current_screen"]
        if ussd_string == "0":
            current_screen = session["previous_screen"]
            response = session["response"]
            print(current_screen, sub_menu)
        if ussd_string == "00":
            current_screen = "main_menu"
        if current_screen == "password":
            if utils.check_password(phone_number):
                response = "CON Welcome to Salaam Microfinance Bank. Please enter the 4 digit PIN you will be using to log in to the service"
                sub_menu = "first_time_login"
            else:
                response = "CON Welcome back to Salaam Microfinance Bank. Please enter your PIN"
                sub_menu = "login"
            current_screen = "main_menu"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": sub_menu,
                    "previous_screen": "main_menu",
                    "response": response,
                },
            )
        elif current_screen == "main_menu":
            if sub_menu == "login":
                if utils.login(phone_number, ussd_string) == True:
                    response = "CON Welcome to Salaam Microfinance Bank.\n1. Balance Enquiry\n2. Buy airtime for account\n3. Payments\n4. Send Money\n5. Withdraw Cash\n6. My Account"
                    current_screen = "main_menu_options"
                else:
                    response = "CON Wrong PIN input. Please try again."
                    return response
            elif sub_menu == "first_time_login":
                if len(ussd_string) == 4 and utils.int_check(ussd_string):
                    response = "CON Please confirm the PIN:"
                    current_screen = "first_time_login_confirm"
                    r.hmset(
                        session_id,
                    {
                        "password": ussd_string,
                    },
                    )
                else:
                    response = "CON Wrong PIN format. Please ensure it is 4 digits and try again."
                    return response
            else:
                response = "CON Welcome to Salaam Microfinance Bank.\n1. Balance Enquiry\n2. Buy airtime for account\n3. Payments\n4. Send Money\n5. Withdraw Cash\n6. My Account"
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
        elif current_screen == "first_time_login_confirm":
            if session['password'] == ussd_string:
                utils.first_time_login(phone_number, ussd_string)
                response = "CON Welcome to Salaam Microfinance Bank.\n1. Balance Enquiry\n2. Buy airtime for account\n3. Payments\n4. Send Money\n5. Withdraw Cash"
                current_screen = "main_menu_options"
            else:
                response = "CON The passwords do not match, please try again."
                return response
        elif current_screen == "main_menu_options":
            if ussd_string == "1" or sub_menu == 'get_balance':
                acc_no = utils.get_acc_no(phone_number)
                response = f'CON Please select the account you wish to check.\n1. {acc_no}'
                current_screen = "balance_enquiry"
            elif ussd_string == "2":
                response = "CON Please select who you wish to buy airtime for.\n1. Self\n2. Other"
                current_screen = "airtime_menu"
            elif ussd_string == "3":
                response = "CON Coming soon! Please check back later!"
                # response = (
                #     "CON Please select what to pay for.\n1. Paybill\n2. Buy goods"
                # )
                # current_screen = "payments"
            elif ussd_string == "4":
                response = "CON Please select what to use.\n1. Account transfer\n2. Send to Mpesa"
                current_screen = "send_money"
            elif ussd_string == "5":
                response = "CON Coming soon! Please check back later!"
                # current_screen = "withdraw"
            elif ussd_string == "6":
                response = "CON 1. Change PIN"
                current_screen = "my_account"
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
            response = f'CON Your current balance is KES {balance}'
            next_menu = 'get_balance'
        elif current_screen == "airtime_menu":
            if ussd_string == "1" or sub_menu == "airtime_amount":
                response = "CON Please enter amount"
                next_menu = "airtime_pin"
            elif ussd_string == "2":
                response = "CON Please enter number to send to"
                next_menu = "airtime_amount"
            elif sub_menu == "airtime_pin":
                if utils.phone_number_validate(phone_number):
                    if int(ussd_string) < 5 or int(ussd_string) > 100000:
                        response = "CON Invalid amount input. Please try again"
                        next_menu = "airtime_amount"
                    else:
                        response = "CON Enter PIN"
                        next_menu = "airtime_confirm"
                else:
                    response = "CON Invalid phone number input, please try again."
                    return response
            elif sub_menu == "airtime_confirm":
                response = (
                    "CON Request received. Kindly wait as we process the transaction."
                )
                sub_menu = "None"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": next_menu,
                    "previous_screen": sub_menu,
                    "response": response,
                },
            )
        elif current_screen == "payments":
            if ussd_string == "1":
                response = "CON Please enter the paybill:"
                next_menu = "paybill_number"
            elif ussd_string == "2":
                response = "CON Please enter buy goods number"
                next_menu = "buy_goods_amount"
            elif sub_menu == "paybill_number":
                response = "CON Please enter the account number:"
                next_menu = "buy_goods_amount"
            elif sub_menu == "buy_goods_amount":
                response = "CON Please enter the amount"
                next_menu = "transaction_confirm"
            elif sub_menu == "transaction_confirm":
                response = "CON Please enter PIN"
                next_menu = "transaction_success"
            elif sub_menu == "transaction_success":
                response = "CON Please wait as your transaction is processed."
                next_menu = "None"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": next_menu,
                    "previous_screen": sub_menu,
                    "response": response,
                },
            )
        elif current_screen == "send_money":
            if ussd_string == "1":
                response = "CON You will receive a text message with instructions"
                next_menu = "None"
            elif ussd_string == "2":
                response = "CON Please enter the amount"
                next_menu = "mpesa_send_money"
            elif sub_menu == "mpesa_send_money":
                response = "CON Please enter PIN:"
                next_menu = "mpesa_send_confirm"
            elif sub_menu == "mpesa_send_confirm":
                response = "CON Please wait as your transaction is processed."
                next_menu = "None"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": next_menu,
                    "previous_screen": sub_menu,
                    "response": response,
                },
            )
        elif current_screen == "withdraw":
            if sub_menu == "None":
                response = "CON Please enter amount"
                next_menu = "agent_pin"
            elif sub_menu == "agent_pin":
                response = "CON Please enter PIN:"
                next_menu = "agent_confirm"
            elif sub_menu == "agent_confirm":
                response = "CON Please wait your transaction is processed."
                next_menu = "None"
            response = "CON Coming soon! Please check back later!"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": next_menu,
                    "previous_screen": sub_menu,
                    "response": response,
                },
            )
        elif current_screen == "my_account":
            if sub_menu == "None" or ussd_string == "1":
                response = "CON Please enter new PIN:"
                next_menu = "change_password"
            elif sub_menu == "change_password":
                if utils.int_check(ussd_string):
                    response = "CON Please confirm new PIN:"
                    next_menu = "confirm_password"
                    r.hmset(
                        session_id,
                    {
                        "password": ussd_string,
                    },
                    )
                else:
                    response = "CON Invalid PIN format. Please ensure it is 4 digits:"
                    return response
            elif sub_menu == "confirm_password":
                if session['password'] == ussd_string:
                    utils.first_time_login(phone_number, ussd_string)
                    response = "CON PIN successfully changed"
                    next_menu = "None"
                else:
                    response = "CON The two PINs do not match. Please try again."
                    return response
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": next_menu,
                    "previous_screen": sub_menu,
                    "response": response,
                },
            )
        if current_screen == "main_menu" or current_screen == "main_menu_options" or current_screen == "first_time_login_confirm":
            return response
        else:
            return response + "\n\n00 Main menu"

    # except Exception as e:
    #     print(f"Shit's fucking {e}")
    #     return "END An error occurred, please try again later"


if __name__ == "__main__":
    app.run(debug=True)
