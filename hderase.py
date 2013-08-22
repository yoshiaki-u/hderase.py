#
import subprocess,re,glob

CMD_HDPARM 	= '/sbin/hdparm'
P_FROZEN	= 'frozen'
P_NOT		= 'not'
P_SUPPORTED	= 'supported:'
P_ENHANCED	= 'enhanced erase'
SYS_WAKETIMER	= '/sys/class/rtc/rtc0/wakealarm'
CMD_SUSPEND	= '/usr/sbin/pm-suspend'
PASSWORD	= 'NULL'
TMP_ERASE       = [CMD_HDPARM, "--security-erase", PASSWORD] 
TMP_EH_ERASE    = [CMD_HDPARM, "--security-erase-enhanced", PASSWORD] 

def get_hdinfo(drv):
    info = subprocess.check_output([CMD_HDPARM, "-I", drv])
    return info.split("\n")

def set_security_password(drv):
    info = subprocess.check_output([CMD_HDPARM, "--security-set-pass", PASSWORD, drv])
    return info.split("\n")

def print_secsec(info_lines):
    frozenp = False
    secp = False

    security_secbegin_p = re.compile("Security:")
    security_sec_p = re.compile("^\S")
    security_frozen_p = re.compile(P_FROZEN)
    security_not_p = re.compile(P_NOT)

    for parm in info_lines:
        if re.match(security_secbegin_p, parm):
            secp = True
            print parm
            continue
        if secp == True :
            print parm
            if re.match(security_sec_p, parm):
                secp = False
            if re.search(security_frozen_p, parm):
                if re.search(security_not_p,parm):
                    frozenp = False
                else:
                    frozenp = True
    return frozenp

def security_erase(erasedrv, enable_enhanced):
    if enable_enhanced:
        print "Enhanced Erase?(y/n) ",
        keyin = raw_input()
        if re.match("[Yy]",keyin):
            cmd_erase = TMP_EH_ERASE
        else:
            cmd_erase = TMP_ERASE
    else:
        cmd_erase = TMP_ERASE
    cmd_erase.append(erasedrv)
    print "Erase OK?(y/n) ",
    keyin = raw_input()
    if re.match("[Yy]", keyin):
        set_security_password(erasedrv)
        subprocess.check_output(cmd_erase)

def check_erase_enhanced(info_lines):
    security_secbegin_p = re.compile("Security:")
    supported_p = re.compile(P_SUPPORTED)
    enhanced_p = re.compile(P_ENHANCED)
    not_p = re.compile("not")
    secp = False
    enhanced = False

    for parm in info_lines:
        if re.match(security_secbegin_p, parm):
            secp = True
            continue
        if secp == True:
            if re.search(supported_p, parm) and re.search(enhanced_p, parm):
                if (not re.search(not_p, parm)):
                    enhanced = True
    return enhanced
        
devdisk = glob.glob("/dev/sd[a-z]")
frz = False

for d in devdisk:
    print d
    hdinfo = get_hdinfo(d)
    if (print_secsec(hdinfo)):
        frz=True

if (frz == True):
    print "SECURITY FROZEN --- syspend -> recycling"
    wakeup_time = subprocess.check_output(["date", "+%s", "-d", "+1min"])
    print "wakeup"
    subprocess.call(["date", "-d", "+1min"])
    set_timer_cmd = "echo " + str(wakeup_time).rstrip() + " > " + SYS_WAKETIMER
    print set_timer_cmd
    subprocess.call([set_timer_cmd],shell=True)
    subprocess.call([CMD_SUSPEND])
    for d in devdisk:
        print d
        print_secsec(get_hdinfo(d))
    
for d in devdisk:
    print "Erase " + d +"?(y/n)",
    keyin = raw_input()
    if re.match("[Y/y]",keyin):
        hdinfo = get_hdinfo(d)
        enh_era = check_erase_enhanced(hdinfo)
	print "Enhance: ", enh_era
        security_erase(d, enh_era)
        hdinfo = get_hdinfo(d)
        print_secsec(hdinfo)
