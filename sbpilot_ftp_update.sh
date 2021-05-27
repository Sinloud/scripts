wget ftp://support:"user"@ftp.farmaimpex.ru/incoming/sbpilot_current/* -P /tmp/sb29
mv /opt/RitfarmNG/sb /opt/RitfarmNG/sb_old
mv /tmp/sb29 /opt/RitfarmNG/sb
cp /opt/RitfarmNG/sb_old/pinpad.ini /opt/RitfarmNG/sb/pinpad.ini
[[ -e /opt/RitfarmNG/sb_old/ttyS99 ]] && cp -a /opt/RitfarmNG/sb_old/ttyS99 /opt/RitfarmNG/sb && echo "terminal=USB" || echo "terminal=COM"
chown user.user -R /opt/RitfarmNG/sb
chmod +x /opt/RitfarmNG/sb/sb_pilot
chmod +x /opt/RitfarmNG/sb/posScheduler
rm -f sbpilot29.sh
