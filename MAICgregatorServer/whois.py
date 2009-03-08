import socket

def getEduWHOIS(domain, whoisServer = "whois.educause.net", port = 43):
    # Make sure we're only looking up the root domain, not the entire domain name
    domainSplit = domain.split(".")
    host = domainSplit[-2] + "." + domainSplit[-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((whoisServer, port))
    s.send(host + "\r\n")

    response = ""
    while True:
        data = s.recv(4096)
        response += data

        if data == '':
            break
    s.close()

    responseSplit = response.split("\n")
    registrantIndex = responseSplit.index("Registrant:")
    result = responseSplit[registrantIndex + 1].strip()
    
    # HEINOUS, but the WHOIS entry doesn't help us here
    if (domain == "umich.edu"):
        result = "University of Michigan"
    return result

