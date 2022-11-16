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
query_wsdl_url = 'http://10.54.66.10:7005/FCUBSAccService/FCUBSAccService?WSDL'
transaction_wsdl_url = 'http://10.54.66.10:7005/FCUBSRTService/FCUBSRTService?WSDL'
prod_query = "http://10.54.12.79:7003/FCUBSAccService/FCUBSAccService?WSDL"
prod_transaction = "http://10.54.12.79:7003/FCUBSRTService/FCUBSRTService?WSDL"
ussd_url = "http://10.54.66.16:8282/api/Solid/SubmitRequest"

history = HistoryPlugin()
logging.info('STARTING APP')
query_client = client.Client(query_wsdl_url, plugins=[history])
logging.info('CONNECTING TO QUERY WSDL')
transaction_client = client.Client(transaction_wsdl_url, plugins=[history])
logging.info('CONNECTING TO TRANSACTION WSDL')

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
    response = requests.post(ussd_url, json=(data)).json()
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
    response = requests.post(ussd_url, json=(data)).json()
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
    response = requests.post(ussd_url, json=data).json()
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
    response = requests.post(ussd_url, json=data).json()
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
    response = requests.post(ussd_url, json=data).json()
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
    response = requests.post(ussd_url, json=data).json()
    if response['error_code'] == '00':
        return response['error_desc']
    else: 
        return False

def get_airtime_token():
    token = base64.b64encode(f'{airtime_key} : {airtime_secret}')
    response = requests.request("POST", airtime_auth_url, headers = { 'Authorization': f'Bearer {token}' })
    return response.json['access_token']

def get_balance(msisdn):
    try:
        data = load_data()
        for key in data['customers']:
            if key['msisdn'] == msisdn:
                acc_no = key['acc_no']
                branch = key['branch']
        time_now = datetime.now()
        header = {
                "SOURCE": "FCAT",
                "UBSCOMP": "FCUBS",
                "USERID": "FCATOP",
                "BRANCH": "001",
                "SERVICE": "FCUBSAccService",
                "OPERATION": "QueryAccBal",
        }
        body = {
                "ACC-Balance": {
                    "ACC_BAL": {
                    "BRANCH_CODE": branch,
                    "CUST_AC_NO": acc_no,
                    }
                }
            }
        result = query_client.service.QueryAccBalIO(
            header,
            body
            )
        return result['FCUBS_BODY']['ACC-Balance']['ACC_BAL'][0]['CURBAL']
    except Exception as e:
        raise Exception(e)

def get_statement(msisdn):
    try:
        data = load_data()
        for key in data['customers']:
            if key['msisdn'] == msisdn:
                acc_no = key['acc_no']
                branch = key['branch']
        header = {
                "SOURCE": "FCAT",
                "UBSCOMP": "FCUBS",
                "USERID": "FCATOP",
                "BRANCH": "001",
                "SERVICE": "FCUBSAccService",
                "OPERATION": "QueryCbStmt",
                "FUNCTIONID": "CSRCSTAD"
        }
        body = {
                "Main-IO": {
                    "STMT_ID": "PLAN_1",
                    "CUSNO": "000864",
                    }
            }
        result = query_client.service.QueryCbStmtIO(
            header,
            body
            )
    except Exception as e:
        raise Exception(e)

def create_transaction(msisdn, amount):
    try:
        data = load_data()
        for key in data['customers']:
            if key['msisdn'] == msisdn:
                acc_no = key['acc_no']
                branch = key['branch']
        header = {
                "SOURCE": "FCAT",
                "UBSCOMP": "FCUBS",
                "USERID": "FCATOP",
                "BRANCH": "002",
                "SERVICE": "FCUBSRTService",
                "OPERATION": "CreateTransaction",
        }
        body = {
                "Transaction-Details-IO": {
                    "XREF": "1234567",
                    "PRD": "123456",
                    "BRN": "1234567",
                    "TXNAMT": amount,
                    "TXNACC": "0020000480",
                    "TXNDATE": "today",
                    }
            }
        result = transaction_client.service.CreateTransactionIO(
            header,
            body
            )
        token = get_token(transaction_key, transaction_secret)
        payload = json.dumps({
            "InitiatorName": "testapiuser",
            "SecurityCredential": "***********",
            "Occassion": "StallOwner",
            "CommandID": "BusinessPayment",
            "PartyA": "896150",
            "PartyB": "254711891648",
            "Remarks": "Test B2C",
            "Amount": amount,
            "QueueTimeOutURL": "http://197.248.93.186:8000/b2c/result",
            "ResultURL": "http://197.248.93.186:8000/b2c/result"
        })
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", b2c_url, headers=headers, data=payload)

    except Exception as e:
        raise Exception(e)
    
def int_check(ussd_string):
    try:
        int(ussd_string)
        return True
    except Exception as e:
        return False

def phone_number_validate(phone_number):
    if (phone_number[:2] != "254" and len(phone_number) != 12):
        if (phone_number[0] != "0" and len(phone_number) != 10):
            return False
        else: 
            return True
    else:
        return True

def initiate_airtime(phone_number, amount):
    try:
        token = get_airtime_token()
        payload = json.dumps({
            "msisdn": "msisdn",
            "amount": amount,
            "service_pin": "service_pin",
            "receiverMsisdn": phone_number
        })
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", airtime_url, headers=headers, data=payload)

        return
    except Exception as e:
        return e
