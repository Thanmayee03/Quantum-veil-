from flask import Flask, request, jsonify, render_template_string, redirect
from quantum_engine import run_bb84
import json, os, time, threading, uuid

app = Flask(__name__)

QUANTUM_THRESHOLD = 11.0
NUMBER_OF_QUBITS = 200
PROFILE_FILE = "profiles.json"

eve_active = False
lock = threading.RLock()


# ============================================================
# FIVE TEAM MEMBERS
# ============================================================
# Your original four profiles are kept.
# Thanmayee is added as the fifth profile.
DEFAULT_USERS = {
    "sam": {
        "name": "Sam",
        "emoji": "👤",
        "photo": "",
        "about": "Quantum Explorer ⚛️",
        "online": True
    },

    "riya": {
        "name": "Riya",
        "emoji": "👩",
        "photo": "",
        "about": "Securing the quantum channel 🔐",
        "online": True
    },

    "alex": {
        "name": "Alex",
        "emoji": "👨",
        "photo": "",
        "about": "Exploring quantum technology 🚀",
        "online": True
    },

    "priya": {
        "name": "Priya",
        "emoji": "👩",
        "photo": "",
        "about": "Data + Quantum 💜",
        "online": True
    },

    "thanmayee": {
        "name": "Thanmayee",
        "emoji": "👩",
        "photo": "",
        "about": "Quantum Explorer 🟣",
        "online": True
    },
}


def load_users():
    users = {k: v.copy() for k, v in DEFAULT_USERS.items()}

    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)

            if isinstance(saved, dict):
                for username in users:
                    if isinstance(saved.get(username), dict):
                        users[username].update(saved[username])

        except Exception as e:
            print("Profile load error:", e)

    return users


users = load_users()

conversations = {}
activity_log = []
pending_messages = []

last_quantum_result = {
    "status": "READY",
    "qber": 0,
    "errors": 0,
    "matching_bases": 0,
    "qubits": NUMBER_OF_QUBITS,
    "eve_active": False
}


# ============================================================
# PROFILE FUNCTIONS
# ============================================================

def save_users():
    try:
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                users,
                f,
                indent=4,
                ensure_ascii=False
            )

    except Exception as e:
        print("Profile save error:", e)


def conversation_key(a, b):
    return tuple(sorted((a.lower(), b.lower())))


def get_conversation(a, b):
    key = conversation_key(a, b)

    if key not in conversations:
        conversations[key] = []

    return conversations[key]


def add_activity(text, kind="info"):
    activity_log.insert(
        0,
        {
            "text": text,
            "kind": kind,
            "time": time.strftime("%H:%M:%S")
        }
    )

    del activity_log[100:]


def public_profiles():
    return {
        username: {
            "name": profile.get(
                "name",
                username.title()
            ),
            "emoji": profile.get(
                "emoji",
                "👤"
            ),
            "photo": profile.get(
                "photo",
                ""
            ),
            "about": profile.get(
                "about",
                ""
            ),
            "online": profile.get(
                "online",
                True
            )
        }

        for username, profile in users.items()
    }


# ============================================================
# MESSAGE FUNCTIONS
# ============================================================

def message_object(
    sender,
    receiver,
    text,
    status,
    qber=0,
    errors=0,
    matching_bases=0,
    blocked=False,
    system=False
):
    return {
        "id": uuid.uuid4().hex,
        "sender": sender,
        "receiver": receiver,
        "text": text,
        "status": status,
        "qber": qber,
        "errors": errors,
        "matching_bases": matching_bases,
        "blocked": blocked,
        "system": system,
        "time": time.strftime("%H:%M")
    }


def process_message(sender, receiver, text):
    global last_quantum_result

    result = run_bb84(
        eve_active=eve_active,
        number_of_qubits=NUMBER_OF_QUBITS
    )

    qber = result["qber"]

    conversation = get_conversation(
        sender,
        receiver
    )

    # --------------------------------------------------------
    # SECURE MESSAGE
    # --------------------------------------------------------

    if qber <= QUANTUM_THRESHOLD:

        msg = message_object(
            sender,
            receiver,
            text,
            "DELIVERED",
            qber,
            result["errors"],
            result["matching_bases"]
        )

        conversation.append(msg)

        last_quantum_result = {
            **result,
            "status": "SECURE",
            "eve_active": eve_active
        }

        add_activity(
            f"🔐 Secure key established: "
            f"{users[sender]['name']} → "
            f"{users[receiver]['name']} | "
            f"QBER {qber}%",
            "secure"
        )

        return True, msg, result

    # --------------------------------------------------------
    # BLOCKED MESSAGE
    # --------------------------------------------------------

    msg = message_object(
        sender,
        receiver,
        text,
        "BLOCKED",
        qber,
        result["errors"],
        result["matching_bases"],
        True
    )

    conversation.append(msg)

    pending_messages.append(
        {
            "sender": sender,
            "receiver": receiver,
            "blocked_message_id": msg["id"],
            "created": time.time()
        }
    )

    last_quantum_result = {
        **result,
        "status": "COMPROMISED",
        "eve_active": eve_active
    }

    add_activity(
        f"🚨 EVE DETECTED: Message blocked | QBER {qber}%",
        "danger"
    )

    alert = message_object(
        "system",
        receiver,
        "🚨 CODE RED\n"
        "Quantum channel compromised.\n"
        "The message was blocked because Eve was detected.",
        "ALERT",
        qber,
        result["errors"],
        result["matching_bases"],
        True,
        True
    )

    conversation.append(alert)

    return False, msg, result


