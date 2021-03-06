#concerned attributes
ATTR_USER_NAME=1
ATTR_USER_PASSWORD=2
ATTR_CHAP_PASSWORD=3
ATTR_CHAP_CHALLENGE=60
ATTR_EAP_MESSAGE=79
ATTR_MESSAGE_AUTHENTICATOR=80
ATTR_CALLING_STATION_ID=31   #get MAC

#codes
CODE_INVALID = 0
CODE_ACCESS_REQUEST = 1
CODE_ACCESS_ACCEPT = 2
CODE_ACCESS_REJECT = 3
CODE_ACCOUNT_REQUEST = 4
CODE_ACCOUNT_RESPONSE = 5

#dipc message types
MT_ACCT_2_ACCP=400
MT_ACCP_2_ACCT=401
MT_AUTT_2_AUTP=402
MT_AUTP_2_AUTT=403

MT_AUTP_2_PASS=404 #request to get password
MT_PASS_2_AUTP=405 #response with password
MT_AUTP_2_HLR=406  #request to get authentication vector
MT_HLR_2_AUTP=407  #response with authentication vector

MT_ACCP_2_EPP=408  #request from acct_processor to E/// prepaid
MT_EPP_2_ACCP=409  #response from E/// prepaid to acct_processor


PROG_NAME="radius_server"
KPI_REPORT_INTERVAL = 10
KPI_OID = {
    "ACCESS_REQ_RCV"     :"1.3.6.1.4.1.193.176.1.4.1",
    "ACCESS_ACCEPT_SND"  :"1.3.6.1.4.1.193.176.1.4.2",
    "ACCESS_INVALID"     :"1.3.6.1.4.1.193.176.1.4.3",
    "ACCOUNT_REQ_RCV"    :"1.3.6.1.4.1.193.176.1.4.4",
    "ACCOUNT_ACK_SND"    :"1.3.6.1.4.1.193.176.1.4.5",
    "ACCOUNT_INVALID"    :"1.3.6.1.4.1.193.176.1.4.6",
    "INVALID_REQ_RCV"    :"1.3.6.1.4.1.193.176.1.4.7",
    "ACCESS_REJECT_SND"  :"1.3.6.1.4.1.193.176.1.4.8",
    "DISCONN_REQ_SND"    :"1.3.6.1.4.1.193.176.1.4.9",
    "DISCONN_FAILED_TO_FIND_SESSION":"1.3.6.1.4.1.193.176.1.4.10",
    "DISCONN_ACK_RCV"    :"1.3.6.1.4.1.193.176.1.4.11",
    "DISCONN_NACK_RCV"   :"1.3.6.1.4.1.193.176.1.4.12",
    "DISCONN_REQ_TIMOUT" :"1.3.6.1.4.1.193.176.1.4.13",
    "DISCONN_REQ_RETRY"  :"1.3.6.1.4.1.193.176.1.4.14",
    "RADIUS_REQUEST_RESEND_RCV": "1.3.6.1.4.1.193.176.1.4.15",
    "FAILED_TO_PROCESS_ACCESS": "1.3.6.1.4.1.193.176.1.4.16",
    "FAILED_TO_PROCESS_ACCOUNT": "1.3.6.1.4.1.193.176.1.4.17",
}
     
