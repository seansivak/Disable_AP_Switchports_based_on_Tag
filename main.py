#!/usr/bin/env python
# Import Requests to get the webpage from DNA Center
import requests
# Bypass certificate warnings
import requests.packages.urllib3.exceptions
from urllib3.exceptions import InsecureRequestWarning
# This enables encoding the username and password to receive a token from DNA Center
import os
import logging
import json

# Suppress Insecure Requests Warnings for self-signed certificate on DNA Center
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def pretty(json_obj):
    return json.dumps(json_obj, indent=2)

def main():
    dnacServer = os.getenv("DNAC_SERVER")
    myUserName = os.getenv("DNAC_USERNAME")
    myPassword = os.getenv("DNAC_PASSWORD")
    verificationSettings = os.getenv("DNAC_VERIFICATION") ## enable | disable
    verificationDeployment = os.getenv("DNAC_VERIFYDEPLOY") ##  deploy | preview
    tagName = os.getenv("DNAC_TAGNAME")
    debugEnabled = os.getenv("DEBUG")

    if debugEnabled is None:
        debugEnabled = False
        debugLevel = logging.INFO
    else:
        debugEnabled = True
        debugLevel = logging.DEBUG


    logging.basicConfig(level=debugLevel)

    if myUserName is None:
        myUserName = input('Username:\n')
    if dnacServer is None:
        dnacServer = input('Enter DNA Center Server IP Address:\n')
    if myPassword is None:
        myPassword = input('Password:\n')
    if verificationSettings is None:
        verificationSettings = input('Do you want to enable or disable switch ports connected to tagged APs? Type enable or disable: ')
    if verificationDeployment is None:
        verificationDeployment = input('Do you want to preview or actually deploy these settings? Type deploy or preview: ')
    if tagName is None:
        tagName = input('Enter Tag Name:\n')




    # Specify the URL to create a token
    tokenURL = "https://" + dnacServer + "/dna/system/api/v1/auth/token"

    myTokenResponse = requests.post(tokenURL, auth=(myUserName, myPassword), verify=False)
    myTokenDict = myTokenResponse.json()

    # Creating a token returns a Dictionary where the attribute is Token and the value is the actual token
    myToken = myTokenDict['Token']

    payload = {}
    headers = {
        'X-Auth-Token': myToken
    }


    url = "https://" + dnacServer + "/dna/intent/api/v1/tag?name=" + tagName
    response = requests.get(url, headers=headers, data=payload, verify=False)
    tagList = response.json()['response']
    for i in tagList:
        tagId = i['id']

    # Get Member Count based on tagId for pagination
    url = "https://" + dnacServer + "/dna/intent/api/v1/tag/" + tagId + "/member/count?memberType=networkdevice"
    response = requests.get(url, headers=headers, data=payload, verify=False)
    memberCount = response.json()['response']

    offset = 1
    limit = 500

    deviceList = []

    # Get devices tagged with tagId
    while offset <= memberCount:
        url = "https://" + dnacServer + "/dna/intent/api/v1/tag/" + tagId + "/member?memberType=networkdevice&limit=" + str(limit) + "&offset=" + str(offset)
        response = requests.get(url, headers=headers, data=payload, verify=False)
        deviceList.extend(response.json()['response'])
        offset += limit

    # Create an AP list from the deviceList
    apList = []
    apCount = 0
    for listItem in deviceList:
        if listItem['family'] == "Unified AP":
            apList.append(listItem)
            apCount = apCount + 1
    logging.info("AP Count = " + str(apCount))

    # Grab the UUIDs from all the APs
    apInstanceList = []
    apInstanceCount = 0
    for listItem in apList:
        apInstanceList.append(listItem['instanceUuid'])
        apInstanceCount = apInstanceCount + 1

    # Get the topology
    url = "https://" + dnacServer + "/dna/intent/api/v1/topology/physical-topology"
    response = requests.get(url, headers=headers, data=payload, verify=False)
    topologyDict = response.json()['response']
    matchesFound = 0
    logging.debug(f"Topology info: {pretty(topologyDict)}")
    # Create a list of switchports connected to APs
    switchPortList = []
    for key, value in topologyDict.items():
        if key == 'links':
            for apInstance in apInstanceList:
                logging.info(f"Processing AP {apInstance}")
                for listItem in value:
                    if str(apInstance) == str(listItem['source']):
                        switchPortList.append(listItem['endPortID'])
                        matchesFound = matchesFound + 1
                        logging.debug(f"Found in source, adding AP info: {pretty(listItem)}")
                    if str(apInstance) == str(listItem['target']):
                        switchPortList.append(listItem['startPortID'])
                        matchesFound = matchesFound + 1
                        logging.debug(f"Found in target, adding AP info: {pretty(listItem)}")


    # Disable all switchports connected to APs
    putHeaders = {
        'X-Auth-Token': myToken,
    }

    disablePorts = { "adminStatus": "DOWN"}
    enablePorts = { "adminStatus": "UP"}

    if verificationSettings == 'enable':
        portSettings = enablePorts
    else:
        portSettings = disablePorts

    if verificationDeployment.lower() == 'deploy':
        deploymentSettings = "Deploy"
    else:
        deploymentSettings = "Preview"

    logging.debug(f"switchPortList: {switchPortList}")
    for listItem in switchPortList:
        params = {"deploymentMode":deploymentSettings}
        url = f"https://{dnacServer}/dna/intent/api/v1/interface/{listItem}"
        logging.debug(f"Sending put: payload={portSettings}, headers={putHeaders} url=*{url}* params={params}")
        setPorts = requests.put(url, headers=putHeaders, json=portSettings, verify=False, params=params)
        logging.info(f"Return payload={setPorts.text}")

if __name__ == "__main__":
    main()


