#!/bin/env python

EAP_CODE={
        'REQUEST':1,
        'RESPONSE':2,
        'SUCCESS':3,
        'FAIL':4,
        }

EAP_TYPE= {
        "IDENTIFY":1,
        "NOTIFY":2,
        "SIM":18,
        "AKA":23,
        }

EAP_SUBTYPE= {
        "START":10,
        "CHALLENGE":11,
        }

EAP_AT = {
        "RAND":1,
        "AUTN":2,
        "RES":3,
        "AUTS":4,
        "PADDING":6,
        "NONCE_MT":7,
        "PERMANENT_ID_REQ":10,
        "MAC":11,
        "NOTIFICATION":12,
        "ANY_ID_REQ":13,
        "IDENTITY":14,
        "VERSION_LIST":15,
        "SELECTED_VERSION":16,
        "FULLAUTH_ID_REQ":17,
        "COUNTER":19,
        "COUNTER_TOO_SMALL":20,
        "NONCE_S":21,
        "CLIENT_ERROR_CODE":22,
        "IV":129,
        "ENCR_DATA":130,
        "NEXT_PSEUDONYM":132,
        "NEXT_REAUTH_ID":133,
        "CHECKCODE":134,
        "RESULT_IND":135,
        }

CODE_EAP = {
        4:"FAIL",
        1:"REQUEST",
        2:"RESPONSE",
        3:"SUCCESS",
        }

TYPE_EAP = {
        23:"AKA",
        1:"IDENTIFY",
        2:"NOTIFY",
        18:"SIM",
        }

AT_EAP = {
        1:"RAND",
        10:"PERMANENT_ID_REQ",
        21:"NONCE_S",
        22:"CLIENT_ERROR_CODE",
        3:"RES",
        19:"COUNTER",
        133:"NEXT_REAUTH_ID",
        17:"FULLAUTH_ID_REQ",
        12:"NOTIFICATION",
        16:"SELECTED_VERSION",
        134:"CHECKCODE",
        2:"AUTN",
        7:"NONCE_MT",
        129:"IV",
        4:"AUTS",
        14:"IDENTITY",
        132:"NEXT_PSEUDONYM",
        13:"ANY_ID_REQ",
        130:"ENCR_DATA",
        6:"PADDING",
        11:"MAC",
        135:"RESULT_IND",
        20:"COUNTER_TOO_SMALL",
        15:"VERSION_LIST",
        }
SUBTYPE_EAP= {
        10:"START",
        11:"CHALLENGE",
        }

def translate_eap(dd, kk):
    try:
        return dd[kk]
    except KeyError:
        return str(kk)

