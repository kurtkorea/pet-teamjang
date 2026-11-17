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
for path in (
    "/maixapp/tmp/last_run.log",
    "/tmp/last_run.log",
    "/var/log/maixvision.log",
):
    print("====", path)
    stdin, stdout, stderr = c.exec_command(f"ls -la {path} 2>&1; echo '---'; tail -n 80 {path} 2>&1")
    print(stdout.read().decode(errors="replace"))
c.close()
