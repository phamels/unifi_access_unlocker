import requests
from getpass import getpass
import urllib3
import ipaddress

print(">>> Unifi Access Hub Unlocker by Pieter Hamels")
unifi_os_uri = input("Please enter the IP address of your Unifi Access Hub Controller: ")
try:
    ipaddress.ip_address(unifi_os_uri)
    unifi_os_uri = f"https://{unifi_os_uri}"
except:
    exit('>>> Please enter a valid IP address for your Unifi Access Hub Controller.')

urllib3.disable_warnings()
s = requests.Session()
s.headers = {
    'Content-type': 'application/json',
    'Accept': 'application/json'
}


def do_auth(username, password):
    print(">>> Authenticating...")
    return s.post(f"{unifi_os_uri}/api/auth/login", json={'username': username, 'password': password}, verify=False)


def get_hubs():
    print(">>> Fetching Unifi Access Hubs...")
    hubs_list = []
    doors = "/proxy/access/api/v2/devices/topology"
    unlock_r = s.get(f"{unifi_os_uri}{doors}", verify=False)
    for data in unlock_r.json()['data']:
        for floor in data['floors']:
            for door in floor['doors']:
                for device_group in door['device_groups']:
                    for device in device_group:
                        if device['device_type'] == "UAH":
                            hubs_list.append(
                                {'unique_id': device['unique_id'], 'resource_name': device['resource_name']})
    return hubs_list


def select_hub(hubs_list):
    selected_hub = int(input("Choose a hub of which to unlock the door: "))
    if 0 < selected_hub <= len(hubs_list):
        return hubs_list[selected_hub - 1]['unique_id']
    return None


def show_found_hubs(hubs_list):
    print("\n>>> Found the following hubs: ")
    x = 1
    for hub in hubs_list:
        print(f"{x} - {hub['resource_name']}")
        x += 1


def unlock_door(ar, hub_to_use):
    print(">>> Unlocking...")
    achterdeur_unlock = f"/proxy/access/api/v2/device/{hub_to_use}/relay_unlock"
    s.headers = {
        'X-Csrf-Token': ar.headers['X-Csrf-Token']
    }
    unlock_r = s.put(f"{unifi_os_uri}{achterdeur_unlock}", verify=False)

    if unlock_r.json()['msg'] == "success":
        return True
    return False


if __name__ == "__main__":
    username = input('Unifi Access Username: ')
    password = getpass('Unifi Access Password: ')
    ar = do_auth(username, password)

    hubs = get_hubs()
    print(hubs)
    show_found_hubs(hubs)
    selected_hub = select_hub(hubs)
    while selected_hub is None:
        selected_hub = select_hub(hubs)
    if unlock_door(ar, selected_hub):
        exit('Door was unlocked!')
    exit('Something went wrong!')