def release_pending_messages():
    global pending_messages
    global last_quantum_result

    if eve_active or not pending_messages:
        return 0

    remaining = []
    released = 0

    for pending in list(pending_messages):

        result = run_bb84(
            eve_active=False,
            number_of_qubits=NUMBER_OF_QUBITS
        )

        if result["qber"] <= QUANTUM_THRESHOLD:

            conversation = get_conversation(
                pending["sender"],
                pending["receiver"]
            )

            found = False

            for msg in conversation:

                if msg.get("id") == pending["blocked_message_id"]:

                    msg["status"] = "RELEASED"
                    msg["blocked"] = False

                    msg["qber_after_retry"] = result["qber"]

                    msg["errors_after_retry"] = (
                        result["errors"]
                    )

                    msg["matching_bases_after_retry"] = (
                        result["matching_bases"]
                    )

                    msg["released_after_eve"] = True

                    found = True
                    break

            if found:

                released += 1

                last_quantum_result = {
                    **result,
                    "status": "SECURE",
                    "eve_active": False
                }

                add_activity(
                    f"🟢 Message released: "
                    f"{users[pending['sender']]['name']} → "
                    f"{users[pending['receiver']]['name']}",
                    "secure"
                )

            else:
                remaining.append(pending)

        else:
            remaining.append(pending)

    pending_messages = remaining

    return released


# ============================================================
# PAGES
# ============================================================

@app.route("/")
def dashboard():
    return render_template_string(
        DASHBOARD_HTML
    )


@app.route("/chat/<current_user>/<selected_user>")
def chat_page(current_user, selected_user):

    current_user = current_user.lower()
    selected_user = selected_user.lower()

    if current_user not in users:
        return redirect("/")

    if (
        selected_user not in users
        or selected_user == current_user
    ):
        selected_user = next(
            (
                u
                for u in users
                if u != current_user
            ),
            current_user
        )

    return render_template_string(
        CHAT_HTML,
        current_user=current_user,
        selected_user=selected_user
    )


# Old links still work
@app.route("/<username>")
def old_chat_link(username):

    username = username.lower()

    if username not in users:
        return redirect("/")

    selected = request.args.get(
        "chat",
        "riya"
    ).lower()

    if (
        selected not in users
        or selected == username
    ):
        selected = next(
            (
                u
                for u in users
                if u != username
            ),
            username
        )

    return redirect(
        f"/chat/{username}/{selected}"
    )


# ============================================================
# API
# ============================================================

@app.route("/api/profiles")
def profiles():

    with lock:
        return jsonify(
            public_profiles()
        )


@app.route(
    "/api/profile/<username>",
    methods=["POST"]
)
def update_profile(username):

    username = username.lower()

    if username not in users:
        return jsonify(
            {
                "success": False,
                "error": "User not found"
            }
        ), 404

    data = request.get_json(
        silent=True
    ) or {}

    with lock:

        name = data.get("name")
        about = data.get("about")
        photo = data.get("photo")

        if (
            name is not None
            and str(name).strip()
        ):
            users[username]["name"] = (
                str(name).strip()[:40]
            )

        if about is not None:
            users[username]["about"] = (
                str(about).strip()[:100]
            )

        if (
            photo is not None
            and len(str(photo)) <= 3000000
        ):
            users[username]["photo"] = str(photo)

        save_users()

        add_activity(
            f"👤 "
            f"{users[username]['name']} "
            f"profile updated"
        )

        return jsonify(
            {
                "success": True,
                "profile": users[username]
            }
        )


@app.route(
    "/api/quantum-test",
    methods=["GET", "POST"]
)
def quantum_test():

    with lock:

        result = run_bb84(
            eve_active=eve_active,
            number_of_qubits=NUMBER_OF_QUBITS
        )

        return jsonify(
            {
                **result,
                "status": (
                    "SECURE"
                    if result["qber"]
                    <= QUANTUM_THRESHOLD
                    else "COMPROMISED"
                ),
                "threshold": QUANTUM_THRESHOLD,
                "eve_active": eve_active
            }
        )


