#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import json
import binascii
import time
import shutil
from ftplib import FTP
import subprocess

###### В переменную firmware нужно прописать версию прошивки, и залить на фтп в папку "incoming/KKT-ATOL-FW/" архивы с прошивкой
###### Имя архива должно быть в формате <версия прошивки>_<модель ккт>_<блок управления (только для 55)>.zip, например 7942_55f_5.2.zip - прошивка 7942 для 55-го атола, БУ 5.2

firmware = 7942

dir = os.path.abspath(os.curdir)
fl = os.path.basename(__file__)

#Диалог y/n
def yn_choice(message, default='n'):
    choices = 'Y/n' if default.lower() in ('y', 'yes') else 'y/N'
    choice = raw_input("%s (%s) " % (message, choices))
    values = ('y', 'yes', '') if choices == 'Y/n' else ('y', 'yes')
    return choice.strip().lower() in values

#Скачивание FWUpdater
if not os.path.isfile('/tmp/updater.zip'):
    os.system('wget ftp://user:"password"@ftp.farmaimpex.ru/incoming/KKT-ATOL-FW/updater.zip -P /tmp')
print 'Распаковка.....'
if os.path.exists('/tmp/updater'):
    shutil.rmtree('/tmp/updater')
os.system('unzip /tmp/updater.zip -d /tmp/updater')
os.system('chmod +x /tmp/updater/FWUpdaterGUI.exe')

sys.path.insert(1, '/tmp/updater')
from termcolor import colored
from libfptr10 import IFptr

#Импорт настроек из json
cassa_settings='/opt/RitfarmNG/frsettings.json'
with open(cassa_settings) as f:
    atol_settings = json.load(f)

#Путь до драйвера, подключение к ккт
LIBRARY_PATH = os.path.dirname(os.path.abspath('/opt/RitfarmNG/lib/atol/libfptr10.so'))
fptr = IFptr(os.path.join(LIBRARY_PATH, 'libfptr10.so'))
fptr.setSettings(atol_settings)
fptr.open()

#Проверка подключения
isOpened = fptr.isOpened()
if not isOpened:
    print 'Соединение:\t\tНет связи с ККТ'
    del fptr
    sys.exit()
else:
    fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
    fptr.queryData()
    model = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODEL)
    modelName = fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)
    serialNumber = fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
    print '\vСоединение:\t\tПодключено'
    print 'Модель ККТ:\t\t{}'.format(modelName.encode('utf-8'))
    print 'Серийный номер:\t\t{}'.format(serialNumber)

if model == 64:
    atolModel = ('{}_52f'.format(firmware))
elif model == 62:
    fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_UNIT_VERSION)
    fptr.setParam(IFptr.LIBFPTR_PARAM_UNIT_TYPE, IFptr.LIBFPTR_UT_CONTROL_UNIT)
    fptr.queryData()
    controlUnitVersion = fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
    print 'Блок управления:\t{}'.format(controlUnitVersion)
    atolModel = ('{}_55f'.format(firmware)+'_{}'.format(controlUnitVersion))
elif model == 69:
    atolModel = ('{}_77f'.format(firmware))

#Коды защиты 4/10
#4 (0x04)
fptr.setParam(IFptr.LIBFPTR_PARAM_TIMEOUT_ENQ, 5000)
fptr.setParam(IFptr.LIBFPTR_PARAM_COMMAND_BUFFER, [0x46, 0x0A, 0x00, 0x04, 0x01])
fptr.runCommand()
license4 = str(binascii.hexlify(bytearray(fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_ANSWER_BUFFER))))
#10 (0x0A)
fptr.setParam(IFptr.LIBFPTR_PARAM_TIMEOUT_ENQ, 5000)
fptr.setParam(IFptr.LIBFPTR_PARAM_COMMAND_BUFFER, [0x46, 0x0A, 0x00, 0x0A, 0x01])
fptr.runCommand()
license10 = str(binascii.hexlify(bytearray(fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_ANSWER_BUFFER))))

with open ('/etc/lsb-release') as file:
    plat = file.read()
    if '11.' in plat:
        print 'Код защиты 4:\t\t'+license4[4:8]+' '+license4[8:12]+' '+license4[12:16]+' '+license4[16:20]
        print 'Код защиты 10:\t\t'+license10[4:8]+' '+license10[8:12]+' '+license10[12:16]+' '+license10[16:20]
    else:
        print 'Код защиты 4:\t\t'+license4[4:20]
        print 'Код защиты 10:\t\t'+license10[4:20]

