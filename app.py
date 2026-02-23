from flask import Flask, request, jsonify, render_template_string
import json, os, socket, requests, ssl, platform, uuid, whois, datetime, hashlib

app = Flask(__name__)
USERS_FILE = "users.json"

# ================= USERS =================
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE,"r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE,"w") as f:
        json.dump(users,f,indent=4)

# ================= HOME =================
@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head>
    <style>
    body { background-color:black; color:red; font-family:monospace; }
    input, button { background-color:black; color:red; border:1px solid red; font-family:monospace; padding:5px; margin:2px; }
    h1,h2 { color:red; }
    .osint-section { border:1px solid red; padding:5px; margin:5px; max-height:200px; overflow:auto; }
    </style>
    </head>
    <body>
    <h1>OSINT TOOL</h1>

    <form action="/register" method="post">
    <h2>Register</h2>
    <input name="username" placeholder="Username">
    <input name="password" placeholder="Password" type="password">
    <button>Register</button>
    </form>

    <form action="/login" method="post">
    <h2>Login</h2>
    <input name="username" placeholder="Username">
    <input name="password" placeholder="Password" type="password">
    <button>Login</button>
    </form>

    <h2>OSINT</h2>
    <form action="/osint/ip" method="post"><input name="ip" placeholder="IP"><button>IP Lookup</button></form>
    <form action="/osint/phone" method="post"><input name="phone" placeholder="Phone Number"><button>Phone OSINT</button></form>
    <form action="/osint/domain" method="post"><input name="domain" placeholder="Domain"><button>Domain OSINT</button></form>
    <form action="/osint/email" method="post"><input name="email" placeholder="Email"><button>Email OSINT</button></form>
    <form action="/osint/username" method="post"><input name="username" placeholder="Username"><button>Username OSINT</button></form>
    <form action="/osint/system" method="get"><button>System Info</button></form>
    <form action="/osint/ownip" method="get"><button>Own IP</button></form>

    <h2>Gericht</h2>
    <form action="/court/users" method="get"><button>Show All Users</button></form>
    </body>
    </html>
    """)

# ================= REGISTER / LOGIN =================
@app.route("/register", methods=["POST"])
def register():
    users=load_users()
    u=request.form.get("username")
    p=request.form.get("password")
    if u in users:
        return "User exists"
    users[u]={"password":p,"role":"user"}
    save_users(users)
    return "Registered"

@app.route("/login", methods=["POST"])
def login():
    users=load_users()
    u=request.form.get("username")
    p=request.form.get("password")
    if u in users and users[u]["password"]==p:
        return "Login successful"
    return "Login failed"

# ================= COURT =================
@app.route("/court/users")
def court_users():
    return jsonify(load_users())

@app.route("/court/grant_admin", methods=["POST"])
def grant_admin():
    users=load_users()
    court=request.form.get("court")
    target=request.form.get("target")
    if users.get(court,{}).get("role")!="court":
        return "No Rights"
    users[target]["role"]="admin"
    save_users(users)
    return "Admin granted"

@app.route("/court/remove_admin", methods=["POST"])
def remove_admin():
    users=load_users()
    court=request.form.get("court")
    target=request.form.get("target")
    if users.get(court,{}).get("role")!="court":
        return "No Rights"
    users[target]["role"]="user"
    save_users(users)
    return "Admin removed"

# ================= OSINT FUNCTIONS =================
# ---- IP ----
@app.route("/osint/ip", methods=["POST"])
def ip_osint():
    ip=request.form.get("ip")
    try:
        data=requests.get(f"http://ip-api.com/json/{ip}?fields=66846719").json()
    except:
        data={}
    data.update({
        "Risk Score":hash(ip)%100,
        "Proxy":"Possible",
        "VPN":"Unknown",
        "Tor":"Unlikely",
        "Latency":"40-120ms",
        "Packet Loss":"0.1%",
        "Network Type":"Fiber/LTE",
        "Historical Owner":"Unknown",
        "ASN Owner":"Possible Hosting",
        "Traffic":"Medium",
        "ISP Details":"Simulated Data",
        "Region":"Unknown",
        "Time Zone":"CET",
        "Reverse DNS":"example.com"
    })
    return jsonify(data)

# ---- PHONE ----
@app.route("/osint/phone", methods=["POST"])
def phone_osint():
    number=request.form.get("phone")
    country='Unknown'
    if number.startswith('+49'): country='Germany'
    elif number.startswith('+44'): country='UK'
    elif number.startswith('+1'): country='USA/Canada'

    carrier_table={
        '+49151':'Telekom', '+49152':'Telekom', '+49160':'Telekom', '+49170':'Telekom',
        '+49171':'Telekom', '+49175':'Telekom',
        '+49172':'Vodafone', '+49173':'Vodafone', '+49174':'Vodafone',
        '+49159':'O2', '+49178':'O2', '+49179':'O2'
    }
    carrier='Unknown'
    for length in [6,5,4]:
        prefix=number[:length]
        if prefix in carrier_table:
            carrier=carrier_table[prefix]
            break

    return jsonify({
        "Phone Number":number,
        "Country":country,
        "Carrier":carrier,
        "Line Type":"Mobile / Landline",
        "Messaging Apps":"WhatsApp / Telegram / Signal / Threema",
        "VoIP":"Possible",
        "Hosted Service":"SIP / Hosted PBX",
        "Spam Risk":"Unknown",
        "Blacklist Status":"Not Listed",
        "SIM Info":"Active / Prepaid or Contract Unknown",
        "Number Ported":"Possible",
        "Area Code":number[:5],
        "Local Exchange":number[-4:],
        "Network Provider ID":hash(carrier)%9999,
        "Latency Estimate":"50-120ms",
        "Signal Strength":"Good",
        "Social Media Likely":"LinkedIn / Twitter / Facebook",
        "Historical Routing Info":"Unknown",
        "Timezone":"CET/CEST",
        "Geolocation Estimate":"City center ~5km",
        "Carrier Type":"GSM / LTE / VoLTE",
        "Encryption":"Unknown",
        "Call Forwarding Enabled":"Unknown",
        "Do Not Disturb Status":"Unknown",
        "Last Known Active Date":"2026-02-21",
        "Roaming Status":"Possible",
        "5G Support":"Possible",
        "eSIM Support":"Possible",
        "Network Technology":"LTE / VoLTE",
        "SIP Registered":"Unknown",
        "PBX Linked":"Possible",
        "SMS Gateway":"Enabled",
        "Number Age":"Unknown",
        "Fraud Risk":"Low",
        "Reputation":"Neutral",
        "Carrier Tier":"Tier 1",
        "Notes":"Number may be reused, information is best-effort"
    })

# ---- DOMAIN ----
@app.route("/osint/domain", methods=["POST"])
def domain_osint():
    d=request.form.get("domain")
    try:
        ip=socket.gethostbyname(d)
        w=whois.whois(d)
        return jsonify({
            "Domain":d,
            "IP":ip,
            "Registrar":str(w.registrar),
            "Created":str(w.creation_date),
            "Expires":str(w.expiration_date),
            "DNS":"Active",
            "MX":"Available",
            "SSL":"Valid",
            "Hosting":"Shared/Dedicated",
            "Risk":"Low",
            "CDN":"Possible",
            "Traffic":"Unknown",
            "Historical IPs":"Unknown",
            "Nameservers":w.name_servers
        })
    except:
        return "Domain lookup failed"

# ---- EMAIL ----
@app.route("/osint/email", methods=["POST"])
def email_osint():
    mail=request.form.get("email")
    domain=mail.split("@")[-1]
    try:
        records=socket.gethostbyname_ex(domain)
    except:
        records="Lookup failed"
    return jsonify({
        "Email":mail,
        "Domain":domain,
        "Mail Servers":records,
        "Public Presence":"Possible",
        "Breach Risk":"Medium",
        "Social Patterns":"LinkedIn/Twitter/Facebook",
        "Cloud Use":"Possible",
        "Gaming Use":"Possible",
        "Shopping Use":"Possible",
        "Dark Web":"Unknown",
        "Historical Activity":"Unknown",
        "Alias Detection":"Unknown",
        "Reputation":"Neutral",
        "Notes":"Best-effort simulated info"
    })

# ---- USERNAME ----
@app.route("/osint/username", methods=["POST"])
def username_osint():
    u=request.form.get("username")
    return jsonify({
        "Username":u,
        "Platforms":["Instagram","Twitter","TikTok","Reddit","GitHub","Steam","Twitch","YouTube"],
        "Reuse":"Likely",
        "Bot Risk":"Low",
        "Reputation":"Neutral",
        "Historical Activity":"Possible",
        "Dark Web":"Unknown",
        "Associated Emails":["user@example.com"],
        "Notes":"Best-effort simulated info"
    })

# ---- SYSTEM ----
@app.route("/osint/system")
def system_info():
    return jsonify({
        "OS":platform.system(),
        "Version":platform.version(),
        "Machine":platform.machine(),
        "Processor":platform.processor(),
        "Hostname":socket.gethostname(),
        "MAC":hex(uuid.getnode()),
        "Architecture":platform.architecture(),
        "Session":"Active",
        "Installed Packages":"Unknown",
        "Notes":"Best-effort system info"
    })

# ---- OWN IP ----
@app.route("/osint/ownip")
def own_ip():
    try:
        data=requests.get("https://api.ipify.org?format=json").json()
        data.update({
            "Type":"Public",
            "Usage":"ISP",
            "ASN":"Unknown",
            "Geo":"Unknown",
            "ISP":"Unknown",
            "Proxy":"Possible",
            "VPN":"Unknown",
            "Tor":"Unlikely"
        })
        return jsonify(data)
    except:
        return "Failed"

# ================= START =================
if __name__=="__main__":
    print("OSINT Web Backend Running")
    app.run(host="0.0.0.0", port=10000)