@app.route(
    "/api/send",
    methods=["POST"]
)
def send_message():

    data = request.get_json(
        silent=True
    ) or {}

    sender = str(
        data.get(
            "sender",
            "sam"
        )
    ).lower()

    receiver = str(
        data.get(
            "receiver",
            "riya"
        )
    ).lower()

    text = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    if (
        sender not in users
        or receiver not in users
    ):
        return jsonify(
            {
                "success": False,
                "error": "Invalid sender or receiver"
            }
        ), 400

    if sender == receiver:
        return jsonify(
            {
                "success": False,
                "error":
                    "Sender and receiver "
                    "must be different"
            }
        ), 400

    if not text:
        return jsonify(
            {
                "success": False,
                "error": "Message is empty"
            }
        ), 400

    if len(text) > 2000:
        return jsonify(
            {
                "success": False,
                "error": "Message is too long"
            }
        ), 400

    with lock:

        secure, msg, result = process_message(
            sender,
            receiver,
            text
        )

        return jsonify(
            {
                "success": secure,
                "status": msg["status"],
                "message": msg,
                "quantum": result,
                "eve_active": eve_active
            }
        )


@app.route(
    "/api/eve",
    methods=["POST"]
)
def toggle_eve():

    global eve_active

    data = request.get_json(
        silent=True
    ) or {}

    with lock:

        eve_active = bool(
            data.get(
                "active",
                not eve_active
            )
        )

        if eve_active:

            add_activity(
                "🔴 EVE MODE ACTIVATED — "
                "Intercept-Resend Attack",
                "danger"
            )

            return jsonify(
                {
                    "success": True,
                    "eve_active": True,
                    "released": 0,
                    "message":
                        "Eve attack mode activated."
                }
            )

        add_activity(
            "🟢 EVE MODE DEACTIVATED — "
            "Channel restored",
            "secure"
        )

        released = release_pending_messages()

        return jsonify(
            {
                "success": True,
                "eve_active": False,
                "released": released,
                "message":
                    f"Eve disabled. "
                    f"{released} pending "
                    f"message(s) released."
            }
        )


@app.route("/api/status")
def status():

    with lock:

        return jsonify(
            {
                "eve_active": eve_active,
                "threshold": QUANTUM_THRESHOLD,
                "pending_messages":
                    len(pending_messages),
                "last_quantum":
                    last_quantum_result,
                "activity":
                    activity_log[:30]
            }
        )


@app.route(
    "/api/messages/<sender>/<receiver>"
)
def messages(sender, receiver):

    sender = sender.lower()
    receiver = receiver.lower()

    if (
        sender not in users
        or receiver not in users
        or sender == receiver
    ):
        return jsonify(
            {
                "messages": []
            }
        )

    with lock:

        return jsonify(
            {
                "messages":
                    list(
                        get_conversation(
                            sender,
                            receiver
                        )
                    )
            }
        )


@app.route(
    "/api/reset",
    methods=["POST"]
)
def reset():

    global conversations
    global activity_log
    global pending_messages
    global last_quantum_result

    with lock:

        conversations = {}
        activity_log = []
        pending_messages = []

        last_quantum_result = {
            "status": "READY",
            "qber": 0,
            "errors": 0,
            "matching_bases": 0,
            "qubits": NUMBER_OF_QUBITS,
            "eve_active": eve_active
        }

        add_activity(
            "♻️ Quantum Veil session reset"
        )

        return jsonify(
            {
                "success": True
            }
        )


# ============================================================
# DASHBOARD HTML
# ============================================================

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width,initial-scale=1.0,viewport-fit=cover">

<title>QUANTUM VEIL</title>

<style>

*{
box-sizing:border-box
}

body{
margin:0;
font-family:Arial,sans-serif;
background:
radial-gradient(
circle at top left,
#172554,
#020617 50%,
#000
);
color:#fff;
min-height:100vh
}

.header{
padding:15px 20px;
border-bottom:1px solid #ffffff18;
background:#020617dd;
display:flex;
justify-content:space-between;
align-items:center;
position:sticky;
top:0;
z-index:5
}

.logo{
font-size:22px;
font-weight:900;
letter-spacing:2px
}

.logo span{
color:#67e8f9
}

.sub{
font-size:9px;
color:#94a3b8;
margin-top:3px
}

.eve{
border:0;
border-radius:20px;
padding:10px 14px;
background:#064e3b;
color:#a7f3d0;
font-weight:bold
}

.eve.on{
background:#7f1d1d;
color:#fecaca
}

.container{
max-width:1100px;
margin:auto;
padding:18px
}

.hero{
padding:24px;
border:1px solid #67e8f925;
border-radius:20px;
background:
linear-gradient(
135deg,
#0f172af5,
#082f4977
)
}

.hero h1{
margin:0;
font-size:clamp(28px,6vw,48px)
}

.hero p{
color:#94a3b8;
line-height:1.6
}

