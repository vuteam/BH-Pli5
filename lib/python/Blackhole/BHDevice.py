from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox
from Screens.Screen import Screen
from enigma import eTimer
from boxbranding import getMachineBrand, getMachineName
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config, ConfigSelection, NoSave, configfile
from Components.Console import Console
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Harddisk import Harddisk
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists, pathExists, createDir
from os import system, rename, path, mkdir, remove, listdir
from time import sleep
import re
from BhUtils import DeliteGetSkinPath

class BHDevicesPanel(Screen):
    skin = '\n\t<screen position="center,center" size="640,460">\n\t\t<ePixmap pixmap="skin_default/buttons/red.png" position="25,0" size="140,40" alphatest="on" />\n\t\t<ePixmap pixmap="skin_default/buttons/green.png" position="175,0" size="140,40" alphatest="on" />\n\t\t<ePixmap pixmap="skin_default/buttons/yellow.png" position="325,0" size="140,40" alphatest="on" />\n\t\t<ePixmap pixmap="skin_default/buttons/blue.png" position="475,0" size="140,40" alphatest="on" />\n\t\t<widget name="key_red" position="25,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />\n\t\t<widget name="key_green" position="175,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t<widget name="key_yellow" position="325,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />\n\t\t<widget name="key_blue" position="475,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />\n\t\t<widget source="list" render="Listbox" position="10,50" size="620,450" scrollbarMode="showOnDemand" >\n\t\t\t<convert type="TemplatedMultiContent">\n\t\t\t\t{"template": [\n\t\t\t\t MultiContentEntryText(pos = (90, 0), size = (600, 30), font=0, text = 0),\n\t\t\t\t MultiContentEntryText(pos = (110, 30), size = (600, 50), font=1, flags = RT_VALIGN_TOP, text = 1),\n\t\t\t\t MultiContentEntryPixmapAlphaBlend(pos = (0, 0), size = (80, 80), png = 2),\n\t\t\t\t],\n\t\t\t\t"fonts": [gFont("Regular", 24),gFont("Regular", 20)],\n\t\t\t\t"itemHeight": 85\n\t\t\t\t}\n\t\t\t</convert>\n\t\t</widget>\n\t\t<widget name="lab1" zPosition="2" position="50,90" size="600,40" font="Regular;22" halign="center" transparent="1"/>\n\t</screen>'

    def __init__(self, session):
        Screen.__init__(self, session)
        Screen.setTitle(self, _('Mount Manager'))
        self['key_red'] = Label('Initialization')
        self['key_green'] = Label(_('Setup Mounts'))
        self['key_yellow'] = Label(_('Unmount'))
        self['key_blue'] = Label(_('Mount'))
        self['lab1'] = Label()
        self.onChangedEntry = []
        self.list = []
        self['list'] = List(self.list)
        self['list'].onSelectionChanged.append(self.selectionChanged)
        self['actions'] = ActionMap(['WizardActions', 'ColorActions', 'MenuActions'], {'back': self.close,
         'green': self.SetupMounts,
         'red': self.Format,
         'yellow': self.Unmount,
         'blue': self.Mount})
        self.activityTimer = eTimer()
        self.activityTimer.timeout.get().append(self.updateList2)
        if not pathExists('/universe'):
            createDir('/universe')
        self.updateList()
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_('Black Hole Mount Manager'))

    def createSummary(self):
        return BHDevicesPanelSummary

    def selectionChanged(self):
        if len(self.list) == 0:
            return
        self.sel = self['list'].getCurrent()
        seldev = self.sel
        if self.sel:
            try:
                name = str(self.sel[0])
                desc = str(self.sel[1].replace('\t', '  '))
            except:
                name = ''
                desc = ''

        else:
            name = ''
            desc = ''
        for cb in self.onChangedEntry:
            cb(name, desc)

    def updateList(self, result = None, retval = None, extra_args = None):
        scanning = _('Wait please while scanning for devices...')
        self['lab1'].setText(scanning)
        self.activityTimer.start(10)

    def updateList2(self):
        self.activityTimer.stop()
        self.list = []
        list2 = []
        f = open('/proc/partitions', 'r')
        for line in f.readlines():
            parts = line.strip().split()
            if not parts:
                continue
            device = parts[3]
            if not re.search('sd[a-z][1-9]', device):
                continue
            if device in list2:
                continue
            self.buildMy_rec(device)
            list2.append(device)

        f.close()
        self['list'].list = self.list
        self['lab1'].hide()

    def buildMy_rec(self, device):
        mypath = DeliteGetSkinPath()
        device2 = re.sub('[0-9]', '', device)
        devicetype = path.realpath('/sys/block/' + device2 + '/device')
        d2 = device
        name = _('HARD DISK: ')
        mypixmap = mypath + 'icons/dev_hdd.png'
        model = file('/sys/block/' + device2 + '/device/model').read()
        model = str(model).replace('\n', '')
        des = ''
        if devicetype.find('usb') != -1:
            name = _('USB: ')
            mypixmap = mypath + 'icons/dev_usb.png'
        name = name + model
        self.Console = Console()
        self.Console.ePopen("sfdisk -l /dev/sd? | grep swap | awk '{print $(NF-9)}' >/tmp/devices.tmp")
        sleep(0.5)
        f = open('/tmp/devices.tmp', 'r')
        swapdevices = f.read()
        f.close()
        if path.exists('/tmp/devices.tmp'):
            remove('/tmp/devices.tmp')
        swapdevices = swapdevices.replace('\n', '')
        swapdevices = swapdevices.split('/')
        f = open('/proc/mounts', 'r')
        for line in f.readlines():
            if line.find(device) != -1:
                parts = line.strip().split()
                d1 = parts[1]
                dtype = parts[2]
                rw = parts[3]
                break
                continue
            elif device in swapdevices:
                parts = line.strip().split()
                d1 = _('None')
                dtype = 'swap'
                rw = _('None')
                break
                continue
            else:
                d1 = _('None')
                dtype = _('unavailable')
                rw = _('None')

        f.close()
        size = Harddisk(device).diskSize()
        if float(size) / 1024 / 1024 >= 1:
            des = _('Size: ') + str(round(float(size) / 1024 / 1024, 2)) + _('TB')
        elif size / 1024 >= 1:
            des = _('Size: ') + str(round(float(size) / 1024, 2)) + _('GB')
        elif size >= 1:
            des = _('Size: ') + str(size) + _('MB')
        else:
            des = _('Size: ') + _('unavailable')
        if des != '':
            if rw.startswith('rw'):
                rw = ' R/W'
            elif rw.startswith('ro'):
                rw = ' R/O'
            else:
                rw = ''
            des += '\t' + _('Mount: ') + d1 + '\n' + _('Device: ') + '/dev/' + device + '\t' + _('Type: ') + dtype + rw
            png = LoadPixmap(mypixmap)
            res = (name, des, png)
            self.list.append(res)

    def SetupMounts(self):
        self.session.openWithCallback(self.updateList, BHDevicesConf)

    def Format(self):
        from Screens.HarddiskSetup import HarddiskSelection
        self.session.openWithCallback(self.updateList, HarddiskSelection)

    def Mount(self):
        sel = self['list'].getCurrent()
        if sel:
            des = sel[1]
            des = des.replace('\n', '\t')
            parts = des.strip().split('\t')
            mountp = parts[1].replace(_('Mount: '), '')
            device = parts[2].replace(_('Device: '), '')
            system('mount ' + device)
            mountok = False
            f = open('/proc/mounts', 'r')
            for line in f.readlines():
                if line.find(device) != -1:
                    mountok = True

            f.close()
            if not mountok:
                self.session.open(MessageBox, _('Mount failed'), MessageBox.TYPE_INFO, timeout=5)
            self.updateList()

    def Unmount(self):
        sel = self['list'].getCurrent()
        if sel:
            des = sel[1]
            des = des.replace('\n', '\t')
            parts = des.strip().split('\t')
            mountp = parts[1].replace(_('Mount: '), '')
            device = parts[2].replace(_('Device: '), '')
            system('umount ' + mountp)
            try:
                mounts = open('/proc/mounts')
                mountcheck = mounts.readlines()
                mounts.close()
                for line in mountcheck:
                    parts = line.strip().split(' ')
                    if path.realpath(parts[0]).startswith(device):
                        self.session.open(MessageBox, _("Can't unmount partition, make sure it is not being used for swap or record/timeshift paths"), MessageBox.TYPE_INFO)

            except IOError:
                return -1

            self.updateList()

    def saveMypoints(self):
        sel = self['list'].getCurrent()
        if sel:
            parts = sel[1].split()
            self.device = parts[5]
            self.mountp = parts[3]
            self.Console.ePopen('umount ' + self.device)
            if self.mountp.find('/media/hdd') < 0:
                self.Console.ePopen('umount /media/hdd')
                self.Console.ePopen('/sbin/blkid | grep ' + self.device, self.add_fstab, [self.device, self.mountp])
            else:
                self.session.open(MessageBox, _('This Device is already mounted as HDD.'), MessageBox.TYPE_INFO, timeout=10, close_on_any_key=True)

    def add_fstab(self, result = None, retval = None, extra_args = None):
        self.device = extra_args[0]
        self.mountp = extra_args[1]
        self.device_uuid = 'UUID=' + result.split('UUID=')[1].split(' ')[0].replace('"', '')
        if not path.exists(self.mountp):
            mkdir(self.mountp, 493)
        file('/etc/fstab.tmp', 'w').writelines([ l for l in file('/etc/fstab').readlines() if '/media/hdd' not in l ])
        rename('/etc/fstab.tmp', '/etc/fstab')
        file('/etc/fstab.tmp', 'w').writelines([ l for l in file('/etc/fstab').readlines() if self.device not in l ])
        rename('/etc/fstab.tmp', '/etc/fstab')
        file('/etc/fstab.tmp', 'w').writelines([ l for l in file('/etc/fstab').readlines() if self.device_uuid not in l ])
        rename('/etc/fstab.tmp', '/etc/fstab')
        out = open('/etc/fstab', 'a')
        line = self.device_uuid + '\t/media/hdd\tauto\tdefaults\t0 0\n'
        out.write(line)
        out.close()
        self.Console.ePopen('mount -a', self.updateList)

    def restBo(self, answer):
        if answer is True:
            self.session.open(TryQuitMainloop, 2)
        else:
            self.updateList()
            self.selectionChanged()


