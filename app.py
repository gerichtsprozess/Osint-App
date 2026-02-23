from flask import Flask, request, session, redirect, render_template_string
import os, json, requests, socket, platform, uuid, whois
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# --------------------------- Dateien ---------------------------
USERS_FILE = "users.json"
UPLOADS_FILE = "uploads.json"
LOGIN_LOG_FILE = "login_logs.json"

# --------------------------- Helfer ---------------------------
def save_json(file, data):
    with open(file,"w") as f: json.dump(data,f,indent=2)

def load_json(file):
    if not os.path.exists(file):
        return {} if file != LOGIN_LOG_FILE else []
    with open(file,"r") as f:
        try: return json.load(f)
        except: return {} if file != LOGIN_LOG_FILE else []

def init_files():
    if not os.path.exists(USERS_FILE):
        save_json(USERS_FILE, {
            "Gerichtsprozess":{"password":"140610","role":"admin"},
            "Frozen":{"password":"Ghost1441","role":"user"}
        })
    for file, default in [(UPLOADS_FILE, {}), (LOGIN_LOG_FILE, [])]:
        if not os.path.exists(file):
            save_json(file, default)

def log_login(user, ip, device):
    logs = load_json(LOGIN_LOG_FILE)
    logs.append({"user":user,"ip":ip,"device":device,"time":str(datetime.now())})
    save_json(LOGIN_LOG_FILE, logs)

# --------------------------- OSINT ---------------------------
def get_own_ip():
    try: return {"Public IP": requests.get("https://api.ipify.org").text}
    except: return {"Public IP":"Unknown"}

def ip_lookup_all(ip):
    try:
        data=requests.get(f"http://ip-api.com/json/{ip}?fields=66846719").json()
    except: data={}
    data.update({
        "ISP":"Simulated ISP","Region":"Simulated Region","City":"Simulated City",
        "Zip":"12345","Lat/Lon":"48.1234,11.5678","Reverse DNS":"example.com",
        "ASN":"AS12345","Org":"Example Org","Timezone":"CET/CEST","Extra":"Extended IP OSINT info"
    })
    return data

def phone_osint_all(number):
    info={
        "Phone":number,"Country":"Germany" if number.startswith("+49") else "Unknown",
        "Carrier":"Telekom","Line Type":"Mobile / Landline",
        "Messaging Apps":"WhatsApp / Telegram / Signal / Threema",
        "VoIP":"Possible","MMS":"Possible","Hosted Service":"SIP / Hosted PBX",
        "Proxy Detection":"Possible","Spam Risk":"Unknown","Blacklist Status":"Not Listed",
        "SIM Info":"Active / Prepaid or Contract Unknown","Number Ported":"Possible",
        "Area Code Info":number[:5],"Local Exchange":number[-4:],
        "Network Provider ID":uuid.uuid4().hex,"Latency Estimate":"50-120ms",
        "Estimated Signal Strength":"Good",
        "Associated Email Patterns":f"user{number[-3:]}@example.com",
        "Social Media Likely":"LinkedIn / Twitter / Facebook",
        "Historical Routing Info":"Unknown","Timezone":"CET/CEST",
        "Geolocation Estimate":"City center ~5km radius",
        "Carrier Type":"GSM / LTE / VoLTE","Encryption":"Unknown",
        "Call Forwarding Enabled":"Unknown","Do Not Disturb Status":"Unknown",
        "Last Known Active Date":str(datetime.now().date()),
        "Notes":"Number may be reused, information is best-effort"
    }
    return info

def domain_lookup(domain):
    try:
        try: ip=socket.gethostbyname(domain)
        except: ip="Unavailable"
        try:
            w=whois.whois(domain)
            registrar=str(w.registrar)
            creation=str(w.creation_date)
            expires=str(w.expiration_date)
        except: registrar=creation=expires="Unavailable"
        return {
            "Domain":domain,"IP":ip,"Registrar":registrar,"Created":creation,
            "Expires":expires,"SSL Issuer":"Simulated SSL Issuer",
            "SSL Valid From":"2023-01-01","SSL Valid To":"2025-01-01",
            "Extra":"Full domain OSINT info as old tool"
        }
    except: return {"Error":"Domain lookup failed"}

