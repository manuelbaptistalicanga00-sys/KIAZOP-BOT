"""Bot de atendimento com IA para WhatsApp (Cloud API) + Claude.
Responde clientes, tira dúvidas, recolhe agendamentos e passa para humano.
As informações do negócio vêm de negocio.json (editar = bot atualizado)."""
import os, json, re, sqlite3, hmac, hashlib, html, secrets, httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool
from anthropic import Anthropic

WA_TOKEN = os.environ["WA_TOKEN"]
WA_PHONE_ID = os.environ["WA_PHONE_ID"]
VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
OWNER_PHONE = os.environ.get("OWNER_PHONE", "")   # número do dono, com código do país
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")
APP_SECRET = os.environ.get("APP_SECRET", "")  # segredo da app Meta: garante que o webhook vem da Meta
LIMITE_HORA = int(os.environ.get("LIMITE_HORA", "30"))  # máx. mensagens por cliente por hora
DB_PATH = os.environ.get("DB_PATH", "bot.db")

client = Anthropic()  # usa ANTHROPIC_API_KEY
app = FastAPI()
db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.executescript("""
create table if not exists msgs(id integer primary key, phone text, role text, text text, ts default current_timestamp);
create table if not exists bookings(id integer primary key, phone text, nome text, servico text, data_hora text, ts default current_timestamp);
create table if not exists paused(phone text primary key);
create table if not exists seen(id text primary key);
""")


def sistema() -> str:
    n = json.load(open("negocio.json", encoding="utf-8"))
    return f"""És o assistente de atendimento de {n['nome']} no WhatsApp. Tom: {n['tom']}.
Responde sempre no idioma do cliente, em mensagens curtas (máx. 3 frases).
Usa APENAS as informações abaixo. Se não souberes, diz que vais passar a um colega.

INFORMAÇÕES DO NEGÓCIO:
{json.dumps(n['informacoes'], ensure_ascii=False, indent=1)}

REGRAS:
- Para marcar, pede: nome, serviço e data/hora preferida. Quando tiveres os três, confirma ao cliente e acrescenta no FIM da resposta, numa linha:
[AGENDAMENTO]{{"nome":"...","servico":"...","data_hora":"..."}}
- Se o cliente estiver zangado, pedir pessoa, ou for assunto médico/jurídico/pagamento, responde que vais passar a um humano e acrescenta no fim: [HUMANO]
- Nunca inventes preços, horários ou promoções.
- {n.get('extra', '')}"""


def enviar(phone: str, texto: str):
    httpx.post(
        f"https://graph.facebook.com/v21.0/{WA_PHONE_ID}/messages",
        headers={"Authorization": f"Bearer {WA_TOKEN}"},
        json={"messaging_product": "whatsapp", "to": phone, "type": "text", "text": {"body": texto}},
        timeout=20,
    )


def historico(phone: str):
    rows = db.execute("select role,text from msgs where phone=? order by id desc limit 20", (phone,)).fetchall()[::-1]
    while rows and rows[0][0] != "user":
        rows.pop(0)
    return [{"role": r, "content": t} for r, t in rows]


def responder(phone: str, texto: str):
    db.execute("insert into msgs(phone,role,text) values(?,?,?)", (phone, "user", texto))
    db.commit()
    if db.execute("select 1 from paused where phone=?", (phone,)).fetchone():
        return  # humano assumiu esta conversa
    n = db.execute("select count(*) from msgs where phone=? and role='user' and ts>datetime('now','-1 hour')", (phone,)).fetchone()[0]
    if n > LIMITE_HORA:
        return  # proteção contra spam e custos
    try:
        r = client.messages.create(model=MODEL, max_tokens=500, system=sistema(), messages=historico(phone))
        bruto = r.content[0].text
    except Exception as e:
        print('erro IA:', e)
        enviar(phone, 'Obrigado pela mensagem! Um colega vai responder em breve.')
        if OWNER_PHONE:
            enviar(OWNER_PHONE, f'A IA falhou ao responder {phone}. Verifique.')
        return
    limpo = re.sub(r"\[(AGENDAMENTO|HUMANO)\].*", "", bruto, flags=re.S).strip()

    m = re.search(r"\[AGENDAMENTO\](\{.*?\})", bruto, flags=re.S)
    if m:
        try:
            d = json.loads(m.group(1))
            db.execute("insert into bookings(phone,nome,servico,data_hora) values(?,?,?,?)",
                       (phone, d.get("nome"), d.get("servico"), d.get("data_hora")))
            if OWNER_PHONE:
                enviar(OWNER_PHONE, f"Novo agendamento: {d.get('nome')} | {d.get('servico')} | {d.get('data_hora')} | {phone}")
        except Exception:
            pass
    if "[HUMANO]" in bruto:
        db.execute("insert or ignore into paused(phone) values(?)", (phone,))
        if OWNER_PHONE:
            enviar(OWNER_PHONE, f"Cliente {phone} precisa de atendimento humano.")
    db.execute("insert into msgs(phone,role,text) values(?,?,?)", (phone, "assistant", limpo))
    db.commit()
    enviar(phone, limpo)


