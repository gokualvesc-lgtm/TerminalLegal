import json
import os
import random

from flask import Flask, jsonify, redirect, render_template, request

app = Flask(__name__)

# ---------------------------------------------------------------- terminal
# Senhas aceitas para desativar o lockdown (comparadas sem espaços, barras ou maiúsculas)
SENHAS_VALIDAS = {"TEC-047", "TEC047", "09121988"}

# Endereço da fábrica revelado nas pistas. TROQUE pelo endereço da sua lore.
ENDERECO_FABRICA = "Av. das Fábricas, 1300, Distrito Industrial"

# Estado do terminal: None | "desbloqueado" | "redefinido"
estado = {"modo": None}


def normalizar(texto: str) -> str:
    return texto.strip().upper().replace(" ", "").replace("/", "")


@app.get("/")
def terminal():
    return render_template("terminal.html", modo=estado["modo"], endereco=ENDERECO_FABRICA)


@app.get("/lucker")
def lucker():
    return render_template("lucker.html", endereco=ENDERECO_FABRICA)


@app.post("/api/desbloquear")
def desbloquear():
    if estado["modo"] is not None:
        return jsonify(ok=False, erro="Terminal já utilizado."), 409
    senha = normalizar((request.get_json(silent=True) or {}).get("senha", ""))
    if senha not in SENHAS_VALIDAS:
        return jsonify(ok=False, erro="Credencial incorreta."), 401
    estado["modo"] = "desbloqueado"
    return jsonify(ok=True)


@app.post("/api/redefinir")
def redefinir():
    if estado["modo"] is not None:
        return jsonify(ok=False, erro="Terminal já utilizado."), 409
    estado["modo"] = "redefinido"
    return jsonify(ok=True)


@app.get("/mestre/reiniciar")
def reiniciar():
    estado["modo"] = None
    return redirect("/")


# -------------------------------------------------------------------- mapa
# PIN da área do mestre. Troque: defina a variável de ambiente MESTRE_PIN.
MESTRE_PIN = os.environ.get("MESTRE_PIN", "1234")

ANDARES = [{"id": "terreo", "nome": "Térreo"}, {"id": "andar1", "nome": "1º andar"}]


def sala(id, andar, nome, x, y, w, h, tipo, notas=""):
    # tipo: "territorio" (animatrônico), "chave" (ponto-chave) ou "neutro"
    return dict(id=id, andar=andar, nome=nome, x=x, y=y, w=w, h=h, tipo=tipo, notas=notas)


