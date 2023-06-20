import ipaddress
import requests
import urllib3
import configparser

try:
    settings = configparser.ConfigParser(interpolation=None)
    settings.read('config.ini')
except:
    exit('Error in configuration - please check the config.ini file.')


if "unifi_os_ip" in settings['DEFAULT']:
    try:
        ipaddress.ip_address(settings["DEFAULT"]["unifi_os_ip"])
        unifi_os_uri = settings['DEFAULT']["unifi_os_ip"]
        unifi_os_uri = f"https://{unifi_os_uri}"
    except Exception as e:
        exit('Error in configuration - not a valid unifi os IP - please check the "config.ini" file.')
else:
    exit('Error in unifi os ip in configuration - please check the "config.ini" file.')


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
    username = None
    password = None
    hub_id = None

    if "username" in settings['DEFAULT'] and "password" in settings['DEFAULT']:
        username = settings['DEFAULT']["username"]
        password = settings['DEFAULT']["password"]
    else:
        exit('Error in username and password configuration - please check the "config.ini" file.')

    ar = do_auth(username, password)

    hubs = get_hubs()
    if "hub_id" in settings['DEFAULT']:
        hub_id = settings['DEFAULT']["hub_id"]
        found = False
        for hub in hubs:
            if hub['unique_id'] == hub_id:
                found = True
        if not found:
            print('Error in configuration - No HUB id given. - please check the "config.ini" file.')
            print('List of possible hubs: ')
            for hub in hubs:
                print(f"HUB ID: '{hub['unique_id']}' : {hub['resource_name']}")
            exit('')
    else:
        print('Error in configuration - No HUB id given. - please check the "config.ini" file.')
        print('List of possible hubs: ')
        for hub in hubs:
            print(f"HUB ID: '{hub['unique_id']}' : {hub['resource_name']}")
        exit('')

    if unlock_door(ar, hub_id):
        exit('Door was unlocked!')
    exit('Something went wrong!')