.title{
color:#cbd5e1;
margin:24px 0 12px
}


/* FIVE PROFILE CARDS */

.people{
display:grid;
grid-template-columns:repeat(5,1fr);
gap:12px
}

.person{
color:#fff;
text-decoration:none;
padding:16px;
border:1px solid #ffffff12;
border-radius:17px;
background:#0f172acc;
transition:.18s
}

.person:hover{
border-color:#67e8f966;
transform:translateY(-2px)
}

.avatar{
width:60px;
height:60px;
border-radius:50%;
overflow:hidden;
background:#164e63;
display:flex;
align-items:center;
justify-content:center;
font-size:26px;
margin-bottom:10px
}

.avatar img{
width:100%;
height:100%;
object-fit:cover
}

.name{
font-weight:900;
font-size:16px
}

.about{
color:#94a3b8;
font-size:11px;
margin-top:4px;
min-height:28px
}

.online{
color:#34d399;
font-size:10px;
margin-top:8px
}

.choose{
color:#67e8f9;
font-size:10px;
font-weight:bold;
margin-top:6px
}

.metrics{
margin-top:20px;
display:grid;
grid-template-columns:repeat(4,1fr);
gap:9px
}

.metric{
padding:14px;
border-radius:14px;
background:#0f172acc;
border:1px solid #ffffff0d
}

.label{
font-size:9px;
color:#94a3b8
}

.value{
font-size:22px;
font-weight:900;
margin-top:3px
}

.status{
margin-top:14px;
padding:14px;
border-radius:14px;
background:#064e3b55;
border:1px solid #34d39933
}

.status.danger{
background:#7f1d1d55;
border-color:#f8717133
}

.activity{
margin-top:18px
}

.item{
padding:8px 2px;
border-bottom:1px solid #ffffff0a;
font-size:11px;
color:#cbd5e1
}

@media(max-width:950px){

.people{
grid-template-columns:repeat(3,1fr)
}

}

@media(max-width:650px){

.people{
grid-template-columns:1fr 1fr
}

.metrics{
grid-template-columns:1fr 1fr
}

.container{
padding:12px
}

}

</style>

</head>

<body>

<div class="header">

<div>

<div class="logo">
⚛️ QUANTUM <span>VEIL</span>
</div>

<div class="sub">
BB84 QUANTUM KEY DISTRIBUTION • SECURE MESSAGING
</div>

</div>

<button
id="eveBtn"
class="eve"
onclick="toggleEve()">

🟢 EVE OFF

</button>

</div>


<div class="container">

<div class="hero">

<h1>
Quantum Secure Messaging
</h1>

<p>
First choose <b>who you are</b>.
Then choose who you want to chat with.
Every message attempts BB84 quantum key establishment.
If Eve interferes, QBER rises and the message is blocked.
</p>

</div>


<h3 class="title">
👤 Choose your identity
</h3>


<div
id="people"
class="people">
</div>


<div class="metrics">

<div class="metric">

<div class="label">
QUBITS
</div>

<div
id="qubits"
class="value">
200
</div>

</div>


<div class="metric">

<div class="label">
MATCHING BASES
</div>

<div
id="bases"
class="value">
—
</div>

</div>


<div class="metric">

<div class="label">
ERRORS
</div>

<div
id="errors"
class="value">
—
</div>

</div>


<div class="metric">

<div class="label">
QBER
</div>

<div
id="qber"
class="value">
0%
</div>

</div>

</div>


<div
id="status"
class="status">

🔐 Quantum channel ready.

</div>


<div class="activity">

<h3>
⚡ Quantum Activity
</h3>

<div id="activity">
</div>

</div>

</div>


<script>

let profiles={};

const esc=x=>
String(x??'')
.replaceAll('&','&amp;')
.replaceAll('<','&lt;')
.replaceAll('>','&gt;')
.replaceAll('"','&quot;')
.replaceAll("'","&#039;");


async function loadProfiles(){

try{

profiles=
await(
await fetch('/api/profiles')
).json();

let box=
document.getElementById('people');

box.innerHTML='';


for(
const [id,u]
of Object.entries(profiles)
){

let first=
Object.keys(profiles)
.find(x=>x!==id);

let a=
document.createElement('a');

a.className='person';

a.href=
`/chat/${id}/${first}`;

a.innerHTML=`

<div class="avatar">

${
u.photo
?
`<img src="${esc(u.photo)}">`
:
esc(u.emoji||'👤')
}

</div>

<div class="name">
${esc(u.name)}
</div>

<div class="about">
${esc(u.about)}
</div>

<div class="online">
● Online
</div>

<div class="choose">
Tap to enter as
${esc(u.name)}
→
</div>

`;

box.appendChild(a);

}

}catch(e){}

}


