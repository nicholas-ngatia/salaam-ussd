import json
import logging
import requests
import base64
from zeep import client
from zeep.plugins import HistoryPlugin
from datetime import datetime
from lxml import etree


logging.basicConfig(format='%(asctime)s - %(message)s', filename='ussd_app.log', filemode='w', level=logging.INFO)
query_wsdl_url = 'http://10.54.66.10:7005/FCUBSAccService/FCUBSAccService?WSDL'
transaction_wsdl_url = 'http://10.54.66.10:7005/FCUBSRTService/FCUBSRTService?WSDL'
prod_query = "http://10.54.12.79:7003/FCUBSAccService/FCUBSAccService?WSDL"
prod_transaction = "http://10.54.12.79:7003/FCUBSRTService/FCUBSRTService?WSDL"

history = HistoryPlugin()
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

def get_airtime_token():
    token = base64.b64encode(f'{airtime_key} : {airtime_secret}')
    response = requests.request("POST", airtime_auth_url, headers = { 'Authorization': f'Bearer {token}' })
    return response.json['access_token']

def login(msisdn, password):
    data = load_data()
    for key in data['customers']:
        if key['msisdn'] == msisdn:
            if password == key['password']:
                return True
    return False

def first_time_login(msisdn, password):
    data = load_data()
    with open('customers.json', 'w') as f:
        for key in data['customers']:
            if key['msisdn'] == msisdn:
                key['password'] = password
        f.write(json.dumps(data, indent=4))
        f.close()

def whitelist_check(msisdn):
    data = load_data()
    response = False
    for key in data['customers']:
        if key['msisdn'] == msisdn:
            response = True
            break
    return response

def get_acc_no(msisdn):
    data = load_data()
    for key in data['customers']:
        if key['msisdn'] == msisdn:
            acc_no = key['acc_no']
    return acc_no

def check_password(msisdn):
    data = load_data()
    for key in data['customers']:
        if key['msisdn'] == msisdn:
            if key['password'] == "":
                return True
    return False

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
        }
        body = {
                "Main-IO": {
                    "STMT_ID": "PLAN_1",
                    "CUSNO": "000941",
                    }
            }
        result = query_client.service.QueryCbStmtIO(
            header,
            body
            )
        for hist in [history.last_sent, history.last_received]:
            print(etree.tostring(hist["envelope"], encoding="unicode", pretty_print=True))
        print(result)
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

        print(response.text)
        print(result)
    except Exception as e:
        raise Exception(e)
    
def int_check(ussd_string):
    try:
        int(ussd_string)
        return True
    except Exception as e:
        return False

def phone_number_validate(phone_number):
    if phone_number[:2] != "254" or phone_number[0] != "0" or len(phone_number) != 10 or len(phone_number) != 12:
        return False
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

# print(get_balance("254725460158"))
# get_statement("254725460158")
# print(whitelist_check('254711891648'))