#Версия прошивки
fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_UNIT_VERSION)
fptr.setParam(IFptr.LIBFPTR_PARAM_UNIT_TYPE, IFptr.LIBFPTR_UT_CONFIGURATION)
fptr.queryData()
configurationVersion = fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
print 'Версия прошивки:\t{}'.format(configurationVersion)

#Параметры ОФД
fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_ID, 273)
fptr.readDeviceSetting()
ofd_param = fptr.getParamString(IFptr.LIBFPTR_PARAM_SETTING_VALUE)
print 'Адрес ОФД:\t\t{}'.format(ofd_param)
#
fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_ID, 274)
fptr.readDeviceSetting()
ofd_param = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SETTING_VALUE)
print 'Порт ОФД:\t\t{}'.format(ofd_param)
#
fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_ID, 275)
fptr.readDeviceSetting()
ofd_param = fptr.getParamString(IFptr.LIBFPTR_PARAM_SETTING_VALUE)
print 'DNS ОФД:\t\t{}'.format(ofd_param)

#Не отправлено чеков
fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_OFD_EXCHANGE_STATUS)
fptr.fnQueryData()
unsentCount = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENTS_COUNT)
if unsentCount > 0:
    colorc = ('red')
else:
    colorc = ('green')
print ('Не отправлено чеков:')+colored('\t{}'.format(unsentCount), colorc)
colorc = ('magenta')

#Состояние смены
fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
fptr.queryData()
shiftState = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)

if shiftState == 0:
    shiftText = ('(Закрыта)')
    colorc = ('green')
if shiftState == 1:
    shiftText = ('(Открыта)')
    colorc = ('red')
if shiftState == 2:
    shiftText = ('(Истекла)')
    colorc = ('red')
print ('Состояние смены:')+colored('\t{}'.format(shiftState), colorc)+colored('{}'.format(shiftText), colorc)
colorc = ('magenta')

#Канал обмена
fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_ID, 239)
fptr.readDeviceSetting()
port = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SETTING_VALUE)
comNum = fptr.getSingleSetting(IFptr.LIBFPTR_SETTING_COM_FILE)

if port == 4:
    colorc = ('red')
    print ('Канал обмена:')+colored('\t\tUSB', colorc)
if port == 0:
    colorc = ('green')
    print ('Канал обмена:')+colored('\t\tCOM{}'.format(comNum), colorc)
colorc = ('magenta')

#Блокировка
fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
fptr.queryData()
isDeviceBlocked = fptr.getParamBool(IFptr.LIBFPTR_PARAM_BLOCKED)
if not isDeviceBlocked:
    colorc = ('green')
if isDeviceBlocked:
    colorc = ('red')
print ('ККТ заблокирована:')+colored('\t{}'.format(isDeviceBlocked), colorc)
colorc = ('magenta')

#Запись в файл
with open('/tmp/kkt_info.txt', 'w') as f:
    f.write('Модель ККТ:\t\t{}\n'.format(modelName.encode('utf-8')))
    f.write('Серийный номер:\t\t{}\n'.format(serialNumber))
    f.write('Код защиты 4:\t\t{}\n'.format(license4[4:20]))
    f.write('Код защиты 10:\t\t{}\n'.format(license10[4:20]))

print '\vКоды защиты/серийник записаны в /tmp/kkt_info.txt'
time.sleep(1)

#Докачивание прошивки
if not os.path.isfile('/tmp/{}.zip'.format(atolModel.encode('utf-8'))):
    print '\vСкачивание прошивки.....'
    ftp = FTP('ftp.farmaimpex.ru', 'support', 'fdnj,ec')
    ftp.cwd('incoming/KKT-ATOL-FW')
    out =('/tmp/{}.zip'.format(atolModel))
    with open (out, 'wb') as f:
        ftp.retrbinary('RETR ' + '{}.zip'.format(atolModel), f.write)
    ftp.quit()
print 'Распаковка прошивки.....'
os.system('unzip /tmp/{}.zip -d /tmp/updater'.format(atolModel))