async function loadStatus(){

try{

let d=
await(
await fetch('/api/status')
).json();

let q=
d.last_quantum||{};


document.getElementById(
'qubits'
).textContent=
q.qubits??200;


document.getElementById(
'bases'
).textContent=
q.matching_bases??'—';


document.getElementById(
'errors'
).textContent=
q.errors??'—';


document.getElementById(
'qber'
).textContent=
(q.qber??0)+'%';


let button=
document.getElementById(
'eveBtn'
);

button.textContent=
d.eve_active
?
'🔴 EVE ON'
:
'🟢 EVE OFF';


button.classList.toggle(
'on',
!!d.eve_active
);


let status=
document.getElementById(
'status'
);

status.className=
'status'+
(d.eve_active?' danger':'');


status.textContent=
d.eve_active
?
'🚨 EVE IS INTERCEPTING THE QUANTUM CHANNEL'
:
'🔐 '+
(
q.status==='SECURE'
?
'QUANTUM CHANNEL SECURE'
:
'Quantum channel ready.'
);


document.getElementById(
'activity'
).innerHTML=
(d.activity||[])
.slice(0,8)
.map(
x=>
`<div class="item">
${esc(x.time)} · ${esc(x.text)}
</div>`
)
.join('');

}catch(e){}

}


async function toggleEve(){

try{

let d=
await(
await fetch('/api/status')
).json();


let r=
await(
await fetch(
'/api/eve',
{
method:'POST',
headers:{
'Content-Type':
'application/json'
},
body:
JSON.stringify({
active:!d.eve_active
})
}
)
).json();


if(
!r.eve_active &&
r.released
){

alert(
'🟢 EVE OFF\n\n'+
r.released+
' blocked message(s) were released.'
);

}

loadStatus();

}catch(e){

alert(
'Could not change Eve mode.'
);

}

}


loadProfiles();
loadStatus();

setInterval(
loadProfiles,
3000
);

setInterval(
loadStatus,
1500
);

</script>

