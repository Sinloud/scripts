#!/bin/bash
#Скрипт обновления статусов ПАК в заббиксе в соответствии с itsm
function auth {
    curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
    {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": "user",
            "password": "pass"
        },
        "id": 1,
        "auth": null
    }' | jq '.result'
}
#Auth=$(auth)

function clean_this_mess {
    /bin/rm -f /tmp/to_activate /tmp/to_disable /tmp/activate /tmp/disable /tmp/notdemont /tmp/demont
}

function update_hosts {
    echo "Обновление статуса узлов на zabbix..."
    if [ -f /tmp/disable ]; then
        while IFS= read -r line; do
            curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
            {
                "jsonrpc": "2.0",
                "method": "host.update",
                "params": {
                    "hostid": '$line',
                    "status": 1
                },
                "auth": "apikey",
                "id": 2
            }'
        done < /tmp/disable
    fi

    if [ -f /tmp/activate ]; then
        while IFS= read -r line; do
            HostDescription=$(
                curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
                {
                    "jsonrpc": "2.0",
                    "method": "host.get",
                    "params": {
                        "output": ["hostid", "description"],
                        "hostids": '$line'
                    },
                    "auth": "apikey",
                    "id": 5
                }' | jq '.result[].description'
            )
            HostDescription="${HostDescription%\"}\\r\\nДата введения в эксплуатацию $(date +%Y-%m-%d)\""
            curl -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.massadd",
                "params": {
                    "groups": [
                        {
                            "groupid": "67"
                        }
                    ],
                    "hosts": [
                        {
                            "hostid": '$line'
                        }
                    ]
                },
                "auth": "apikey",
                "id": 4
            }'
            curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
            {
                "jsonrpc": "2.0",
                "method": "host.update",
                "params": {
                    "hostid": '$line',                    
                    "description": '"$HostDescription"',
                    "status": 0
                },
                "auth": "apikey",
                "id": 3
            }'
        done < /tmp/activate
    fi
}

function get_itsm_statuses_old {
    echo "Получение списка ПАКов от itsm..."
    ITSM="$(curl -s -X POST 'https://arcius.itsm365.com/sd/services/rest/find/cmdbmain$komplekt?attrs=kompID,state,removed,UUID&accessKey=key')"
    echo "$ITSM" | jq -r '.[] | select((.state != "demont") and (.kompID != null) and (.removed == false) and (.kompID | contains ("270920181900-"))) | .kompID' > /tmp/notdemont
    echo "$ITSM" | jq -r '.[] | select((.state == "demont") and (.kompID != null) and (.removed == false) and (.kompID | contains ("270920181900-"))) | .kompID' > /tmp/demont
    ITSM2="$(curl -s -X POST 'https://arcius.itsm365.com/sd/services/rest/find/cmdbmain$komplekt?attrs=kompID,state,removed,UUID&accessKey=key&offset=5000')"
    echo "$ITSM2" | jq -r '.[] | select((.state != "demont") and (.kompID != null) and (.removed == false) and (.kompID | contains ("270920181900-"))) | .kompID' >> /tmp/notdemont
    echo "$ITSM2" | jq -r '.[] | select((.state == "demont") and (.kompID != null) and (.removed == false) and (.kompID | contains ("270920181900-"))) | .kompID' >> /tmp/demont
    ITSMA="$(cat /tmp/notdemont)"
    ITSMD="$(cat /tmp/demont)"
}

GetItsmStatuses() {
    echo "Получение списка ПАКов от itsm..."
    ITSM="$(curl -s -X POST 'https://arcius.itsm365.com/sd/services/rest/find/cmdbmain$komplekt?attrs=kompID,state,removed,kompLastState&accessKey=key')"
    echo "$ITSM" | jq -r '.[] | select((.removed == false) and (.state != "demont") and (.kompLastState.code == "1" or .kompLastState.code == "2" or .kompLastState.code == "3" or .kompLastState.code == "5") and (.kompID != null) and (.kompID | startswith("A270920181900-"))) | .kompID' > /tmp/notdemont
    echo "$ITSM" | jq -r '.[] | select((.removed == false) and (.state == "demont" or .kompLastState.code == "4") and (.kompID != null) and (.kompID | startswith("A270920181900-"))) | .kompID' > /tmp/demont
    ITSM2="$(curl -s -X POST 'https://arcius.itsm365.com/sd/services/rest/find/cmdbmain$komplekt?attrs=kompID,state,removed,kompLastState&accessKey=key&offset=5000')"
    echo "$ITSM2" | jq -r '.[] | select((.removed == false) and (.state != "demont") and (.kompLastState.code == "1" or .kompLastState.code == "2" or .kompLastState.code == "3" or .kompLastState.code == "5") and (.kompID != null) and (.kompID | startswith("A270920181900-"))) | .kompID' >> /tmp/notdemont
    echo "$ITSM2" | jq -r '.[] | select((.removed == false) and (.state == "demont" or .kompLastState.code == "4") and (.kompID != null) and (.kompID | startswith("A270920181900-"))) | .kompID' >> /tmp/demont
    ITSMA="$(cat /tmp/notdemont)"
    ITSMD="$(cat /tmp/demont)"
}

GetZabbixStatuses() {
    echo "Получение списка ПАКов от zabbix..."
    ZABB=$(curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
    {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host", "status"],
            "searchWildcardsEnabled": "true",
            "search": {
                "host": ["a270920181900*"]
            }
        },
        "auth": "apikey",
        "id": 7
    }')
    ZABBA=$(echo $ZABB | jq -r '.result[] | select(.status == "0") | .host')
    ZABBD=$(echo $ZABB | jq -r '.result[] | select(.status == "1") | .host')
}

function to_activate {
    echo "Поиск ПАКов на активацию..."
    while read -r line; do
        echo "$ZABBD" | grep -i "$line" >> /tmp/to_activate
    done < <(printf '%s\n' "$ITSMA")
}

function to_disable {
    echo "Поиск ПАКов на деактивацию..."
    while read -r line; do
        echo "$ZABBA" | grep -i "$line" >> /tmp/to_disable
    done < <(printf '%s\n' "$ITSMD")
}

function activate {
    COUNTA=0
    #ограничить количество активируемых паков максимумом в 100
    #sed -i '101,$d' /tmp/to_activate
    while IFS= read -r line; do
        echo "$ZABB" | jq '.result[] | select(.host == "'$line'") | .hostid' >> /tmp/activate
        ((COUNTA++))
    done < /tmp/to_activate
}

function disable {
    COUNTD=0
    while IFS= read -r line; do
        echo "$ZABB" | jq '.result[] | select(.host == "'$line'") | .hostid' >> /tmp/disable
        ((COUNTD++))
    done < /tmp/to_disable
}

DisablePacsToDemont() {
    ToDemont=$(curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
            {
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                    "output": ["hostid", "status"],
                    "searchWildcardsEnabled": "true",
                    "groupids": 65,
                    "search": {
                        "host": ["a270920181900*"]
                    }
                },
                "auth": "apikey",
                "id": 8
            }' | jq '.result[].hostid')
    ActivateFile="/tmp/activate"
    while IFS= read -r line; do
        if grep -Fxq "$line" "$ActivateFile"; then
            sed -i "/$line/d" "$ActivateFile"
            ((COUNTA--))
        fi
    done <<< "$ToDemont"
}

clean_this_mess
GetItsmStatuses
GetZabbixStatuses
to_activate
to_disable
activate
disable
DisablePacsToDemont
update_hosts
clean_this_mess

echo -e "\nАктивировано ПАКов: $COUNTA\nДеактивировано ПАКов: $COUNTD"