SALAS = [
    sala("linha", "terreo", "Linha de montagem", 40, 40, 290, 110, "territorio", "Tio Gancho (EXP-017) pendurado nos trilhos do teto, caça pelo som."),
    sala("oficina", "terreo", "Oficina", 336, 40, 150, 110, "neutro", "Peças e sucata. Bom lugar para achar pilhas e ferramentas."),
    sala("doca", "terreo", "Doca de cargas", 492, 40, 148, 110, "chave", "Acesso alternativo ao prédio."),
    sala("corredor_t", "terreo", "Corredor técnico", 40, 156, 470, 52, "neutro", "Liga todas as alas do térreo."),
    sala("escadab", "terreo", "Escada B", 516, 156, 124, 52, "chave", "Desce ao subsolo. Selada até religarem a energia no 1º andar."),
    sala("lanchonete", "terreo", "Lanchonete", 40, 214, 170, 120, "territorio", "Pipoca (EXP-014) imita frases de funcionários pelo alto-falante."),
    sala("salao", "terreo", "Salão do tour", 216, 214, 200, 120, "neutro", "Palco e cartazes antigos com o mascote Rock (pista)."),
    sala("escadaa_t", "terreo", "Escada A e elevador", 422, 214, 218, 120, "chave", "Sobem ao 1º andar. Elevador sem energia."),
    sala("sagao", "terreo", "Saguão", 40, 340, 420, 112, "territorio", "Sol (EXP-011) segue a luz, fica junto da luz de emergência. Foto de grupo de 1992 na parede (pista)."),
    sala("entrada", "terreo", "Entrada principal", 466, 340, 174, 112, "chave", "Travas soltas, sem energia."),
    sala("controle", "andar1", "Sala de controle", 40, 40, 170, 110, "chave", "Painel de energia. Religar libera a Escada B, tranca a saída e acorda os animatrônicos (ação irreversível)."),
    sala("celas", "andar1", "Celas de experimento", 216, 40, 204, 110, "territorio", "Os Gêmeos (EXP-009 e 010) se movem em sincronia: se um vê, o outro sabe."),
    sala("cela003", "andar1", "Cela 003", 426, 40, 90, 110, "chave", "Aberta, vazia, com maçaneta instalada por dentro (pista difícil sobre o Kcor)."),
    sala("camara", "andar1", "Câmara fria", 522, 40, 118, 110, "neutro", "Porta trancada: material orgânico, refrigerado. Isca para a sessão 5."),
    sala("corredor_1", "andar1", "Corredor central", 40, 156, 600, 52, "neutro", "Liga todas as salas do 1º andar."),
    sala("escritorios", "andar1", "Escritórios", 40, 214, 190, 120, "neutro", "Administração."),
    sala("fundadores", "andar1", "Sala dos fundadores", 236, 214, 200, 120, "neutro", "Trancada com código (a definir)."),
    sala("reunioes", "andar1", "Sala de reuniões", 442, 214, 198, 120, "neutro", "Sala de treinamento."),
    sala("escadaa_1", "andar1", "Escada A e elevador", 40, 340, 200, 112, "chave", "Descem ao térreo."),
    sala("dutos", "andar1", "Dutos de ventilação", 246, 340, 394, 112, "territorio", "Miúdo (EXP-020) recolhe pilhas. Não ataca."),
]


# Marcadores arrastáveis: (id, nome, andar, x, y, visível aos jogadores, tipo)
TOKENS = [
    ("grupo", "Grupo", "terreo", 553, 420, True, "grupo"),
    ("sol", "Sol", "terreo", 160, 425, False, "anim"),
    ("pipoca", "Pipoca", "terreo", 125, 310, False, "anim"),
    ("gancho", "Tio Gancho", "terreo", 185, 125, False, "anim"),
    ("gemeo1", "Gêmeo 009", "andar1", 290, 125, False, "anim"),
    ("gemeo2", "Gêmeo 010", "andar1", 350, 125, False, "anim"),
    ("miudo", "Miúdo", "andar1", 440, 430, False, "anim"),
]
SONS = {"alarme", "sirene", "estatica", "sistema", "grave"}
ARQUIVO_NOTAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notas_mestre.txt")


def estado_inicial():
    salas = {s["id"]: "oculta" for s in SALAS}
    salas["entrada"] = "revelada"
    return {
        "salas": salas,
        "andares": {"terreo": True, "andar1": False},
        "tokens": [dict(id=i, nome=n, andar=a, x=x, y=y, visivel=v, tipo=t) for i, n, a, x, y, v, t in TOKENS],
        "avisos": [], "rolagens": [], "dt": None, "seq": 0,
    }


estado_mapa = estado_inicial()


def pin_ok():
    return request.headers.get("X-PIN", "") == MESTRE_PIN


def corpo():
    return request.get_json(silent=True) or {}


def proximo_id():
    estado_mapa["seq"] += 1
    return estado_mapa["seq"]


def rolagem_visivel(r, gm):
    d = {k: r[k] for k in ("id", "nome", "dado", "valor", "ok", "secreta")}
    if gm:
        d["dt"] = r["dt"]  # jogadores veem só sucesso/falha, nunca a DT
    return d


ARQUIVO_DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arquivos.json")


