import PySimpleGUI as sg
import requests
import json
import urllib3
import socket
from pyzabbix import ZabbixAPI

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#function to add host to group
def mon_l2_plus():
    url = "https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php"
    license_list = [y for y in (x.strip() for x in values['lic_field'].splitlines()) if y]
    for line in license_list:
        if "a270920181900-" not in line and len(line) == 5:
            api_lic = f"a270920181900-{line}"
        elif len(line) == 19:
            api_lic = f"{line}"
        else:
            print('-ACHTUNG- Допустимые форматы ввода лицензий:\n01234 (5 символов)\na270920181900-01234 (19 символов)\n')
            break
        try:
            zabbhost = requests.post(url,verify=False,
                json={
                    "jsonrpc": "2.0",
                    "method": "host.get",
                    "params": {
                        "output": ["hostid", "host"],
                        "searchWildcardsEnabled": "true",
                        "search": {"host": api_lic}
                    },
                    "auth": "apikey",
                    "id": 1
                })
            a = json.dumps(zabbhost.json(), indent=3)
            b = json.loads(a)
            host_id = (b["result"][0]["hostid"])
            print(api_lic)

            mongroup = requests.post(url,verify=False,
                json={
                    "jsonrpc": "2.0",
                    "method": "hostgroup.get",
                    "params": {
                        "output": "extend",
                        "hostids": host_id,
                        "filter": {"name": "Monitor_HDD"}
                    },
                    "auth": "apikey",
                    "id": 1
                })
            a = json.dumps(mongroup.json(), indent=3)
            b = json.loads(a)
            group_id = (b["result"])
            if group_id == []:
                print('Добавление в Monitor_HDD')
                if requests.post(url,verify=False,
                    json={
                        "jsonrpc": "2.0",
                        "method": "hostgroup.massadd",
                        "params": {
                            "groups": [{"groupid": "44"}],
                            "hosts": [{"hostid": host_id}]
                        },
                        "auth": "apikey",
                        "id": 1
                    }
                ):
                    print('OK\n')
            else:
                print('ПАК уже в группе мониторинга HDD\n')
        except:
            print('-ERROR- Ты чиво наделал, верни как было')
#function to remove host from monitor group
def mon_l2_minus():
    url = "https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php"
    license_list = [y for y in (x.strip() for x in values['lic_field'].splitlines()) if y]
    for line in license_list:
        if "a270920181900-" not in line and len(line) == 5:
            api_lic = f"a270920181900-{line}"
        elif len(line) == 19:
            api_lic = f"{line}"
        else:
            print('-ACHTUNG- Допустимые форматы ввода лицензий:\n01234 (5 символов)\na270920181900-01234 (19 символов)\n')
            break
        try:
            zabbhost = requests.post(url,verify=False,
                json={
                    "jsonrpc": "2.0",
                    "method": "host.get",
                    "params": {
                        "output": ["hostid", "host"],
                        "searchWildcardsEnabled": "true",
                        "search": {"host": api_lic}
                    },
                    "auth": "apikey",
                    "id": 1
                    }
                )

            a = json.dumps(zabbhost.json(), indent=3)
            b = json.loads(a)
            host_id = (b["result"][0]["hostid"])
            print(api_lic)

            mongroup = requests.post(url,verify=False,
                json={
                    "jsonrpc": "2.0",
                    "method": "hostgroup.get",
                    "params": {
                        "output": "extend",
                        "hostids": host_id,
                        "filter": {"name": "Monitor_HDD"}
                    },
                    "auth": "apikey",
                    "id": 1
                })
            a = json.dumps(mongroup.json(), indent=3)
            b = json.loads(a)
            group_id = (b["result"])
            if group_id == []:
                print('ПАК не в группе мониторинга\n')
            else:
                print('Удаление из Monitor_HDD')
                if requests.post(url,verify=False,
                    json={
                        "jsonrpc": "2.0",
                        "method": "hostgroup.massremove",
                        "params": {
                            "groupids": ["44"],
                            "hostids": [host_id]
                        },
                        "auth": "apikey",
                        "id": 1
                    }
                ):
                    print('OK\n')
        except:
            print('-ERROR- Ты чиво наделал, верни как было')
#check connection to zabbix server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(3)
result = sock.connect_ex(('10.255.6.40',10051))
if result == 0:
    zab = 'Сервер zabbix доступен'
else:
    zab = 'Нет связи с сервером zabbix'
sock.close()

#GUI
layout = [[sg.Button('Мониторинг HDD +', size=(15), font=('Arial Black', 11))],
          [sg.Button('Мониторинг HDD -', size=(15), font=('Arial Black', 11))],
          [sg.T(f"{zab}")],
          [sg.T('Список лицензий (в столбец)')],
          [sg.Multiline('',key='lic_field', size = (35, 15),focus=True)],
          [sg.Exit('Выход')]]

window = sg.Window('Monitoring HDD v1.1', size = (300, 450)).Layout(layout)

while True:
    event, values = window.Read()
    if event in (None, 'Выход'):
        break
    if event == 'Мониторинг HDD +':
        mon_l2_plus()
    if event == 'Мониторинг HDD -':
        mon_l2_minus()
    if event == 'check':
        zabbix_check()
window.Close()
