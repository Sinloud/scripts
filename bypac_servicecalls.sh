#!/bin/bash
#Скрипт формирования отчета по клиентской обращаемости
export PGPASSWORD=pass
DateStart=$(date -d 'today - 7 days 00:00:00' +%Y-%m-%d)
DateEnd=$(date -d 'today - 1 day 00:00:00' +%Y-%m-%d)
Week="W$(date -d '1 week ago' +%V)"

psql -h distmed.com -p 5432 -U user -d medist -c "SELECT
  pool.started_at,
  hosts.license
FROM
  processing.inspections_pool_resolved pool
  LEFT JOIN structures.hosts ON structures.hosts.id = pool.host_id
WHERE
  structures.hosts.is_active = true
  AND structures.hosts.license ILIKE 'A270920181900%'
  AND pool.started_at BETWEEN ('$DateStart 00:00:00.000') AND ('$DateEnd 23:59:59.000');" -F "," -A > /tmp/bypac_distmed_raw.csv
sed -i '/rows)/d' /tmp/bypac_distmed_raw.csv
awk -F ',' 'NR==1 {next} {license_count[$2]++} END {print "license,count"; for (license in license_count) print license "," license_count[license] | "sort -t, -k2nr"}' /tmp/bypac_distmed_raw.csv > /tmp/bypac_inspections.csv
curl -s "https://arcius.itsm365.com/sd/services/rest/exec?func=modules.custRest.getServiceCalls&params=%22${DateStart}%22,%22${DateEnd}%22&accessKey=key" > /tmp/bypac_servicecalls_itsm.json
jq -r 'map(select((.subject | startswith("ZABBIX: ") | not) and (.subject | contains("[MASSMAIL]") | not) and (.compleksId != "") and (.scSection != "") and (.scSection | contains("Нарушение работы ПАКа")) or (.service | contains("Нарушения в работе комплекса")))) | [.[] | {compleksId, subject, service, scSection}] | (.[0] | keys_unsorted) as $keys | map([.[ $keys[] ]])[] | @csv' /tmp/bypac_servicecalls_itsm.json > /tmp/bypac_servicecalls_itsm.csv
awk -F',' 'BEGIN { print "license,count_itsm" } { count[$1]++ } END { for (key in count) print key "," count[key] }' /tmp/bypac_servicecalls_itsm.csv > /tmp/bypac_servicecalls_itsm_count.csv
awk -F',' 'BEGIN { print "license,count_itsm" } { gsub(/"/, "", $1); count[$1]++ } END { for (key in count) print key "," count[key] }' /tmp/bypac_servicecalls_itsm.csv > /tmp/bypac_servicecalls_itsm_count.csv
awk -F, 'BEGIN{OFS=","} NR==FNR{if(NR>1) a[$1]=$2; next} FNR==1{print $0,"count_itsm"; next} {count=(($1 in a)?a[$1]:0); print $0,count}' /tmp/bypac_servicecalls_itsm_count.csv /tmp/bypac_inspections.csv > /tmp/bypac_callings_initial.csv
ItsmList=$(tail -n +2 /tmp/bypac_servicecalls_itsm_count.csv)
while IFS=',' read -r Lic ItsmCount; do
    if [ $(grep -c $Lic /tmp/bypac_callings_initial.csv) -eq 0 ]; then
        echo $Lic,0,$ItsmCount >> /tmp/bypac_callings_initial.csv
    fi
done <<< "$ItsmList"
#awk -F',' 'BEGIN {OFS=","} NR==1 {print $0, "result"; next} {result = sprintf("%.2f", $3 / $2 * 100); print $0, result}' /tmp/bypac_callings_initial.csv > /tmp/bypac_callings_result.csv
awk -F',' 'BEGIN {OFS=","} NR==1 {print $0, "result"; next} { if ($2 != 0) result = sprintf("%.2f", $3 / $2 * 100); else result = "N/A"; print $0, result}' /tmp/bypac_callings_initial.csv > /tmp/bypac_callings_result.csv
sed -i '1s/.*/Лицензия,Осмотры,Обращения,Обращаемость %/' /tmp/bypac_callings_result.csv
InspectionsCount=$(awk -F ',' 'NR>1 {sum += $2} END {print sum}' /tmp/bypac_callings_result.csv)
ServiceCallsCount=$(awk -F ',' 'NR>1 {sum += $3} END {print sum}' /tmp/bypac_callings_result.csv)
Callings=$(awk -v sc="$ServiceCallsCount" -v ic="$InspectionsCount" 'BEGIN {result = (sc / ic) * 100; printf "%.2f", result}')
echo "Всего,$InspectionsCount,$ServiceCallsCount,$Callings" >> /tmp/bypac_callings_result.csv
libreoffice --headless --convert-to xlsx --infilter="CSV:44,34,UTF8" --outdir /tmp /tmp/bypac_callings_result.csv

(cat <<EOF
From: zabbix@distmed.com
To: p.shilyaev@medpoint24.ru
Subject: Обращаемость по ПАК с $DateStart по $DateEnd
Content-Type: multipart/mixed; boundary="boundarystring"

--boundarystring
Content-Type: text/plain; charset=UTF-8

Это автоматическое сообщение, пожалуйста не отвечайте на него.

--boundarystring
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; name="=?UTF-8?B?$(echo -n "Обращаемость по ПАК $Week.xlsx" | base64)?="
Content-Disposition: attachment; filename="=?UTF-8?B?$(echo -n "Обращаемость по ПАК $Week.xlsx" | base64)?="
Content-Transfer-Encoding: base64

$(base64 /tmp/bypac_callings_result.xlsx | sed 's/\r$//')

--boundarystring--
EOF
) | msmtp --read-recipients

/bin/rm -f /tmp/bypac_*