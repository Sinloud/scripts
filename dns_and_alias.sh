#!/bin/bash
#Скрипт установки отображаемого имени хоста в соответствии с инвентарным полем, установка типа подключения на DNS, удаление не основных интерфейсов
function get_real_info {
    APIRAW=$(curl -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
    {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["host", "hostid", "name"],
            "searchWildcardsEnabled": "true",
            "selectInventory": ["alias"],
            "filter": {
                "status": "0"
            },
            "search": {
                "host": "a270920181900-*"
            }
        },
        "auth": "apikey",
        "id": 1
    }' | jq -r '.result[]')

    APIALIAS=$(echo "$APIRAW" | jq -r 'select((.inventory.alias != "") and (.inventory.alias != "n\\a") and (.inventory.alias | contains("администратор") | not) and (.inventory.alias | contains("Administrator") | not)) | .host, .hostid, .inventory.alias')

    HOSTS=$(curl -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
    {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["host", "hostid"],
            "searchWildcardsEnabled": "true",
            "filter": {
                "status": "0"
            },
            "search": {
                "host": "a270920181900-*"
            }
        },
        "auth": "apikey",
        "id": 1
    }' | jq -r '.result[] | .host, .hostid')
    
    echo "$APIALIAS" > /tmp/alias
    echo "$HOSTS" > /tmp/hosts
    sed -i 's/"//g' /tmp/alias
    sed -i 's/\\//g' /tmp/alias
    APIALIAS=$(cat /tmp/alias)
    HOSTS=$(cat /tmp/hosts)
}

function get_test_info {
    APIALIAS=$(cat /tmp/alias_test)
    HOSTS=$(cat /tmp/hosts_test)
}

function setalias {
    LIM=$(echo "$APIALIAS" | wc -l)
    COUNTER=1
    while [ $COUNTER -le $LIM ]; do
        HOSTID=$(sed -n "$(($COUNTER+1))"p /tmp/alias)
        ALIAS=$(sed -n "$((COUNTER)) s/^.\{14\}\(.....\).*/\1/p" /tmp/alias)" | "$(sed -n "$(($COUNTER+2))"p /tmp/alias)
        echo -e "\nХост: $HOSTID | Название: $ALIAS"
        curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
        {
            "jsonrpc": "2.0",
            "method": "host.update",
            "params": {
                "hostid": "'$HOSTID'",
                "name": "'"$ALIAS"'"
            },
            "auth": "apikey",
            "id": 1
        }'
        ((COUNTER=COUNTER+3))
    done < <(printf '%s\n' "$APIALIAS")
}

function setdns {
    LIM=$(echo "$HOSTS" | wc -l)
    COUNTER=1
    while [ $COUNTER -le $LIM ]; do
        DNS=$(sed -n "$COUNTER"p /tmp/hosts | cut -c15-)
        HOSTID=$(sed -n "$((COUNTER+1))"p /tmp/hosts)
        INTERFACE=$(curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
        {
            "jsonrpc": "2.0",
            "method": "hostinterface.get",
            "params": {
                "output": ["interfaceid", "main"],
                "hostids": "'$HOSTID'"
            },
            "auth": "apikey",
            "id": 1
        }' | jq -r '.result[] | select(.main == "1") | .interfaceid')

        echo -e "\nХост: $HOSTID | DNS: $DNS.terminal.medpoint24.lo"
        curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
        {
            "jsonrpc": "2.0",
            "method": "hostinterface.update",
            "params": {
                "interfaceid": "'$INTERFACE'",
                "dns": "'$DNS'.terminal.medpoint24.lo",
                "useip": 0
            },
            "auth": "apikey",
            "id": 1
        }'
        ((COUNTER=COUNTER+2))
    done < <(printf '%s\n' "$HOSTS")
}

function remove_non_default_interfaces {
    INTERFACES_ND=$(curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
        {
            "jsonrpc": "2.0",
            "method": "hostinterface.get",
            "params": {
                "output": ["interfaceid", "main"]
            },
            "auth": "apikey",
            "id": 1
        }' | jq -r '.result[] | select(.main == "0") | .interfaceid')

    while read -r line; do
        curl -s -k -X POST -H "Content-Type: application/json-rpc" https://zabbix.terminal.infra.medpoint24.lo/api_jsonrpc.php -d '
            {
                "jsonrpc": "2.0",
                "method": "hostinterface.delete",
                "params": [
                    "'$line'"
                ],
                "auth": "apikey",
                "id": 1
            }'
    done < <(printf '%s\n' "$INTERFACES_ND")
}

function clean_this_mess {
    /bin/rm -f /tmp/alias /tmp/hosts
}

FixInterfacesPhantomErrors() {
    export PGPASSWORD=pass
    InterfaceIDs=$(/bin/psql -h distmed.com -p 5432 -U zabbix -d zabbix -t -A -c "
        select interface.interfaceid
        from interface
        where interface.error != ''
        and interface.errors_from = 0
        and interface.available = 1
    " 2>/dev/null)
    if [ -n "$InterfaceIDs" ]; then
        echo "$InterfaceIDs"
        for id in $InterfaceIDs; do
          InterfaceID+="$id,"
        done
        InterfaceID=${InterfaceID%,}

        /bin/psql -h distmed.com -p 5432 -U zabbix -d zabbix -t -A -c "
            update interface set error = '' where interfaceid in ("$InterfaceID")
        " 2>/dev/null
    fi
}

#get_test_info
clean_this_mess
get_real_info
setalias
setdns
remove_non_default_interfaces
FixInterfacesPhantomErrors
clean_this_mess
