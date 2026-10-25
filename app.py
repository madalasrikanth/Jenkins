import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB_PATH = os.getenv("DB_PATH", "bank.db")

PAGE = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Demo Banking System</title><style>
body{font-family:Arial,sans-serif;max-width:760px;margin:30px auto;padding:0 16px;background:#f5f7fb;color:#172033}
section{background:white;padding:18px;margin:14px 0;border-radius:12px;box-shadow:0 2px 10px #0001}
input,button{padding:10px;margin:5px 0;max-width:100%;box-sizing:border-box}input{width:100%;border:1px solid #ccd2dc;border-radius:6px}
button{cursor:pointer;border:0;border-radius:6px;background:#155eef;color:white}pre{white-space:pre-wrap;overflow-wrap:anywhere}
</style></head><body><h1>Demo Banking Management System</h1>
<p>Training/demo application only. Do not use real banking or personal data.</p>
<section><h2>Create account</h2><input id="name" placeholder="Account holder name"><button onclick="createAccount()">Create account</button></section>
<section><h2>Deposit / Withdraw</h2><input id="account" type="number" placeholder="Account number"><input id="amount" type="number" min="0.01" step="0.01" placeholder="Amount">
<button onclick="money('deposit')">Deposit</button><button onclick="money('withdraw')">Withdraw</button><button onclick="balance()">Check balance</button><button onclick="history()">Transaction history</button></section>
<section><h2>Result</h2><pre id="result">Ready.</pre></section>
<script>
async function call(url,method='GET',body=null){const opts={method,headers:{'Content-Type':'application/json'}};if(body)opts.body=JSON.stringify(body);const r=await fetch(url,opts);const data=await r.json();document.getElementById('result').textContent=JSON.stringify(data,null,2);}
async function createAccount(){await call('/api/accounts','POST',{name:document.getElementById('name').value});}
async function money(action){await call('/api/'+action,'POST',{account_no:Number(document.getElementById('account').value),amount:Number(document.getElementById('amount').value)});}
async function balance(){await call('/api/accounts/'+Number(document.getElementById('account').value));}
async function history(){await call('/api/accounts/'+Number(document.getElementById('account').value)+'/transactions');}
</script></body></html>
"""

def connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS accounts(
            account_no INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0 CHECK(balance >= 0))""")
        db.execute("""CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_no INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(account_no) REFERENCES accounts(account_no))""")

@app.get("/")
def home():
    return render_template_string(PAGE)

@app.get("/health")
def health():
    return jsonify(status="ok"), 200

@app.post("/api/accounts")
def create_account():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name or len(name) > 100:
        return jsonify(error="Provide a name between 1 and 100 characters."), 400
    with connect() as db:
        cur = db.execute("INSERT INTO accounts(name) VALUES (?)", (name,))
        account_no = cur.lastrowid
    return jsonify(message="Account created", account_no=account_no, name=name, balance=0.0), 201

@app.get("/api/accounts/<int:account_no>")
def get_account(account_no):
    with connect() as db:
        row = db.execute("SELECT account_no,name,balance FROM accounts WHERE account_no=?", (account_no,)).fetchone()
    if row is None:
        return jsonify(error="Account not found"), 404
    return jsonify(dict(row))

def apply_transaction(kind):
    data = request.get_json(silent=True) or {}
    try:
        account_no = int(data.get("account_no"))
        amount = round(float(data.get("amount")), 2)
    except (TypeError, ValueError):
        return jsonify(error="account_no and numeric amount are required"), 400
    if amount <= 0 or amount > 10000000:
        return jsonify(error="Amount must be greater than 0 and no more than 10,000,000"), 400
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        account = db.execute("SELECT balance FROM accounts WHERE account_no=?", (account_no,)).fetchone()
        if account is None:
            db.rollback()
            return jsonify(error="Account not found"), 404
        balance = float(account["balance"])
        if kind == "withdraw" and balance < amount:
            db.rollback()
            return jsonify(error="Insufficient balance", balance=balance), 400
        new_balance = balance + amount if kind == "deposit" else balance - amount
        db.execute("UPDATE accounts SET balance=? WHERE account_no=?", (round(new_balance, 2), account_no))
        db.execute("INSERT INTO transactions(account_no,transaction_type,amount) VALUES (?,?,?)",
                   (account_no, kind.title(), amount))
    return jsonify(message=f"{kind.title()} successful", account_no=account_no, balance=round(new_balance, 2))

@app.post("/api/deposit")
def deposit():
    return apply_transaction("deposit")

@app.post("/api/withdraw")
def withdraw():
    return apply_transaction("withdraw")

@app.get("/api/accounts/<int:account_no>/transactions")
def transactions(account_no):
    with connect() as db:
        exists = db.execute("SELECT 1 FROM accounts WHERE account_no=?", (account_no,)).fetchone()
        if not exists:
            return jsonify(error="Account not found"), 404
        rows = db.execute("SELECT transaction_type,amount,created_at FROM transactions WHERE account_no=? ORDER BY id DESC",
                          (account_no,)).fetchall()
    return jsonify(transactions=[dict(row) for row in rows])

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
