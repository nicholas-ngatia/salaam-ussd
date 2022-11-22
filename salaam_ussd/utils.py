import json
import logging
import requests
import base64
import nanoid
from zeep import client
from zeep.plugins import HistoryPlugin
from datetime import datetime
from lxml import etree


logging.basicConfig(format='%(asctime)s - %(message)s', filename='ussd_app.log', level=logging.INFO)
ussd_url = "http://10.54.66.16:8282/api/Solid/SubmitRequest"

history = HistoryPlugin()
logging.info('STARTING APP')

b2c_url = 'https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest'
auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
airtime_auth_url = 'https://api.safaricom.co.ke/oauth2/v3/generate?grant_type=client_credentials'
airtime_url = 'https://prod.safaricom.co.ke/v1/pretups/api/recharge'
transaction_key = ''
transaction_secret = ''
airtime_key = ''
airtime_secret = ''

def load_data():
    with open('customers.json', "r") as f:
        data = json.load(f)
        f.close()
    return data

def get_token():
    token = base64.b64encode(f'{transaction_key} : {transaction_secret}')
    response = requests.request("GET", auth_url, headers = { 'Authorization': f'Bearer {token}' })
    return response.json['access_token']

def get_session_token():
    data = {
        "message_validation": {
            "api_user": base64.b64encode(b'africastalking').decode('utf-8'),
            "api_password": base64.b64encode(b'123456').decode('utf-8')
        },
        "message_route": {
            "interface": "TOKEN"
        }
}
    response = requests.post(ussd_url, json=data).json()
    return response['error_desc']['token']

def generate_securiy_credentials(msisdn, token, last_value):
    b64token = base64.b64encode(token.encode('ascii'))
    ref_no = nanoid.generate(size=20)
    encoding = f'{token}#{ref_no}#{msisdn}#{last_value}'.encode('ascii')
    security_stamp = base64.b64encode(encoding).decode('utf-8')
    return b64token, ref_no, security_stamp


def check_customer_details(msisdn, token, imsi):
    b64token, ref_no, security_stamp = generate_securiy_credentials(msisdn, token, imsi)
    data = {
        "message_validation": {
            "api_user": "",
            "api_password": "",
            "token": b64token.decode('utf-8'),
        },
        "message_route": {
            "interface": "MOBILE",
            "request_type": "VALIDATE",
            "external_ref_number": ref_no
        },
        "message_body": {
            "mobile_number": msisdn,
            "IMSI": imsi,
            "security_stamp": security_stamp
        }
    }
    logging.info(f'Sending request: {data} for validation with ref_no {ref_no}')
    response = requests.post(ussd_url, json=data).json()
    logging.info(f'Response received for {ref_no}: {response}')
    if response['error_code'] == '00':
        customer_details = response['error_desc']['customerdetails'][0]
        return customer_details
    else: 
        return False

def set_pin(msisdn, token, pin):
    b64token, ref_no, security_stamp = generate_securiy_credentials(msisdn, token, pin)
    data = {
        "message_validation": {
            "api_user": "",
            "api_password": "",
            "token": b64token.decode('utf-8'),
        },
        "message_route": {
            "interface": "MOBILE",
            "request_type": "SETPIN",
            "external_ref_number": ref_no
        },
        "message_body": {
            "mobile_number": msisdn,
            "newpin": base64.b64encode(pin.encode('ascii')).decode('utf-8'),
            "security_stamp": security_stamp
        }
    }
    logging.info(f'Sending request: {data} for set pin with ref_no {ref_no}')
    response = requests.post(ussd_url, json=data).json()
    logging.info(f'Response received for {ref_no}: {response}')
    if response['error_code'] == '00':
        customer_details = response['error_desc']['customerdetails']
        return customer_details
    else: 
        return False

def change_pin(msisdn, token, old_pin, new_pin):
    b64token, ref_no, security_stamp = generate_securiy_credentials(msisdn, token, f'{new_pin}#{old_pin}')
    data = {
        "message_validation": {
            "api_user": "",
            "api_password": "",
            "token": b64token.decode('utf-8'),
        },
        "message_route": {
            "interface": "MOBILE",
            "request_type": "CHANGEPIN",
            "external_ref_number": ref_no
        },
        "message_body": {
            "mobile_number": msisdn,
            "oldpin": base64.b64encode(old_pin.encode('ascii')).decode('utf-8'),
            "newpin":  base64.b64encode(new_pin.encode('ascii')).decode('utf-8'),
            "security_stamp": security_stamp
        }
    }
    logging.info(f'Sending request: {data} for change pin with ref_no {ref_no}')
    response = requests.post(ussd_url, json=data).json()
    logging.info(f'Response received for {ref_no}: {response}')
    return response