</body>
</html>
"""


# ============================================================
# CHAT HTML
# ============================================================

CHAT_HTML = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width,initial-scale=1.0,viewport-fit=cover">

<title>
Quantum Veil Chat
</title>


<style>

*{
box-sizing:border-box
}

html,body{
margin:0;
width:100%;
height:100%;
background:#020617;
color:#fff;
font-family:Arial,sans-serif;
overflow:hidden
}

.app{
width:100%;
height:100dvh;
display:flex;
flex-direction:column
}


/* TOP BAR */

.top{
padding:9px 12px;
min-height:62px;
border-bottom:1px solid #ffffff10;
background:#0f172af5;
display:flex;
align-items:center;
gap:9px
}

.back{
color:#fff;
text-decoration:none;
font-size:24px;
padding:4px
}

.avatar{
width:42px;
height:42px;
border-radius:50%;
overflow:hidden;
background:#164e63;
display:flex;
align-items:center;
justify-content:center;
font-size:20px;
flex-shrink:0
}

.avatar img{
width:100%;
height:100%;
object-fit:cover
}

.headname{
font-weight:900;
font-size:15px
}

.headabout{
color:#34d399;
font-size:9px;
margin-top:3px;
max-width:55vw;
white-space:nowrap;
overflow:hidden;
text-overflow:ellipsis
}

.eve{
margin-left:auto;
border:0;
border-radius:18px;
padding:7px 10px;
background:#064e3b;
color:#a7f3d0;
font-size:10px;
font-weight:bold
}

.eve.on{
background:#7f1d1d;
color:#fecaca
}


/* IDENTITY */

.identity{
padding:6px 11px;
background:#0b1220;
border-bottom:1px solid #ffffff0a;
display:flex;
align-items:center;
font-size:10px
}

.identity b{
color:#67e8f9;
margin-left:4px
}

.profile{
margin-left:auto;
border:0;
background:#1e293b;
color:#fff;
border-radius:14px;
padding:6px 9px;
font-size:9px
}


/* OTHER PEOPLE */

.partners{
display:flex;
gap:7px;
padding:7px 9px;
background:#0f172a;
border-bottom:1px solid #ffffff0a;
overflow-x:auto
}

.partner{
display:flex;
align-items:center;
gap:5px;
padding:6px 9px;
border-radius:17px;
background:#172033;
color:#cbd5e1;
text-decoration:none;
font-size:10px;
flex:0 0 auto
}

.partner.selected{
background:#075985;
color:#fff
}

.mini{
width:24px;
height:24px;
border-radius:50%;
overflow:hidden;
background:#164e63;
display:flex;
align-items:center;
justify-content:center
}

.mini img{
width:100%;
height:100%;
object-fit:cover
}


/* MESSAGES */

.messages{
flex:1;
min-height:0;
overflow-y:auto;
padding:12px;
display:flex;
flex-direction:column;
gap:7px
}

.day{
align-self:center;
color:#64748b;
font-size:8px;
background:#ffffff0a;
padding:5px 9px;
border-radius:14px
}

.msg{
max-width:min(520px,82%);
padding:8px 10px 5px;
border-radius:14px;
font-size:14px;
line-height:1.4;
white-space:pre-wrap;
overflow-wrap:anywhere
}

.sent{
align-self:flex-end;
background:#075985;
border-bottom-right-radius:4px
}

.received{
align-self:flex-start;
background:#1e293b;
border-bottom-left-radius:4px
}

.system{
align-self:center;
max-width:92%;
text-align:center;
background:#7f1d1d55;
border:1px solid #f8717133;
color:#fecaca
}

.released{
border:1px solid #34d39955
}

.time{
display:block;
text-align:right;
margin-top:3px;
font-size:8px;
color:#94a3b8
}

.msgstatus{
display:block;
text-align:right;
font-size:8px;
color:#67e8f9;
margin-top:2px
}


/* QUANTUM STATUS */

.quantum{
display:flex;
gap:13px;
overflow-x:auto;
white-space:nowrap;
padding:6px 10px;
background:#020617;
border-top:1px solid #ffffff0a;
color:#94a3b8;
font-size:9px
}

.secure{
color:#34d399
}

.danger{
color:#f87171
}


/* INPUT */

.inputbar{
display:flex;
gap:7px;
padding:8px 9px;
padding-bottom:
max(8px,env(safe-area-inset-bottom));
background:#0f172a;
border-top:1px solid #ffffff0d
}

input.msginput{
min-width:0;
flex:1;
border:0;
outline:0;
border-radius:22px;
padding:11px 14px;
background:#1e293b;
color:#fff;
font-size:16px
}

button.send{
width:44px;
height:44px;
border:0;
border-radius:50%;
background:#06b6d4;
color:#001018;
font-size:18px;
font-weight:900
}


/* PROFILE MODAL */

.modal{
display:none;
position:fixed;
inset:0;
z-index:10;
background:#000c;
align-items:center;
justify-content:center;
padding:15px
}

.modal.show{
display:flex
}

.box{
width:min(430px,100%);
background:#0f172a;
border:1px solid #67e8f933;
border-radius:20px;
padding:18px
}

.field{
margin-top:11px
}

.field label{
display:block;
color:#94a3b8;
font-size:9px;
margin-bottom:4px
}

.field input,
.field textarea{
width:100%;
border:1px solid #ffffff14;
background:#020617;
color:#fff;
border-radius:9px;
padding:9px;
font:inherit;
outline:0
}

.field textarea{
min-height:65px
}

.preview{
width:70px;
height:70px;
border-radius:50%;
overflow:hidden;
background:#164e63;
display:flex;
align-items:center;
justify-content:center;
font-size:27px;
margin-bottom:8px
}

.preview img{
width:100%;
height:100%;
object-fit:cover
}

.actions{
display:flex;
gap:7px;
margin-top:14px
}

.actions button{
flex:1;
border:0;
border-radius:9px;
padding:10px;
font-weight:bold
}

.cancel{
background:#1e293b;
color:#fff
}

.save{
background:#06b6d4;
color:#001018
}


@media(min-width:800px){

.app{
max-width:900px;
margin:auto;
border-left:1px solid #ffffff08;
border-right:1px solid #ffffff08
}

}

</style>

</head>


<body>


<div class="app">


<!-- TOP -->

<div class="top">

<a
class="back"
href="/">

←

</a>


<div
id="chatAvatar"
class="avatar">

👤

</div>


<div>

<div
id="chatName"
class="headname">

Loading…

</div>


<div
id="chatAbout"
class="headabout">

● Online

</div>

</div>


<button
id="eveBtn"
class="eve"
onclick="toggleEve()">

🟢 EVE OFF

</button>

</div>


<!-- CURRENT USER -->

<div class="identity">

👤 You are:

<b id="myName">
{{ current_user|title }}
</b>

<button
class="profile"
onclick="openProfile()">

Edit profile

</button>

</div>


<!-- OTHER PROFILES -->

<div
id="partners"
class="partners">
</div>


<!-- MESSAGES -->

<div
id="messages"
class="messages">
</div>


<!-- QUANTUM DATA -->

<div class="quantum">

<span>
⚛️ Qubits:
<b id="qQubits">200</b>
</span>

<span>
Bases:
<b id="qBases">—</b>
</span>

<span>
Errors:
<b id="qErrors">—</b>
</span>

<span>
QBER:
<b id="qQber">0%</b>
</span>

<span
id="qSecurity"
class="secure">

🔐 READY

</span>

</div>


<!-- INPUT -->

<div class="inputbar">

<input
id="messageInput"
class="msginput"
maxlength="2000"
placeholder="Message securely…"
autocomplete="off">

<button
class="send"
onclick="sendMessage()">

➤

</button>

</div>


</div>


<!-- PROFILE EDIT MODAL -->

<div
id="profileModal"
class="modal">


<div class="box">

<h2>
👤 Edit Profile
</h2>


<div
id="preview"
class="preview">

👤

</div>


<div class="field">

<label>
Profile picture
</label>

<input
id="photoInput"
type="file"
accept="image/*">

</div>


<div class="field">

<label>
Name
</label>

<input
id="profileName"
maxlength="40">

</div>


<div class="field">

<label>
About
</label>

<textarea
id="profileAbout"
maxlength="100">
</textarea>

</div>


<div class="actions">

<button
class="cancel"
onclick="closeProfile()">

Cancel

</button>


<button
class="save"
onclick="saveProfile()">

Save Profile

</button>

</div>

</div>

</div>


<script>


const CURRENT_USER =
{{ current_user|tojson }};

const SELECTED_USER =
{{ selected_user|tojson }};


let profiles = {};

let photo = "";


const esc = x =>
String(x ?? '')
.replaceAll('&','&amp;')
.replaceAll('<','&lt;')
.replaceAll('>','&gt;')
.replaceAll('"','&quot;')
.replaceAll("'","&#039;");


function av(
u,
c='avatar'
){

return u.photo

?
`<div class="${c}">
<img src="${esc(u.photo)}">
</div>`

:

`<div class="${c}">
${esc(u.emoji||'👤')}
</div>`;

}


/* LOAD ALL FIVE PEOPLE */

async function loadProfiles(){

try{

profiles =
await(
await fetch(
'/api/profiles'
)
).json();


const box =
document.getElementById(
'partners'
);

box.innerHTML='';


for(
const [id,u]
of Object.entries(profiles)
){

if(id===CURRENT_USER)
continue;


const a =
document.createElement(
'a'
);


a.className =
'partner' +
(
id===SELECTED_USER
?
' selected'
:
''
);


a.href =
`/chat/${CURRENT_USER}/${id}`;


a.innerHTML =
av(u,'mini') +
`<span>${esc(u.name)}</span>`;


box.appendChild(a);

}


updateHeader();


}
catch(e){}

}


/* UPDATE CHAT HEADER */

function updateHeader(){

const u =
profiles[SELECTED_USER];

const me =
profiles[CURRENT_USER];


if(!u || !me)
return;


document.getElementById(
'chatName'
).textContent =
u.name;


document.getElementById(
'chatAbout'
).textContent =
'● Online · ' + u.about;


document.getElementById(
'myName'
).textContent =
me.name;


document.getElementById(
'chatAvatar'
).innerHTML =

u.photo

?

`<img src="${esc(u.photo)}">`

:

esc(u.emoji||'👤');

}


/* LOAD MESSAGES */

async function loadMessages(){

try{

const d =
await(
await fetch(
`/api/messages/${CURRENT_USER}/${SELECTED_USER}`
)
).json();


renderMessages(
d.messages || []
);


}
catch(e){}

}


/* DISPLAY MESSAGES */

function renderMessages(list){

const box =
document.getElementById(
'messages'
);


const nearBottom =
box.scrollHeight -
box.scrollTop -
box.clientHeight < 100;


box.innerHTML =
'<div class="day">' +
'Quantum Veil secure session' +
'</div>';


for(
const m of list
){

/*
Blocked messages are not displayed as
normal delivered messages.
The security alert remains visible.
*/

if(
m.status === 'BLOCKED'
)
continue;


const d =
document.createElement(
'div'
);


d.className =
'msg ' +

(
m.system
?
'system'
:
m.sender === CURRENT_USER
?
'sent'
:
'received'
) +

(
m.status === 'RELEASED'
?
' released'
:
''
);


let label = '';


if(
m.status === 'RELEASED'
){

label =
'🟢 RELEASED · channel restored';

}
else if(
m.status === 'ALERT'
){

label =
'SECURITY ALERT';

}
else if(
m.status === 'DELIVERED'
){

label =
'🔐 DELIVERED';

}


d.innerHTML =

`${esc(m.text)}

<span class="time">
${esc(m.time)}
</span>

<span class="msgstatus">
${esc(label)}
</span>`;


box.appendChild(d);

}


if(nearBottom)
box.scrollTop =
box.scrollHeight;

}


/* QUANTUM STATUS */

function updateQuantum(
q,
eve
){

document.getElementById(
'qQubits'
).textContent =
q.qubits ?? 200;


document.getElementById(
'qBases'
).textContent =
q.matching_bases ?? '—';


document.getElementById(
'qErrors'
).textContent =
q.errors ?? '—';


document.getElementById(
'qQber'
).textContent =
(q.qber ?? 0) + '%';


const security =
document.getElementById(
'qSecurity'
);


security.className =
eve
?
'danger'
:
'secure';


security.textContent =

eve

?

'🚨 EVE ACTIVE'

:

q.status === 'SECURE'

?

'🔐 SECURE'

:

'⚛️ READY';

}


/* LOAD EVE STATUS */

async function loadStatus(){

try{

const d =
await(
await fetch(
'/api/status'
)
).json();


const q =
d.last_quantum || {};


const button =
document.getElementById(
'eveBtn'
);


button.textContent =
d.eve_active
?
'🔴 EVE ON'
:
'🟢 EVE OFF';


button.classList.toggle(
'on',
!!d.eve_active
);


updateQuantum(
q,
d.eve_active
);


}
catch(e){}

}


/* TOGGLE EVE */

async function toggleEve(){

try{

const d =
await(
await fetch(
'/api/status'
)
).json();


const r =
await(
await fetch(
'/api/eve',
{
method:'POST',

headers:{
'Content-Type':
'application/json'
},

body:
JSON.stringify({
active:
!d.eve_active
})

}
)
).json();


if(
!r.eve_active &&
r.released
){

alert(
'🟢 EVE OFF\n\n' +
r.released +
' blocked message(s) ' +
'released automatically.'
);

}


await loadStatus();

await loadMessages();


}
catch(e){

alert(
'Could not change Eve mode.'
);

}

}


/* SEND MESSAGE */

async function sendMessage(){

const input =
document.getElementById(
'messageInput'
);


const text =
input.value.trim();


if(!text)
return;


input.disabled = true;


try{

const r =
await fetch(
'/api/send',
{
method:'POST',

headers:{
'Content-Type':
'application/json'
},

body:
JSON.stringify({
sender:CURRENT_USER,
receiver:SELECTED_USER,
message:text
})
}
);


const d =
await r.json();


if(!r.ok){

alert(
d.error ||
'Could not send'
);

return;

}


input.value='';


await loadMessages();


updateQuantum(
d.quantum || {},
d.eve_active
);


const box =
document.getElementById(
'messages'
);

box.scrollTop =
box.scrollHeight;


}
catch(e){

alert(
'Connection error.'
);

}
finally{

input.disabled=false;

input.focus();

}

}


/* ENTER TO SEND */

document.getElementById(
'messageInput'
).addEventListener(
'keydown',
e => {

if(
e.key === 'Enter' &&
!e.shiftKey
){

e.preventDefault();

sendMessage();

}

}
);


/* PROFILE EDIT */

function openProfile(){

const me =
profiles[CURRENT_USER];


if(!me)
return;


document.getElementById(
'profileName'
).value =
me.name;


document.getElementById(
'profileAbout'
).value =
me.about;


photo =
me.photo || '';


document.getElementById(
'preview'
).innerHTML =

photo

?

`<img src="${esc(photo)}">`

:

esc(me.emoji||'👤');


document.getElementById(
'profileModal'
).classList.add(
'show'
);

}


function closeProfile(){

document.getElementById(
'profileModal'
).classList.remove(
'show'
);

}


/* PROFILE PHOTO */

document.getElementById(
'photoInput'
).addEventListener(
'change',
e => {

const file =
e.target.files[0];


if(!file)
return;


if(
file.size > 2200000
){

alert(
'Please choose an image smaller than 2 MB.'
);

e.target.value='';

return;

}


const reader =
new FileReader();


reader.onload = () => {

photo =
reader.result;


document.getElementById(
'preview'
).innerHTML =
`<img src="${esc(photo)}">`;

};


reader.readAsDataURL(
file
);

}
);


/* SAVE PROFILE */

async function saveProfile(){

const name =
document.getElementById(
'profileName'
).value.trim();


const about =
document.getElementById(
'profileAbout'
).value.trim();


if(!name){

alert(
'Name cannot be empty.'
);

return;

}


try{

const r =
await fetch(
`/api/profile/${CURRENT_USER}`,
{
method:'POST',

headers:{
'Content-Type':
'application/json'
},

body:
JSON.stringify({
name:name,
about:about,
photo:photo
})
}
);


const d =
await r.json();


if(!d.success){

alert(
d.error ||
'Could not save'
);

return;

}


closeProfile();

await loadProfiles();


}
catch(e){

alert(
'Could not save profile.'
);

}

}


/* START */

loadProfiles();

loadMessages();

loadStatus();


setInterval(
loadProfiles,
3000
);

setInterval(
loadMessages,
1800
);

setInterval(
loadStatus,
1500
);

</script>


</body>
</html>
"""


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "⚛️  QUANTUM VEIL — "
        "BB84 SECURE MESSAGING"
    )

    print("=" * 60)

    print(
        "Local: "
        "http://127.0.0.1:5000"
    )

    print(
        "LAN:   "
        "http://<YOUR-LAN-IP>:5000"
    )

    print(
        "Profiles:",
        ", ".join(users.keys())
    )

    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
    