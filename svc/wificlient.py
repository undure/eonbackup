import subprocess
def load_dns_clients():
    lease_file="/var/lib/misc/dnsmasq.leases"

    proc = subprocess.Popen(["cat", lease_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #(out, err) = proc.communicate()
    out = proc.stdout.readlines()
    clients = []
    for line in out:
        l = line.strip()
        [t, mac, ip, host, mac2] = l.split(" ")
        clients.append({"ip": ip, "mac":mac, "host":host, "mac2":mac2, "t":t})
    return clients

def load_wifi_clients():
    cmd_arg="/sbin/iw dev uap0 station dump".split(' ')
    proc = subprocess.Popen(cmd_arg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #(out, err) = proc.communicate()
    out = proc.stdout.readlines()
    clients = []
    for line in out:
        l = line.strip()
        if l.startswith("Station"):
            [_, mac,_,_] = l.split(" ")
            clients.append(mac)
    return clients

def get_active_clients():
    wific = load_wifi_clients()
    dnsc = load_dns_clients() 

    return list(filter(lambda x: x["mac"] in wific, dnsc))
    
if __name__== "__main__":
    print(get_active_clients())
