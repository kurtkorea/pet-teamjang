import paramiko
import time

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

# foreground with pty so we see early crash
cmd = "python -u /root/detect_save.py"
print("running:", cmd)
stdin, stdout, stderr = c.exec_command(cmd, timeout=25, get_pty=True)
time.sleep(12)
# if still running, stop reading
out = b""
err = b""
if stdout.channel.recv_ready():
    out += stdout.channel.recv(65535)
if stderr.channel.recv_ready():
    err += stderr.channel.recv(65535)
# also try exit status if finished
if stdout.channel.exit_status_ready():
    print("exit", stdout.channel.recv_exit_status())
else:
    print("still running after 12s; sending SIGTERM via pkill")
    c.exec_command("pkill -f /root/detect_save.py")
    time.sleep(1)
    if stdout.channel.recv_ready():
        out += stdout.channel.recv(65535)
print("STDOUT:\n", out.decode(errors="replace"))
print("STDERR:\n", err.decode(errors="replace"))
c.close()
