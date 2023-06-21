import datetime
import json
import sys

import requests

'''
.Name
    -CrewAllocationDelta.py

.Description
    -Automate Crew Allocations for Click Schedule. Will delete oldest allocation, create the next newest allocation,
    and assign crew leader to the newest allocation if present.

.Version
    -Original Release Dalen Hurtt - 04/11/23
    -Code Review Steve On         - 05/03/23
    -Code Refactor Dalen Hurtt    - 05/03/23
    -Code Review Steve On         - 05/04/23
    -Code Refactor Dalen Hurtt    - 06/01/23    

.Frequency 
    -Daily
'''

''' GLOBAL VARIABLES '''


argumentU = str(sys.argv[1])
argumentP = str(sys.argv[2])
if str(sys.argv[3] == 'False'):
    prodCheck = False
elif str(sys.argv == 'True'):
    prodCheck = True
else:
    print('Prodcheck error, make sure the True or False has a capital T or F')
EngineerObject = 'Engineer'
AllocationObject = 'CrewAllocation'

''' FUNCTIONS '''


def deleteClickObject(objName, key, prod, username, password):
    url = prod + objName + '/' + str(key)
    print(url)
    try:
        from requests.auth import HTTPBasicAuth
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.delete(url=url, headers=headers,auth=(username,password))
        print(r)
    except Exception as e:
        print(e)

def UpdateClickObject(data, URL, username, password):
    print('Update Click Object')
    try:
        # Attempt a POST call to Click
        from requests.auth import HTTPBasicAuth
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        print(json.dumps(data))
        print(URL)
        r = requests.post(URL + 'Task', data=json.dumps(data), headers=headers, auth=(username, password))
        print(r.status_code)
        if (r.status_code == 200 or r.status_code == 500):
            res = r.text
            print(res)
        else:
            res = r.text
            print(res)
    except Exception as e:
        print(e)

def GetClickObject(obj, PARAMS, url, username, password):
    #print('Get Click Objects')
    #print(obj,PARAMS,url,username,password)
    er = url + obj + "?" + PARAMS
    print(url + obj + "?" + PARAMS)
    ObjList = []
    #Get REST Call
    try:
        from requests.auth import HTTPBasicAuth
        r = requests.get(url=url + obj + "?" + PARAMS,
                         auth=(username, password))
        #print(r)
        print(r.status_code)
        if (r.status_code == 200 or r.status_code == 500):
            #convert string response to Python JSON
            data = r.json()
            # print(data)
            #print('object Size: ' + str(len(data)))
            #loop through objects and create an object List
            for item in data:
                ObjList.append(item)
            '''
            #Get object properties
            for item in data[0]:
                print(item)
            '''
            return ObjList
    except Exception as e:
        print(e)

def prodObjectCheck(prod):
    # api-endpoint
    URL_Objects = "https://fse-na-sb-int01.cloud.clicksoftware.com/so/api/objects/"
    PRODURL_Objects = "https://fse-na-int01.cloud.clicksoftware.com/so/api/objects/"
    if prod:
        return PRODURL_Objects
    else:
        return URL_Objects

def create_crew_allocation(hasCrewLeader, crewLeader, obj):
    """ Builds a payload by passing X object with a crew leader role if any exists."""
    crewLeaderSO = []
    leadChangeDate = "1899-12-30T00:00:00"
    # if there is a crewleader, updates fields accordingly in the return statement
    if hasCrewLeader:
        crewLeaderSO = [{"Key": crewLeader[0]['Key'], "@DisplayString": "CrewLeader"}]
        leadChangeDate = datetime.datetime.now().isoformat()

    startTime = datetime.datetime.fromisoformat(obj['FinishTime']) + datetime.timedelta(days=1)
    finishTime = startTime + datetime.timedelta(days=1)

    return {
        "@objectType": "CrewAllocation",
        "Key": -1,
        "Crew": {
            "Key": obj['Crew']['Key'],
            "@DisplayString": obj['Crew']['@DisplayString']
        },
        "StartTime": startTime.isoformat(),
        "FinishTime": finishTime.isoformat(),
        "AllocatedResource": {
            "Key": obj['AllocatedResource']['Key'],
        },
        "ContinueFromHomeBase": obj['ContinueFromHomeBase'],
        "Critical": obj['Critical'],
        "Relocation": obj['Relocation'],
        "Recurrence_SO": {
            "Key": obj['Recurrence_SO']['Key'],
        },
        "MobileKey_SO": obj['MobileKey_SO'],
        "CrewAllocationRoles_SO": crewLeaderSO,
        "LeaderChangeDate_SO": leadChangeDate
    }


def get_crewAllocation_records(engineer, crewLeader):
    '''Gets the crew allocation for a specific engineer. then creates a payload for a new allocation and a
    payload for the most recent allocation and updates both. Returns the key for the oldest allocation'''
    earliest_allocation = GetClickObject(
        AllocationObject,
        "$top=1&$orderby=StartTime asc&$expand=AllocatedResource&$filter=AllocatedResource/Name eq " +
        "'" + engineer + "'", prodObjectCheck(prodCheck), argumentU, argumentP)

    latest_allocation = GetClickObject(
        AllocationObject,
        "$top=1&$orderby=StartTime desc&$expand=AllocatedResource&$filter=AllocatedResource/Name eq " +
        "'" + engineer + "'", prodObjectCheck(prodCheck), argumentU, argumentP)

    # if resource does not have any allocations, exit function
    if latest_allocation.__len__() == 0 or earliest_allocation.__len__() == 0:
        return 0

    # Check if the latest allocation has crew leader role
    try:

        payloadNew = create_crew_allocation(latest_allocation[0]['CrewAllocationRoles_SO'], crewLeader, latest_allocation[0])
        payloadLatest = {
            "@objectType": "CrewAllocation", "Key": latest_allocation[0]['Key'],
            "CrewAllocationRoles_SO": [],
            "LeaderChangeDate_SO": "1899-12-30T00:00:00"
        }

        # Update most recent crew allocation
        UpdateClickObject(payloadLatest, prodObjectCheck(prodCheck), argumentU, argumentP)

        # Create new crew allocation
        UpdateClickObject(payloadNew, prodObjectCheck(prodCheck), argumentU, argumentP)

    except TypeError as e:
        print("Crew")

    return earliest_allocation[0]['Key']


''' Main '''
crewLeader = GetClickObject("SOUserRole",
                            "$filter=Name eq 'CrewLeader'",
                            prodObjectCheck(prodCheck), argumentU, argumentP)
active_engineers = GetClickObject(
    EngineerObject, '$filter=Active eq true', prodObjectCheck(prodCheck), argumentU, argumentP)

for eng in active_engineers:

    if eng['Crew']:
        continue

    # get_crewAllocation returns zero if there is no crew allocation for user
    key_for_delete = get_crewAllocation_records(eng['Name'], crewLeader)

    if key_for_delete > 0:
        deleteClickObject(
            AllocationObject, key_for_delete, prodObjectCheck(prodCheck), argumentU, argumentP)

