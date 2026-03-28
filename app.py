from flask import Flask, request, redirect, render_template
import time, os, json

app = Flask(__name__)

DB_FILE = "db.json"
KEYS_FILE = "keys.txt"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    return json.load(open(DB_FILE))

def save_db(db):
    json.dump(db, open(DB_FILE, "w"), indent=4)

def pegar_key():
    if not os.path.exists(KEYS_FILE):
        return None
    with open(KEYS_FILE, "r") as f:
        keys = f.read().splitlines()
    if not keys:
        return None
    key = keys[0]
    with open(KEYS_FILE, "w") as f:
        f.write("\n".join(keys[1:]))
    return key

@app.route("/gerar/<code>")
def gerar(code):
    db = load_db()
    db[code] = {
        "ip": None,
        "ua": None,
        "t1": None,
        "t2": None,
        "step2": False,
        "verified": False
    }
    save_db(db)
    return {"link": f"https://SEU_DOMINIO/r/{code}"}

@app.route("/r/<code>")
def step1(code):
    db = load_db()
    d = db.get(code)
    if not d:
        return "Erro"
    d["ip"] = request.remote_addr
    d["ua"] = request.headers.get("User-Agent")
    d["t1"] = time.time()
    save_db(db)
    return redirect("https://alpharede.com/abc123")

@app.route("/step2")
def step2():
    db = load_db()
    ip = request.remote_addr
    for code, d in db.items():
        if d["ip"] == ip and not d["step2"]:
            d["t2"] = time.time()
            d["step2"] = True
            save_db(db)
            return redirect("https://alpharede.com/xyz789")
    return "Sessão inválida"

@app.route("/final")
def final():
    db = load_db()
    ip = request.remote_addr
    for code, d in db.items():
        if d["ip"] == ip and d["step2"]:
            if request.headers.get("User-Agent") != d["ua"]:
                return "Suspeito"
            tempo_total = time.time() - d["t1"]
            if tempo_total < 15:
                return "Bypass detectado"
            if d["t2"] - d["t1"] < 5:
                return "Pulou etapa"
            key = pegar_key()
            d["verified"] = True
            save_db(db)
            return render_template("final.html", key=key)
    return "Acesso inválido"

@app.route("/status/<code>")
def status(code):
    db = load_db()
    d = db.get(code)
    if not d:
        return {"ok": False}
    return {"ok": d["verified"]}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
