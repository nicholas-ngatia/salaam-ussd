import logging
import requests
import base64
import nanoid
from datetime import datetime


logging.basicConfig(format='%(asctime)s - %(message)s', filename='ussd_app.log', level=logging.INFO)
base_ussd_url = "https://10.54.12.76"

logging.info('STARTING APP')

def get_session_token():
    data = {
        "email": "itsupport@salaammfbank.co.ke",
        "password": "@UssdAfricasTalking023"
    }
    response = requests.post(base_ussd_url + "/api/login", json=data, verify=False).json()
    return response['api_token']

def check_customer_details(msisdn, token):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    data = {
            "telephone_number": msisdn,
        }
    logging.info(f'Sending request: {data} for validation with phone number {msisdn}')
    response = requests.post(base_ussd_url + "/api/v1/ussd/validate", data=data, headers=header, verify=False).json()
    logging.info(f'Response received for {msisdn}: {response}')
    if response['error_code'] == 0:
        onboarded_status = response['data']
        return onboarded_status
    else: 
        return False

def set_pin(msisdn, token, pin):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    data = {
        "mobile_number": msisdn,
        "new_pin": base64.b64encode(pin.encode('ascii')).decode('utf-8'),
        "new_pin_confirmation": base64.b64encode(pin.encode('ascii')).decode('utf-8')
        }
    logging.info(f'Sending request: {data} for set pin for phone number {msisdn}')
    response = requests.post(base_ussd_url + '/api/v1/ussd/onboard/pin/setup', json=data, headers=header, verify=False).json()
    logging.info(f'Response received for {msisdn}: {response}')
    if response['error_code'] == 0:
        return response['data']['accounts']
    else: 
        return False

def change_pin(msisdn, token, old_pin, new_pin):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    data = {
        "mobile_number": msisdn,
        "old_pin": base64.b64encode(old_pin.encode('ascii')).decode('utf-8'),
        "new_pin": base64.b64encode(new_pin.encode('ascii')).decode('utf-8'),
        "new_pin_confirmation": base64.b64encode(new_pin.encode('ascii')).decode('utf-8')
        }
    logging.info(f'Sending request: {data} for set pin for phone number {msisdn}')
    response = requests.post(base_ussd_url + '/api/v1/ussd/onboard/pin/change', json=data, headers=header, verify=False).json()
    logging.info(f'Response received for {msisdn}: {response}')
    if response['error_code'] == 0:
        return True
    else: 
        return False

def login(msisdn, token, pin):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    data = {
            "telephone_number": msisdn,
            "pin_number": base64.b64encode(pin.encode('ascii')).decode('utf-8'),
            "send_otp": 0
    }
    logging.info(f'Sending request: {data} for login for phone number {msisdn}')
    response = requests.post(base_ussd_url + "/api/v1/ussd/login", json=data, headers=header, verify=False).json()
    logging.info(f'Response received for {msisdn}: {response}')
    if response['error_code'] == 0:
        return response['data']['accounts']
    else: 
        return False

def account_balance(msisdn, token, customer_account):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    data = {
            "telephone_number": msisdn,
            "account_number": customer_account
    }
    logging.info(f'Sending request: {data} for account balance with phone number {msisdn}')
    response = requests.post(base_ussd_url + "/api/v1/ussd/customer/balance", json=data, headers=header, verify=False).json()
    logging.info(f'Response received for {msisdn}: {response}')
    if response['error_code'] == 0:
        return response['data']
    else: 
        return False

def account_ministatement(msisdn, token, customer_account):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    data = {
            "telephone_number": msisdn,
            "account_number":  customer_account,
    }
    logging.info(f'Sending request: {data} for ministatement with phone number {msisdn}')
    response = requests.post(base_ussd_url + "/api/v1/ussd/customer/ministatement", json=data, headers=header, verify=False).json()
    logging.info(f'Response received for {msisdn}: {response}')
    if response['error_code'] == 0:
        return response['data']
    else: 
        return False

