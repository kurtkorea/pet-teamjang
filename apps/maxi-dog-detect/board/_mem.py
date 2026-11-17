import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "192.168.0.41",
    port=22,
    username="root",
    password="sipeed",
    timeout=20,
    banner_timeout=30,
    allow_agent=False,
    look_for_keys=True,
)
stdin, stdout, stderr = c.exec_command(
    "free -m; echo ---; ps aux --sort=-%mem | head -15; echo ---; "
    "ls /maixapp/tmp 2>/dev/null; ls /tmp/maix* 2>/dev/null"
)
print(stdout.read().decode(errors="replace"))
c.close()
