import json
from zeep import client
from zeep.plugins import HistoryPlugin
from datetime import datetime
from lxml import etree

query_wsdl_url = 'http://10.54.66.10:7005/FCUBSAccService/FCUBSAccService?WSDL'
transaction_wsdl_url = 'http://10.54.66.10:7005/FCUBSRTService/FCUBSRTService?WSDL'
prod_query = "http://10.54.12.79:7003/FCUBSAccService/FCUBSAccService?WSDL"
prod_transaction = "http://10.54.12.79:7003/FCUBSRTService/FCUBSRTService?WSDL"

f = open('customers.json')
data = json.load(f)['customers']
history = HistoryPlugin()
query_client = client.Client(query_wsdl_url, plugins=[history])
transaction_client = client.Client(transaction_wsdl_url, plugins=[history])


def get_acc_no(msisdn):
        for key in data:
            if key['msisdn'] == msisdn:
                acc_no = key['acc_no']
        return acc_no

def get_balance(msisdn):
    try:
        for key in data:
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
        for key in data:
            if key['msisdn'] == msisdn:
                acc_no = key['acc_no']
                branch = key['branch']
        header = {
                "SOURCE": "FCAT",
                "UBSCOMP": "FCUBS",
                "USERID": "FCATOP",
                "BRANCH": "001",
                "SERVICE": "FCUBSAccService",
                "OPERATION": "QueryAccBal",
        }
        body = {
                "Main-IO": {
                    "STMT_ID": "000941",
                    "CUSNO": acc_no,
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

def create_transaction(msisdn):
    try:
        for key in data:
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
                    "TXNAMT": "1000",
                    "TXNACC": "0020000480",
                    "TXNDATE": "today",
                    }
            }
        result = transaction_client.service.CreateTransactionIO(
            header,
            body
            )
        print(result)
    except Exception as e:
        raise Exception(e)


# print(get_balance("254722590742"))
get_statement("254725460158")