class BHDevicesConf(Screen, ConfigListScreen):
    skin = '\n\t<screen position="center,center" size="640,460" title="Choose where to mount your devices to:">\n\t\t<ePixmap pixmap="skin_default/buttons/red.png" position="25,0" size="140,40" alphatest="on" />\n\t\t<ePixmap pixmap="skin_default/buttons/green.png" position="175,0" size="140,40" alphatest="on" />\n\t\t<widget name="key_red" position="25,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />\n\t\t<widget name="key_green" position="175,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t<widget name="config" position="30,60" size="580,275" scrollbarMode="showOnDemand"/>\n\t\t<widget name="Linconn" position="30,375" size="580,20" font="Regular;18" halign="center" valign="center" backgroundColor="#9f1313"/>\n\t</screen>'

    def __init__(self, session):
        Screen.__init__(self, session)
        self.list = []
        ConfigListScreen.__init__(self, self.list)
        Screen.setTitle(self, _('Choose where to mount your devices to:'))
        self['key_green'] = Label(_('Save'))
        self['key_red'] = Label(_('Cancel'))
        self['Linconn'] = Label(_('Wait please while scanning your %s %s devices...') % (getMachineBrand(), getMachineName()))
        self['actions'] = ActionMap(['WizardActions', 'ColorActions'], {'green': self.saveMypoints,
         'red': self.close,
         'back': self.close})
        self.updateList()

    def updateList(self):
        self.list = []
        list2 = []
        self.Console = Console()
        self.Console.ePopen("sfdisk -l /dev/sd? | grep swap | awk '{print $(NF-9)}' >/tmp/devices.tmp")
        sleep(0.5)
        f = open('/tmp/devices.tmp', 'r')
        swapdevices = f.read()
        f.close()
        if path.exists('/tmp/devices.tmp'):
            remove('/tmp/devices.tmp')
        swapdevices = swapdevices.replace('\n', '')
        swapdevices = swapdevices.split('/')
        f = open('/proc/partitions', 'r')
        for line in f.readlines():
            parts = line.strip().split()
            if not parts:
                continue
            device = parts[3]
            if not re.search('sd[a-z][1-9]', device):
                continue
            if device in list2:
                continue
            if device in swapdevices:
                continue
            self.buildMy_rec(device)
            list2.append(device)

        f.close()
        self['config'].list = self.list
        self['config'].l.setList(self.list)
        self['Linconn'].hide()

    def buildMy_rec(self, device):
        mypath = DeliteGetSkinPath()
        device2 = re.sub('[0-9]', '', device)
        devicetype = path.realpath('/sys/block/' + device2 + '/device')
        d2 = device
        name = _('HARD DISK: ')
        mypixmap = mypath + 'icons/dev_hdd.png'
        model = file('/sys/block/' + device2 + '/device/model').read()
        model = str(model).replace('\n', '')
        des = ''
        if devicetype.find('usb') != -1:
            name = _('USB: ')
            mypixmap = mypath + 'icons/dev_usb.png'
        name = name + model
        f = open('/proc/mounts', 'r')
        for line in f.readlines():
            if line.find(device) != -1:
                parts = line.strip().split()
                d1 = parts[1]
                dtype = parts[2]
                break
                continue
            else:
                d1 = _('None')
                dtype = _('unavailable')

        f.close()
        size = Harddisk(device).diskSize()
        if float(size) / 1024 / 1024 >= 1:
            des = _('Size: ') + str(round(float(size) / 1024 / 1024, 2)) + _('TB')
        elif size / 1024 >= 1:
            des = _('Size: ') + str(round(float(size) / 1024, 2)) + _('GB')
        elif size >= 1:
            des = _('Size: ') + str(size) + _('MB')
        else:
            des = _('Size: ') + _('unavailable')
        item = NoSave(ConfigSelection(default='/media/' + device, choices=[('/media/' + device, '/media/' + device),
         ('/universe', '/universe'),
         ('/media/hdd', '/media/hdd'),
         ('/media/usb', '/media/usb'),
         ('/media/downloads', '/media/downloads'),
         ('/media/music', '/media/music'),
         ('/media/personal', '/media/personal'),
         ('/media/video', '/media/video'),
         ('/media/photo', '/media/photo')]))
        if dtype == 'Linux':
            dtype = 'ext3'
        else:
            dtype = 'auto'
        item.value = d1.strip()
        text = name + ' ' + des + ' /dev/' + device
        res = getConfigListEntry(text, item, device, dtype)
        if des != '' and self.list.append(res):
            pass

    def saveMypoints(self):
        self.Console = Console()
        mycheck = False
        for x in self['config'].list:
            self.device = x[2]
            self.mountp = x[1].value
            self.type = x[3]
            self.Console.ePopen('umount ' + self.device)
            self.Console.ePopen('/sbin/blkid | grep ' + self.device + ' && opkg list-installed ntfs-3g', self.add_fstab, [self.device, self.mountp])

        message = _('Updating mount locations.')
        ybox = self.session.openWithCallback(self.delay, MessageBox, message, type=MessageBox.TYPE_INFO, timeout=5, enable_input=False)
        ybox.setTitle(_('Please wait.'))

    def delay(self, val):
        message = _('Changes need a system restart to take effect.\nRestart your %s %s now?') % (getMachineBrand(), getMachineName())
        ybox = self.session.openWithCallback(self.restartBox, MessageBox, message, MessageBox.TYPE_YESNO)
        ybox.setTitle(_('Restart %s %s.') % (getMachineBrand(), getMachineName()))

    def add_fstab(self, result = None, retval = None, extra_args = None):
        print '[MountManager] RESULT:', result
        if result:
            self.device = extra_args[0]
            self.mountp = extra_args[1]
            self.device_uuid = 'UUID=' + result.split('UUID=')[1].split(' ')[0].replace('"', '')
            self.device_type = result.split('TYPE=')[1].split(' ')[0].replace('"', '')
            if self.device_type.startswith('ext'):
                self.device_type = 'auto'
            elif self.device_type.startswith('ntfs') and result.find('ntfs-3g') != -1:
                self.device_type = 'ntfs-3g'
            elif self.device_type.startswith('ntfs') and result.find('ntfs-3g') == -1:
                self.device_type = 'ntfs'
            if not path.exists(self.mountp):
                mkdir(self.mountp, 493)
            file('/etc/fstab.tmp', 'w').writelines([ l for l in file('/etc/fstab').readlines() if self.device not in l ])
            rename('/etc/fstab.tmp', '/etc/fstab')
            file('/etc/fstab.tmp', 'w').writelines([ l for l in file('/etc/fstab').readlines() if self.device_uuid not in l ])
            rename('/etc/fstab.tmp', '/etc/fstab')
            out = open('/etc/fstab', 'a')
            line = self.device_uuid + '\t' + self.mountp + '\t' + self.device_type + '\tdefaults\t0 0\n'
            out.write(line)
            out.close()

    def restartBox(self, answer):
        if answer is True:
            self.session.open(TryQuitMainloop, 2)
        else:
            self.close()


class BHDevicesPanelSummary(Screen):

    def __init__(self, session, parent):
        Screen.__init__(self, session, parent=parent)
        self['entry'] = StaticText('')
        self['desc'] = StaticText('')
        self.onShow.append(self.addWatcher)
        self.onHide.append(self.removeWatcher)

    def addWatcher(self):
        self.parent.onChangedEntry.append(self.selectionChanged)
        self.parent.selectionChanged()

    def removeWatcher(self):
        self.parent.onChangedEntry.remove(self.selectionChanged)

    def selectionChanged(self, name, desc):
        self['entry'].text = name
        self['desc'].text = desc
