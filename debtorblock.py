import PySimpleGUI as sg
import sys
import os
import requests
import json
import urllib3
from pyzabbix import ZabbixAPI

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#remove zenity banner
def Unblock():
    print('Unblock:')
    url = "https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php"
    license_list = [y for y in (x.strip() for x in values['lic_field'].splitlines()) if y]
    for line in license_list:
        api_lic = f"a270920181900-{line}"
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
        print(host_id)
        item_key = ("system.run[sudo /etc/zabbix/zabbix_agentd.d/zabbix_custom.sh -H unblock]")
        zabbinfo = requests.post(url,verify=False,
            json={
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": "itemid",
                "hostids": host_id,
                "search": {"name": "Блокировка ПАКа"},
            },
            "auth": "apikey",
            "id": 1
        })
        a = json.dumps(zabbinfo.json(), indent=3)
        b = json.loads(a)
        item_id = (b["result"][0]["itemid"])

        requests.post(url,verify=False,
            json={
                "jsonrpc": "2.0",
                "method": "item.delete",
                "params": [item_id],
                "auth": "apikey",
                "id": 1
            }
        )

        requests.post(url,verify=False,
            json={
                "jsonrpc": "2.0",
                "method": "hostgroup.massremove",
                "params": {
                    "groupids": ["58"],
                    "hostids": [host_id]
                },
                "auth": "abc",
                "id": 1
            }
        )
        #Проверка находится ли хост в группе МТА
        mta = requests.post(url,verify=False,
            json={
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": "extend",
                "hostids": ['"$line"']
            },
            "auth": "abc",
            "id": 1
        })
        print(mta)
#add zenity banner
def Block():
    print('Block:')
    url = "https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php"
    license_list = [y for y in (x.strip() for x in values['lic_field'].splitlines()) if y]
    for line in license_list:
        api_lic = f"a270920181900-{line}"
        zabbinfo = requests.post(url,verify=False,
            json={
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                    "output": ["hostid", "host"],
                    "searchWildcardsEnabled": "true",
                    "search": {"host": api_lic}
                },
                "auth": "abc",
                "id": 1
            })
        a = json.dumps(zabbinfo.json(), indent=3)
        b = json.loads(a)
        host_id = (b["result"][0]["hostid"])
        print(host_id)
        #with open('temp.txt', 'a') as f:
            #f.write(b["result"][0]["hostid"]+"\n")
        item_key = ("system.run[sudo /etc/zabbix/zabbix_agentd.d/zabbix_custom.sh -H "+values['date_field'] +"]")
        requests.post(url,verify=False,
            json={
                "jsonrpc": "2.0",
                "method": "item.create",
                "params": {
                    "name": "Блокировка ПАКа",
                    "key_": item_key,
                    "hostid": host_id,
                    "type": 7,
                    "value_type": 4,
                    "delay": "5m",
                    "history": "0",
                    "trends": "0"
                },
                "auth": "apikey",
                "id": 1
            }
        )

        requests.post(url,verify=False,
            json={
                "jsonrpc": "2.0",
                "method": "host.massupdate",
                "params": {
                    "hosts": [{"hostid": host_id}],
                    "templates_clear": [{"templateid": "23426"}]
                },
                "auth": "abc",
                "id": 1
            }
        )

        requests.post(url,verify=False,
            json={
                "jsonrpc": "2.0",
                "method": "hostgroup.massadd",
                "params": {
                    "groups": [{"groupid": "58"}],
                    "hosts": [{"hostid": host_id}]
                },
                "auth": "abc",
                "id": 1
            }
        )
        
#GUI
layout = [[sg.T('Дата блокировки\n')],
          [sg.In(key='date_field', size=(31,10))],
          [sg.CalendarButton('Выбор даты', target='date_field', key='calendar', format = "%Y%m%d")],
          [sg.Button('Заблокировать'),sg.Button('Разблокировать')],
          [sg.Multiline('02680',key='lic_field', size = (28, 20),focus=True)],
          [sg.Exit('Выход')],]

window = sg.Window('GiveMoney v1.0', size = (300, 550)).Layout(layout)

while True:
    event, values = window.Read()
    if event in (None, 'Выход'):
        break
    if event == 'Заблокировать':
        Block()
    elif event == 'Разблокировать':
        Unblock()
window.Close()