def account_transfer(msisdn, token, customer_account, customer_branch, amount, offset_account):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    ref_no = nanoid.generate(size=12)
    d = datetime.today().strftime('%Y-%m-%d')
    data = {
            "initiator": 2,
            "trn_req_ref": nanoid.generate(size=12),
            "customer_telephone": msisdn,
            "trn_product": "CHWL",
            "trn_acc": customer_account,
            "trn_tx_branch":  customer_branch,
            "trn_offset_acc": offset_account,
            "trn_offset_branch": customer_branch,
            "trn_ccy": "KES",
            "trn_offset_ccy": "KES",
            "trn_description": f'Transfer from {customer_account} to {offset_account}',
            "trn_amount": amount,
            "trn_offset_amount": amount,
            "trn_date": '2023-03-02',
            "trn_val_date": '2023-03-02'
    }
    logging.info(f'Sending request: {data} for account transfer with ref_no {ref_no}')
    response = requests.post(base_ussd_url + '/api/v1/ussd/customer/transaction', json=data, headers=header, verify=False).json()
    logging.info(f'Response received for {ref_no}: {response}')
    return response

def airtime_transfer(msisdn, token, customer_account, amount):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    data = {
            "initiator": 2,
            "account_number": customer_account,
            "telephone_number":  f'254{msisdn[1:]}' if msisdn[0] == '0' else msisdn,
            "purchase_amount": amount,
    }
    logging.info(f'Sending request: {data} for airtime for phone number ref_no {msisdn}')
    response = requests.post(base_ussd_url + '/api/v1/ussd/airtime/sell', json=data, headers=header, verify=False).json()
    logging.info(f'Response received for {msisdn}: {response}')
    return response

def mpesa_parties(token):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    logging.info(f'Sending for mpesa parties')
    response = requests.get(base_ussd_url + '/api/v1/ussd/mpesa/parties', headers=header, verify=False).json()
    logging.info(f'Response received: {response}')
    if response['error_code'] == 0:
        return response['data']
    else: 
        return False
    

def calculate_cost(token, amount):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    data = {
            "charge_type": 1,
            "amount":  amount,
    }
    logging.info(f'Sending for cost')
    response = requests.post(base_ussd_url + '/api/v1/ussd/charges/calculate', json=data, headers=header, verify=False).json()
    logging.info(f'Response received: {response}')
    if response['error_code'] == 0:
        return response['data']['transaction_cost']
    else: 
        return False

def mpesa_transfer(msisdn, receiver_msisdn, token, customer_account, amount):
    header = {
        "Authorization": f"Bearer {token}",
        'X-CSRF-TOKEN': '',
        'Accept': 'application/json'
    }
    ref_no = nanoid.generate(size=12)
    d = datetime.today().strftime('%Y-%m-%d')
    parties = mpesa_parties(token)
    data = {
            "initiator": 2,
            'telephone_number': msisdn,
            'receiver_telephone': receiver_msisdn,
            'account_number': customer_account,
            'transfer_amount': amount,
            'tr_caller_party': parties['caller_party'],
            'tr_initiator_party': parties['initiator_party'],
            'tr_primary_party': parties['primary_party'],
            'tr_remarks': f'Transfer of {amount} from {msisdn} to {receiver_msisdn}'

    }
    logging.info(f'Sending request: {data} for MPESA transfer with ref_no {ref_no}')
    response = requests.post(base_ussd_url + '/api/v1/ussd/mpesa/transaction', json=data, headers=header, verify=False).json()
    logging.info(f'Response received for {ref_no}: {response}')
    return response

def int_check(ussd_string):
    try:
        int(ussd_string)
        return True
    except Exception as e:
        return False

def phone_number_validate(phone_number):
    if (phone_number[:2] != "254" or len(phone_number) != 12):
        if (phone_number[0] != "0" or len(phone_number) != 10):
            return False
        else: 
            return True
    else:
        return True
