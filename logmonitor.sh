#!/bin/bash
LOGSOURCE=/opt/pp-terminal/log/local_api_stdout.txt
LOGFILE=/etc/zabbix/zabbix_agentd.d/errlog.txt
LINE1="[HttpClient]"
LINE2="[DeviceGateway]"
LINE3="Delay on page"
A=0
#Проверка какой девайс подключен в системе
ALK="dingo_e200"

if [ $(lsusb | grep -c '10c4:8105') -eq 1 ]; then
    PIR="rycomm_jxb183"
elif [ $(lsusb | grep -c '10c4:ea60') -eq 1 ]; then
    PIR="berrcom_jxb183"
fi

if [ $(lsusb | grep -c '04d9:b554') -eq 1 ]; then
    TON="microlife_wbp"
elif [ $(lsusb | grep -c '1a86:7523') -eq 1 ]; then
    TON="ld7"
elif [ $(lsusb | grep -c '0590:0028') -eq 1 ]; then
    TON="omron"
fi

#Если файла логов нет - создать
if [ ! -f $LOGFILE ]; then
    echo -n >> $LOGFILE
fi
truncate -s 0 $LOGFILE
tail -F $LOGSOURCE >> $LOGFILE &
while true 
do
    if [ $A -eq 1 ]; then
    tail -F $LOGFILE | egrep --line-buffered "$LINE1.*Received error with status code 504" | while read line ; 
        do if [[ $line == *"Received error with status code 504"* ]]; then
            zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -s "$(hostname)" -k sender3.err -o ERRLOG504
            truncate -s 0 $LOGFILE
        fi
        done &
    tail -F $LOGFILE | egrep --line-buffered "$LINE1.*Received error with status code 503" | while read line ; 
        do if [[ $line == *"Received error with status code 503"* ]]; then
            zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -s "$(hostname)" -k sender3.err -o ERRLOG503
            truncate -s 0 $LOGFILE
        fi
        done &
    tail -F $LOGFILE | egrep --line-buffered "$LINE2.*Couldn't start driver.*$ALK.*not found" | while read line ; 
        do if [[ $line == *"$ALK"* ]]; then
            zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -s "$(hostname)" -k sender3.err -o ERRLOGALK
            truncate -s 0 $LOGFILE
        fi
        done &
    tail -F $LOGFILE | egrep --line-buffered "$LINE2.*Couldn't start driver.*$TON.*not found" | while read line ; 
        do if [[ $line == *"$TON"* ]]; then
            zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -s "$(hostname)" -k sender3.err -o ERRLOGTON
            truncate -s 0 $LOGFILE
        fi
        done &
    tail -F $LOGFILE | egrep --line-buffered "$LINE2.*Couldn't start driver.*$PIR.*not found" | while read line ; 
        do if [[ $line == *"$PIR"* ]]; then
            zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -s "$(hostname)" -k sender3.err -o ERRLOGPIR
            truncate -s 0 $LOGFILE
        fi
        done &
    tail -F $LOGFILE | egrep --line-buffered "$LINE3.*/inspection" | while read line ; 
        do if [[ $line == *"$LINE3"* ]]; then
            zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -s "$(hostname)" -k sender3.err -o ERRLOGDEL
            truncate -s 0 $LOGFILE
        fi
        done
    fi
    A=1
done