@app.get("/webhook")
def verificar(request: Request):
    q = request.query_params
    if q.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(q.get("hub.challenge"), media_type="text/plain")
    return Response(status_code=403)


def processar(body):
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                if db.execute("select 1 from seen where id=?", (msg["id"],)).fetchone():
                    continue  # a Meta repete envios; ignora duplicados
                db.execute("insert into seen(id) values(?)", (msg["id"],))
                db.commit()
                if msg.get("type") == "text":
                    responder(msg["from"], msg["text"]["body"])
                else:
                    enviar(msg["from"], "Por agora só consigo ler mensagens de texto. Pode escrever a sua dúvida?")


@app.post("/webhook")
async def receber(request: Request):
    raw = await request.body()
    if APP_SECRET:
        esperado = "sha256=" + hmac.new(APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(esperado, request.headers.get("x-hub-signature-256", "")):
            return Response(status_code=403)
    try:
        await run_in_threadpool(processar, json.loads(raw))
    except Exception as e:
        print("erro:", e)
    return {"ok": True}


@app.get("/agendamentos")
def agendamentos(key: str = ""):
    if not ADMIN_KEY or key != ADMIN_KEY:
        return Response(status_code=403)
    rows = db.execute("select ts,nome,servico,data_hora,phone from bookings order by id desc limit 200").fetchall()
    return [dict(zip(["registado", "nome", "servico", "data_hora", "telefone"], r)) for r in rows]


@app.get("/retomar/{phone}")
def retomar(phone: str, key: str = ""):
    if not ADMIN_KEY or key != ADMIN_KEY:
        return Response(status_code=403)
    db.execute("delete from paused where phone=?", (phone,))
    db.commit()
    return {"ok": True}


def _auth(key):
    return bool(ADMIN_KEY) and secrets.compare_digest(key or "", ADMIN_KEY)


@app.get("/pausar/{phone}")
def pausar(phone: str, key: str = ""):
    if not _auth(key):
        return Response(status_code=403)
    db.execute("insert or ignore into paused(phone) values(?)", (phone,))
    db.commit()
    return RedirectResponse(f"/painel?key={key}", status_code=303)


@app.get("/liberar/{phone}")
def liberar(phone: str, key: str = ""):
    if not _auth(key):
        return Response(status_code=403)
    db.execute("delete from paused where phone=?", (phone,))
    db.commit()
    return RedirectResponse(f"/painel?key={key}", status_code=303)


@app.get("/painel", response_class=HTMLResponse)
def painel(key: str = ""):
    if not _auth(key):
        return HTMLResponse("Acesso negado", status_code=403)
    k, e = html.escape(key), html.escape
    ag = "".join("<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>" for r in db.execute(
        "select ts,nome,servico,data_hora,phone from bookings order by id desc limit 100"))
    conv = ""
    for (phone,) in db.execute("select phone from msgs group by phone order by max(id) desc limit 20").fetchall():
        ult = db.execute("select role,text from msgs where phone=? order by id desc limit 1", (phone,)).fetchone()
        pausado = db.execute("select 1 from paused where phone=?", (phone,)).fetchone()
        acao = (f"<a href='/liberar/{e(phone)}?key={k}'>reativar bot</a>" if pausado
                else f"<a href='/pausar/{e(phone)}?key={k}'>assumir (pausar bot)</a>")
        conv += f"<tr><td>{e(phone)}</td><td>{e(ult[0])}: {e(ult[1][:140])}</td><td>{acao}</td></tr>"
    total = db.execute("select count(distinct phone) from msgs").fetchone()[0]
    return (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<style>body{{font-family:system-ui;padding:12px}}td,th{{border-bottom:1px solid #ddd;padding:8px;text-align:left;vertical-align:top}}</style>"
            f"<h2>Painel do Atendente IA</h2><p>Clientes atendidos: <b>{total}</b></p>"
            f"<h3>Agendamentos</h3><table><tr><th>Registo</th><th>Nome</th><th>Serviço</th><th>Data/hora</th><th>Telefone</th></tr>{ag}</table>"
            f"<h3>Conversas recentes</h3><table><tr><th>Cliente</th><th>Última mensagem</th><th>Ação</th></tr>{conv}</table>")