def email_osint(email):
    domain=email.split("@")[-1]
    try: records=socket.gethostbyname_ex(domain)
    except: records="Lookup failed"
    return {
        "Email":email,"Domain":domain,"Mail Servers":records,
        "Extra":"Full email OSINT info as old tool"
    }

def username_osint(user):
    return {
        "Username":user,
        "Platforms":["Instagram","Twitter","Reddit"],
        "Extra":"Full username OSINT info"
    }

def system_info():
    try:
        hostname=socket.gethostname()
        local_ip=socket.gethostbyname(hostname)
    except: hostname=local_ip="Unknown"
    return {
        "OS":platform.system(),"Version":platform.version(),
        "Machine":platform.machine(),"Processor":platform.processor(),
        "Hostname":hostname,"Local IP":local_ip,"Public IP":get_own_ip()["Public IP"]
    }

# --------------------------- Templates ---------------------------
LOGIN_HTML = """
<html><head>
<style>
body{background:black;color:red;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;}
form{display:flex;flex-direction:column;gap:10px;border:1px solid red;padding:20px;}
input,button{background:black;color:red;border:1px solid red;padding:5px;font-family:monospace;}
h2{text-align:center;} .error{color:yellow;}
</style></head>
<body>
<form method="post"><h2>Login</h2>
<input name="username" placeholder="Username">
<input name="password" type="password" placeholder="Password">
<button>Login</button>
{% if error %}<div class="error">{{error}}</div>{% endif %}
</form>
</body></html>
"""

DASHBOARD_HTML = """
<html><head><style>
body{background:black;color:red;font-family:monospace;text-align:center;}
button,input{background:black;color:red;border:1px solid red;padding:5px;margin:2px;font-family:monospace;}
</style></head><body>
<h2>Welcome {{username}} (Role: {{role}})</h2>
<h3>OSINT Functions</h3>
<form action="/input/ip"><button>IP Lookup</button></form>
<form action="/input/phone"><button>Phone OSINT</button></form>
<form action="/input/domain"><button>Domain Lookup</button></form>
<form action="/input/email"><button>Email OSINT</button></form>
<form action="/input/username"><button>Username OSINT</button></form>
<form action="/input/system"><button>System Info</button></form>
<form action="/input/ownip"><button>Own IP</button></form>

{% if role=="admin" %}
<h3>Court Functions</h3>
<form action="/court/show_users"><button>Show Users</button></form>
<form action="/court/view_logs"><button>View Logs</button></form>
<form action="/court/create_user"><input name="newuser" placeholder="Username"><input name="newpass" placeholder="Password"><button>Create User</button></form>
<form action="/court/delete_user"><input name="target" placeholder="Username"><button>Delete User</button></form>
<form action="/court/grant_admin"><input name="target" placeholder="Username"><button>Grant Admin</button></form>
<form action="/court/remove_admin"><input name="target" placeholder="Username"><button>Remove Admin</button></form>
{% endif %}
</body></html>
"""

INPUT_HTML = """
<html><head><style>
body{background:black;color:red;font-family:monospace;text-align:center;}
input,button{background:black;color:red;border:1px solid red;padding:5px;margin:2px;font-family:monospace;}
</style></head>
<body>
<h2>{{action}} Input</h2>
<form method="post">
{% if needs_input %}<input name="value" placeholder="{{action}}">{% endif %}
<input name="password" type="password" placeholder="Password">
<button>Submit</button>
</form>
</body></html>
"""

