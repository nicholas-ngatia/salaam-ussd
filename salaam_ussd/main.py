import redis
import utils
import ast
import logging
from flask import Flask, request

app = Flask(__name__)
r = redis.StrictRedis("localhost", 6379, charset="utf-8", decode_responses=True)


@app.post("/ussd")
def ussd():
    try:
        session_id = request.values.get("sessionId", None)
        service_code = request.values.get("serviceCode", None)
        phone_number = request.values.get("phoneNumber", None).split("+")[-1]
        ussd_string = str(request.values.get("text", "default"))
        ussd_string = ussd_string.split("*")[-1]
        logging.info(f'SERVING USSD SESSION {session_id} FROM {phone_number} - {ussd_string}')
        session = r.hgetall(session_id)
        # if True:
        #     response = "END The service is currently undergoing maintenance, apologies for the disruption."
        #     return response
        current_screen = "password"
        if session:
            sub_menu = session["sub_menu"] 
            current_screen = session["current_screen"]
        if ussd_string == "0":
            current_screen = session["previous_screen"]
            response = session["response"]
        if ussd_string == "00":
            current_screen = "main_menu"
        if current_screen == "password":
            token = utils.get_session_token()
            logging.info(f'Token received: {token}')
            result = utils.check_customer_details(phone_number, token)
            logging.info(f'Customer retrieved: {result}')
            if result['onboarded_status'] != 1:
                response = "END You are currenly not permitted to use this service. Please contact Salaam bank to gain access"
                return response
            elif result['is_active'] == False:
                response = "CON Welcome to Salaam Microfinance Bank. Please enter the 4 digit PIN you will be using to log in to the service"
                sub_menu = "first_time_login"
            elif result['is_active'] == True:
                response = "CON Welcome back to Salaam Microfinance Bank. Please enter your PIN"
                sub_menu = "login"
            current_screen = "main_menu"
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "sub_menu": sub_menu,
                    "previous_screen": "main_menu",
                    "token": token,
                    "response": response,
                },
            )
        elif current_screen == "main_menu":
            if sub_menu == "login":
                details = utils.login(phone_number, session['token'], ussd_string)
                if details:
                    response = "CON Welcome to Salaam Microfinance Bank.\n1. Balance Enquiry\n2. Buy airtime\n3. Payments\n4. Send Money\n5. Withdraw Cash\n6. My Account"
                    current_screen = "main_menu_options"
                else:
                    response = "CON Wrong PIN input. Please try again."
                    return response
                r.hmset(
                        session_id,
                    {
                        "customer_details": str(details),
                    },
                    )
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
                response = "CON Welcome to Salaam Microfinance Bank.\n1. Balance Enquiry\n2. Buy airtime\n3. Payments\n4. Send Money\n5. Withdraw Cash\n6. My Account"
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
                result = utils.set_pin(phone_number, session['token'], ussd_string)
                if result:
                    response = "CON Welcome to Salaam Microfinance Bank.\n1. Balance Enquiry\n2. Buy airtime\n3. Payments\n4. Send Money\n5. Withdraw Cash\n6. My Account"
                    current_screen = "main_menu_options"
                else:
                    raise Exception
            else:
                response = "CON The passwords do not match, please try again."
                return response
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "previous_screen": "main_menu",
                    "response": response,
                    "customer_details": str(result),
                },
            )
        elif current_screen == "main_menu_options":
            if ussd_string == "1" or sub_menu == "balance_enquiry":
                customer_details = ast.literal_eval(session['customer_details'])
                acc_no = ""
                i = 1
                for customer in customer_details:
                    acc_no += f'{i}. {customer["account_number"]}\n'
                    i += 1
                response = f'CON Please select the account you wish to check.\n{acc_no}'
                current_screen = "balance_enquiry"
            elif ussd_string == "2" or sub_menu == "airtime_menu":
                response = "CON Please select who you wish to buy airtime for.\n1. Self\n2. Other"
                current_screen = "airtime_menu"
            elif ussd_string == "3":
                response = "CON Coming soon! Please check back later!"
                # response = (
                #     "CON Please select what to pay for.\n1. Paybill\n2. Buy goods"
                # )
                # current_screen = "payments"
            elif ussd_string == "4":
                response = "CON Please select what to use:\n1. Account transfer\n2. Send to Mpesa"
                current_screen = "send_money"
            elif ussd_string == "5":
                response = "CON Coming soon! Please check back later!"
                # current_screen = "withdraw"
            elif ussd_string == "6":
                response = "CON 1. Ministatement\n2. Change PIN"
                current_screen = "my_account"
            else:
                raise IndexError
            r.hmset(
                session_id,
                {
                    "current_screen": current_screen,
                    "previous_screen": "main_menu",
                    "response": response,
                },
            )
        elif current_screen == "balance_enquiry":
            customer_details = ast.literal_eval(session['customer_details'])
            selection = int(ussd_string) - 1
            acc_no = customer_details[selection]['account_number']
            balance = utils.account_balance(phone_number, session['token'], customer_details[selection]['account_number'])
            logging.info(f'Data returned {balance}')
            response = f'CON Balances for account {acc_no}:\nActual Balance: {balance["current_balance"]}\nAvailable Balance: KES {balance["available_balance"]}'
            next_menu = 'get_balance'
        elif current_screen == "airtime_menu":
            if sub_menu == "None":
                if ussd_string == "1":
                    response = "CON Please enter amount"
                    next_menu = "airtime_account"
                    r.hmset(
                            session_id,
                        {
                            "phone_number": phone_number,
                        },
                        )
                elif ussd_string == "2":
                    response = "CON Please enter number to send to:"
                    next_menu = "airtime_amount"
                else:
                    raise IndexError
            elif sub_menu == "airtime_amount":
                if utils.phone_number_validate(ussd_string) == False:
                    response = "CON Invalid number input. Please try again:\n\n00 Main Menu"
                    return response
                else:
                    response = "CON Please enter amount"
                    next_menu = "airtime_account"
                    r.hmset(
                            session_id,
                        {
                            "phone_number": ussd_string,
                        },
                        )
            elif sub_menu == "airtime_account":
                msisdn = session['phone_number']
                if int(ussd_string) < 5 or int(ussd_string) > 100000 or not utils.int_check(ussd_string):
                    response = "CON Invalid amount input. Please try again"
                    return response
                else:
                    customer_details = ast.literal_eval(session['customer_details'])
                    acc_no = ""
                    i = 1
                    for customer in customer_details:
                        acc_no += f'{i}. {customer["account_number"]}\n'
                        i += 1
                    response = f'CON Please select the account you wish to use.\n {acc_no}'
                    next_menu = "airtime_confirm"
                    r.hmset(
                        session_id,
                        {
                            "amount": ussd_string,
                        },
                )
            elif sub_menu == "airtime_confirm":
                customer_details = ast.literal_eval(session['customer_details'])
                selection = int(ussd_string) - 1
                transaction_cost = utils.calculate_cost(amount=session["amount"], token=session['token'])
                response = f'CON Confirm details\nPhone number: {session["phone_number"]}\nAmount: KES {session["amount"]}\nAccount number: {customer_details[selection]["account_number"]}\nCost: {transaction_cost}\n1. Confirm'
                r.hmset(
                    session_id,
                    {
                        "account_number": customer_details[selection]["account_number"],
                        "account_branch": customer_details[selection]["branch_code"],
                    },
                    )
                next_menu = 'airtime_complete'
            elif sub_menu == "airtime_complete":
                res = utils.airtime_transfer(session['phone_number'], session['token'], session['account_number'], session['amount'])
                if res:
                    if res['error_code'] != 0:
                        response = (
                            f'CON {res["error_message"]}.'
                        )
                    else:
                        response = "CON Request received. Kindly wait as we process the transaction."
                else:
                    response = "CON An error has occurred, please try again."
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
            if sub_menu == "None":
                if ussd_string == "1":
                    response = "CON Select where to send money:\n1. To self\n2. To other account"
                    next_menu = "account_transfer_start"
                elif ussd_string == "2":
                    response = "CON Select where to send the money:\n1. To self\n2. To other number"
                    next_menu = "mpesa_transfer_start"
                else:
                    raise IndexError
            elif sub_menu == "account_transfer_start":
                if ussd_string == "1":
                    customer_details = ast.literal_eval(session["customer_details"])
                    if len(customer_details) == 1:
                        response = "CON You cannot send to self with only 1 account\n\n00 Main Menu"
                        return response
                    acc_no = ""
                    i = 1
                    for customer in customer_details:
                        acc_no += f'{i}. {customer["account_number"]}\n'
                        i += 1
                    response = f'CON Please select the account you would like to send to.\n{acc_no}'
                elif ussd_string == "2":
                    response = 'CON Please enter the account number you would like to send to:'
                next_menu = "account_transfer_continue"
            elif sub_menu == "account_transfer_continue":
                acc_no = ussd_string
                customer_details = ast.literal_eval(session['customer_details'])
                if len(ussd_string) < 2:
                    selection = int(ussd_string) - 1
                    acc_no = customer_details[selection]['account_number']
                acc_no_from = ""
                i = 1
                for customer in customer_details:
                    acc_no_from += f'{i}. {customer["account_number"]}\n'
                    i += 1
                response = f'CON Please select account to send from:\n{acc_no_from}'
                r.hmset(
                    session_id,
                    {
                        "account_number": acc_no,
                    },
                    )                   
                next_menu = "account_transfer_amount"
            elif sub_menu == "account_transfer_amount":
                customer_details = ast.literal_eval(session['customer_details'])
                selection = int(ussd_string) - 1
                acc_no_from = customer_details[selection]['account_number']
                acc_branch = customer_details[selection]['branch_code']
                r.hmset(
                        session_id,
                        {
                            "account_number_from": acc_no_from,
                            "account_branch": acc_branch,
                        },
                        ) 
                response = "CON Please enter the amount to be sent:"
                next_menu = "account_transfer_confirm"
            elif sub_menu == "account_transfer_confirm":
                if int(ussd_string) > 70000 or not utils.int_check(ussd_string):
                    response = "CON Invalid amount input. Please ensure it is below 70000."
                    return response
                else:
                    r.hmset(
                        session_id,
                        {
                            "amount": ussd_string,
                        },
                )
                transaction_cost = utils.calculate_cost(amount=session["amount"], token=session['token'])
                response = f'CON Confirm details:\nAccount from: {session["account_number_from"]}\nAccount to: {session["account_number"]}\nAmount: KES {ussd_string}\nCost: KES {transaction_cost}\n1. Confrim'
                next_menu = 'account_transfer_complete'
            elif sub_menu == "account_transfer_complete":
                res = utils.account_transfer(phone_number, session['token'], session['account_number_from'], session['account_branch'], session['amount'], session['account_number'])
                if res:
                    if res['error_code'] != 0:
                        response = (
                            f'CON {res["error_message"]}.'
                        )
                    else:
                        response = "CON Request received. Kindly wait as we process the transaction."
                else:
                    response = "CON An error has occurred, please try again."
                next_menu = "None"
            elif sub_menu == "mpesa_transfer_start":
                if ussd_string == "1":
                    response = "CON Please enter amount"
                    next_menu = "mpesa_account"
                    r.hmset(
                            session_id,
                        {
                            "phone_number": phone_number,
                        },
                        )
                elif ussd_string == "2":
                    response = "CON Please enter number to send to:"
                    next_menu = "mpesa_amount"
                else:
                    raise IndexError
            elif sub_menu == "mpesa_amount":
                if utils.phone_number_validate(ussd_string) == False:
                    response = "CON Invalid number input. Please try again:\n\n00 Main Menu"
                    return response
                else:
                    response = "CON Please enter amount"
                    next_menu = "mpesa_account"
                    r.hmset(
                            session_id,
                        {
                            "phone_number": ussd_string,
                        },
                        )
            elif sub_menu == "mpesa_account":
                msisdn = session['phone_number']
                if int(ussd_string) < 10 or int(ussd_string) > 150000 or not utils.int_check(ussd_string):
                    response = "CON Invalid amount input. Please ensure it is between 10 and 150000."
                    return response
                else:
                    customer_details = ast.literal_eval(session['customer_details'])
                    acc_no = ""
                    i = 1
                    for customer in customer_details:
                        acc_no += f'{i}. {customer["account_number"]}\n'
                        i += 1
                    response = f'CON Please select the account you wish to use.\n {acc_no}'
                    next_menu = "mpesa_confirm"
                    r.hmset(
                        session_id,
                        {
                            "amount": ussd_string,
                        },
                )
            elif sub_menu == "mpesa_confirm":
                customer_details = ast.literal_eval(session['customer_details'])
                selection = int(ussd_string) - 1
                transaction_cost = utils.calculate_cost(amount=session["amount"], token=session['token'])
                response = f'CON Confirm details\nPhone number: {session["phone_number"]}\nAmount: KES {session["amount"]}\nAccount number: {customer_details[selection]["account_number"]}\nCost: {transaction_cost}\n1. Confirm'
                r.hmset(
                    session_id,
                    {
                        "account_number": customer_details[selection]["account_number"],
                        "account_branch": customer_details[selection]["branch_code"],
                    },
                    )
                next_menu = 'mpesa_complete'
            elif sub_menu == "mpesa_complete":
                res = utils.mpesa_transfer(phone_number, session['phone_number'], session['token'], session['account_number'], session['amount'])
                if res:
                    if res['error_code'] != 0:
                        response = (
                            f'CON {res["error_message"]}.'
                        )
                    else:
                        response = "CON Request received. Kindly wait as we process the transaction."
                else:
                    response = "CON An error has occurred, please try again."
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
            if sub_menu == "None":
                if ussd_string == "1":
                    customer_details = ast.literal_eval(session['customer_details'])
                    acc_no = ""
                    i = 1
                    for customer in customer_details:
                        acc_no += f'{i}. {customer["account_number"]}\n'
                        i += 1
                    response = f'CON Please select the account you wish to check.\n{acc_no}'
                    next_menu = "ministatement"
                elif ussd_string == "2":
                    response = "CON Please enter old PIN:"
                    next_menu = "change_password"
                else:
                    raise IndexError
            elif sub_menu == "ministatement":
                customer_details = ast.literal_eval(session['customer_details'])
                selection = int(ussd_string) - 1
                acc_no = customer_details[selection]['account_number']
                statement = utils.account_ministatement(phone_number, session['token'], customer_details[selection]['account_number'])
                logging.info(f'Data returned {statement}')
                if len(statement) == 0:
                    response = "CON No recent transactions found"
                else:
                    response = "CON "
                    for s in statement:
                        response += f'{s["trx_trn_date"]} - {s["trx_drbrind"]} - KES {s["trx_lcyamt"]}\n'
                next_menu = "None"
            elif sub_menu == "change_password":
                response = "CON Please enter new PIN:"
                next_menu = "change_password_con"
                r.hmset(
                        session_id,
                    {
                        "old_password": ussd_string,
                    },
                    )
            elif sub_menu == "change_password_con": 
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
                    result = utils.change_pin(phone_number, session['token'], session['old_password'], ussd_string)
                    if result:
                        response = "CON PIN successfully changed"
                    else:
                        response = "CON Wrong old PIN input. Please start again."
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
    
    except IndexError:
        logging.error(f'INVALID CHOICE INPUT FOR SESSION_ID {session_id}')
        return session['response']

    except Exception as e:
        logging.error(f'AN ERROR HAS OCCURED FOR SESSION_ID {session_id}: {e}')
        return "END An error occurred, please try again later"


if __name__ == "__main__":
    logging.info('STARTING APP')
    app.run(debug=True, port=6000)
