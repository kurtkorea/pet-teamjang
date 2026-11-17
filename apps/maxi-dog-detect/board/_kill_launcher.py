import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "192.168.0.41",
    22,
    "root",
    "sipeed",
    timeout=20,
    banner_timeout=40,
    allow_agent=False,
    look_for_keys=True,
)
cmd = r"""
echo before:
ps w | grep -iE 'launcher|detect_save' | grep -v grep || true
# only launcher binaries, not whole /maixapp
kill $(pgrep -f '/maixapp/apps/launcher/launcher') 2>/dev/null || true
sleep 2
echo after:
ps w | grep -iE 'launcher|detect_save' | grep -v grep || true
ls -lt /root/dog_db/detect/miss/20261116 2>/dev/null | head -10
"""
i, o, e = c.exec_command(cmd, timeout=30)
print(o.read().decode())
print(e.read().decode())
c.close()