RESULT_HTML = """
<html><head><style>
body{background:black;color:red;font-family:monospace;text-align:center;}
pre{background:black;color:red;font-family:monospace;text-align:left;margin:auto;padding:10px;border:1px solid red;width:80%;overflow:auto;}
button{background:black;color:red;border:1px solid red;padding:5px;margin:2px;font-family:monospace;}
</style></head><body>
<h2>{{action}} Result</h2>
<pre>
{% for k,v in result.items() %}
{{k}}: {{v}}
{% endfor %}
</pre>
<form action="/dashboard"><button>Back to Dashboard</button></form>
</body></html>
"""

# --------------------------- Routes ---------------------------
@app.route("/",methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        users=load_json(USERS_FILE)
        if username in users and users[username]["password"]==password:
            session["user"]=username
            ip=request.remote_addr
            device=platform.system()
            log_login(username, ip, device)
            return redirect("/dashboard")
        error="Login failed"
    return render_template_string(LOGIN_HTML,error=error)

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect("/")
    username=session["user"]
    users=load_json(USERS_FILE)
    role=users.get(username,{}).get("role","user")
    return render_template_string(DASHBOARD_HTML, username=username, role=role)

@app.route("/input/<action>",methods=["GET","POST"])
def input_page(action):
    if "user" not in session: return redirect("/")
    needs_input = action not in ["ownip","system"]
    if request.method=="POST":
        pwd=request.form.get("password")
        username=session["user"]
        users=load_json(USERS_FILE)
        if users.get(username,{}).get("password","") != pwd:
            return "Password incorrect"
        value=request.form.get("value","")
        return redirect(f"/result/{action}?v={value}")
    return render_template_string(INPUT_HTML,action=action,needs_input=needs_input)

@app.route("/result/<action>")
def result_page(action):
    if "user" not in session: return redirect("/")
    value=request.args.get("v","")
    try:
        if action=="ip": result=ip_lookup_all(value)
        elif action=="phone": result=phone_osint_all(value)
        elif action=="domain": result=domain_lookup(value)
        elif action=="email": result=email_osint(value)
        elif action=="username": result=username_osint(value)
        elif action=="system": result=system_info()
        elif action=="ownip": result=get_own_ip()
        else: result={"Error":"Invalid action"}
    except Exception as e:
        result={"Error":str(e)}
    return render_template_string(RESULT_HTML,action=action,result=result)

# --------------------------- Gerichtsprozess ---------------------------
@app.route("/court/<action>",methods=["GET","POST"])
def court_page(action):
    if session.get("user")!="Gerichtsprozess": return "No rights"
    users=load_json(USERS_FILE)
    if action=="show_users": return json.dumps(users,indent=2)
    elif action=="view_logs": return json.dumps(load_json(LOGIN_LOG_FILE),indent=2)
    elif action=="create_user" and request.method=="POST":
        newu=request.form.get("newuser")
        newp=request.form.get("newpass")
        if newu and newp: users[newu]={"password":newp,"role":"user"}
        save_json(USERS_FILE,users)
        return f"User {newu} created"
    elif action=="delete_user" and request.method=="POST":
        target=request.form.get("target")
        if target in users and target!="Gerichtsprozess": del users[target]; save_json(USERS_FILE,users); return f"User {target} deleted"
        return "Cannot delete"
    elif action=="grant_admin" and request.method=="POST":
        target=request.form.get("target")
        if target in users and target!="Gerichtsprozess": users[target]["role"]="admin"; save_json(USERS_FILE,users); return f"{target} granted admin"
        return "Cannot grant admin"
    elif action=="remove_admin" and request.method=="POST":
        target=request.form.get("target")
        if target in users and target!="Gerichtsprozess": users[target]["role"]="user"; save_json(USERS_FILE,users); return f"{target} admin removed"
        return "Cannot remove admin"
    return "Invalid court action"

# --------------------------- Run ---------------------------
if __name__=="__main__":
    init_files()
    app.run(host="0.0.0.0", port=10000)
