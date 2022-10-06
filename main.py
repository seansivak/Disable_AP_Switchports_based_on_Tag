#!/usr/bin/env python
# Import Requests to get the webpage from DNA Center
import requests
# Import HTTPBasicAuth to authenticate to DNA Center
from requests.auth import HTTPBasicAuth
# Bypass certificate warnings
import requests.packages.urllib3.exceptions
from urllib3.exceptions import InsecureRequestWarning
# Import json to return the results from the get request in a json format
import json
import difflib
# This is used to write the results to a csv file.
import csv
# This allows the csv filename to include the timestamp
import datetime as dt
import time
# time.sleep(10) pauses for 10 seconds
# This enables encoding the username and password to receive a token from DNA Center
import base64

# Today's date
currentDate = dt.datetime.today().strftime('%m-%d-%Y-%Hh-%Mm-%Ss')
# Suppress Insecure Requests Warnings for self-signed certificate on DNA Center
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# Import pretty print
from pprint import pprint

# Specify the DNA Center Server
# dnacServer = "172.21.21.10"
# Prompt the user for the DNA Center Server
dnacServer = input('Enter DNA Center Server IP Address:\n')
# Specify the URL to create a token
tokenURL = "https://" + dnacServer + "/dna/system/api/v1/auth/token"
# Username and password used to create the token
myUserName = input('Username:\n')
myPassword = input('Password:\n')
# myUserName = "admin"
# myPassword = "Cisco123"
myUserPass = myUserName + ":" + myPassword
# print(myUserPass)

# Encode the username and password to submit as a header when creating the token
encodedUserPass = str(base64.b64encode(bytes(myUserPass, "utf-8")))
encodedLength = len(encodedUserPass) - 1
encodedUserPass = encodedUserPass[2:encodedLength]
encodedUserPass = "Basic " + encodedUserPass

# Create the header used to create the token
headers = {
    'Authorization': encodedUserPass
}
# Create the token
myTokenResponse = requests.post(tokenURL, headers=headers, verify=False)
myTokenDict = myTokenResponse.json()
# Creating a token returns a Dictionary where the attribute is Token and the value is the actual token
myToken = myTokenDict['Token']

payload = {}
headers = {
    'X-Auth-Token': myToken,
    'Authorization': encodedUserPass
}


# Get Tag ID
tagName = "Power Save AP"
# tagName = input('Enter Tag Name:\n')
url = "https://" + dnacServer + "/dna/intent/api/v1/tag?name=" + tagName
response = requests.get(url, headers=headers, data=payload, verify=False)
json_object = json.loads(response.text)
tagList = json_object['response']
for i in tagList:
    tagId = i['id']

# Get Member Count based on tagId for pagination
url = "https://" + dnacServer + "/dna/intent/api/v1/tag/" + tagId + "/member/count?memberType=networkdevice"
response = requests.get(url, headers=headers, data=payload, verify=False)
json_object = json.loads(response.text)
memberCount = json_object['response']

offset = 1
limit = 500

deviceList = []

# Get devices tagged with tagId
while offset <= memberCount:
    url = "https://" + dnacServer + "/dna/intent/api/v1/tag/" + tagId + "/member?memberType=networkdevice&limit=" + str(limit) + "&offset=" + str(offset)
    response = requests.get(url, headers=headers, data=payload, verify=False)
    json_object = json.loads(response.text)
    deviceList.extend(json_object['response'])
    offset += limit

# Create an AP list from the deviceList
apList = []
apCount = 0
for listItem in deviceList:
    if listItem['family'] == "Unified AP":
        apList.append(listItem)
        apCount = apCount + 1
print("AP Count = " + str(apCount))

# Grab the UUIDs from all the APs
apInstanceList = []
apInstanceCount = 0
for listItem in apList:
    apInstanceList.append(listItem['instanceUuid'])
    apInstanceCount = apInstanceCount + 1

# Get the topology
url = "https://" + dnacServer + "/dna/intent/api/v1/topology/physical-topology"
response = requests.get(url, headers=headers, data=payload, verify=False)
json_object = json.loads(response.text)
topologyDict = json_object['response']
matchesFound = 0

# Create a list of switchports connected to APs
switchPortList = []
for key, value in topologyDict.items():
    if key == 'links':
        for apInstance in apInstanceList:
            for listItem in value:
                if str(apInstance) == str(listItem['source']):
                    switchPortList.append(listItem['endPortID'])
                    matchesFound = matchesFound + 1

# Disable all switchports connected to APs
putHeaders = {
    'X-Auth-Token': myToken,
    'Authorization': encodedUserPass,
    'Content-Type': "application/json",
    'Accept': "application/json"
}

disablePorts = '''{ "adminStatus": "DOWN"}'''
enablePorts = '''{ "adminStatus": "UP"}'''
portSettings = enablePorts

verificationSettings = input('Do you want to enable or disable switch ports connected to tagged APs? Type enable or disable: ')

if verificationSettings == 'enable':
    portSettings = enablePorts
if verificationSettings == 'disable':
    portSettings = disablePorts

verificationDeployment = input('Do you want to preview or actually deploy these settings? Type deploy or preview: ')

if verificationDeployment == 'deploy':
    deploymentSettings = "Deploy"
if verificationDeployment == 'preview':
    deploymentSettings = "Preview"


for listItem in switchPortList:
    url = "https://" + dnacServer + "/dna/intent/api/v1/interface/" + listItem + "?deploymentMode=" + deploymentSettings
    print(url)
    setPorts = requests.put(url, headers=putHeaders, data=portSettings, verify=False)
    json_object = json.loads(setPorts.text)
    print(json_object['response'])