def _carregar_docs():
    try:
        with open(ARQUIVO_DOCS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


docs = _carregar_docs()  # documentos da janela Arquivos, salvos em arquivos.json


def gravar_docs():
    with open(ARQUIVO_DOCS, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=1)


def docs_publicos():
    # o texto NUNCA sai nesta lista: só pelo /api/arquivo, e com a senha, se houver
    return [{"id": d["id"], "titulo": d["titulo"], "pasta": d["pasta"], "bloqueado": bool(d["senha"])}
            for d in docs if d["liberado"]]


def dados_publicos():
    st = estado_mapa
    vis = {a["id"] for a in ANDARES if st["andares"][a["id"]]}
    salas = [s for s in SALAS if st["salas"][s["id"]] == "revelada" and s["andar"] in vis]
    return dict(
        andares=[a for a in ANDARES if a["id"] in vis],
        salas=[{k: s[k] for k in ("id", "andar", "nome", "x", "y", "w", "h")} for s in salas],
        tokens=[{k: t[k] for k in ("id", "nome", "andar", "x", "y", "tipo")}
                for t in st["tokens"] if t["visivel"] and t["andar"] in vis],
        avisos=st["avisos"][-5:],
        rolagens=[rolagem_visivel(r, False) for r in st["rolagens"] if not r["secreta"]][-15:],
        arquivos=docs_publicos(),
    )


def dados_mestre():
    st = estado_mapa
    try:
        with open(ARQUIVO_NOTAS, encoding="utf-8") as f:
            notas = f.read()
    except OSError:
        notas = ""
    return dict(
        andares=[{**a, "visivel": st["andares"][a["id"]]} for a in ANDARES],
        salas=[{**s, "estado": st["salas"][s["id"]]} for s in SALAS],
        tokens=st["tokens"], avisos=st["avisos"][-5:],
        rolagens=[rolagem_visivel(r, True) for r in st["rolagens"]][-15:],
        dt=st["dt"], notas=notas, arquivos=docs,
    )


@app.get("/mapa")
def mapa():
    return render_template("mapa.html", modo="jogador")


@app.get("/mestre/mapa")
def mapa_mestre():
    return render_template("mapa.html", modo="mestre")


@app.get("/api/jogo")
def api_jogo():
    return jsonify(dados_publicos())


@app.get("/api/mestre/jogo")
def api_mestre_jogo():
    if not pin_ok():
        return jsonify(erro="PIN incorreto"), 401
    return jsonify(dados_mestre())


@app.post("/api/rolar")
def rolar():
    d = corpo()
    lado = d.get("dado")
    if lado not in (4, 6, 8, 10, 12, 20, 100):
        return jsonify(ok=False), 400
    gm = pin_ok()
    valor = random.randint(1, lado)
    dt = estado_mapa["dt"]
    r = dict(id=proximo_id(), nome=str(d.get("nome") or "Alguém")[:20], dado=lado, valor=valor, dt=dt,
             ok=(valor >= dt) if (dt and lado == 20) else None, secreta=bool(d.get("secreta")) and gm)
    estado_mapa["rolagens"] = (estado_mapa["rolagens"] + [r])[-60:]
    return jsonify(ok=True, rolagem=rolagem_visivel(r, gm))


def so_mestre(f):
    def envolvido():
        if not pin_ok():
            return jsonify(ok=False), 401
        f()
        return jsonify(ok=True)
    envolvido.__name__ = f.__name__
    return envolvido


@app.post("/api/mestre/aviso")
@so_mestre
def mestre_aviso():
    d = corpo()
    texto = str(d.get("texto", "")).strip()[:200]
    if texto:
        aviso = dict(id=proximo_id(), texto=texto,
                     som=d.get("som") if d.get("som") in SONS else "sistema",
                     nivel=d.get("nivel") if d.get("nivel") in ("info", "alerta", "critico") else "info")
        estado_mapa["avisos"] = (estado_mapa["avisos"] + [aviso])[-20:]


@app.post("/api/mestre/notas")
@so_mestre
def mestre_notas():
    with open(ARQUIVO_NOTAS, "w", encoding="utf-8") as f:
        f.write(str(corpo().get("texto", ""))[:20000])


@app.post("/api/mestre/dt")
@so_mestre
def mestre_dt():
    dt = corpo().get("dt")
    estado_mapa["dt"] = dt if isinstance(dt, int) and 1 <= dt <= 40 else None


@app.post("/api/mestre/sala")
@so_mestre
def mestre_sala():
    d = corpo()
    if d.get("id") in estado_mapa["salas"] and d.get("estado") in ("oculta", "revelada"):
        estado_mapa["salas"][d["id"]] = d["estado"]


@app.post("/api/mestre/andar")
@so_mestre
def mestre_andar():
    d = corpo()
    if d.get("id") in estado_mapa["andares"]:
        estado_mapa["andares"][d["id"]] = bool(d.get("visivel"))


@app.post("/api/mestre/tudo")
@so_mestre
def mestre_tudo():
    d = corpo()
    if d.get("estado") in ("oculta", "revelada"):
        for s in SALAS:
            if d.get("andar") in (None, s["andar"]):
                estado_mapa["salas"][s["id"]] = d["estado"]


@app.post("/api/mestre/token")
@so_mestre
def mestre_token():
    d = corpo()
    t = next((t for t in estado_mapa["tokens"] if t["id"] == d.get("id")), None)
    if not t:
        return
    for k, limite in (("x", 680), ("y", 490)):
        if isinstance(d.get(k), (int, float)):
            t[k] = max(0, min(limite, d[k]))
    if "visivel" in d:
        t["visivel"] = bool(d["visivel"])
    if d.get("andar") in estado_mapa["andares"]:
        t["andar"] = d["andar"]
        if t["id"] == "grupo":
            estado_mapa["andares"][d["andar"]] = True  # jogadores acompanham o grupo
    if t["id"] == "grupo":  # a sala onde o grupo é solto é revelada
        for s in SALAS:
            if s["andar"] == t["andar"] and s["x"] <= t["x"] <= s["x"] + s["w"] and s["y"] <= t["y"] <= s["y"] + s["h"]:
                estado_mapa["salas"][s["id"]] = "revelada"


@app.post("/api/mestre/reiniciar")
@so_mestre
def mestre_reiniciar():
    estado_mapa.clear()
    estado_mapa.update(estado_inicial())


@app.post("/api/arquivo")
def abrir_arquivo():
    d = corpo()
    gm = pin_ok()
    doc = next((x for x in docs if x["id"] == d.get("id")), None)
    if not doc or not (doc["liberado"] or gm):
        return jsonify(ok=False, erro="Arquivo indisponível."), 404
    if doc["senha"] and not gm and normalizar(str(d.get("senha", ""))) != normalizar(doc["senha"]):
        return jsonify(ok=False, erro="Senha incorreta."), 401
    return jsonify(ok=True, titulo=doc["titulo"], texto=doc["texto"])


@app.post("/api/mestre/arquivo")
@so_mestre
def mestre_arquivo():
    d = corpo()
    ident = "".join(c for c in str(d.get("id", "")) if c.isalnum())[:20]
    if not ident:
        return
    if d.get("apagar"):
        docs[:] = [x for x in docs if x["id"] != ident]
    else:
        novo = dict(id=ident, titulo=str(d.get("titulo", "")).strip()[:80] or "Sem título",
                    pasta=str(d.get("pasta", "")).strip()[:40], texto=str(d.get("texto", ""))[:20000],
                    senha=str(d.get("senha", "")).strip()[:40], liberado=bool(d.get("liberado")))
        for i, x in enumerate(docs):
            if x["id"] == ident:
                docs[i] = novo
                break
        else:
            docs.append(novo)
    gravar_docs()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)