fptr.close()
if yn_choice('Открыть драйвер?'):
    os.system('/opt/RitfarmNG/lib/atol/./fptr10_t.sh')

print 'Запускаем прошивку.....'
fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_ID, 239)
fptr.readDeviceSetting()
comNum = fptr.getSingleSetting(IFptr.LIBFPTR_SETTING_COM_FILE)
comNum = int(comNum)
comNum = comNum + 1
with open('/tmp/updater/settings.json', 'r') as f:
    old_data = f.read()
new_data = old_data.replace('\"number\" : 1', '\"number\" : {}'.format(comNum))
with open('/tmp/updater/settings.json', 'w') as f:
    f.write(new_data)
os.chdir('/tmp/updater')
os.system('./FWUpdaterGUI.exe')

fptr.open()

fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
fptr.queryData()
serialNumber = fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
print '\vСерийный номер:\t\t{}'.format(serialNumber)

#Коды защиты 4/10
#4 (0x04)
fptr.setParam(IFptr.LIBFPTR_PARAM_TIMEOUT_ENQ, 5000)
fptr.setParam(IFptr.LIBFPTR_PARAM_COMMAND_BUFFER, [0x46, 0x0A, 0x00, 0x04, 0x01])
fptr.runCommand()
license4 = str(binascii.hexlify(bytearray(fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_ANSWER_BUFFER))))
#10 (0x0A)
fptr.setParam(IFptr.LIBFPTR_PARAM_TIMEOUT_ENQ, 5000)
fptr.setParam(IFptr.LIBFPTR_PARAM_COMMAND_BUFFER, [0x46, 0x0A, 0x00, 0x0A, 0x01])
fptr.runCommand()
license10 = str(binascii.hexlify(bytearray(fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_ANSWER_BUFFER))))

with open ('/etc/lsb-release') as file:
    plat = file.read()
    if '11.' in plat:
        print 'Код защиты 4:\t\t'+license4[4:8]+' '+license4[8:12]+' '+license4[12:16]+' '+license4[16:20]
        print 'Код защиты 10:\t\t'+license10[4:8]+' '+license10[8:12]+' '+license10[12:16]+' '+license10[16:20]
    else:
        print 'Код защиты 4:\t\t'+license4[4:20]
        print 'Код защиты 10:\t\t'+license10[4:20]

#Версия прошивки
fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_UNIT_VERSION)
fptr.setParam(IFptr.LIBFPTR_PARAM_UNIT_TYPE, IFptr.LIBFPTR_UT_CONFIGURATION)
fptr.queryData()
configurationVersion = fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
print 'Версия прошивки:\t{}'.format(configurationVersion)

#Параметры ОФД
fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_ID, 273)
fptr.readDeviceSetting()
ofd_param = fptr.getParamString(IFptr.LIBFPTR_PARAM_SETTING_VALUE)
print 'Адрес ОФД:\t\t{}'.format(ofd_param)
#
fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_ID, 274)
fptr.readDeviceSetting()
ofd_param = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SETTING_VALUE)
print 'Порт ОФД:\t\t{}'.format(ofd_param)
#
fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_ID, 275)
fptr.readDeviceSetting()
ofd_param = fptr.getParamString(IFptr.LIBFPTR_PARAM_SETTING_VALUE)
print 'DNS ОФД:\t\t{}'.format(ofd_param)

#Блокировка
fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
fptr.queryData()
isDeviceBlocked = fptr.getParamBool(IFptr.LIBFPTR_PARAM_BLOCKED)
if not isDeviceBlocked:
    colorc = ('green')
if isDeviceBlocked:
    colorc = ('red')
print ('ККТ заблокирована:')+colored('\t{}'.format(isDeviceBlocked), colorc)
colorc = ('magenta')

fptr.close()
if yn_choice('\vОткрыть драйвер?'):
    os.system('/opt/RitfarmNG/lib/atol/./fptr10_t.sh')

if yn_choice('Удалить файлы?', 'y'):
    if os.path.exists('/tmp/updater.zip'):
        os.remove('/tmp/updater.zip')
    if os.path.exists('/tmp/{}.zip'.format(atolModel)):
        os.remove('/tmp/{}.zip'.format(atolModel))
    if os.path.exists('/tmp/updater'):
        shutil.rmtree('/tmp/updater')
    os.remove ('{}/'.format(dir) + '{}'.format(fl))
