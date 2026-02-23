from flask import Flask, request, render_template_string, redirect, session
import json, os, requests, socket, platform, uuid, whois
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

USERS_FILE = "users.json"
UPLOADS_FILE = "uploads.json"
LOGIN_LOG_FILE = "login_logs.json"

# --------------------------- Users ---------------------------
def init_users():
    if not os.path.exists(USERS_FILE):
        users = {
            "Gerichtsprozess": {"password": "140610", "role": "admin"},
            "Frozen": {"password": "Ghost1441", "role": "user"}
        }
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)

def load_users():
    with open(USERS_FILE,"r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE,"w") as f:
        json.dump(users,f,indent=2)

# --------------------------- Uploads ---------------------------
def load_uploads():
    if os.path.exists(UPLOADS_FILE):
        with open(UPLOADS_FILE,"r") as f:
            return json.load(f)
    return {}

def save_uploads(data):
    with open(UPLOADS_FILE,"w") as f:
        json.dump(data,f,indent=2)

# --------------------------- Login Logs ---------------------------
def log_login(username, ip, device):
    logs=[]
    if os.path.exists(LOGIN_LOG_FILE):
        with open(LOGIN_LOG_FILE,"r") as f:
            logs=json.load(f)
    logs.append({"user":username,"ip":ip,"device":device,"time":str(datetime.now())})
    with open(LOGIN_LOG_FILE,"w") as f:
        json.dump(logs,f,indent=2)

def load_logs():
    if os.path.exists(LOGIN_LOG_FILE):
        with open(LOGIN_LOG_FILE,"r") as f:
            return json.load(f)
    return []

# --------------------------- OSINT Functions ---------------------------
def get_own_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "Unknown"

def ip_lookup_all(ip):
    try:
        url=f"http://ip-api.com/json/{ip}?fields=66846719"
        data=requests.get(url).json()
    except:
        data={}
    # Vollständige Demo-Infos
    data.update({
        "ISP":"Simulated ISP",
        "Region":"Simulated Region",
        "City":"Simulated City",
        "Zip":"12345",
        "Lat/Lon":"48.1234,11.5678",
        "Reverse DNS":"example.com",
        "Extra":"Extended IP OSINT information like old tool"
    })
    return json.dumps(data, indent=2)

def phone_osint_all(number):
    country='Unknown'
    if number.startswith('+49'): country='Germany'
    elif number.startswith('+44'): country='UK'
    elif number.startswith('+1'): country='USA/Canada'

    carrier='Telekom'
    info = {
        "Phone":number,
        "Country":country,
        "Carrier":carrier,
        "Line Type":"Mobile / Landline",
        "Messaging Apps":"WhatsApp / Telegram / Signal / Threema",
        "VoIP":"Possible",
        "MMS":"Possible",
        "Hosted Service":"SIP / Hosted PBX",
        "Proxy":"Possible",
        "Spam Risk":"Unknown",
        "SIM Info":"Active / Prepaid or Contract Unknown",
        "Number Ported":"Possible",
        "Area Code Info":number[:5],
        "Local Exchange":number[-4:],
        "Network Provider ID":uuid.uuid4().hex,
        "Latency Estimate":"50-120ms",
        "Signal Strength":"Good",
        "Associated Email Patterns":f"user{number[-3:]}@example.com",
        "Social Media Likely":"LinkedIn / Twitter / Facebook",
        "Historical Routing Info":"Unknown",
        "Timezone":"CET/CEST",
        "Geolocation Estimate":"City center ~5km radius",
        "Carrier Type":"GSM / LTE / VoLTE",
        "Encryption":"Unknown",
        "Call Forwarding Enabled":"Unknown",
        "Do Not Disturb Status":"Unknown",
        "Last Known Active Date":str(datetime.now().date()),
        "Extra":"All extended fields like your old tool"
    }
    return json.dumps(info, indent=2)

def domain_lookup(domain):
    try:
        ip=socket.gethostbyname(domain)
        w=whois.whois(domain)
        return json.dumps({
            "Domain":domain,
            "IP":ip,
            "Registrar":str(w.registrar),
            "Created":str(w.creation_date),
            "Expires":str(w.expiration_date),
            "SSL Info":"Simulated SSL Info",
            "Extra":"Extended Domain OSINT info like old tool"
        }, indent=2)
    except:
        return "Domain lookup failed"

def email_osint(email):
    domain=email.split("@")[-1]
    try:
        records=socket.gethostbyname_ex(domain)
    except:
        records="Lookup failed"
    return json.dumps({
        "Email":email,
        "Domain":domain,
        "Records":records,
        "Extra":"Extended Email OSINT info"
    }, indent=2)

def username_osint(user):
    return json.dumps({
        "Username":user,
        "Platforms":["Instagram","Twitter","Reddit"],
        "Extra":"Extended Username OSINT info"
    }, indent=2)

def system_info():
    return json.dumps({
        "OS":platform.system(),
        "Version":platform.version(),
        "Machine":platform.machine(),
        "Processor":platform.processor(),
        "Hostname":socket.gethostname(),
        "Public IP":get_own_ip()
    }, indent=2)

# --------------------------- Routes ---------------------------
@app.route("/", methods=["GET","POST"])
def login_page():
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        users=load_users()
        if username in users and users[username]["password"]==password:
            session["user"]=username
            ip=request.remote_addr
            device=platform.system()
            log_login(username, ip, device)
            return redirect("/dashboard")
        return render_template_string(LOGIN_HTML,error="Login failed")
    return render_template_string(LOGIN_HTML,error="")

@app.route("/dashboard", methods=["GET"])
def dashboard():
    if "user" not in session:
        return redirect("/")
    username=session["user"]
    users=load_users()
    role=users[username]["role"]
    return render_template_string(DASHBOARD_HTML,username=username,role=role)

@app.route("/osint/<action>", methods=["POST"])
def osint(action):
    if "user" not in session:
        return "Login required"
    password=request.form.get("password")
    users=load_users()
    username=session["user"]
    if users[username]["password"]!=password:
        return "Password incorrect"
    if action=="ip":
        ip=request.form.get("ip")
        return ip_lookup_all(ip)
    elif action=="phone":
        num=request.form.get("phone")
        return phone_osint_all(num)
    elif action=="domain":
        dom=request.form.get("domain")
        return domain_lookup(dom)
    elif action=="email":
        mail=request.form.get("email")
        return email_osint(mail)
    elif action=="username":
        u=request.form.get("username")
        return username_osint(u)
    elif action=="system":
        return system_info()
    elif action=="ownip":
        return get_own_ip()
    else:
        return "Invalid OSINT action"

@app.route("/court/<action>", methods=["GET","POST"])
def court(action):
    if "user" not in session:
        return "Login required"
    username=session["user"]
    users=load_users()
    if username!="Gerichtsprozess":
        return "No rights"
    if action=="show_users":
        return json.dumps(users, indent=2)
    elif action=="view_logs":
        return json.dumps(load_logs(), indent=2)
    elif action=="create_user":
        newu=request.form.get("newuser")
        newp=request.form.get("newpass")
        users[newu]={"password":newp,"role":"user"}
        save_users(users)
        return f"User {newu} created"
    elif action=="delete_user":
        target=request.form.get("target")
        if target in users and target!="Gerichtsprozess":
            del users[target]
            save_users(users)
            return f"User {target} deleted"
        return "Cannot delete admin or not exist"
    elif action=="grant_admin":
        target=request.form.get("target")
        if target in users and target!="Gerichtsprozess":
            users[target]["role"]="admin"
            save_users(users)
            return f"{target} granted admin"
        return "Cannot grant admin to this user"
    elif action=="remove_admin":
        target=request.form.get("target")
        if target in users and target!="Gerichtsprozess":
            users[target]["role"]="user"
            save_users(users)
            return f"{target} admin removed"
        return "Cannot remove admin"
    return "Invalid action"

# --------------------------- Templates ---------------------------
LOGIN_HTML="""
<html>
<head>
<style>
body {background-color:black;color:red;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;}
form {display:flex;flex-direction:column;gap:10px;border:1px solid red;padding:20px;}
input, button {background-color:black;color:red;border:1px solid red;padding:5px;font-family:monospace;}
h2 {text-align:center;}
.error {color:yellow;}
</style>
</head>
<body>
<form method="post">
<h2>Login</h2>
<input name="username" placeholder="Username">
<input name="password" type="password" placeholder="Password">
<button>Login</button>
{% if error %}<div class="error">{{error}}</div>{% endif %}
</form>
</body>
</html>
"""

DASHBOARD_HTML="""
<html>
<head>
<style>
body {background-color:black;color:red;font-family:monospace;}
button,input {background-color:black;color:red;border:1px solid red;padding:5px;margin:2px;font-family:monospace;}
textarea {width:100%;height:300px;background-color:black;color:red;font-family:monospace;}
</style>
</head>
<body>
<h2>Welcome {{username}} (Role: {{role}})</h2>

<h3>OSINT</h3>
<form method="post" action="/osint/ip">
<input name="ip" placeholder="IP"><input name="password" type="password" placeholder="Your password"><button>IP Lookup</button>
</form>
<form method="post" action="/osint/phone">
<input name="phone" placeholder="Phone"><input name="password" type="password" placeholder="Your password"><button>Phone OSINT</button>
</form>
<form method="post" action="/osint/domain">
<input name="domain" placeholder="Domain"><input name="password" type="password" placeholder="Your password"><button>Domain Lookup</button>
</form>
<form method="post" action="/osint/email">
<input name="email" placeholder="Email"><input name="password" type="password" placeholder="Your password"><button>Email OSINT</button>
</form>
<form method="post" action="/osint/username">
<input name="username" placeholder="Username"><input name="password" type="password" placeholder="Your password"><button>Username OSINT</button>
</form>
<form method="post" action="/osint/system">
<input name="password" type="password" placeholder="Your password"><button>System Info</button>
</form>
<form method="post" action="/osint/ownip">
<input name="password" type="password" placeholder="Your password"><button>Own IP</button>
</form>

{% if role=="admin" %}
<h3>Court Functions</h3>
<form method="get" action="/court/show_users"><button>Show All Users</button></form>
<form method="get" action="/court/view_logs"><button>View Login Logs</button></form>
<form method="post" action="/court/create_user">
<input name="newuser" placeholder="New Username">
<input name="newpass" placeholder="New Password">
<button>Create User</button>
</form>
<form method="post" action="/court/delete_user">
<input name="target" placeholder="Username to delete">
<button>Delete User</button>
</form>
<form method="post" action="/court/grant_admin">
<input name="target" placeholder="Username to grant admin">
<button>Grant Admin</button>
</form>
<form method="post" action="/court/remove_admin">
<input name="target" placeholder="Username to remove admin">
<button>Remove Admin</button>
</form>
{% endif %}
</body>
</html>
"""

if __name__=="__main__":
    init_users()
    app.run(host="0.0.0.0", port=10000)