def login(msisdn, token, pin):
    b64token, ref_no, security_stamp = generate_securiy_credentials(msisdn, token, pin)
    data = {
        "message_validation": {
            "api_user": "",
            "api_password": "",
            "token": b64token.decode('utf-8'),
        },
        "message_route": {
            "interface": "MOBILE",
            "request_type": "LOGIN",
            "external_ref_number": ref_no
        },
        "message_body": {
            "mobile_number": msisdn,
            "pin": base64.b64encode(pin.encode('ascii')).decode('utf-8'),
            "security_stamp": security_stamp
        }
    }
    logging.info(f'Sending request: {data} for login with ref_no {ref_no}')
    response = requests.post(ussd_url, json=data).json()
    logging.info(f'Response received for {ref_no}: {response}')
    if response['error_code'] == '00':
        return response['error_desc']['customerdetails']
    else: 
        return False

def account_balance(msisdn, token, customer_account, customer_branch):
    b64token, ref_no, security_stamp = generate_securiy_credentials(msisdn, token, f'{customer_account}#{customer_branch}')
    data = {
        "message_validation": {
            "api_user": "",
            "api_password": "",
            "token": b64token.decode('utf-8'),
        },
        "message_route": {
            "interface": "COREBANKING",
            "request_type": "BALANCE_REQ",
            "external_ref_number": ref_no
        },
        "message_body": {
            "CustomerAccount": customer_account,
            "CustomerBranch":  customer_branch,
            "security_stamp": security_stamp
        }
    }
    logging.info(f'Sending request: {data} for account balance with ref_no {ref_no}')
    response = requests.post(ussd_url, json=data).json()
    logging.info(f'Response received for {ref_no}: {response}')
    if response['error_code'] == '00':
        return response['error_desc']
    else: 
        return False

def account_ministatement(msisdn, token, customer_account, customer_branch):
    b64token, ref_no, security_stamp = generate_securiy_credentials(msisdn, token, f'{customer_account}#{customer_branch}')
    data = {
        "message_validation": {
            "api_user": "",
            "api_password": "",
            "token": b64token.decode('utf-8'),
        },
        "message_route": {
            "interface": "COREBANKING",
            "request_type": "MINISTATEMENT_REQ",
            "external_ref_number": ref_no
        },
        "message_body": {
            "CustomerAccount": customer_account,
            "CustomerBranch":  customer_branch,
            "security_stamp": security_stamp
        }
    }
    logging.info(f'Sending request: {data} for ministatement with ref_no {ref_no}')
    response = requests.post(ussd_url, json=data).json()
    logging.info(f'Response received for {ref_no}: {response}')
    if response['error_code'] == '00':
        return response['error_desc']
    else: 
        return False

def account_transfer(msisdn, token, customer_account, customer_branch, amount, offset_account):
    b64token, ref_no, security_stamp = generate_securiy_credentials(msisdn, token, f'{customer_account}#{customer_branch}#{amount}#{offset_account}')
    data = {
        "message_validation": {
            "api_user": "",
            "api_password": "",
            "token": b64token.decode('utf-8'),
        },
        "message_route": {
            "interface": "FCUBS",
            "request_type": "TRANSFER_REQ",
            "external_ref_number": ref_no
        },
        "message_body": {
            "txntrn": "FTR",
            "account": customer_account,
            "branch":  customer_branch,
            "offsetacc": offset_account,
            "offsetbranch": customer_branch,
            "currency": "KES",
            "narration": f'Transfer from {customer_account} to {offset_account}',
            "mobile": f'0{msisdn[3:]}',
            "amount": amount,
            "security_stamp": security_stamp
        }
    }
    logging.info(f'Sending request: {data} for account transfer with ref_no {ref_no}')
    response = requests.post(ussd_url, json=data).json()
    logging.info(f'Response received for {ref_no}: {response}')
    if response['error_code'] == '00':
        return response['error_desc']
    else: 
        return False

def airtime_transfer(msisdn, token, customer_account, customer_branch, amount):
    b64token, ref_no, security_stamp = generate_securiy_credentials(msisdn, token, f'{customer_account}#{customer_branch}#{amount}')
    data = {
        "message_validation": {
            "api_user": "",
            "api_password": "",
            "token": b64token.decode('utf-8'),
        },
        "message_route": {
            "interface": "AIRTIME",
            "request_type": "AIRTIME_REQ",
            "external_ref_number": ref_no
        },
        "message_body": {
            "txntrn": "FTR",
            "account": customer_account,
            "branch":  customer_branch,
            "currency": "KES",
            "narration": f'Airtime request for {msisdn}',
            "mobile": f'0{msisdn[3:]}' if msisdn[3:] == '254' else msisdn,
            "amount": amount,
            "security_stamp": security_stamp
        }
    }
    logging.info(f'Sending request: {data} for airtime with ref_no {ref_no}')
    response = requests.post(ussd_url, json=data).json()
    logging.info(f'Response received for {ref_no}: {response}')
    if response['error_code'] == '00':
        return response['error_desc']
    else: 
        return False
    
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
