#!/bin/bash
LOC=$(pwd)
wget ftp://user:"password"@ftp.farmaimpex.ru/incoming/KKT-ATOL-FW/7942_77f.zip -P /tmp
unzip /tmp/7942_77f.zip -d /tmp
chmod +x /tmp/7942_77f/FWUpdaterGUI.exe
/opt/RitfarmNG/lib/atol/./fptr10_t.sh
#grep -o "Com[^,]\+" /opt/RitfarmNG/frsettings.json
#sleep 2
TEMP=$(sed '7q;d' /opt/RitfarmNG/frsettings.json)
PORT=${TEMP:16:1}
let "PORT += 1"
sed -i 's@"number" : 1@"number" : '"$PORT@"'' /tmp/7942_77f/settings.json
cd /tmp/7942_77f/
./FWUpdaterGUI.exe
/opt/RitfarmNG/lib/atol/./fptr10_t.sh
while true; do
    read -p "Delete files?(y/n) " yn
    case $yn in
        [Yy]* ) rm -f /tmp/7942_77f.zip rm -R /tmp/7942_77f/; break;;
        [Nn]* ) exit;;
        * ) echo "Please type 'y' or 'n' ";;
    esac
done
cd $LOC
rm -f fw77.sh
