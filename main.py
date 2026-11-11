# -*- coding: utf-8 -*-
# ============================================================================
#
#
#
#
#
# ============================================================================
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
print("\u25b6 Self Speed \u0634\u0631\u0648\u0639 \u0634\u062f ...")
import asyncio, os, json, time, re, html, base64, hmac, hashlib, secrets
import sqlite3, logging, random, ast, operator, collections, io
from datetime import datetime, timedelta, timezone

try:
    from telethon import TelegramClient, events, functions, types, errors, utils, Button
    from telethon.sessions import StringSession
except ImportError:
    print("\n\u274c \u06a9\u062a\u0627\u0628\u062e\u0627\u0646\u0647\u200c\u06cc telethon \u0646\u0635\u0628 \u0646\u06cc\u0633\u062a.")
    print("   \u062f\u0631 \u067e\u0627\u06cc\u062f\u0631\u0648\u06cc\u062f: \u0645\u0646\u0648\u06cc \u2261 \u2190 Pip \u2190 \u0628\u0646\u0648\u06cc\u0633 telethon \u2190 Install\n")
    sys.exit(1)

#
#
API_ID = 0                 #
API_HASH = ""              #
BOT_TOKEN = ""             #
OWNER_ID = 0               #
MTPROXY = ""               #
TZ_OFFSET_MIN = int(os.environ.get("TZ_OFFSET_MIN") or 210)   #
MAX_USERS = int(os.environ.get("MAX_USERS") or 100)   #

try:
    BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE = os.getcwd()
#
ON_SERVER = bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_PROJECT_ID")
                 or os.environ.get("RAILWAY_SERVICE_ID") or os.environ.get("SELFSAZ_SERVER"))
HAS_VOLUME = bool(os.environ.get("DATA_DIR") or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH"))
DATA = (os.environ.get("DATA_DIR") or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
        or os.path.join(BASE, "selfsaz_data"))
CACHE_DIR = os.path.join(DATA, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

_handlers = [logging.StreamHandler()]
try:
    _handlers.append(logging.FileHandler(os.path.join(DATA, "log.txt"), encoding="utf-8"))
except Exception:
    pass
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=_handlers,
)
ERRS = collections.deque(maxlen=30)


class _ErrH(logging.Handler):
    def emit(self, r):
        if r.levelno >= logging.WARNING:
            try:
                ERRS.append("%s %s" % (time.strftime("%H:%M:%S"), self.format(r)[-500:]))
            except Exception:
                pass


_eh = _ErrH()
_eh.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
logging.getLogger().addHandler(_eh)
logging.getLogger("telethon").setLevel(logging.WARNING)
log = logging.getLogger("selfsaz")

SERVICE_IDS = {777000, 42777, 93372553}   #
FA_DIGITS = str.maketrans("0123456789", "\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9")
EN_DIGITS = str.maketrans("\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669", "01234567890123456789")
JMONTHS = ["\u0641\u0631\u0648\u0631\u062f\u06cc\u0646", "\u0627\u0631\u062f\u06cc\u0628\u0647\u0634\u062a", "\u062e\u0631\u062f\u0627\u062f", "\u062a\u06cc\u0631", "\u0645\u0631\u062f\u0627\u062f", "\u0634\u0647\u0631\u06cc\u0648\u0631", "\u0645\u0647\u0631", "\u0622\u0628\u0627\u0646", "\u0622\u0630\u0631", "\u062f\u06cc", "\u0628\u0647\u0645\u0646", "\u0627\u0633\u0641\u0646\u062f"]


def _err(*names):
    out = []
    for n in names:
        e = getattr(errors, n, None)
        if e:
            out.append(e)
    return tuple(out)


AUTH_DEAD = _err("AuthKeyUnregisteredError", "SessionRevokedError", "SessionExpiredError",
                 "UserDeactivatedError", "UserDeactivatedBanError", "AuthKeyDuplicatedError")


#
def fa(x):
    return str(x).translate(FA_DIGITS)


def esc(x):
    return html.escape(str(x if x is not None else ""), quote=False)


def u16(s):
    return len(s.encode("utf-16-le")) // 2


def now_local():
    return datetime.now(timezone.utc) + timedelta(minutes=TZ_OFFSET_MIN)


def g2j(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def jdate_str(dt=None):
    dt = dt or now_local()
    jy, jm, jd = g2j(dt.year, dt.month, dt.day)
    return "%s %s %s" % (fa(jd), JMONTHS[jm - 1], fa(jy))


def uname(u):
    if u is None:
        return "?"
    n = " ".join(x for x in (getattr(u, "first_name", None), getattr(u, "last_name", None)) if x)
    return n or getattr(u, "title", None) or str(getattr(u, "id", "?"))


def ulabel(u):
    s = esc(uname(u))
    un = getattr(u, "username", None)
    if un:
        s += " (@%s)" % esc(un)
    return s


def tpl(text, user=None):
    t = now_local()
    out = text.replace("{time}", t.strftime("%H:%M")).replace("{date}", jdate_str(t))
    if user is not None:
        out = out.replace("{name}", uname(user)).replace("{first}", getattr(user, "first_name", "") or uname(user))
    return out


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
        ast.USub: operator.neg, ast.UAdd: operator.pos}


def calc(expr):
    expr = expr.translate(EN_DIGITS).replace("\u00d7", "*").replace("\u00f7", "/").replace("^", "**").replace("\u060c", "")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and (abs(b) > 1000 or abs(a) > 10 ** 6):
                raise ValueError("big")
            return _OPS[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("bad")
    return ev(ast.parse(expr.strip(), mode="eval"))


def ask(prompt, kind="str"):
    while True:
        v = input(prompt).strip().translate(EN_DIGITS)
        if not v:
            continue
        if kind == "int":
            v = v.lstrip("-")
            if not v.isdigit():
                print("\u0641\u0642\u0637 \u0639\u062f\u062f \u0648\u0627\u0631\u062f \u06a9\u0646.")
                continue
            return int(v)
        return v


def _env_int(name):
    v = (os.environ.get(name) or "").strip().translate(EN_DIGITS).lstrip("-")
    return int(v) if v.isdigit() else 0


def load_config():
    global API_ID, API_HASH, BOT_TOKEN, OWNER_ID, MTPROXY
    path = os.path.join(DATA, "config.json")
    cfg = {}
    if not ON_SERVER and os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    API_ID = API_ID or _env_int("API_ID") or int(cfg.get("api_id") or 0)
    API_HASH = API_HASH or (os.environ.get("API_HASH") or "").strip() or cfg.get("api_hash") or ""
    BOT_TOKEN = BOT_TOKEN or (os.environ.get("BOT_TOKEN") or "").strip() or cfg.get("bot_token") or ""
    OWNER_ID = OWNER_ID or _env_int("OWNER_ID") or int(cfg.get("owner_id") or 0)
    MTPROXY = MTPROXY or (os.environ.get("MTPROXY") or "").strip() or cfg.get("mtproxy") or ""
    missing = [n for n, v in (("API_ID", API_ID), ("API_HASH", API_HASH), ("BOT_TOKEN", BOT_TOKEN),
                              ("OWNER_ID", OWNER_ID)) if not v]
    if missing and ON_SERVER:
        print("\n\u274c \u0627\u06cc\u0646 \u0645\u062a\u063a\u06cc\u0631\u0647\u0627 \u062f\u0631 Variables \u0631\u06cc\u0644\u0648\u06cc \u0646\u06cc\u0633\u062a: " + ", ".join(missing))
        print("   Service \u2190 Variables \u2190 New Variable \u0648 \u0622\u0646\u200c\u0647\u0627 \u0631\u0627 \u0628\u0633\u0627\u0632\u060c \u0628\u0639\u062f Redeploy \u06a9\u0646.\n")
        sys.exit(1)
    try:
        if not API_ID:
            API_ID = ask("1) API_ID (\u0639\u062f\u062f\u060c \u0627\u0632 my.telegram.org): ", "int")
        if not API_HASH:
            API_HASH = ask("2) API_HASH (\u0627\u0632 my.telegram.org): ")
        if not BOT_TOKEN:
            BOT_TOKEN = ask("3) \u062a\u0648\u06a9\u0646 \u0631\u0628\u0627\u062a (\u0627\u0632 @BotFather): ")
        if not OWNER_ID:
            OWNER_ID = ask("4) \u0622\u06cc\u062f\u06cc \u0639\u062f\u062f\u06cc \u062e\u0648\u062f\u062a (\u0627\u0632 @userinfobot): ", "int")
    except EOFError:
        print("\n\u274c \u0645\u0642\u062f\u0627\u0631\u0647\u0627\u06cc \u0644\u0627\u0632\u0645 \u062f\u0627\u062f\u0647 \u0646\u0634\u062f\u0647: " + ", ".join(missing))
        sys.exit(1)
    if ON_SERVER:
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"api_id": API_ID, "api_hash": API_HASH, "bot_token": BOT_TOKEN,
                   "owner_id": OWNER_ID, "mtproxy": MTPROXY}, f, ensure_ascii=False, indent=1)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


#
#
#
KEY = b""


def init_key():
    global KEY
    env_key = (os.environ.get("SECRET_KEY") or "").strip()
    if env_key:
        KEY = hashlib.sha256(env_key.encode("utf-8")).digest()
        return
    p = os.path.join(DATA, "secret.key")
    if os.path.exists(p):
        with open(p, "rb") as f:
            KEY = f.read()
    if len(KEY) != 32:
        KEY = secrets.token_bytes(32)
        with open(p, "wb") as f:
            f.write(KEY)
        try:
            os.chmod(p, 0o600)
        except Exception:
            pass


def _sub(label):
    return hmac.new(KEY, label, hashlib.sha256).digest()


def enc(plain):
    nonce = os.urandom(16)
    data = plain.encode("utf-8")
    ek, mk = _sub(b"enc"), _sub(b"mac")
    stream = b"".join(hmac.new(ek, nonce + i.to_bytes(8, "big"), hashlib.sha256).digest()
                      for i in range((len(data) + 31) // 32))
    ct = bytes(a ^ b for a, b in zip(data, stream))
    tag = hmac.new(mk, nonce + ct, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(nonce + tag + ct).decode()


def dec(token):
    raw = base64.urlsafe_b64decode(token.encode())
    nonce, tag, ct = raw[:16], raw[16:48], raw[48:]
    ek, mk = _sub(b"enc"), _sub(b"mac")
    if not hmac.compare_digest(tag, hmac.new(mk, nonce + ct, hashlib.sha256).digest()):
        raise ValueError("bad session token")
    stream = b"".join(hmac.new(ek, nonce + i.to_bytes(8, "big"), hashlib.sha256).digest()
                      for i in range((len(ct) + 31) // 32))
    return bytes(a ^ b for a, b in zip(ct, stream)).decode("utf-8")


#
class Database(object):
    def __init__(self, path):
        self.c = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        try:
            self.c.execute("PRAGMA journal_mode=WAL")
            self.c.execute("PRAGMA synchronous=NORMAL")
        except Exception:
            pass
        self.c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY, phone TEXT, name TEXT, username TEXT, session TEXT,
            status TEXT DEFAULT 'active', settings TEXT DEFAULT '{}', created INTEGER, last_seen INTEGER);
        CREATE TABLE IF NOT EXISTS cache(
            uid INTEGER, chat_id INTEGER, msg_id INTEGER, sender_id INTEGER, sender_name TEXT,
            text TEXT, media TEXT, path TEXT, date INTEGER, out INTEGER DEFAULT 0,
            PRIMARY KEY(uid, chat_id, msg_id));
        CREATE INDEX IF NOT EXISTS cache_date ON cache(date);
        CREATE INDEX IF NOT EXISTS cache_mid ON cache(uid, msg_id);
        CREATE TABLE IF NOT EXISTS kv(uid INTEGER, k TEXT, v TEXT, PRIMARY KEY(uid, k));
        CREATE TABLE IF NOT EXISTS bill(
            uid INTEGER PRIMARY KEY, exp INTEGER DEFAULT 0, test_used INTEGER DEFAULT 0,
            wheel_ts INTEGER DEFAULT 0, warned INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS game(
            id INTEGER PRIMARY KEY AUTOINCREMENT, chat INTEGER, w INTEGER, l INTEGER, stake INTEGER, ts INTEGER);
        CREATE TABLE IF NOT EXISTS pay(
            id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, coins INTEGER, price INTEGER,
            status TEXT, ts INTEGER);
        """)

    def q(self, sql, a=()):
        return self.c.execute(sql, a)

    def one(self, sql, a=()):
        return self.c.execute(sql, a).fetchone()

    def all(self, sql, a=()):
        return self.c.execute(sql, a).fetchall()


DB = None


def kv_get(uid, k, default=None):
    r = DB.one("SELECT v FROM kv WHERE uid=? AND k=?", (uid, k))
    return r[0] if r else default


def kv_set(uid, k, v):
    DB.q("INSERT OR REPLACE INTO kv(uid,k,v) VALUES(?,?,?)", (uid, k, str(v)))


def kv_del(uid, k):
    DB.q("DELETE FROM kv WHERE uid=? AND k=?", (uid, k))


#
def _fd(base):
    return "".join(chr(base + i) for i in range(10))


FONTS = {
    "en": "0123456789",
    "fa": "\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9",
    "bold": _fd(0x1D7CE),
    "dbl": _fd(0x1D7D8),
    "sans": _fd(0x1D7E2),
    "sansb": _fd(0x1D7EC),
    "mono": _fd(0x1D7F6),
    "full": _fd(0xFF10),
    "circ": "\u24ea\u2460\u2461\u2462\u2463\u2464\u2465\u2466\u2467\u2468",
    "neg": "\u24ff\u2776\u2777\u2778\u2779\u277a\u277b\u277c\u277d\u277e",
    "sub": "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089",
    "sup": "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079",
}
FONT_NAMES = [("en", "\u0645\u0639\u0645\u0648\u0644\u06cc"), ("fa", "\u0641\u0627\u0631\u0633\u06cc"), ("bold", "\u0628\u0648\u0644\u062f"), ("dbl", "\u062a\u0648\u062e\u0627\u0644\u06cc"), ("sans", "\u0633\u0627\u062f\u0647"),
              ("sansb", "\u0633\u0627\u062f\u0647\u200c\u0628\u0648\u0644\u062f"), ("mono", "\u0645\u0648\u0646\u0648"), ("full", "\u067e\u0647\u0646"), ("circ", "\u062f\u0627\u06cc\u0631\u0647\u200c\u0627\u06cc"),
              ("neg", "\u062f\u0627\u06cc\u0631\u0647\u200c\u067e\u0631"), ("sub", "\u0631\u06cc\u0632 \u067e\u0627\u06cc\u06cc\u0646"), ("sup", "\u0631\u06cc\u0632 \u0628\u0627\u0644\u0627")]
CLOCK_FONT_OPTS = [(k, "%s %s" % (FONTS[k][1:5], n)) for k, n in FONT_NAMES]
TZ_OPTS = [("210", "\u0627\u06cc\u0631\u0627\u0646"), ("270", "\u0627\u0641\u063a\u0627\u0646\u0633\u062a\u0627\u0646"), ("180", "\u062a\u0631\u06a9\u06cc\u0647/\u0639\u0631\u0627\u0642"), ("240", "\u0627\u0645\u0627\u0631\u0627\u062a"),
           ("300", "\u067e\u0627\u06a9\u0633\u062a\u0627\u0646"), ("330", "\u0647\u0646\u062f"), ("60", "\u0627\u0631\u0648\u067e\u0627"), ("0", "UTC")]


def fontify(text, font):
    table = FONTS.get(font) or FONTS["en"]
    return "".join(table[int(ch)] if ch.isdigit() and ch in "0123456789" else ch for ch in text)


CATS = [
    ("sec", "\U0001f6e1 \u0646\u0638\u0627\u0631\u062a \u0648 \u0627\u0645\u0646\u06cc\u062a"),
    ("auto", "\u2699\ufe0f \u062e\u0648\u062f\u06a9\u0627\u0631\u0633\u0627\u0632\u06cc"),
    ("pub", "\U0001f4e3 \u0627\u0646\u062a\u0634\u0627\u0631"),
    ("dl", "\U0001f4e5 \u062f\u0627\u0646\u0644\u0648\u062f\u0647\u0627"),
    ("look", "\U0001f3a8 \u0638\u0627\u0647\u0631"),
    ("rel", "\U0001f49e \u0631\u0648\u0627\u0628\u0637"),
    ("tools", "\U0001f9f0 \u0627\u0628\u0632\u0627\u0631\u0647\u0627"),
    ("game", "\U0001f3ae \u0631\u0628\u0627\u062a\u200c\u0647\u0627\u06cc \u0628\u0627\u0632\u06cc"),
]
CAT_TITLE = dict(CATS)

FEATS = collections.OrderedDict()


def F(key, cat, title, desc, params=(), need=(), on=False):
    FEATS[key] = dict(key=key, cat=cat, title=title, desc=desc, params=list(params), need=tuple(need), on=on)


def pt(n, l, d="", h=""):
    return dict(t="text", n=n, l=l, d=d, h=h)


def pi(n, l, d, lo, hi):
    return dict(t="int", n=n, l=l, d=d, lo=lo, hi=hi)


def pc(n, l, d, opts):
    return dict(t="choice", n=n, l=l, d=d, o=opts)


def pl(n, l, kind, h="", mx=20):
    return dict(t="list", n=n, l=l, k=kind, h=h, mx=mx, d=[])


def po(n, l, kind, h="", admin=False):
    return dict(t="one", n=n, l=l, k=kind, h=h, admin=admin, d=None)


#
F("adel", "sec", "\u0636\u062f \u062d\u0630\u0641",
  "\u0627\u0632 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc\u06cc \u06a9\u0647 \u0637\u0631\u0641 \u0645\u0642\u0627\u0628\u0644 \u062f\u0631 \u067e\u06cc\u0648\u06cc \u062d\u0630\u0641 \u0645\u06cc\u200c\u06a9\u0646\u062f \u06cc\u06a9 \u0646\u0633\u062e\u0647 \u0646\u06af\u0647 \u0645\u06cc\u200c\u062f\u0627\u0631\u062f \u0648 \u0645\u062a\u0646 (\u0648 \u0639\u06a9\u0633/\u0641\u0627\u06cc\u0644 \u06a9\u0648\u0686\u06a9) \u0631\u0627 \u0628\u0631\u0627\u06cc\u062a \u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u062f.",
  [pc("media", "\u0630\u062e\u06cc\u0631\u0647\u200c\u06cc \u0639\u06a9\u0633 \u0648 \u0641\u0627\u06cc\u0644", "yes", [("yes", "\u0628\u0644\u0647"), ("no", "\u0641\u0642\u0637 \u0645\u062a\u0646")]),
   pi("maxmb", "\u062d\u062f\u0627\u06a9\u062b\u0631 \u062d\u062c\u0645 \u0641\u0627\u06cc\u0644 (\u0645\u06af\u0627\u0628\u0627\u06cc\u062a)", 10, 1, 30)])
F("aedit", "sec", "\u0636\u062f \u0648\u06cc\u0631\u0627\u06cc\u0634",
  "\u0648\u0642\u062a\u06cc \u0637\u0631\u0641 \u0645\u0642\u0627\u0628\u0644 \u062f\u0631 \u067e\u06cc\u0648\u06cc \u067e\u06cc\u0627\u0645\u0634 \u0631\u0627 \u0648\u06cc\u0631\u0627\u06cc\u0634 \u06a9\u0646\u062f\u060c \u0645\u062a\u0646 \u0642\u0628\u0644 \u0648 \u0628\u0639\u062f \u0631\u0627 \u0628\u0631\u0627\u06cc\u062a \u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u062f.")
F("pvlock", "sec", "\u0642\u0641\u0644 \u067e\u06cc\u0648\u06cc",
  "\u063a\u0631\u06cc\u0628\u0647\u200c\u0627\u06cc (\u06a9\u0647 \u0645\u062e\u0627\u0637\u0628 \u0646\u06cc\u0633\u062a \u0648 \u0642\u0628\u0644\u0627\u064b \u0628\u0627 \u0627\u0648 \u0686\u062a \u0646\u06a9\u0631\u062f\u0647\u200c\u0627\u06cc) \u067e\u06cc\u0627\u0645 \u0628\u062f\u0647\u062f\u060c \u0627\u062e\u0637\u0627\u0631 \u0645\u06cc\u200c\u06af\u06cc\u0631\u062f \u0648 \u0628\u0639\u062f \u0627\u0632 \u0686\u0646\u062f \u0627\u062e\u0637\u0627\u0631 \u0645\u0633\u062f\u0648\u062f \u0645\u06cc\u200c\u0634\u0648\u062f.",
  [pi("warns", "\u062a\u0639\u062f\u0627\u062f \u0627\u062e\u0637\u0627\u0631 \u0642\u0628\u0644 \u0627\u0632 \u0645\u0633\u062f\u0648\u062f \u0634\u062f\u0646", 3, 1, 10),
   pt("msg", "\u0645\u062a\u0646 \u0627\u062e\u0637\u0627\u0631", "\u0633\u0644\u0627\u0645 \U0001f44b \u0627\u06cc\u0646 \u062d\u0633\u0627\u0628 \u067e\u06cc\u0627\u0645 \u063a\u0631\u06cc\u0628\u0647\u200c\u0647\u0627 \u0631\u0627 \u0646\u0645\u06cc\u200c\u067e\u0630\u06cc\u0631\u062f. \u0644\u0637\u0641\u0627\u064b \u067e\u06cc\u0627\u0645 \u0646\u062f\u0647\u06cc\u062f\u060c \u062f\u0631 \u063a\u06cc\u0631 \u0627\u06cc\u0646 \u0635\u0648\u0631\u062a \u0645\u0633\u062f\u0648\u062f \u0645\u06cc\u200c\u0634\u0648\u06cc\u062f."),
   pl("ok", "\u0627\u0641\u0631\u0627\u062f \u0645\u062c\u0627\u0632", "user", "\u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0622\u06cc\u062f\u06cc \u0639\u062f\u062f\u06cc")])
F("asilent", "sec", "\u0633\u06a9\u0648\u062a \u06a9\u0627\u0631\u0628\u0631\u0627\u0646 \u062f\u0631 \u06af\u0631\u0648\u0647",
  "\u067e\u06cc\u0627\u0645 \u06a9\u0627\u0631\u0628\u0631\u0627\u0646\u06cc \u06a9\u0647 \u0627\u0646\u062a\u062e\u0627\u0628 \u0645\u06cc\u200c\u06a9\u0646\u06cc \u0631\u0627 \u062f\u0631 \u00ab\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u00bb \u062d\u0630\u0641 \u0645\u06cc\u200c\u06a9\u0646\u062f (\u0628\u0627\u06cc\u062f \u062f\u0631 \u0622\u0646 \u06af\u0631\u0648\u0647 \u0627\u062c\u0627\u0632\u0647\u200c\u06cc \u062d\u0630\u0641 \u067e\u06cc\u0627\u0645 \u062f\u0627\u0634\u062a\u0647 \u0628\u0627\u0634\u06cc).",
  [pl("users", "\u06a9\u0627\u0631\u0628\u0631\u0627\u0646 \u0633\u0627\u06a9\u062a\u200c\u0634\u062f\u0647", "user", "\u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0622\u06cc\u062f\u06cc \u0639\u062f\u062f\u06cc")], need=("users",))
F("alogin", "sec", "\u0636\u062f \u0644\u0627\u06af\u06cc\u0646",
  "\u0648\u0631\u0648\u062f \u062a\u0627\u0632\u0647 \u0628\u0647 \u062d\u0633\u0627\u0628\u062a \u0631\u0627 \u0634\u0646\u0627\u0633\u0627\u06cc\u06cc \u0645\u06cc\u200c\u06a9\u0646\u062f\u061b \u0627\u06af\u0631 \u062a\u0627 \u0686\u0646\u062f \u062f\u0642\u06cc\u0642\u0647 \u062a\u0623\u06cc\u06cc\u062f \u0646\u06a9\u0646\u06cc (\u062f\u06a9\u0645\u0647\u200c\u06cc \u00ab\u0645\u0646 \u0628\u0648\u062f\u0645\u00bb)\u060c \u0622\u0646 \u0646\u0634\u0633\u062a \u0631\u0627 \u0628\u06cc\u0631\u0648\u0646 \u0645\u06cc\u200c\u0627\u0646\u062f\u0627\u0632\u062f. "
  "\u0646\u06a9\u062a\u0647: \u062a\u0644\u06af\u0631\u0627\u0645 \u0627\u062c\u0627\u0632\u0647\u200c\u06cc \u0627\u062e\u0631\u0627\u062c \u0646\u0634\u0633\u062a \u0631\u0627 \u0641\u0642\u0637 \u0628\u0647 \u0646\u0634\u0633\u062a\u06cc \u0645\u06cc\u200c\u062f\u0647\u062f \u06a9\u0647 \u0628\u06cc\u0634 \u0627\u0632 \u06f2\u06f4 \u0633\u0627\u0639\u062a \u0627\u0632 \u0639\u0645\u0631\u0634 \u06af\u0630\u0634\u062a\u0647 \u0628\u0627\u0634\u062f.",
  [pi("grace", "\u0645\u0647\u0644\u062a \u062a\u0623\u06cc\u06cc\u062f (\u062f\u0642\u06cc\u0642\u0647)", 3, 1, 30)])
F("fjoin", "sec", "\u0639\u0636\u0648\u06cc\u062a \u0627\u062c\u0628\u0627\u0631\u06cc",
  "\u062a\u0627 \u0648\u0642\u062a\u06cc \u06a9\u0633\u06cc \u062f\u0631 \u06a9\u0627\u0646\u0627\u0644\u062a \u0639\u0636\u0648 \u0646\u0634\u062f\u0647\u060c \u0645\u0646\u0634\u06cc \u062e\u0648\u062f\u06a9\u0627\u0631 \u0648 \u067e\u0627\u0633\u062e\u200c\u0647\u0627\u06cc \u06a9\u0644\u0645\u0647\u200c\u0627\u06cc \u0628\u0647 \u0627\u0648 \u062c\u0648\u0627\u0628 \u0646\u0645\u06cc\u200c\u062f\u0647\u0646\u062f \u0648 \u0627\u0632 \u0627\u0648 \u0645\u06cc\u200c\u062e\u0648\u0627\u0647\u0646\u062f \u0639\u0636\u0648 \u0634\u0648\u062f. "
  "(\u0628\u0627\u06cc\u062f \u0627\u062f\u0645\u06cc\u0646 \u0622\u0646 \u06a9\u0627\u0646\u0627\u0644 \u0628\u0627\u0634\u06cc.)",
  [po("chan", "\u06a9\u0627\u0646\u0627\u0644", "chat", "\u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0644\u06cc\u0646\u06a9 \u06a9\u0627\u0646\u0627\u0644", admin=True)], need=("chan",))
F("joinreq", "sec", "\u067e\u0630\u06cc\u0631\u0634 \u062e\u0648\u062f\u06a9\u0627\u0631 \u062f\u0631\u062e\u0648\u0627\u0633\u062a \u0639\u0636\u0648\u06cc\u062a",
  "\u062f\u0631\u062e\u0648\u0627\u0633\u062a \u0639\u0636\u0648\u06cc\u062a \u06a9\u0627\u0646\u0627\u0644\u200c\u0647\u0627 \u0648 \u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc\u06cc \u06a9\u0647 \u0627\u062f\u0645\u06cc\u0646\u0634\u0627\u0646 \u0647\u0633\u062a\u06cc \u0631\u0627 \u062e\u0648\u062f\u06a9\u0627\u0631 \u062a\u0623\u06cc\u06cc\u062f \u0645\u06cc\u200c\u06a9\u0646\u062f.")
F("abetray", "sec", "\u0636\u062f \u062e\u06cc\u0627\u0646\u062a",
  "\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc\u06cc \u06a9\u0647 \u0633\u0627\u0632\u0646\u062f\u0647\u200c\u0634\u0627\u0646 \u0647\u0633\u062a\u06cc \u0631\u0627 \u0645\u06cc\u200c\u067e\u0627\u06cc\u062f\u061b \u0627\u06af\u0631 \u0627\u062f\u0645\u06cc\u0646\u06cc \u062f\u0633\u062a\u0647\u200c\u062c\u0645\u0639\u06cc \u06a9\u0627\u0631\u0628\u0631 \u0628\u0646 \u06a9\u0631\u062f\u060c \u0627\u0648 \u0631\u0627 \u0627\u0632 \u0627\u062f\u0645\u06cc\u0646\u06cc \u0628\u0631\u06a9\u0646\u0627\u0631 \u0645\u06cc\u200c\u06a9\u0646\u062f.",
  [pi("limit", "\u062a\u0639\u062f\u0627\u062f \u0628\u0646 \u062f\u0631 \u0628\u0627\u0632\u0647", 5, 3, 30), pi("mins", "\u0628\u0627\u0632\u0647 (\u062f\u0642\u06cc\u0642\u0647)", 10, 2, 120)])
F("track", "sec", "\u0631\u062f\u06cc\u0627\u0628 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627",
  "\u0647\u0631 \u067e\u06cc\u0627\u0645\u06cc \u06a9\u0647 \u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u06cc \u0631\u0627 \u06f2\u06f4 \u0633\u0627\u0639\u062a \u0628\u0647 \u062e\u0627\u0637\u0631 \u0645\u06cc\u200c\u0633\u067e\u0627\u0631\u062f \u062a\u0627 \u0628\u062a\u0648\u0627\u0646\u06cc \u0647\u0645\u0647 \u0631\u0627 \u06cc\u06a9\u200c\u062c\u0627 \u067e\u0627\u06a9 \u06a9\u0646\u06cc (\u0627\u0628\u0632\u0627\u0631\u0647\u0627 \u2190 \u062d\u0630\u0641 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u06f2\u06f4 \u0633\u0627\u0639\u062a\u0647).")
F("kwatch", "sec", "\u0634\u0646\u0648\u062f",
  "\u0628\u0647 \u0645\u062d\u0636 \u0627\u06cc\u0646\u06a9\u0647 \u06a9\u0644\u0645\u0647\u200c\u0627\u06cc \u06a9\u0647 \u0631\u0635\u062f \u0645\u06cc\u200c\u06a9\u0646\u06cc \u062f\u0631 \u0647\u0631 \u0686\u062a\u06cc \u06af\u0641\u062a\u0647 \u0634\u0648\u062f\u060c \u062e\u0628\u0631\u062a \u0645\u06cc\u200c\u06a9\u0646\u062f.",
  [pl("words", "\u06a9\u0644\u0645\u0647\u200c\u0647\u0627", "text", "\u06cc\u06a9 \u06a9\u0644\u0645\u0647 \u06cc\u0627 \u0639\u0628\u0627\u0631\u062a")], need=("words",))
F("uwatch", "sec", "\u062f\u06cc\u062f\u0647\u200c\u0628\u0627\u0646",
  "\u0648\u0642\u062a\u06cc \u06a9\u0633\u06cc \u06a9\u0647 \u0631\u0635\u062f\u0634 \u0645\u06cc\u200c\u06a9\u0646\u06cc \u0622\u0646\u0644\u0627\u06cc\u0646 \u0634\u0648\u062f\u060c \u067e\u06cc\u0627\u0645\u062a \u0631\u0627 \u0628\u062e\u0648\u0627\u0646\u062f \u06cc\u0627 \u0634\u0631\u0648\u0639 \u0628\u0647 \u062a\u0627\u06cc\u067e \u06a9\u0646\u062f \u062e\u0628\u0631\u062a \u0645\u06cc\u200c\u06a9\u0646\u062f.",
  [pl("users", "\u0627\u0641\u0631\u0627\u062f \u0631\u0635\u062f\u0634\u062f\u0647", "user", "\u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0622\u06cc\u062f\u06cc \u0639\u062f\u062f\u06cc"),
   pc("what", "\u0686\u0647 \u0686\u06cc\u0632\u06cc\u061f", "all", [("all", "\u0647\u0645\u0647"), ("online", "\u0622\u0646\u0644\u0627\u06cc\u0646 \u0634\u062f\u0646"), ("typing", "\u062a\u0627\u06cc\u067e"), ("read", "\u062e\u0648\u0627\u0646\u062f\u0646 \u067e\u06cc\u0627\u0645")])],
  need=("users",))
F("welcome", "sec", "\u062e\u0648\u0634\u200c\u0622\u0645\u062f\u06af\u0648\u06cc\u06cc",
  "\u0628\u0647 \u0647\u0631 \u0639\u0636\u0648 \u062a\u0627\u0632\u0647\u200c\u06cc \u00ab\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u00bb \u062e\u0648\u0634\u200c\u0622\u0645\u062f \u0645\u06cc\u200c\u06af\u0648\u06cc\u062f.",
  [pt("text", "\u0645\u062a\u0646 \u062e\u0648\u0634\u200c\u0622\u0645\u062f", "\u0633\u0644\u0627\u0645 {name} \U0001f339 \u0628\u0647 \u06af\u0631\u0648\u0647 {group} \u062e\u0648\u0634 \u0627\u0648\u0645\u062f\u06cc!", "\u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u06cc \u0627\u0632 {name} \u0648 {group} \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u06a9\u0646\u06cc")])
F("alink", "sec", "\u0642\u0641\u0644 \u0644\u06cc\u0646\u06a9",
  "\u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u062f\u0627\u0631\u0627\u06cc \u0644\u06cc\u0646\u06a9 \u0631\u0627 (\u0627\u0632 \u063a\u06cc\u0631\u0627\u062f\u0645\u06cc\u0646\u200c\u0647\u0627) \u062f\u0631 \u00ab\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u00bb \u062d\u0630\u0641 \u0645\u06cc\u200c\u06a9\u0646\u062f.")
F("afwd", "sec", "\u0642\u0641\u0644 \u0641\u0648\u0631\u0648\u0627\u0631\u062f",
  "\u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u0641\u0648\u0631\u0648\u0627\u0631\u062f\u200c\u0634\u062f\u0647 \u0631\u0627 (\u0627\u0632 \u063a\u06cc\u0631\u0627\u062f\u0645\u06cc\u0646\u200c\u0647\u0627) \u062f\u0631 \u00ab\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u00bb \u062d\u0630\u0641 \u0645\u06cc\u200c\u06a9\u0646\u062f.")

#
F("areply", "auto", "\u0645\u0646\u0634\u06cc \u062e\u0648\u062f\u06a9\u0627\u0631",
  "\u0628\u0647 \u06a9\u0633\u0627\u0646\u06cc \u06a9\u0647 \u062f\u0631 \u067e\u06cc\u0648\u06cc \u067e\u06cc\u0627\u0645 \u0645\u06cc\u200c\u062f\u0647\u0646\u062f \u062e\u0648\u062f\u06a9\u0627\u0631 \u062c\u0648\u0627\u0628 \u0645\u06cc\u200c\u062f\u0647\u062f (\u0647\u0631 \u0646\u0641\u0631 \u062f\u0631 \u0647\u0631 \u0628\u0627\u0632\u0647 \u0641\u0642\u0637 \u06cc\u06a9\u200c\u0628\u0627\u0631).",
  [pt("text", "\u0645\u062a\u0646 \u067e\u0627\u0633\u062e", "\u0633\u0644\u0627\u0645 \U0001f339 \u0627\u0644\u0627\u0646 \u062f\u0631 \u062f\u0633\u062a\u0631\u0633 \u0646\u06cc\u0633\u062a\u0645\u060c \u0628\u0647\u200c\u0632\u0648\u062f\u06cc \u062c\u0648\u0627\u0628 \u0645\u06cc\u200c\u062f\u0647\u0645.", "\u0627\u0632 {name} \u0648 {time} \u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u06cc \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u06a9\u0646\u06cc"),
   pi("hours", "\u0641\u0627\u0635\u0644\u0647\u200c\u06cc \u067e\u0627\u0633\u062e \u0628\u0647 \u0647\u0631 \u0646\u0641\u0631 (\u0633\u0627\u0639\u062a)", 6, 1, 72),
   pc("who", "\u0628\u0647 \u0686\u0647 \u06a9\u0633\u0627\u0646\u06cc\u061f", "all", [("all", "\u0647\u0645\u0647"), ("stranger", "\u0641\u0642\u0637 \u063a\u06cc\u0631\u0645\u062e\u0627\u0637\u0628\u200c\u0647\u0627")])])
F("kreply", "auto", "\u067e\u0627\u0633\u062e \u06a9\u0644\u0645\u0647\u200c\u0627\u06cc",
  "\u0627\u06af\u0631 \u062f\u0631 \u067e\u06cc\u0648\u06cc \u06a9\u0633\u06cc \u06a9\u0644\u0645\u0647\u200c\u06cc \u0645\u0634\u062e\u0635\u06cc \u06af\u0641\u062a\u060c \u067e\u0627\u0633\u062e \u0622\u0645\u0627\u062f\u0647 \u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u062f. \u0647\u0631 \u0642\u0627\u0646\u0648\u0646: \u06a9\u0644\u0645\u0647=\u067e\u0627\u0633\u062e",
  [pl("rules", "\u0642\u0627\u0646\u0648\u0646\u200c\u0647\u0627", "kv", "\u0628\u0647 \u0627\u06cc\u0646 \u0634\u06a9\u0644 \u0628\u0641\u0631\u0633\u062a:  \u0633\u0644\u0627\u0645=\u062f\u0631\u0648\u062f \u0628\u0631 \u0634\u0645\u0627", mx=30)], need=("rules",))
F("dnd", "auto", "\u062d\u0627\u0644\u062a \u0633\u06a9\u0648\u062a \u0634\u0628\u0627\u0646\u0647",
  "\u062f\u0631 \u0633\u0627\u0639\u062a\u200c\u0647\u0627\u06cc \u0645\u0634\u062e\u0635 (\u0645\u062b\u0644\u0627\u064b \u0634\u0628) \u0628\u0647 \u067e\u06cc\u0648\u06cc\u200c\u0647\u0627 \u06cc\u06a9 \u067e\u06cc\u0627\u0645 \u00ab\u0627\u0644\u0627\u0646 \u062e\u0648\u0627\u0628\u0645\u00bb \u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u062f (\u0647\u0631 \u0646\u0641\u0631 \u0647\u0631 \u06f6 \u0633\u0627\u0639\u062a \u06cc\u06a9\u200c\u0628\u0627\u0631).",
  [pt("text", "\u0645\u062a\u0646 \u067e\u0627\u0633\u062e", "\u0633\u0644\u0627\u0645 \U0001f319 \u0627\u0644\u0627\u0646 \u0627\u0633\u062a\u0631\u0627\u062d\u062a \u0645\u06cc\u200c\u06a9\u0646\u0645\u060c \u0635\u0628\u062d \u062c\u0648\u0627\u0628 \u0645\u06cc\u200c\u062f\u0647\u0645.", "\u0627\u0632 {name} \u0648 {time} \u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u06cc \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u06a9\u0646\u06cc"),
   pi("start", "\u0627\u0632 \u0633\u0627\u0639\u062a (\u06f0 \u062a\u0627 \u06f2\u06f3)", 23, 0, 23),
   pi("end", "\u062a\u0627 \u0633\u0627\u0639\u062a (\u06f0 \u062a\u0627 \u06f2\u06f3)", 7, 0, 23)])
F("pvspam", "sec", "\u0636\u062f \u0627\u0633\u067e\u0645 \u067e\u06cc\u0648\u06cc",
  "\u0627\u06af\u0631 \u06cc\u06a9 \u063a\u0631\u06cc\u0628\u0647 \u062f\u0631 \u06f1\u06f0 \u062b\u0627\u0646\u06cc\u0647 \u0628\u06cc\u0634\u062a\u0631 \u0627\u0632 \u062d\u062f \u0645\u062c\u0627\u0632 \u067e\u06cc\u0627\u0645 \u0628\u0641\u0631\u0633\u062a\u062f\u060c \u062e\u0648\u062f\u06a9\u0627\u0631 \u0645\u0633\u062f\u0648\u062f \u0645\u06cc\u200c\u0634\u0648\u062f (\u0645\u062e\u0627\u0637\u0628\u06cc\u0646 \u0648 \u0648\u06cc\u0698\u0647\u200c\u0647\u0627 \u0645\u0633\u062a\u062b\u0646\u06cc\u200c\u0627\u0646\u062f).",
  [pi("limit", "\u062d\u062f\u0627\u06a9\u062b\u0631 \u067e\u06cc\u0627\u0645 \u062f\u0631 \u06f1\u06f0 \u062b\u0627\u0646\u06cc\u0647", 6, 3, 30)])
F("online", "auto", "\u0622\u0646\u0644\u0627\u06cc\u0646 \u0645\u0627\u0646\u062f\u0646",
  "\u062d\u0633\u0627\u0628\u062a \u0631\u0627 \u0647\u0645\u06cc\u0634\u0647 \u0622\u0646\u0644\u0627\u06cc\u0646 \u0646\u06af\u0647 \u0645\u06cc\u200c\u062f\u0627\u0631\u062f.")
F("aread", "auto", "\u062e\u0648\u0627\u0646\u062f\u0646 \u062e\u0648\u062f\u06a9\u0627\u0631 \u067e\u06cc\u0648\u06cc",
  "\u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u067e\u06cc\u0648\u06cc \u0631\u0627 \u062e\u0648\u062f\u06a9\u0627\u0631 \u00ab\u062e\u0648\u0627\u0646\u062f\u0647\u200c\u0634\u062f\u0647\u00bb \u0645\u06cc\u200c\u06a9\u0646\u062f.")
F("react", "auto", "\u0648\u0627\u06a9\u0646\u0634 \u062e\u0648\u062f\u06a9\u0627\u0631",
  "\u0628\u0647 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u0686\u062a\u200c\u0647\u0627\u06cc\u06cc \u06a9\u0647 \u0627\u0646\u062a\u062e\u0627\u0628 \u0645\u06cc\u200c\u06a9\u0646\u06cc \u062e\u0648\u062f\u06a9\u0627\u0631 \u0648\u0627\u06a9\u0646\u0634 (\u0631\u06cc\u200c\u0627\u06a9\u0634\u0646) \u0645\u06cc\u200c\u0632\u0646\u062f.",
  [pl("chats", "\u0686\u062a\u200c\u0647\u0627", "chat", "\u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0644\u06cc\u0646\u06a9 \u06a9\u0627\u0646\u0627\u0644/\u06af\u0631\u0648\u0647"),
   pt("emoji", "\u0627\u06cc\u0645\u0648\u062c\u06cc", "\U0001f44d", "\u0641\u0642\u0637 \u06cc\u06a9 \u0627\u06cc\u0645\u0648\u062c\u06cc")], need=("chats",))

#
F("fwd", "pub", "\u06a9\u067e\u06cc \u062e\u0648\u062f\u06a9\u0627\u0631 \u067e\u0633\u062a\u200c\u0647\u0627",
  "\u0647\u0631 \u067e\u0633\u062a \u062a\u0627\u0632\u0647\u200c\u06cc \u06cc\u06a9 \u06a9\u0627\u0646\u0627\u0644/\u06af\u0631\u0648\u0647 (\u0645\u0628\u062f\u0623) \u0631\u0627 \u0628\u062f\u0648\u0646 \u0628\u0631\u0686\u0633\u0628 \u0641\u0648\u0631\u0648\u0627\u0631\u062f \u062f\u0631 \u0645\u0642\u0635\u062f \u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u062f. \u0642\u0627\u0646\u0648\u0646: \u0645\u0628\u062f\u0623 > \u0645\u0642\u0635\u062f (\u06a9\u0627\u0646\u0627\u0644\u200c\u0647\u0627\u06cc \u0645\u062d\u0627\u0641\u0638\u062a\u200c\u0634\u062f\u0647 \u0646\u0627\u062f\u06cc\u062f\u0647 \u06af\u0631\u0641\u062a\u0647 \u0645\u06cc\u200c\u0634\u0648\u0646\u062f)",
  [pl("rules", "\u0642\u0627\u0646\u0648\u0646\u200c\u0647\u0627", "fwd", "\u0628\u0647 \u0627\u06cc\u0646 \u0634\u06a9\u0644 \u0628\u0641\u0631\u0633\u062a:  @source > @dest", mx=10)], need=("rules",))

#
F("ttl", "dl", "\u0630\u062e\u06cc\u0631\u0647\u200c\u06cc \u0645\u062f\u06cc\u0627\u06cc \u062a\u0627\u06cc\u0645\u0631\u062f\u0627\u0631",
  "\u0639\u06a9\u0633/\u0648\u06cc\u062f\u06cc\u0648\u06cc \u00ab\u06cc\u06a9\u200c\u0628\u0627\u0631 \u0645\u0634\u0627\u0647\u062f\u0647\u00bb \u0648 \u062a\u0627\u06cc\u0645\u0631\u062f\u0627\u0631 \u06a9\u0647 \u062f\u0631 \u067e\u06cc\u0648\u06cc \u0628\u0631\u0627\u06cc\u062a \u0645\u06cc\u200c\u0622\u06cc\u062f \u0631\u0627 \u0630\u062e\u06cc\u0631\u0647 \u0648 \u0628\u0631\u0627\u06cc\u062a \u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u062f.")

#
F("cname", "look", "\u0633\u0627\u0639\u062a \u062f\u0631 \u0646\u0627\u0645",
  "\u0633\u0627\u0639\u062a \u0631\u0627 \u06a9\u0646\u0627\u0631 \u0627\u0633\u0645\u062a \u0646\u0645\u0627\u06cc\u0634 \u0645\u06cc\u200c\u062f\u0647\u062f \u0648 \u0647\u0631 \u062f\u0642\u06cc\u0642\u0647 \u0628\u0647\u200c\u0631\u0648\u0632 \u0645\u06cc\u200c\u06a9\u0646\u062f.",
  [pt("base", "\u0627\u0633\u0645 \u067e\u0627\u06cc\u0647", "", "\u0627\u06af\u0631 \u062e\u0627\u0644\u06cc \u0628\u0627\u0634\u062f \u0627\u0632 \u0627\u0633\u0645 \u0641\u0639\u0644\u06cc \u06af\u0631\u0641\u062a\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f"),
   pt("fmt", "\u0642\u0627\u0644\u0628", "{name} | {time}", "\u0627\u0632 {name} \u0648 {time} \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u06a9\u0646"),
   pc("digits", "\u0641\u0648\u0646\u062a \u0633\u0627\u0639\u062a", "en", CLOCK_FONT_OPTS),
   pc("hour", "\u0642\u0627\u0644\u0628 \u0633\u0627\u0639\u062a", "24", [("24", "\u06f2\u06f4 \u0633\u0627\u0639\u062a\u0647"), ("12", "\u06f1\u06f2 \u0633\u0627\u0639\u062a\u0647")]),
   pc("tz", "\u0645\u0646\u0637\u0642\u0647\u200c\u06cc \u0632\u0645\u0627\u0646\u06cc", str(TZ_OFFSET_MIN), TZ_OPTS)])
F("cbio", "look", "\u0633\u0627\u0639\u062a \u062f\u0631 \u0628\u06cc\u0648",
  "\u0633\u0627\u0639\u062a \u0631\u0627 \u062f\u0631 \u0628\u06cc\u0648\u06cc \u062d\u0633\u0627\u0628\u062a \u0645\u06cc\u200c\u06af\u0630\u0627\u0631\u062f \u0648 \u0647\u0631 \u062f\u0642\u06cc\u0642\u0647 \u0628\u0647\u200c\u0631\u0648\u0632 \u0645\u06cc\u200c\u06a9\u0646\u062f. (\u0628\u06cc\u0648 \u062d\u062f\u0627\u06a9\u062b\u0631 \u06f7\u06f0 \u0646\u0648\u06cc\u0633\u0647\u061b \u0628\u0627 \u067e\u0631\u06cc\u0645\u06cc\u0648\u0645 \u06f1\u06f4\u06f0)",
  [pt("base", "\u0645\u062a\u0646 \u0628\u06cc\u0648", "", "\u0627\u06af\u0631 \u062e\u0627\u0644\u06cc \u0628\u0627\u0634\u062f \u0627\u0632 \u0628\u06cc\u0648\u06cc \u0641\u0639\u0644\u06cc \u06af\u0631\u0641\u062a\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f"),
   pt("fmt", "\u0642\u0627\u0644\u0628", "{bio} | \u23f0 {time}", "\u0627\u0632 {bio} \u0648 {time} \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u06a9\u0646"),
   pc("digits", "\u0641\u0648\u0646\u062a \u0633\u0627\u0639\u062a", "en", CLOCK_FONT_OPTS),
   pc("hour", "\u0642\u0627\u0644\u0628 \u0633\u0627\u0639\u062a", "24", [("24", "\u06f2\u06f4 \u0633\u0627\u0639\u062a\u0647"), ("12", "\u06f1\u06f2 \u0633\u0627\u0639\u062a\u0647")]),
   pc("tz", "\u0645\u0646\u0637\u0642\u0647\u200c\u06cc \u0632\u0645\u0627\u0646\u06cc", str(TZ_OFFSET_MIN), TZ_OPTS)])
F("brot", "look", "\u0628\u06cc\u0648\u06cc \u0686\u0631\u062e\u0634\u06cc",
  "\u0628\u06cc\u0648 \u0631\u0627 \u0628\u0647\u200c\u0635\u0648\u0631\u062a \u0686\u0631\u062e\u0634\u06cc \u0628\u06cc\u0646 \u0686\u0646\u062f \u0645\u062a\u0646 \u0639\u0648\u0636 \u0645\u06cc\u200c\u06a9\u0646\u062f. (\u0627\u06af\u0631 \u00ab\u0633\u0627\u0639\u062a \u062f\u0631 \u0628\u06cc\u0648\u00bb \u0631\u0648\u0634\u0646 \u0628\u0627\u0634\u062f\u060c \u0622\u0646 \u0627\u0648\u0644\u0648\u06cc\u062a \u062f\u0627\u0631\u062f.)",
  [pl("bios", "\u0628\u06cc\u0648\u0647\u0627", "text", "\u062d\u062f\u0627\u06a9\u062b\u0631 \u06f7\u06f0 \u0646\u0648\u06cc\u0633\u0647", mx=12), pi("mins", "\u062a\u063a\u06cc\u06cc\u0631 \u0647\u0631 \u0686\u0646\u062f \u062f\u0642\u06cc\u0642\u0647", 30, 10, 720)],
  need=("bios",))
F("mstyle", "look", "\u0641\u0631\u0645\u062a \u062e\u0648\u062f\u06a9\u0627\u0631 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627",
  "\u062a\u0645\u0627\u0645 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc\u06cc \u06a9\u0647 \u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u06cc \u0631\u0627 \u062e\u0648\u062f\u06a9\u0627\u0631 \u0628\u0627 \u06cc\u06a9 \u0627\u0633\u062a\u0627\u06cc\u0644 \u0645\u06cc\u200c\u06a9\u0646\u062f. (\u067e\u06cc\u0627\u0645\u200c\u0647\u0627 \u00ab\u0648\u06cc\u0631\u0627\u06cc\u0634\u200c\u0634\u062f\u0647\u00bb \u062f\u06cc\u062f\u0647 \u0645\u06cc\u200c\u0634\u0648\u0646\u062f.)",
  [pc("style", "\u0627\u0633\u062a\u0627\u06cc\u0644", "bold", [("bold", "\u0628\u0648\u0644\u062f"), ("italic", "\u0627\u06cc\u062a\u0627\u0644\u06cc\u06a9"), ("mono", "\u062a\u06a9\u200c\u0641\u0627\u0635\u0644\u0647"), ("underline", "\u0632\u06cc\u0631\u062e\u0637"),
                                   ("strike", "\u062e\u0637\u200c\u062e\u0648\u0631\u062f\u0647"), ("spoiler", "\u0627\u0633\u067e\u0648\u06cc\u0644\u0631"), ("quote", "\u0646\u0642\u0644\u200c\u0642\u0648\u0644")])])
F("msign", "look", "\u0627\u0645\u0636\u0627\u06cc \u067e\u06cc\u0627\u0645",
  "\u0632\u06cc\u0631 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u0645\u062a\u0646\u06cc\u200c\u0627\u062a \u06cc\u06a9 \u0627\u0645\u0636\u0627 \u0627\u0636\u0627\u0641\u0647 \u0645\u06cc\u200c\u06a9\u0646\u062f. (\u067e\u06cc\u0627\u0645\u200c\u0647\u0627 \u00ab\u0648\u06cc\u0631\u0627\u06cc\u0634\u200c\u0634\u062f\u0647\u00bb \u062f\u06cc\u062f\u0647 \u0645\u06cc\u200c\u0634\u0648\u0646\u062f.)",
  [pt("sig", "\u0645\u062a\u0646 \u0627\u0645\u0636\u0627", "", "\u0645\u062b\u0644\u0627\u064b: \u2014 \u0639\u0644\u06cc"),
   pc("where", "\u06a9\u062c\u0627\u061f", "groups", [("groups", "\u0641\u0642\u0637 \u06af\u0631\u0648\u0647\u200c\u0647\u0627"), ("all", "\u0647\u0645\u0647\u200c\u062c\u0627")])], need=("sig",))

#
F("vip", "rel", "\u0645\u062e\u0627\u0637\u0628\u0627\u0646 \u0648\u06cc\u0698\u0647",
  "\u0647\u0631 \u067e\u06cc\u0627\u0645\u06cc \u06a9\u0647 \u0627\u0632 \u0627\u06cc\u0646 \u0627\u0641\u0631\u0627\u062f \u0628\u0631\u0627\u06cc\u062a \u0628\u06cc\u0627\u06cc\u062f (\u062d\u062a\u06cc \u0627\u06af\u0631 \u0686\u062a \u0628\u06cc\u200c\u0635\u062f\u0627 \u0628\u0627\u0634\u062f) \u062f\u0631 \u0647\u0645\u06cc\u0646 \u0631\u0628\u0627\u062a \u062e\u0628\u0631\u062a \u0645\u06cc\u200c\u06a9\u0646\u062f \u0648 \u0642\u0641\u0644 \u067e\u06cc\u0648\u06cc/\u0645\u0646\u0634\u06cc \u0631\u0648\u06cc \u0622\u0646\u200c\u0647\u0627 \u0627\u0639\u0645\u0627\u0644 \u0646\u0645\u06cc\u200c\u0634\u0648\u062f.",
  [pl("users", "\u0627\u0641\u0631\u0627\u062f \u0648\u06cc\u0698\u0647", "user", "\u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0622\u06cc\u062f\u06cc \u0639\u062f\u062f\u06cc")], need=("users",))

#
F("dot", "tools", "\u062f\u0633\u062a\u0648\u0631\u0627\u062a \u0646\u0642\u0637\u0647\u200c\u0627\u06cc",
  "\u0628\u0627 \u062a\u0627\u06cc\u067e \u062f\u0633\u062a\u0648\u0631 \u062f\u0631 \u0647\u0631 \u0686\u062a (\u0645\u062b\u0644 .ping \u06cc\u0627 .help) \u0627\u0632 \u062d\u0633\u0627\u0628 \u062e\u0648\u062f\u062a \u06a9\u0627\u0631 \u0627\u0646\u062c\u0627\u0645 \u0645\u06cc\u200c\u062f\u0647\u06cc. \u0644\u06cc\u0633\u062a \u06a9\u0627\u0645\u0644 \u0631\u0627 \u0628\u0627 .help \u0628\u0628\u06cc\u0646.", on=True)

#
F("sched", "game", "\u0627\u0631\u0633\u0627\u0644 \u0632\u0645\u0627\u0646\u200c\u0628\u0646\u062f\u06cc\u200c\u0634\u062f\u0647",
  "\u0647\u0631 \u0686\u0646\u062f \u062f\u0642\u06cc\u0642\u0647 \u06cc\u06a9 \u0645\u062a\u0646/\u062f\u0633\u062a\u0648\u0631 \u0631\u0627 \u0628\u0647 \u06cc\u06a9 \u0686\u062a \u06cc\u0627 \u0631\u0628\u0627\u062a \u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u062f (\u0645\u062b\u0644\u0627\u064b \u062f\u0631\u06cc\u0627\u0641\u062a \u062c\u0627\u06cc\u0632\u0647\u200c\u06cc \u0631\u0648\u0632\u0627\u0646\u0647\u200c\u06cc \u0631\u0628\u0627\u062a\u200c\u0647\u0627\u06cc \u0628\u0627\u0632\u06cc). "
  "\u0642\u0627\u0646\u0648\u0646: \u0686\u062a | \u062f\u0642\u06cc\u0642\u0647 | \u0645\u062a\u0646  (\u062d\u062f\u0627\u0642\u0644 \u06f1\u06f0 \u062f\u0642\u06cc\u0642\u0647)",
  [pl("jobs", "\u06a9\u0627\u0631\u0647\u0627", "sched", "\u0645\u062b\u0644\u0627\u064b:  @SomeGameBot | 480 | /daily", mx=10)], need=("jobs",))
F("click", "game", "\u06a9\u0644\u06cc\u06a9 \u062e\u0648\u062f\u06a9\u0627\u0631 \u0631\u0648\u06cc \u062f\u06a9\u0645\u0647",
  "\u0648\u0642\u062a\u06cc \u062f\u0631 \u06cc\u06a9 \u0686\u062a/\u0631\u0628\u0627\u062a \u067e\u06cc\u0627\u0645\u06cc \u0628\u0627 \u062f\u06a9\u0645\u0647\u200c\u06cc \u0645\u0634\u062e\u0635 \u0628\u06cc\u0627\u06cc\u062f\u060c \u062e\u0648\u062f\u06a9\u0627\u0631 \u0631\u0648\u06cc \u0622\u0646 \u062f\u06a9\u0645\u0647 \u0645\u06cc\u200c\u0632\u0646\u062f. \u0642\u0627\u0646\u0648\u0646: \u0686\u062a | \u0645\u062a\u0646 \u062f\u06a9\u0645\u0647",
  [pl("rules", "\u0642\u0627\u0646\u0648\u0646\u200c\u0647\u0627", "click", "\u0645\u062b\u0644\u0627\u064b:  @SomeGameBot | Claim", mx=10)], need=("rules",))

GROUP_FEATS = ("asilent", "welcome", "alink", "afwd")

ACTIONS = [
    ("st", "\U0001f4ca \u0648\u0636\u0639\u06cc\u062a \u0648 \u067e\u06cc\u0646\u06af"),
    ("ch", "\U0001f6aa \u06a9\u0627\u0646\u0627\u0644\u200c\u0647\u0627 \u0648 \u06af\u0631\u0648\u0647\u200c\u0647\u0627 (\u062e\u0631\u0648\u062c)"),
    ("ses", "\U0001f511 \u0646\u0634\u0633\u062a\u200c\u0647\u0627\u06cc \u0641\u0639\u0627\u0644 \u062d\u0633\u0627\u0628"),
    ("mg", "\U0001f465 \u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc"),
    ("d24", "\U0001f9f9 \u062d\u0630\u0641 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u06f2\u06f4 \u0633\u0627\u0639\u062a\u0647\u200c\u06cc \u0645\u0646"),
    ("clr", "\U0001f5d1 \u067e\u0627\u06a9\u0633\u0627\u0632\u06cc \u062d\u0627\u0641\u0638\u0647\u200c\u06cc \u067e\u06cc\u0627\u0645\u200c\u0647\u0627"),
]

S = {}   #


def load_settings(uid, raw):
    try:
        d = json.loads(raw or "{}")
    except Exception:
        d = {}
    d.setdefault("f", {})
    d.setdefault("mg", [])
    S[uid] = d


def save_settings(uid):
    DB.q("UPDATE users SET settings=? WHERE id=?", (json.dumps(S[uid], ensure_ascii=False), uid))


def spec(key, name):
    for p in FEATS[key]["params"]:
        if p["n"] == name:
            return p
    return None


def is_on(uid, key):
    d = S.get(uid, {}).get("f", {}).get(key)
    return bool(d["on"]) if d and "on" in d else FEATS[key]["on"]


def get_p(uid, key, name):
    d = S.get(uid, {}).get("f", {}).get(key)
    if d and name in d.get("p", {}):
        return d["p"][name]
    sp = spec(key, name)
    dv = sp["d"] if sp else None
    return list(dv) if isinstance(dv, list) else dv


def _slot(uid, key):
    f = S[uid]["f"].setdefault(key, {})
    f.setdefault("p", {})
    return f


def set_p(uid, key, name, val):
    _slot(uid, key)["p"][name] = val
    save_settings(uid)


def set_on(uid, key, on):
    _slot(uid, key)["on"] = bool(on)
    save_settings(uid)


def in_list(uid, key, name, ident):
    for it in (get_p(uid, key, name) or []):
        if isinstance(it, dict) and it.get("id") == ident:
            return True
    return False


def idset(uid, key, name="users"):
    if not is_on(uid, key):
        return set()
    return set(it.get("id") for it in (get_p(uid, key, name) or []) if isinstance(it, dict))


def is_managed(uid, chat_id):
    return any(g.get("id") == chat_id for g in S.get(uid, {}).get("mg", []))


def count_on(uid):
    return sum(1 for k in FEATS if is_on(uid, k))


# ============================================================================
#
# ============================================================================
BOT = None
RTS = {}      #


def make_client(session):
    kw = dict(device_model="Self Speed", system_version="Android", app_version="1.0",
              lang_code="fa", system_lang_code="fa", connection_retries=10, retry_delay=3,
              auto_reconnect=True)
    if MTPROXY:
        try:
            from telethon.network.connection.tcpmtproxy import ConnectionTcpMTProxyRandomizedIntermediate
            host, port, secret = MTPROXY.split(":")
            kw["connection"] = ConnectionTcpMTProxyRandomizedIntermediate
            kw["proxy"] = (host, int(port), secret)
        except Exception as e:
            log.warning("MTPROXY invalid: %s", e)
    return TelegramClient(session, API_ID, API_HASH, **kw)


class RT(object):
    """\u0648\u0636\u0639\u06cc\u062a \u0627\u062c\u0631\u0627\u06cc\u06cc \u0633\u0644\u0641\u200c\u0628\u0627\u062a \u06cc\u06a9 \u06a9\u0627\u0631\u0628\u0631"""

    def __init__(self, uid, client):
        self.uid = uid
        self.client = client
        self.me = None
        self.started = time.time()
        self.tasks = []
        self.known = set()          #
        self.own = []               #
        self.last = {}
        self.gaps = {}
        self.clicked = collections.deque(maxlen=500)
        self.admin_cache = {}
        self.pend_auth = {}
        self.creator_groups = []
        self.cg_ts = 0
        self.clock_block = 0
        self.last_name = None
        self.last_bio = None
        self.ping = None

    #
    def due(self, name, sec):
        now = time.time()
        if now - self.last.get(name, 0) >= sec:
            self.last[name] = now
            return True
        return False

    def allow(self, name, gap):
        now = time.time()
        if now - self.gaps.get(name, 0) >= gap:
            self.gaps[name] = now
            if len(self.gaps) > 2000:
                self.gaps = dict(list(self.gaps.items())[-500:])
            return True
        return False

    #
    def mark_own(self, chat_id, text):
        now = time.time()
        self.own = [o for o in self.own if o[2] > now]
        self.own.append((chat_id, text, now + 20))

    def is_own(self, chat_id, text):
        now = time.time()
        self.own = [o for o in self.own if o[2] > now]
        for i, o in enumerate(self.own):
            if o[0] == chat_id and o[1] == text:
                del self.own[i]
                return True
        return False

    async def send(self, chat, text, **kw):
        if isinstance(chat, int):
            cid = chat
        else:
            cid = utils.get_peer_id(await self.client.get_input_entity(chat))
        self.mark_own(cid, text)
        return await self.client.send_message(chat, text, **kw)


async def notify(uid, text, file=None, buttons=None):
    """\u067e\u06cc\u0627\u0645 \u0628\u0647 \u06a9\u0627\u0631\u0628\u0631 \u0627\u0632 \u0637\u0631\u06cc\u0642 \u0631\u0628\u0627\u062a \u06a9\u0646\u062a\u0631\u0644 (\u062f\u0631 \u0635\u0648\u0631\u062a \u062e\u0637\u0627\u060c \u062f\u0631 Saved Messages)"""
    for btn in ((buttons, None) if buttons else (None,)):
        try:
            if file and os.path.exists(file):
                await BOT.send_message(uid, text[:3500], parse_mode="html", link_preview=False, buttons=btn)
                await BOT.send_file(uid, file)
            else:
                await BOT.send_message(uid, text[:4000], parse_mode="html", link_preview=False, buttons=btn)
            return True
        except Exception as e:
            log.warning("notify via bot failed for %s: %s", uid, e)
    rt = RTS.get(uid)
    if rt:
        try:
            await rt.client.send_message("me", re.sub(r"<[^>]+>", "", html.unescape(text))[:4000])
            return True
        except Exception:
            pass
    return False


async def safe(rt, fn, *a):
    try:
        await fn(rt, *a)
    except asyncio.CancelledError:
        raise
    except AUTH_DEAD as e:
        await session_dead(rt, e)
    except errors.FloodWaitError as e:
        log.warning("FloodWait %ss in %s (uid %s)", getattr(e, "seconds", "?"), fn.__name__, rt.uid)
    except Exception:
        log.exception("%s failed (uid %s)", fn.__name__, rt.uid)


async def ent(rt, item):
    """\u067e\u06cc\u062f\u0627 \u06a9\u0631\u062f\u0646 \u0686\u062a \u0627\u0632 \u0631\u0648\u06cc \u0622\u06cc\u062a\u0645 \u0630\u062e\u06cc\u0631\u0647\u200c\u0634\u062f\u0647"""
    try:
        return await rt.client.get_input_entity(item["id"])
    except Exception:
        u = item.get("u")
        if u:
            return await rt.client.get_input_entity(u)
        raise


async def is_admin(rt, chat_id, user_id):
    key = (chat_id, user_id)
    c = rt.admin_cache.get(key)
    if c and time.time() - c[1] < 300:
        return c[0]
    try:
        p = await rt.client.get_permissions(chat_id, user_id)
        v = bool(p and p.is_admin)
    except Exception:
        v = False
    rt.admin_cache[key] = (v, time.time())
    return v


def describe_media(m):
    if m.photo:
        return "\U0001f4f7 \u0639\u06a9\u0633"
    if m.voice:
        return "\U0001f3a4 \u0648\u06cc\u0633"
    if m.video_note:
        return "\u2b55 \u0648\u06cc\u062f\u06cc\u0648 \u0645\u0633\u06cc\u062c"
    if m.video:
        return "\U0001f3ac \u0648\u06cc\u062f\u06cc\u0648"
    if m.audio:
        return "\U0001f3b5 \u0645\u0648\u0632\u06cc\u06a9"
    if m.sticker:
        return "\U0001f3f7 \u0627\u0633\u062a\u06cc\u06a9\u0631"
    if m.gif:
        return "\U0001f39e \u06af\u06cc\u0641"
    if m.document:
        n = getattr(m.file, "name", None)
        return "\U0001f4ce \u0641\u0627\u06cc\u0644" + (": " + n if n else "")
    if m.geo:
        return "\U0001f4cd \u0645\u0648\u0642\u0639\u06cc\u062a"
    if m.contact:
        return "\U0001f464 \u0645\u062e\u0627\u0637\u0628"
    if m.poll:
        return "\U0001f4ca \u0646\u0638\u0631\u0633\u0646\u062c\u06cc"
    return "\U0001f4e6 \u0631\u0633\u0627\u0646\u0647"


#
async def start_rt(uid, client=None):
    if uid in RTS:
        return RTS[uid]
    if client is None:
        row = DB.one("SELECT session FROM users WHERE id=?", (uid,))
        client = make_client(StringSession(dec(row[0])))
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            raise SessionDead()
    rt = RT(uid, client)
    rt.me = await client.get_me()
    RTS[uid] = rt
    try:
        await client.get_dialogs(limit=200)     #
    except Exception as e:
        log.warning("dialogs preload failed: %s", e)
    attach(rt)
    rt.tasks.append(asyncio.create_task(ticker(rt)))
    DB.q("UPDATE users SET status='active', last_seen=? WHERE id=?", (int(time.time()), uid))
    log.info("selfbot started for %s", uid)
    return rt


class SessionDead(Exception):
    pass


async def stop_rt(uid):
    rt = RTS.pop(uid, None)
    if not rt:
        return
    cur = asyncio.current_task()
    for t in rt.tasks:
        if t is not cur:
            t.cancel()
    try:
        await rt.client.disconnect()
    except Exception:
        pass


async def session_dead(rt, e=None):
    uid = rt.uid
    if RTS.get(uid) is not rt:
        return
    log.warning("session dead for %s: %s", uid, e)
    DB.q("UPDATE users SET status='down' WHERE id=?", (uid,))
    await notify(uid, "\U0001f4e1 <b>\u06cc\u0648\u0632\u0631\u0628\u0627\u062a \u0634\u0645\u0627 \u0642\u0637\u0639 \u0634\u062f</b>\n\n\u0628\u0647 \u0627\u062d\u062a\u0645\u0627\u0644 \u0632\u06cc\u0627\u062f \u0646\u0634\u0633\u062a \u062a\u0644\u06af\u0631\u0627\u0645 \u0622\u0646 \u0628\u0633\u062a\u0647 \u06cc\u0627 \u0645\u0646\u0642\u0636\u06cc \u0634\u062f\u0647 \u0627\u0633\u062a.\n"
                      "\u0628\u0631\u0627\u06cc \u0648\u0635\u0644 \u06a9\u0631\u062f\u0646 \u062f\u0648\u0628\u0627\u0631\u0647 \u0631\u0648\u06cc \u062f\u06a9\u0645\u0647\u200c\u06cc \u0632\u06cc\u0631 \u0628\u0632\u0646\u061b \u06cc\u06a9 \u06a9\u062f \u0648\u0631\u0648\u062f \u062a\u0627\u0632\u0647 \u0628\u0631\u0627\u06cc\u062a \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f.",
                 buttons=[[Button.inline("\U0001f504 \u0648\u0631\u0648\u062f \u062f\u0648\u0628\u0627\u0631\u0647", "rl")]])
    await stop_rt(uid)


#
def attach(rt):
    c = rt.client

    async def _msg(ev):
        await safe(rt, h_msg, ev)

    async def _edit(ev):
        await safe(rt, h_edit, ev)

    async def _del(ev):
        await safe(rt, h_deleted, ev)

    async def _act(ev):
        await safe(rt, h_action, ev)

    async def _uu(ev):
        await safe(rt, h_uu, ev)

    async def _read(ev):
        await safe(rt, h_read, ev)

    async def _raw(upd):
        await safe(rt, h_raw, upd)

    c.add_event_handler(_msg, events.NewMessage())
    c.add_event_handler(_edit, events.MessageEdited())
    c.add_event_handler(_del, events.MessageDeleted())
    c.add_event_handler(_act, events.ChatAction())
    c.add_event_handler(_uu, events.UserUpdate())
    c.add_event_handler(_read, events.MessageRead())
    c.add_event_handler(_raw, events.Raw(types.UpdatePendingJoinRequests))


#
async def h_msg(rt, ev):
    m = ev.message
    await safe(rt, do_forward, ev)
    if m.out:
        await h_out(rt, ev)
        return
    await safe(rt, do_autoclick, ev)
    await safe(rt, do_react, ev)
    await safe(rt, do_keywatch, ev)
    if ev.is_private:
        await safe(rt, do_private, ev)
    elif ev.is_group:
        await safe(rt, do_group, ev)


async def do_forward(rt, ev):
    uid = rt.uid
    if not is_on(uid, "fwd"):
        return
    m = ev.message
    if m.action:
        return
    for r in get_p(uid, "fwd", "rules") or []:
        if r.get("s") != ev.chat_id:
            continue
        chat = await ev.get_chat()
        if getattr(chat, "noforwards", False):
            continue
        dst = await ent(rt, {"id": r["d"], "u": r.get("du")})
        await rt.client.send_message(dst, m)


async def do_autoclick(rt, ev):
    uid = rt.uid
    if not is_on(uid, "click"):
        return
    m = ev.message
    if m.out or not m.buttons:
        return
    rules = [r for r in (get_p(uid, "click", "rules") or []) if r.get("id") == ev.chat_id]
    if not rules:
        return
    ed = int(m.edit_date.timestamp()) if getattr(m, "edit_date", None) else 0
    key = (ev.chat_id, m.id, ed)
    if key in rt.clicked:
        return
    for r in rules:
        want = r["b"].lower()
        for row in m.buttons:
            for b in row:
                if getattr(b, "url", None):
                    continue
                if want in (b.text or "").lower():
                    rt.clicked.append(key)
                    await asyncio.sleep(random.uniform(1.0, 3.0))
                    await b.click()
                    return


async def do_react(rt, ev):
    uid = rt.uid
    if not is_on(uid, "react") or not in_list(uid, "react", "chats", ev.chat_id):
        return
    m = ev.message
    if m.action:
        return
    emoji = (get_p(uid, "react", "emoji") or "\U0001f44d").strip()
    await asyncio.sleep(random.uniform(1.0, 4.0))
    peer = await ev.get_input_chat()
    try:
        await rt.client(functions.messages.SendReactionRequest(
            peer=peer, msg_id=m.id, reaction=[types.ReactionEmoji(emoticon=emoji)]))
    except errors.ReactionInvalidError:
        if rt.allow("react_bad", 3600):
            await notify(uid, "\u26a0\ufe0f \u0627\u06cc\u0645\u0648\u062c\u06cc \u00ab%s\u00bb \u062f\u0631 \u0622\u0646 \u0686\u062a \u0628\u0647\u200c\u0639\u0646\u0648\u0627\u0646 \u0648\u0627\u06a9\u0646\u0634 \u0645\u062c\u0627\u0632 \u0646\u06cc\u0633\u062a." % esc(emoji))


async def do_keywatch(rt, ev):
    uid = rt.uid
    if not is_on(uid, "kwatch"):
        return
    m = ev.message
    text = m.raw_text or ""
    if not text:
        return
    low = text.lower()
    hit = [w for w in (get_p(uid, "kwatch", "words") or []) if w.lower() in low]
    if not hit or not rt.allow("kw", 2):
        return
    chat = await ev.get_chat()
    sender = await ev.get_sender()
    link = ""
    if getattr(chat, "username", None):
        link = "\n\U0001f517 https://t.me/%s/%d" % (chat.username, m.id)
    elif isinstance(chat, types.Channel):
        link = "\n\U0001f517 https://t.me/c/%d/%d" % (chat.id, m.id)
    await notify(uid, "\U0001f50e <b>\u0634\u0646\u0648\u062f</b>: \u00ab%s\u00bb\n\U0001f4ac \u0686\u062a: %s\n\U0001f464 \u0627\u0632: %s\n\n%s%s" % (
        esc("\u060c ".join(hit)), esc(uname(chat)), ulabel(sender), esc(text[:600]), link))


#
async def is_member(rt, chan, user_id):
    try:
        ch = await ent(rt, chan)
        us = await rt.client.get_input_entity(user_id)
        await rt.client(functions.channels.GetParticipantRequest(channel=ch, participant=us))
        return True
    except errors.UserNotParticipantError:
        return False
    except Exception as e:
        log.warning("membership check failed: %s", e)
        return True


async def has_history_out(rt, sender):
    try:
        msgs = await rt.client.get_messages(sender.id, limit=30)
        return any(x.out for x in msgs)
    except Exception:
        return False


SPAMQ = {}


async def do_private(rt, ev):
    uid = rt.uid
    m = ev.message
    sender = await ev.get_sender()
    if not isinstance(sender, types.User):
        return
    if sender.bot or sender.id in SERVICE_IDS or getattr(sender, "is_self", False):
        return
    if is_on(uid, "adel") or is_on(uid, "aedit"):
        await safe(rt, cache_in, m, sender)
    if is_on(uid, "ttl") and getattr(m.media, "ttl_seconds", None):
        await safe(rt, save_ttl, m, sender)
    vips = idset(uid, "vip")
    vip = sender.id in vips
    if vip:
        body = (m.raw_text or "").strip() or describe_media(m)
        await notify(uid, "\U0001f49e <b>\u067e\u06cc\u0627\u0645 \u0627\u0632 \u0645\u062e\u0627\u0637\u0628 \u0648\u06cc\u0698\u0647</b>\n\U0001f464 %s\n\n%s" % (ulabel(sender), esc(body[:800])))
    if is_on(uid, "pvspam") and not vip and not (sender.contact or getattr(sender, "mutual_contact", False)):
        dq = SPAMQ.setdefault((uid, sender.id), collections.deque(maxlen=60))
        now_ = time.time()
        dq.append(now_)
        if sum(1 for x in dq if now_ - x <= 10) > int(get_p(uid, "pvspam", "limit") or 6):
            SPAMQ.pop((uid, sender.id), None)
            try:
                await rt.client(functions.contacts.BlockRequest(id=await rt.client.get_input_entity(sender)))
            except Exception as e:
                log.warning("spam block failed: %s", e)
            await notify(uid, "\U0001f6e1 <b>\u0636\u062f \u0627\u0633\u067e\u0645</b>\n%s \u0628\u0647\u200c\u062e\u0627\u0637\u0631 \u0627\u0631\u0633\u0627\u0644 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u067e\u0634\u062a\u200c\u0633\u0631\u0647\u0645 \u0645\u0633\u062f\u0648\u062f \u0634\u062f." % ulabel(sender))
            return
    if is_on(uid, "aread"):
        try:
            await rt.client.send_read_acknowledge(ev.chat_id, m)
        except Exception:
            pass
    if is_on(uid, "pvlock") and not vip:
        if await pv_lock(rt, ev, sender):
            return
    if is_on(uid, "areply") or is_on(uid, "kreply") or is_on(uid, "dnd"):
        await auto_replies(rt, ev, sender, vip)


async def pv_lock(rt, ev, sender):
    uid = rt.uid
    if sender.contact or getattr(sender, "mutual_contact", False):
        return False
    if sender.id in rt.known or in_list(uid, "pvlock", "ok", sender.id):
        return False
    if await has_history_out(rt, sender):
        rt.known.add(sender.id)
        return False
    limit = int(get_p(uid, "pvlock", "warns") or 3)
    n = int(kv_get(uid, "w:%d" % sender.id, 0) or 0) + 1
    if n > limit:
        await rt.client(functions.contacts.BlockRequest(id=await rt.client.get_input_entity(sender)))
        kv_del(uid, "w:%d" % sender.id)
        await notify(uid, "\U0001f512 <b>\u0642\u0641\u0644 \u067e\u06cc\u0648\u06cc</b>\n%s \u0628\u0639\u062f \u0627\u0632 %s \u0627\u062e\u0637\u0627\u0631 \u0645\u0633\u062f\u0648\u062f \u0634\u062f." % (ulabel(sender), fa(limit)))
        return True
    kv_set(uid, "w:%d" % sender.id, n)
    msg = get_p(uid, "pvlock", "msg") or ""
    await rt.send(ev.chat_id, "%s\n\n\u26a0\ufe0f \u0627\u062e\u0637\u0627\u0631 %s \u0627\u0632 %s" % (tpl(msg, sender), fa(n), fa(limit)))
    return True


async def gate(rt, ev, sender):
    """\u0639\u0636\u0648\u06cc\u062a \u0627\u062c\u0628\u0627\u0631\u06cc: \u0622\u06cc\u0627 \u0627\u062c\u0627\u0632\u0647\u200c\u06cc \u067e\u0627\u0633\u062e\u200c\u06af\u0648\u06cc\u06cc \u0647\u0633\u062a\u061f"""
    uid = rt.uid
    if not is_on(uid, "fjoin"):
        return True
    ch = get_p(uid, "fjoin", "chan")
    if not ch:
        return True
    if await is_member(rt, ch, sender.id):
        return True
    if rt.allow("fj%d" % sender.id, 600):
        who = ("@" + ch["u"]) if ch.get("u") else ch.get("n", "\u06a9\u0627\u0646\u0627\u0644")
        await rt.send(ev.chat_id, "\u0628\u0631\u0627\u06cc \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u0627\u0632 \u067e\u0627\u0633\u062e\u200c\u06af\u0648\u06cc\u06cc \u062e\u0648\u062f\u06a9\u0627\u0631\u060c \u0627\u0648\u0644 \u0639\u0636\u0648 \u06a9\u0627\u0646\u0627\u0644 %s \u0634\u0648 \u0648 \u0628\u0639\u062f \u062f\u0648\u0628\u0627\u0631\u0647 \u067e\u06cc\u0627\u0645 \u0628\u062f\u0647 \U0001f339" % who)
    return False


async def auto_replies(rt, ev, sender, vip):
    uid = rt.uid
    m = ev.message
    text = (m.raw_text or "").strip()
    if not text and not m.media:
        return
    low = text.lower()
    if is_on(uid, "kreply") and low:
        for r in get_p(uid, "kreply", "rules") or []:
            k, _, ans = r.partition("=")
            k, ans = k.strip().lower(), ans.strip()
            if k and ans and k in low:
                if not await gate(rt, ev, sender):
                    return
                await rt.send(ev.chat_id, tpl(ans, sender), reply_to=m.id)
                return
    if is_on(uid, "dnd") and not vip:
        h = now_local().hour
        a, b = int(get_p(uid, "dnd", "start")), int(get_p(uid, "dnd", "end"))
        inwin = (a <= h < b) if a < b else (h >= a or h < b)
        if inwin:
            k = "dnd:%d" % sender.id
            if time.time() - float(kv_get(uid, k, 0) or 0) >= 6 * 3600:
                kv_set(uid, k, time.time())
                await rt.send(ev.chat_id, tpl(get_p(uid, "dnd", "text") or "", sender))
                return
    if is_on(uid, "areply") and not vip:
        if get_p(uid, "areply", "who") == "stranger" and (sender.contact or sender.id in rt.known):
            return
        hours = int(get_p(uid, "areply", "hours") or 6)
        k = "ar:%d" % sender.id
        last = float(kv_get(uid, k, 0) or 0)
        if time.time() - last < hours * 3600:
            return
        if not await gate(rt, ev, sender):
            return
        kv_set(uid, k, time.time())
        await rt.send(ev.chat_id, tpl(get_p(uid, "areply", "text") or "", sender))


#
async def cache_in(rt, m, sender):
    uid = rt.uid
    media = describe_media(m) if m.media else None
    path = None
    if m.media and is_on(uid, "adel") and get_p(uid, "adel", "media") == "yes":
        try:
            size = getattr(m.file, "size", 0) or 0
            limit = int(get_p(uid, "adel", "maxmb") or 10) * 1024 * 1024
            if m.file and size <= limit and (m.photo or m.voice or m.video_note or m.video or m.audio or m.document) \
                    and not m.sticker:
                path = await m.download_media(file=os.path.join(CACHE_DIR, "%d_%d_%d" % (uid, abs(m.chat_id or 0), m.id)))
        except Exception as e:
            log.warning("media cache failed: %s", e)
    DB.q("INSERT OR REPLACE INTO cache(uid,chat_id,msg_id,sender_id,sender_name,text,media,path,date,out) "
         "VALUES(?,?,?,?,?,?,?,?,?,0)",
         (uid, m.chat_id, m.id, sender.id, uname(sender) + ((" (@" + sender.username + ")") if sender.username else ""),
          m.raw_text or "", media, path, int(m.date.timestamp())))


async def save_ttl(rt, m, sender):
    uid = rt.uid
    path = await m.download_media(file=os.path.join(CACHE_DIR, "ttl_%d_%d" % (uid, m.id)))
    await notify(uid, "\u23f3 <b>\u0645\u062f\u06cc\u0627\u06cc \u062a\u0627\u06cc\u0645\u0631\u062f\u0627\u0631</b> \u0627\u0632 %s \u0630\u062e\u06cc\u0631\u0647 \u0634\u062f:" % ulabel(sender), file=path)
    if path:
        try:
            os.remove(path)
        except Exception:
            pass


async def h_deleted(rt, ev):
    uid = rt.uid
    if not is_on(uid, "adel"):
        return
    if ev.chat_id is not None and ev.chat_id < 0:      #
        return
    ids = ev.deleted_ids or []
    rows = []
    for mid in ids:
        r = DB.one("SELECT sender_name,text,media,path,date,chat_id FROM cache WHERE uid=? AND msg_id=? AND out=0 AND chat_id>0",
                   (uid, mid))
        if r:
            rows.append(r)
    if not rows:
        return
    if len(ids) > 5:
        await notify(uid, "\U0001f5d1 <b>\u0636\u062f \u062d\u0630\u0641</b>\n%s \u067e\u06cc\u0627\u0645 \u06cc\u06a9\u200c\u062c\u0627 \u067e\u0627\u06a9 \u0634\u062f (\u0627\u062d\u062a\u0645\u0627\u0644\u0627\u064b \u067e\u0627\u06a9\u200c\u06a9\u0631\u062f\u0646 \u062a\u0627\u0631\u06cc\u062e\u0686\u0647\u200c\u06cc \u0686\u062a). "
                          "\u0646\u0633\u062e\u0647\u200c\u06cc \u0622\u0646\u200c\u0647\u0627 \u062a\u0627 \u06f4\u06f8 \u0633\u0627\u0639\u062a \u062f\u0631 \u062d\u0627\u0641\u0638\u0647\u200c\u06cc \u0631\u0628\u0627\u062a \u0647\u0633\u062a." % fa(len(ids)))
        return
    for name, text, media, path, date, chat_id in rows:
        t = datetime.fromtimestamp(date, timezone.utc) + timedelta(minutes=TZ_OFFSET_MIN)
        msg = "\U0001f5d1 <b>\u067e\u06cc\u0627\u0645 \u062d\u0630\u0641 \u0634\u062f</b>\n\U0001f464 \u0627\u0632: %s\n\U0001f552 \u0627\u0631\u0633\u0627\u0644: %s\n" % (esc(name), fa(t.strftime("%H:%M")))
        if media:
            msg += "\U0001f4ce %s\n" % esc(media)
        if text:
            msg += "\n\U0001f4dd %s" % esc(text[:3000])
        await notify(uid, msg, file=path)


async def h_edit(rt, ev):
    uid = rt.uid
    m = ev.message
    if m.out:
        return
    await safe(rt, do_autoclick, ev)
    if not ev.is_private or not is_on(uid, "aedit"):
        return
    sender = await ev.get_sender()
    if not isinstance(sender, types.User) or sender.bot or sender.id in SERVICE_IDS:
        return
    new = m.raw_text or ""
    r = DB.one("SELECT text FROM cache WHERE uid=? AND chat_id=? AND msg_id=?", (uid, ev.chat_id, m.id))
    if r is None:
        await cache_in(rt, m, sender)
        return
    old = r[0] or ""
    if old != new:
        await notify(uid, "\u270f\ufe0f <b>\u067e\u06cc\u0627\u0645 \u0648\u06cc\u0631\u0627\u06cc\u0634 \u0634\u062f</b>\n\U0001f464 \u0627\u0632: %s\n\n<b>\u0642\u0628\u0644:</b>\n%s\n\n<b>\u0628\u0639\u062f:</b>\n%s" % (
            ulabel(sender), esc(old[:1500] or "\u2014"), esc(new[:1500] or "\u2014")))
        DB.q("UPDATE cache SET text=? WHERE uid=? AND chat_id=? AND msg_id=?", (new, uid, ev.chat_id, m.id))


#
LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|\b[\w-]+\.(com|ir|me|org|net|io|info|xyz)\b)", re.I)


def has_link(m):
    for e in (m.entities or []):
        if isinstance(e, (types.MessageEntityUrl, types.MessageEntityTextUrl)):
            return True
    return bool(LINK_RE.search(m.raw_text or ""))


async def do_group(rt, ev):
    uid = rt.uid
    if not is_managed(uid, ev.chat_id):
        return
    m = ev.message
    sid = m.sender_id
    if sid is None or sid == rt.me.id:
        return
    try:
        if sid in idset(uid, "asilent"):
            await m.delete()
            return
        if is_on(uid, "alink") and has_link(m) and not await is_admin(rt, ev.chat_id, sid):
            await m.delete()
            return
        if is_on(uid, "afwd") and m.fwd_from and not await is_admin(rt, ev.chat_id, sid):
            await m.delete()
            return
    except errors.ChatAdminRequiredError:
        if rt.allow("noadmin%d" % ev.chat_id, 3600):
            await notify(uid, "\u26a0\ufe0f \u062f\u0631 \u06af\u0631\u0648\u0647 \u00ab%s\u00bb \u0627\u062c\u0627\u0632\u0647\u200c\u06cc \u062d\u0630\u0641 \u067e\u06cc\u0627\u0645 \u0646\u062f\u0627\u0631\u0645\u061b \u0642\u0627\u0628\u0644\u06cc\u062a\u200c\u0647\u0627\u06cc \u06af\u0631\u0648\u0647\u06cc \u0622\u0646\u062c\u0627 \u06a9\u0627\u0631 \u0646\u0645\u06cc\u200c\u06a9\u0646\u062f." % esc(uname(await ev.get_chat())))
    except errors.MessageDeleteForbiddenError:
        pass


async def h_action(rt, ev):
    uid = rt.uid
    if not (ev.user_joined or ev.user_added) or not is_on(uid, "welcome"):
        return
    if not is_managed(uid, ev.chat_id):
        return
    users = await ev.get_users()
    chat = await ev.get_chat()
    text = get_p(uid, "welcome", "text") or ""
    for u in users or []:
        if getattr(u, "bot", False) or u.id == rt.me.id:
            continue
        if not rt.allow("wl%d" % ev.chat_id, 3):
            await asyncio.sleep(3)
        out = text.replace("{name}", uname(u)).replace("{group}", getattr(chat, "title", "") or "")
        await rt.send(ev.chat_id, out)


async def h_raw(rt, upd):
    uid = rt.uid
    if not is_on(uid, "joinreq"):
        return
    peer = await rt.client.get_input_entity(upd.peer)
    await rt.client(functions.messages.HideAllChatJoinRequestsRequest(peer=peer, approved=True))
    try:
        title = uname(await rt.client.get_entity(upd.peer))
    except Exception:
        title = ""
    await notify(uid, "\u2705 %s \u062f\u0631\u062e\u0648\u0627\u0633\u062a \u0639\u0636\u0648\u06cc\u062a \u062f\u0631 \u00ab%s\u00bb \u062a\u0623\u06cc\u06cc\u062f \u0634\u062f." % (fa(upd.requests_pending), esc(title)))


#
async def h_uu(rt, ev):
    uid = rt.uid
    if not is_on(uid, "uwatch"):
        return
    who = ev.user_id
    if not in_list(uid, "uwatch", "users", who):
        return
    what = get_p(uid, "uwatch", "what")
    kind = None
    if ev.online and what in ("all", "online"):
        kind = "online"
    elif ev.typing and what in ("all", "typing"):
        kind = "typing"
    if not kind or not rt.allow("uw%s%d" % (kind, who), 300):
        return
    u = await ev.get_user()
    await notify(uid, ("\U0001f7e2 %s \u0622\u0646\u0644\u0627\u06cc\u0646 \u0634\u062f" if kind == "online" else "\u2328\ufe0f %s \u062f\u0631 \u062d\u0627\u0644 \u062a\u0627\u06cc\u067e \u0627\u0633\u062a") % ulabel(u))


async def h_read(rt, ev):
    uid = rt.uid
    if not is_on(uid, "uwatch") or get_p(uid, "uwatch", "what") not in ("all", "read"):
        return
    who = ev.chat_id
    if who is None or not in_list(uid, "uwatch", "users", who) or not rt.allow("uwr%d" % who, 180):
        return
    try:
        u = await rt.client.get_entity(who)
    except Exception:
        u = None
    await notify(uid, "\U0001f441 %s \u067e\u06cc\u0627\u0645 \u062a\u0648 \u0631\u0627 \u062e\u0648\u0627\u0646\u062f" % (ulabel(u) if u else str(who)))


#
STYLES = {
    "bold": types.MessageEntityBold, "italic": types.MessageEntityItalic, "mono": types.MessageEntityCode,
    "underline": types.MessageEntityUnderline, "strike": types.MessageEntityStrike,
    "spoiler": types.MessageEntitySpoiler, "quote": types.MessageEntityBlockquote,
}
DICE = {"dice": "\U0001f3b2", "\u062a\u0627\u0633": "\U0001f3b2", "dart": "\U0001f3af", "\u062f\u0627\u0631\u062a": "\U0001f3af", "ball": "\U0001f3c0", "\u0628\u0633\u06a9\u062a": "\U0001f3c0",
        "foot": "\u26bd", "\u0641\u0648\u062a\u0628\u0627\u0644": "\u26bd", "slot": "\U0001f3b0", "\u0627\u0633\u0644\u0627\u062a": "\U0001f3b0", "bowl": "\U0001f3b3", "\u0628\u0648\u0644\u06cc\u0646\u06af": "\U0001f3b3"}

HELP_CMDS = (
    "\U0001f9f0 <b>\u062f\u0633\u062a\u0648\u0631\u0627\u062a \u0646\u0642\u0637\u0647\u200c\u0627\u06cc</b> (\u062f\u0631 \u0647\u0631 \u0686\u062a \u062a\u0627\u06cc\u067e \u06a9\u0646)\n\n"
    "<code>.ping</code> \u067e\u06cc\u0646\u06af\n"
    "<code>.time</code> \u0633\u0627\u0639\u062a \u0648 \u062a\u0627\u0631\u06cc\u062e\n"
    "<code>.id</code> \u0622\u06cc\u062f\u06cc \u0686\u062a/\u06a9\u0627\u0631\u0628\u0631 (\u0631\u0648\u06cc \u067e\u06cc\u0627\u0645 \u0631\u06cc\u067e\u0644\u0627\u06cc \u06a9\u0646)\n"
    "<code>.info</code> \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u06a9\u0627\u0631\u0628\u0631 (\u0631\u06cc\u067e\u0644\u0627\u06cc \u06cc\u0627 \u062f\u0631 \u067e\u06cc\u0648\u06cc)\n"
    "<code>.del 5</code> \u062d\u0630\u0641 \u06f5 \u067e\u06cc\u0627\u0645 \u0622\u062e\u0631 \u062e\u0648\u062f\u062a \u062f\u0631 \u0647\u0645\u06cc\u0646 \u0686\u062a\n"
    "<code>.save</code> \u0630\u062e\u06cc\u0631\u0647\u200c\u06cc \u067e\u06cc\u0627\u0645\u0650 \u0631\u06cc\u067e\u0644\u0627\u06cc\u200c\u0634\u062f\u0647 \u062f\u0631 Saved Messages\n"
    "<code>.mute</code> / <code>.unmute</code> \u0628\u06cc\u200c\u0635\u062f\u0627 / \u0635\u062f\u0627\u062f\u0627\u0631 \u06a9\u0631\u062f\u0646 \u0647\u0645\u06cc\u0646 \u0686\u062a\n"
    "<code>.calc 2*(3+4)</code> \u0645\u0627\u0634\u06cc\u0646\u200c\u062d\u0633\u0627\u0628\n"
    "<code>.dice .dart .ball .foot .slot .bowl</code> \u062a\u0627\u0633 \u0648 \u0628\u0627\u0632\u06cc\u200c\u0647\u0627\u06cc \u0645\u062a\u062d\u0631\u06a9\n"
    "<code>.type \u0645\u062a\u0646</code> \u062a\u0627\u06cc\u067e\u200c\u0634\u062f\u0646\u0650 \u062d\u0631\u0641\u200c\u0628\u0647\u200c\u062d\u0631\u0641  \u2022  <code>.sd 10 \u0645\u062a\u0646</code> \u067e\u06cc\u0627\u0645 \u062e\u0648\u062f\u062d\u0630\u0641 (\u062b\u0627\u0646\u06cc\u0647)\n"
    "<code>.rev \u0645\u062a\u0646</code> \u0628\u0631\u0639\u06a9\u0633  \u2022  <code>.coin</code> \u0634\u06cc\u0631 \u06cc\u0627 \u062e\u0637  \u2022  <code>.rand 1 100</code> \u0639\u062f\u062f \u062a\u0635\u0627\u062f\u0641\u06cc  \u2022  <code>.pass 12</code> \u0631\u0645\u0632 \u0642\u0648\u06cc\n"
    "<code>.manage</code> \u0627\u0641\u0632\u0648\u062f\u0646/\u062d\u0630\u0641 \u0627\u06cc\u0646 \u06af\u0631\u0648\u0647 \u0628\u0647 \u00ab\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u00bb\n"
    "<code>.get \u0644\u06cc\u0646\u06a9</code> \u06af\u0631\u0641\u062a\u0646 \u067e\u06cc\u0627\u0645 \u0627\u0632 \u0644\u06cc\u0646\u06a9 t.me \u0639\u0645\u0648\u0645\u06cc\n"
    "<code>.help</code> \u0647\u0645\u06cc\u0646 \u0631\u0627\u0647\u0646\u0645\u0627"
)


async def h_out(rt, ev):
    uid = rt.uid
    m = ev.message
    text = m.raw_text or ""
    if rt.is_own(ev.chat_id, text):
        return
    if text.startswith(".") and len(text) > 1 and is_on(uid, "dot"):
        if await run_cmd(rt, ev, text):
            return
    if is_on(uid, "track") and not m.action:
        DB.q("INSERT OR REPLACE INTO cache(uid,chat_id,msg_id,sender_id,sender_name,text,media,path,date,out) "
             "VALUES(?,?,?,?,?,?,?,?,?,1)",
             (uid, ev.chat_id, m.id, rt.me.id, "", text[:100], None, None, int(m.date.timestamp())))
    await style_sign(rt, ev, m, text)


async def style_sign(rt, ev, m, text):
    uid = rt.uid
    st, sg = is_on(uid, "mstyle"), is_on(uid, "msign")
    if not (st or sg) or not text:
        return
    if (m.media and not isinstance(m.media, types.MessageMediaWebPage)) or m.fwd_from or m.via_bot_id:
        return
    if text.startswith(("/", ".")):
        return
    new = text
    ents = list(m.entities or [])
    if sg:
        sig = (get_p(uid, "msign", "sig") or "").strip()
        if sig and (get_p(uid, "msign", "where") == "all" or not ev.is_private):
            new = text + "\n\n" + sig
    if st:
        cls = STYLES.get(get_p(uid, "mstyle", "style"))
        if cls:
            ents.append(cls(offset=0, length=u16(new)))
    if new == text and not st:
        return
    await rt.client.edit_message(m, new, formatting_entities=ents, link_preview=bool(m.media))


async def measure_ping(client):
    """\u067e\u06cc\u0646\u06af \u0648\u0627\u0642\u0639\u06cc\u0650 \u062e\u0648\u062f\u0650 \u0633\u0644\u0641 \u062a\u0627 \u0633\u0631\u0648\u0631\u0647\u0627\u06cc \u062a\u0644\u06af\u0631\u0627\u0645 (\u0645\u06cc\u0627\u0646\u0647\u200c\u06cc \u06f3 \u0628\u0627\u0631 \u0627\u0646\u062f\u0627\u0632\u0647\u200c\u06af\u06cc\u0631\u06cc)"""
    vals = []
    for _ in range(3):
        t0 = time.perf_counter()
        await client(functions.PingRequest(ping_id=random.getrandbits(62)))
        vals.append(int((time.perf_counter() - t0) * 1000))
    vals.sort()
    return vals[1]


async def run_cmd(rt, ev, text):
    m = ev.message
    c = rt.client
    parts = text[1:].split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""
    if cmd in ("help", "\u0631\u0627\u0647\u0646\u0645\u0627"):
        await m.edit(HELP_CMDS, parse_mode="html")
    elif cmd == "ping":
        ms = await measure_ping(c)
        rt.ping = ms
        await m.edit("\U0001f3d3 \u067e\u06cc\u0646\u06af \u0633\u0644\u0641: %s ms" % fa(ms))
    elif cmd in ("time", "\u0633\u0627\u0639\u062a"):
        t = now_local()
        await m.edit("\U0001f552 %s\n\U0001f4c5 %s\n\U0001f5d3 %s" % (fa(t.strftime("%H:%M:%S")), jdate_str(t), t.strftime("%Y-%m-%d")))
    elif cmd == "id":
        r = await m.get_reply_message()
        lines = ["\U0001f194 \u0686\u062a: <code>%s</code>" % ev.chat_id, "\U0001f464 \u0634\u0645\u0627: <code>%s</code>" % rt.me.id]
        if r is not None:
            lines.append("\u21a9\ufe0f \u0641\u0631\u0633\u062a\u0646\u062f\u0647\u200c\u06cc \u067e\u06cc\u0627\u0645: <code>%s</code>" % r.sender_id)
        await m.edit("\n".join(lines), parse_mode="html")
    elif cmd == "info":
        r = await m.get_reply_message()
        target = (await r.get_sender()) if r is not None else (await ev.get_chat())
        info = ["\u2139\ufe0f <b>%s</b>" % esc(uname(target)), "\U0001f194 <code>%s</code>" % target.id]
        if getattr(target, "username", None):
            info.append("\U0001f517 @%s" % esc(target.username))
        for attr, label in (("bot", "\U0001f916 \u0631\u0628\u0627\u062a"), ("premium", "\U0001f48e \u067e\u0631\u06cc\u0645\u06cc\u0648\u0645"), ("verified", "\u2714\ufe0f \u062a\u0623\u06cc\u06cc\u062f\u0634\u062f\u0647"),
                            ("contact", "\U0001f4c7 \u062f\u0631 \u0645\u062e\u0627\u0637\u0628\u06cc\u0646 \u0634\u0645\u0627")):
            if getattr(target, attr, False):
                info.append(label)
        await m.edit("\n".join(info), parse_mode="html")
    elif cmd in ("del", "\u062d\u0630\u0641"):
        n = int(arg.translate(EN_DIGITS)) if arg.translate(EN_DIGITS).isdigit() else 1
        n = max(1, min(n, 100))
        ids = [x.id async for x in c.iter_messages(ev.chat_id, from_user="me", limit=n + 1)]
        if m.id not in ids:
            ids.append(m.id)
        await c.delete_messages(ev.chat_id, ids)
    elif cmd in ("save", "\u0630\u062e\u06cc\u0631\u0647"):
        r = await m.get_reply_message()
        if r is None:
            await m.edit("\u0631\u0648\u06cc \u06cc\u06a9 \u067e\u06cc\u0627\u0645 \u0631\u06cc\u067e\u0644\u0627\u06cc \u06a9\u0646 \u0648 \u0628\u0646\u0648\u06cc\u0633 .save")
        else:
            try:
                await c.forward_messages("me", r)
                await m.edit("\u2705 \u0630\u062e\u06cc\u0631\u0647 \u0634\u062f")
            except Exception:
                await m.edit("\u274c \u0627\u06cc\u0646 \u067e\u06cc\u0627\u0645 \u0642\u0627\u0628\u0644 \u0630\u062e\u06cc\u0631\u0647 \u0646\u06cc\u0633\u062a")
            await asyncio.sleep(2)
            await m.delete()
    elif cmd in ("mute", "unmute", "\u0633\u06a9\u0648\u062a"):
        peer = await ev.get_input_chat()
        until = 2 ** 31 - 1 if cmd != "unmute" else 0
        await c(functions.account.UpdateNotifySettingsRequest(
            peer=types.InputNotifyPeer(peer=peer), settings=types.InputPeerNotifySettings(mute_until=until)))
        await m.edit("\U0001f515 \u0628\u06cc\u200c\u0635\u062f\u0627 \u0634\u062f" if until else "\U0001f514 \u0635\u062f\u0627\u062f\u0627\u0631 \u0634\u062f")
        await asyncio.sleep(2)
        await m.delete()
    elif cmd in ("calc", "\u062d\u0633\u0627\u0628"):
        try:
            v = calc(arg)
            if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
                v = int(v)
            await m.edit("\U0001f9ee %s = %s" % (arg, v))
        except Exception:
            await m.edit("\u274c \u0639\u0628\u0627\u0631\u062a \u0646\u0627\u0645\u0639\u062a\u0628\u0631")
    elif cmd in DICE:
        await m.delete()
        await c.send_file(ev.chat_id, types.InputMediaDice(DICE[cmd]))
    elif cmd in ("type", "\u062a\u0627\u06cc\u067e"):
        if not arg:
            await m.edit("\u0645\u062b\u0627\u0644: .type \u0633\u0644\u0627\u0645 \u062f\u0646\u06cc\u0627")
        else:
            out = ""
            for ch in arg[:40]:
                out += ch
                try:
                    await m.edit(out + "\u258c")
                except errors.MessageNotModifiedError:
                    pass
                await asyncio.sleep(0.4)
            await m.edit(out)
    elif cmd == "sd":
        a = arg.split(None, 1)
        if len(a) == 2 and a[0].isdigit():
            await m.edit(a[1] + "\n\n\u23f3 \u062d\u0630\u0641 \u062e\u0648\u062f\u06a9\u0627\u0631 \u062a\u0627 %s \u062b\u0627\u0646\u06cc\u0647" % fa(min(int(a[0]), 600)))
            await asyncio.sleep(min(int(a[0]), 600))
            await m.delete()
        else:
            await m.edit("\u0645\u062b\u0627\u0644: .sd 10 \u0627\u06cc\u0646 \u067e\u06cc\u0627\u0645 \u0628\u0639\u062f \u0627\u0632 \u06f1\u06f0 \u062b\u0627\u0646\u06cc\u0647 \u067e\u0627\u06a9 \u0645\u06cc\u200c\u0634\u0648\u062f")
    elif cmd in ("rev", "\u0628\u0631\u0639\u06a9\u0633"):
        await m.edit(arg[::-1] if arg else "\u0645\u062b\u0627\u0644: .rev \u0645\u062a\u0646")
    elif cmd in ("coin", "\u0633\u06a9\u0647"):
        await m.edit("\U0001fa99 " + random.choice(["\u0634\u06cc\u0631", "\u062e\u0637"]))
    elif cmd in ("rand", "\u0631\u0646\u062f\u0648\u0645"):
        a = arg.translate(EN_DIGITS).split()
        try:
            lo, hi = (int(a[0]), int(a[1])) if len(a) >= 2 else (1, int(a[0]))
            await m.edit("\U0001f3b2 %s" % fa(random.randint(min(lo, hi), max(lo, hi))))
        except Exception:
            await m.edit("\u0645\u062b\u0627\u0644: .rand 1 100")
    elif cmd in ("pass", "\u0631\u0645\u0632"):
        n = int(arg) if arg.isdigit() and 4 <= int(arg) <= 40 else 12
        chars = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%&*"
        await m.edit("\U0001f511 <code>%s</code>" % "".join(random.SystemRandom().choice(chars) for _ in range(n)), parse_mode="html")
    elif cmd in ("manage", "\u0645\u062f\u06cc\u0631\u06cc\u062a"):
        if ev.is_private:
            await m.edit("\u0627\u06cc\u0646 \u062f\u0633\u062a\u0648\u0631 \u0631\u0627 \u062f\u0627\u062e\u0644 \u06af\u0631\u0648\u0647 \u0628\u0632\u0646.")
        else:
            chat = await ev.get_chat()
            mg = S[rt.uid]["mg"]
            hit = [g for g in mg if g["id"] == ev.chat_id]
            if hit:
                mg.remove(hit[0])
                msg = "\u2796 \u0627\u06cc\u0646 \u06af\u0631\u0648\u0647 \u0627\u0632 \u00ab\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u00bb \u062d\u0630\u0641 \u0634\u062f"
            else:
                mg.append({"id": ev.chat_id, "n": uname(chat), "u": getattr(chat, "username", None)})
                msg = "\u2795 \u0627\u06cc\u0646 \u06af\u0631\u0648\u0647 \u0628\u0647 \u00ab\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u00bb \u0627\u0636\u0627\u0641\u0647 \u0634\u062f"
            save_settings(rt.uid)
            await m.edit(msg)
            await asyncio.sleep(3)
            await m.delete()
    elif cmd in ("get", "\u06af\u0631\u0641\u062a\u0646"):
        mm = re.search(r"t\.me/(c/)?([\w]+)/(\d+)", arg)
        if not mm:
            await m.edit("\u0644\u06cc\u0646\u06a9 \u067e\u06cc\u0627\u0645 t.me \u0631\u0627 \u0628\u0639\u062f \u0627\u0632 .get \u0628\u0646\u0648\u06cc\u0633")
        else:
            peer = types.PeerChannel(int(mm.group(2))) if mm.group(1) else mm.group(2)
            src = await c.get_entity(peer)
            if getattr(src, "noforwards", False):
                await m.edit("\U0001f512 \u0627\u06cc\u0646 \u0686\u062a \u0645\u062d\u062a\u0648\u0627\u06cc \u0645\u062d\u0627\u0641\u0638\u062a\u200c\u0634\u062f\u0647 \u062f\u0627\u0631\u062f.")
            else:
                msg = await c.get_messages(src, ids=int(mm.group(3)))
                if not msg:
                    await m.edit("\u274c \u067e\u06cc\u0627\u0645 \u067e\u06cc\u062f\u0627 \u0646\u0634\u062f")
                else:
                    await m.delete()
                    await c.send_message(ev.chat_id, msg)
    else:
        return False
    return True


#
def clock_str(uid, key):
    try:
        off = int(get_p(uid, key, "tz"))
    except Exception:
        off = TZ_OFFSET_MIN
    t = datetime.now(timezone.utc) + timedelta(minutes=off, seconds=3)
    if get_p(uid, key, "hour") == "12":
        txt = "%d:%02d %s" % (t.hour % 12 or 12, t.minute, "AM" if t.hour < 12 else "PM")
    else:
        txt = t.strftime("%H:%M")
    return fontify(txt, get_p(uid, key, "digits"))


async def job_clock(rt, now):
    uid = rt.uid
    if now < rt.clock_block or not rt.due("clock", 3):
        return
    try:
        if is_on(uid, "cname"):
            base = get_p(uid, "cname", "base") or (rt.me.first_name or "")
            fmt = get_p(uid, "cname", "fmt") or "{name} | {time}"
            tm = clock_str(uid, "cname")
            new = fmt.replace("{name}", base).replace("{time}", tm)
            if len(new) > 64:
                over = len(new) - 64
                new = fmt.replace("{name}", base[:max(1, len(base) - over)]).replace("{time}", tm)[:64]
            if new != rt.last_name:
                await rt.client(functions.account.UpdateProfileRequest(first_name=new))
                rt.last_name = new
        limit = 140 if getattr(rt.me, "premium", False) else 70
        text = None
        if is_on(uid, "cbio"):
            base = get_p(uid, "cbio", "base") or ""
            fmt = get_p(uid, "cbio", "fmt") or "{bio} | \u23f0 {time}"
            tm = clock_str(uid, "cbio")
            text = fmt.replace("{bio}", base).replace("{time}", tm)
            if len(text) > limit:
                over = len(text) - limit
                text = fmt.replace("{bio}", base[:max(0, len(base) - over)]).replace("{time}", tm)[:limit]
        elif is_on(uid, "brot"):
            bios = get_p(uid, "brot", "bios") or []
            if bios:
                mins = int(get_p(uid, "brot", "mins") or 30)
                text = bios[int(now // (mins * 60)) % len(bios)][:limit]
        if text is not None and text != rt.last_bio:
            await rt.client(functions.account.UpdateProfileRequest(about=text))
            rt.last_bio = text
    except errors.FloodWaitError as e:
        rt.clock_block = now + e.seconds + 5


async def job_online(rt, now):
    if is_on(rt.uid, "online") and rt.due("online", 240):
        await rt.client(functions.account.UpdateStatusRequest(offline=False))


async def job_health(rt, now):
    if not rt.due("health", 180):
        return
    t0 = time.perf_counter()
    try:
        await rt.client(functions.PingRequest(ping_id=random.getrandbits(62)))
        rt.ping = int((time.perf_counter() - t0) * 1000)
    except AUTH_DEAD:
        raise
    except Exception as e:
        log.warning("ping failed for %s: %s", rt.uid, e)
    await rt.client.get_me()


async def job_sched(rt, now):
    uid = rt.uid
    if not is_on(uid, "sched") or not rt.due("sched", 30):
        return
    for j in get_p(uid, "sched", "jobs") or []:
        k = "sch:%s" % j["j"]
        last = float(kv_get(uid, k, 0) or 0)
        if now - last >= max(10, j["m"]) * 60:
            kv_set(uid, k, now)
            try:
                await rt.send(await ent(rt, j), j["t"])
            except errors.FloodWaitError:
                raise
            except Exception as e:
                log.warning("sched send failed: %s", e)
            await asyncio.sleep(2)


async def kick_auth(rt, h, auto=False):
    uid = rt.uid
    try:
        await rt.client(functions.account.ResetAuthorizationRequest(hash=h))
        rt.pend_auth.pop(h, None)
        await notify(uid, "\U0001f6ab \u0646\u0634\u0633\u062a \u0645\u0634\u06a9\u0648\u06a9 %s \u0628\u06cc\u0631\u0648\u0646 \u0627\u0646\u062f\u0627\u062e\u062a\u0647 \u0634\u062f." % ("(\u062e\u0648\u062f\u06a9\u0627\u0631)" if auto else ""))
        return True
    except errors.FreshResetAuthorisationForbiddenError:
        rt.pend_auth[h] = float("inf")
        await notify(uid, "\u26a0\ufe0f \u0647\u0646\u0648\u0632 \u06f2\u06f4 \u0633\u0627\u0639\u062a \u0627\u0632 \u0648\u0631\u0648\u062f \u0631\u0628\u0627\u062a \u0628\u0647 \u062d\u0633\u0627\u0628\u062a \u0646\u06af\u0630\u0634\u062a\u0647 \u0648 \u062a\u0644\u06af\u0631\u0627\u0645 \u0627\u062c\u0627\u0632\u0647\u200c\u06cc \u0627\u062e\u0631\u0627\u062c \u0646\u0634\u0633\u062a \u0631\u0627 \u0646\u0645\u06cc\u200c\u062f\u0647\u062f.\n"
                          "\u062f\u0633\u062a\u06cc \u0627\u0632 \u00ab\u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u062a\u0644\u06af\u0631\u0627\u0645 \u2190 \u062f\u0633\u062a\u06af\u0627\u0647\u200c\u0647\u0627\u00bb \u0622\u0646 \u0631\u0627 \u0628\u0628\u0646\u062f.")
        return False


async def job_alogin(rt, now):
    uid = rt.uid
    if not is_on(uid, "alogin") or not rt.due("alogin", 45):
        return
    r = await rt.client(functions.account.GetAuthorizationsRequest())
    cur = set(a.hash for a in r.authorizations)
    raw = kv_get(uid, "auth_known")
    if raw is None:
        kv_set(uid, "auth_known", json.dumps(sorted(cur)))
        return
    known = set(json.loads(raw))
    grace = int(get_p(uid, "alogin", "grace") or 3) * 60
    for a in r.authorizations:
        h = a.hash
        if a.current or h in known:
            continue
        if h not in rt.pend_auth:
            rt.pend_auth[h] = now + grace
            where = "\u060c ".join(x for x in (a.country, a.region) if x)
            await notify(uid, "\U0001f6a8 <b>\u0648\u0631\u0648\u062f \u062a\u0627\u0632\u0647 \u0628\u0647 \u062d\u0633\u0627\u0628\u062a</b>\n\U0001f4f1 %s %s\n\U0001f30d %s\n\U0001f310 IP: <code>%s</code>\n\n"
                              "\u0627\u06af\u0631 \u062e\u0648\u062f\u062a \u0646\u06cc\u0633\u062a\u06cc \u0627\u062e\u0631\u0627\u062c\u0634 \u06a9\u0646\u061b \u062f\u0631 \u063a\u06cc\u0631 \u0627\u06cc\u0646 \u0635\u0648\u0631\u062a \u0628\u0639\u062f \u0627\u0632 %s \u062f\u0642\u06cc\u0642\u0647 \u062e\u0648\u062f\u06a9\u0627\u0631 \u0627\u062e\u0631\u0627\u062c \u0645\u06cc\u200c\u0634\u0648\u062f." % (
                                  esc(a.device_model), esc(a.app_name), esc(where or "\u0646\u0627\u0645\u0634\u062e\u0635"), esc(a.ip),
                                  fa(grace // 60)),
                         buttons=[[Button.inline("\u2705 \u0645\u0646 \u0628\u0648\u062f\u0645", "al:ok:%d" % h),
                                   Button.inline("\U0001f6ab \u0627\u062e\u0631\u0627\u062c", "al:kick:%d" % h)]])
        elif now >= rt.pend_auth[h]:
            await kick_auth(rt, h, auto=True)
    for h in list(rt.pend_auth):
        if h not in cur:
            del rt.pend_auth[h]


async def refresh_groups(rt):
    ds = await rt.client.get_dialogs(limit=150)
    rt.creator_groups = [d.entity for d in ds if d.is_group and getattr(d.entity, "creator", False)]
    rt.cg_ts = time.time()


async def job_betray(rt, now):
    uid = rt.uid
    if not is_on(uid, "abetray") or not rt.due("betray", 90):
        return
    if now - rt.cg_ts > 600:
        await refresh_groups(rt)
    limit = int(get_p(uid, "abetray", "limit") or 5)
    mins = int(get_p(uid, "abetray", "mins") or 10)
    for chat in rt.creator_groups[:8]:
        counts = collections.Counter()
        async for e in rt.client.iter_admin_log(chat, limit=60, ban=True, restrict=True):
            if e.user_id and e.user_id != rt.me.id and now - e.date.timestamp() <= mins * 60:
                counts[e.user_id] += 1
        for actor, n in counts.items():
            k = "bt:%d:%d" % (chat.id, actor)
            if n >= limit and now - float(kv_get(uid, k, 0) or 0) > 3600:
                kv_set(uid, k, now)
                try:
                    await rt.client.edit_admin(chat, actor, is_admin=False)
                    res = "\u0627\u0632 \u0627\u062f\u0645\u06cc\u0646\u06cc \u0628\u0631\u06a9\u0646\u0627\u0631 \u0634\u062f \u2705"
                except Exception as e:
                    res = "\u0628\u0631\u06a9\u0646\u0627\u0631\u06cc \u0645\u0645\u06a9\u0646 \u0646\u0634\u062f (%s)" % esc(type(e).__name__)
                await notify(uid, "\U0001f6e1 <b>\u0636\u062f \u062e\u06cc\u0627\u0646\u062a</b>\n\u062f\u0631 \u06af\u0631\u0648\u0647 \u00ab%s\u00bb \u06a9\u0627\u0631\u0628\u0631 <code>%s</code> \u062f\u0631 %s \u062f\u0642\u06cc\u0642\u0647 %s \u0646\u0641\u0631 \u0631\u0627 \u0628\u0646 \u06a9\u0631\u062f\u061b %s" % (
                    esc(uname(chat)), actor, fa(mins), fa(n), res))


async def ticker(rt):
    await asyncio.sleep(3)
    while RTS.get(rt.uid) is rt:
        now = time.time()
        for job in (job_health, job_clock, job_online, job_sched, job_alogin, job_betray):
            if RTS.get(rt.uid) is not rt:
                return
            await safe(rt, job, now)
        await asyncio.sleep(4)


async def on_toggle(rt, key, on):
    """\u06a9\u0627\u0631\u0647\u0627\u06cc \u0644\u0627\u0632\u0645 \u0647\u0646\u06af\u0627\u0645 \u0631\u0648\u0634\u0646/\u062e\u0627\u0645\u0648\u0634 \u0634\u062f\u0646 \u0628\u0639\u0636\u06cc \u0642\u0627\u0628\u0644\u06cc\u062a\u200c\u0647\u0627"""
    uid = rt.uid
    if key == "cname":
        if on:
            if not get_p(uid, "cname", "base"):
                set_p(uid, "cname", "base", (rt.me.first_name or "").split(" | ")[0])
        else:
            base = get_p(uid, "cname", "base")
            if base:
                await rt.client(functions.account.UpdateProfileRequest(first_name=base))
            rt.last_name = None
    elif key in ("cbio", "brot"):
        other = "brot" if key == "cbio" else "cbio"
        if on:
            if not is_on(uid, other):
                full = await rt.client(functions.users.GetFullUserRequest(types.InputUserSelf()))
                about = full.full_user.about or ""
                kv_set(uid, "orig_bio", about)
                if key == "cbio" and not get_p(uid, "cbio", "base"):
                    set_p(uid, "cbio", "base", about)
        elif not is_on(uid, other):
            await rt.client(functions.account.UpdateProfileRequest(about=kv_get(uid, "orig_bio", "") or ""))
            rt.last_bio = None
    elif key == "alogin" and on:
        kv_del(uid, "auth_known")
        rt.pend_auth.clear()


# ============================================================================
#
# ============================================================================
LOGIN = {}        #
PEND = {}         #
LAST_LOGIN = {}

HELP_PANEL = (
    "\u2753 <b>\u0631\u0627\u0647\u0646\u0645\u0627</b>\n\n"
    "\u2022 \u0627\u0632 \u0645\u0646\u0648\u06cc \u0627\u0635\u0644\u06cc \u06cc\u06a9 \u062f\u0633\u062a\u0647 \u0631\u0627 \u0628\u0627\u0632 \u06a9\u0646\u061b \u0631\u0648\u06cc <b>\u0646\u0627\u0645 \u0642\u0627\u0628\u0644\u06cc\u062a</b> \u0628\u0632\u0646 \u062a\u0627 \u0631\u0648\u0634\u0646/\u062e\u0627\u0645\u0648\u0634 \u0634\u0648\u062f.\n"
    "\u2022 \u0631\u0648\u06cc <b>\u2699\ufe0f</b> \u06a9\u0646\u0627\u0631 \u0647\u0631 \u0642\u0627\u0628\u0644\u06cc\u062a \u0628\u0632\u0646 \u062a\u0627 \u062a\u0648\u0636\u06cc\u062d \u0648 \u062a\u0646\u0638\u06cc\u0645\u0627\u062a\u0634 \u0631\u0627 \u0628\u0628\u06cc\u0646\u06cc.\n"
    "\u2022 \u0627\u0639\u0644\u0627\u0646\u200c\u0647\u0627 (\u0636\u062f \u062d\u0630\u0641\u060c \u0634\u0646\u0648\u062f\u060c \u062f\u06cc\u062f\u0647\u200c\u0628\u0627\u0646 \u0648 ...) \u0647\u0645\u06cc\u0646\u200c\u062c\u0627 \u0628\u0631\u0627\u06cc\u062a \u0645\u06cc\u200c\u0622\u06cc\u0646\u062f.\n"
    "\u2022 \u062f\u0633\u062a\u0648\u0631\u0627\u062a \u0646\u0642\u0637\u0647\u200c\u0627\u06cc \u0631\u0627 \u062f\u0631 \u0647\u0631 \u0686\u062a \u062a\u0627\u06cc\u067e \u06a9\u0646: <code>.help</code>\n"
    "\u2022 \u062f\u0627\u062e\u0644 \u06cc\u06a9 \u06af\u0631\u0648\u0647 \u0628\u0646\u0648\u06cc\u0633 <code>.manage</code> \u062a\u0627 \u0628\u0647 \u00ab\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u00bb \u0627\u0636\u0627\u0641\u0647 \u0634\u0648\u062f "
    "(\u0628\u0631\u0627\u06cc \u062e\u0648\u0634\u200c\u0622\u0645\u062f\u06af\u0648\u06cc\u06cc\u060c \u0642\u0641\u0644 \u0644\u06cc\u0646\u06a9 \u0648 \u0633\u06a9\u0648\u062a \u06a9\u0627\u0631\u0628\u0631\u0627\u0646).\n"
    "\u2022 <b>\u062e\u0631\u0648\u062c</b>: \u062f\u06a9\u0645\u0647\u200c\u06cc \U0001f50c \u062e\u0631\u0648\u062c\u060c \u0646\u0634\u0633\u062a \u0631\u0627 \u06a9\u0627\u0645\u0644 \u067e\u0627\u06a9 \u0645\u06cc\u200c\u06a9\u0646\u062f.\n\n"
    "\u062f\u0633\u062a\u0648\u0631\u0647\u0627\u06cc \u0631\u0628\u0627\u062a: /panel \u067e\u0646\u0644  \u2022  /coins \u0633\u06a9\u0647 \u0648 \u0627\u0634\u062a\u0631\u0627\u06a9  \u2022  /logout \u062e\u0631\u0648\u062c  \u2022  /cancel \u0627\u0646\u0635\u0631\u0627\u0641"
)

START_TEXT = (
    "\U0001f44b \u0628\u0647 <b>Self Speed</b> \u062e\u0648\u0634 \u0622\u0645\u062f\u06cc!\n"
    "\u062d\u0633\u0627\u0628 \u062a\u0644\u06af\u0631\u0627\u0645\u062a \u0631\u0627 \u0628\u0647 \u06cc\u06a9 \u062f\u0633\u062a\u06cc\u0627\u0631 \u0647\u0648\u0634\u0645\u0646\u062f \u062a\u0628\u062f\u06cc\u0644 \u06a9\u0646: \u0636\u062f \u062d\u0630\u0641\u060c \u0636\u062f \u0648\u06cc\u0631\u0627\u06cc\u0634\u060c \u0645\u0646\u0634\u06cc \u062e\u0648\u062f\u06a9\u0627\u0631\u060c \u0633\u0627\u0639\u062a \u06a9\u0646\u0627\u0631 \u0627\u0633\u0645 \u0628\u0627 \u0641\u0648\u0646\u062a \u062f\u0644\u062e\u0648\u0627\u0647 \u0648 \u062f\u0647\u200c\u0647\u0627 \u0642\u0627\u0628\u0644\u06cc\u062a \u062f\u06cc\u06af\u0631.\n"
    "\U0001f381 \u0628\u0639\u062f \u0627\u0632 \u0648\u0631\u0648\u062f\u060c <b>\u062a\u0633\u062a \u0631\u0627\u06cc\u06af\u0627\u0646</b> \u0641\u0639\u0627\u0644 \u0645\u06cc\u200c\u0634\u0648\u062f. \u0628\u0639\u062f\u0634 \u0647\u0631 \U0001fa99 \u0633\u06a9\u0647 = \u06f1 \u0633\u0627\u0639\u062a \u0633\u0644\u0641.\n\n"
    "\U0001f510 <b>\u0642\u0628\u0644 \u0627\u0632 \u0648\u0631\u0648\u062f \u0628\u062e\u0648\u0627\u0646:</b>\n"
    "\u2022 \u0648\u0631\u0648\u062f \u0641\u0642\u0637 \u0628\u0627 <b>\u0634\u0645\u0627\u0631\u0647 \u0648 \u06a9\u062f \u062e\u0648\u062f\u062a</b> \u0627\u0646\u062c\u0627\u0645 \u0645\u06cc\u200c\u0634\u0648\u062f (\u062f\u06a9\u0645\u0647\u200c\u06cc \u0632\u06cc\u0631 \u0641\u0642\u0637 \u0634\u0645\u0627\u0631\u0647\u200c\u06cc \u062e\u0648\u062f\u062a \u0631\u0627 \u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u062f).\n"
    "\u2022 \u06a9\u062f \u0648\u0631\u0648\u062f \u0648 \u0631\u0645\u0632 \u062f\u0648\u0645\u0631\u062d\u0644\u0647\u200c\u0627\u06cc \u062c\u0627\u06cc\u06cc \u0630\u062e\u06cc\u0631\u0647 \u0646\u0645\u06cc\u200c\u0634\u0648\u0646\u062f\u061b \u0641\u0642\u0637 \u0646\u0634\u0633\u062a (Session) <b>\u0631\u0645\u0632\u0646\u06af\u0627\u0631\u06cc\u200c\u0634\u062f\u0647</b> \u0646\u06af\u0647 \u062f\u0627\u0634\u062a\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f.\n"
    "\u2022 \u0647\u0631 \u0632\u0645\u0627\u0646 \u0628\u0627 \u062f\u06a9\u0645\u0647\u200c\u06cc \u00ab\u062e\u0631\u0648\u062c\u00bb \u0646\u0634\u0633\u062a \u067e\u0627\u06a9 \u0645\u06cc\u200c\u0634\u0648\u062f\u060c \u06cc\u0627 \u0627\u0632 \u00ab\u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u062a\u0644\u06af\u0631\u0627\u0645 \u2190 \u062f\u0633\u062a\u06af\u0627\u0647\u200c\u0647\u0627\u00bb \u062f\u0633\u062a\u0631\u0633\u06cc \u0631\u0627 \u0642\u0637\u0639 \u06a9\u0646.\n"
    "\u2022 \u0631\u0628\u0627\u062a \u0647\u06cc\u0686 \u067e\u06cc\u0627\u0645\u06cc \u0627\u0632 \u0637\u0631\u0641 \u062a\u0648 \u0646\u0645\u06cc\u200c\u0641\u0631\u0633\u062a\u062f \u0645\u06af\u0631 \u0642\u0627\u0628\u0644\u06cc\u062a\u06cc \u06a9\u0647 \u062e\u0648\u062f\u062a \u0631\u0648\u0634\u0646 \u06a9\u0631\u062f\u0647\u200c\u0627\u06cc.\n\n"
    "\u0628\u0627 \u0632\u062f\u0646 \u062f\u06a9\u0645\u0647\u200c\u06cc \u0632\u06cc\u0631 \u0628\u0627 \u0627\u06cc\u0646 \u0645\u0648\u0627\u0631\u062f \u0645\u0648\u0627\u0641\u0642\u062a \u0645\u06cc\u200c\u06a9\u0646\u06cc \U0001f447"
)

BACK_MAIN = [Button.inline("\u2b05 \u0628\u0627\u0632\u06af\u0634\u062a", "m")]


def fmt_item(kind, it):
    if kind == "user":
        return "%s (%s)" % (it.get("n"), it.get("id"))
    if kind == "chat":
        return it.get("n") or str(it.get("id"))
    if kind == "sched":
        return "%s \u2022 \u0647\u0631 %s \u062f\u0642\u06cc\u0642\u0647 \u2022 %s" % (it.get("n"), fa(it.get("m")), (it.get("t") or "")[:30])
    if kind == "click":
        return "%s \u2022 \u00ab%s\u00bb" % (it.get("n"), it.get("b"))
    if kind == "fwd":
        return "%s \u279c %s" % (it.get("sn"), it.get("dn"))
    if kind == "kv":
        k, _, v = str(it).partition("=")
        return "%s \u279c %s" % (k, v[:30])
    return str(it)[:60]


def show_val(p, val):
    if p["t"] == "choice":
        return dict(p["o"]).get(val, val)
    if p["t"] == "one":
        return val.get("n", "\u2014") if val else "\u2014"
    if p["t"] == "int":
        return fa(val)
    return (val or "\u2014") if not isinstance(val, str) else (val[:120] or "\u2014")


#
def v_main(uid):
    rt = RTS.get(uid)
    t = now_local()
    up = int((time.time() - rt.started) / 60) if rt else 0
    lines = ["\U0001f39b <b>\u067e\u0646\u0644 Self Speed</b>",
             "%s  |  \u23f1 %s \u062f\u0642\u06cc\u0642\u0647  |  \U0001f4f6 %s" % ("\U0001f7e2 \u0622\u0646\u0644\u0627\u06cc\u0646" if rt else "\U0001f534 \u0642\u0637\u0639", fa(up),
                                                (fa(rt.ping) + " ms") if rt and rt.ping else "\u2014"),
             "\U0001f527 \u0642\u0627\u0628\u0644\u06cc\u062a \u0641\u0639\u0627\u0644: %s \u0627\u0632 %s" % (fa(count_on(uid)), fa(len(FEATS))),
             "\u23f3 \u0632\u0645\u0627\u0646 \u0633\u0644\u0641: %s" % fmt_left(left_sec(uid)),
             "\U0001f552 %s \u2014 %s" % (fa(t.strftime("%H:%M")), jdate_str(t))]
    rows, cur = [], []
    for key, title in CATS:
        n = sum(1 for k, f in FEATS.items() if f["cat"] == key and is_on(uid, k))
        cur.append(Button.inline(title + ((" \u2713" + fa(n)) if n else ""), "c:" + key))
        if len(cur) == 2:
            rows.append(cur)
            cur = []
    if cur:
        rows.append(cur)
    rows.append([Button.inline("\u26a1 \u0628\u062e\u0634\u200c\u0647\u0627\u06cc \u0631\u0648\u0634\u0646 %s" % fa(count_on(uid)), "on")])
    rows.append([Button.inline("\U0001fa99 \u0633\u06a9\u0647 \u0648 \u0627\u0634\u062a\u0631\u0627\u06a9", "w")])
    rows.extend(webapp_rows())
    if uid == OWNER_ID:
        rows.append([Button.inline("\U0001f6e0 \u0645\u062f\u06cc\u0631\u06cc\u062a (\u0645\u062f\u06cc\u0631)", "ad:home")])
    rows.append([Button.inline("\u2753 \u0631\u0627\u0647\u0646\u0645\u0627", "hlp"), Button.inline("\U0001f50c \u062e\u0631\u0648\u062c", "lo"), Button.inline("\u2716 \u0628\u0633\u062a\u0646", "x")])
    return "\n".join(lines), rows


def v_cat(uid, cat):
    rows = []
    for k, f in FEATS.items():
        if f["cat"] == cat:
            rows.append([Button.inline(("\u2705 " if is_on(uid, k) else "\u25ab\ufe0f ") + f["title"], "t:%s:c" % k),
                         Button.inline("\u2699\ufe0f", "f:" + k)])
    if cat == "tools":
        for a, title in ACTIONS:
            rows.append([Button.inline(title, "a:%s:0" % a)])
    rows.append(BACK_MAIN)
    return "<b>%s</b>\n\u0631\u0648\u06cc \u0646\u0627\u0645 \u0642\u0627\u0628\u0644\u06cc\u062a \u0628\u0632\u0646 \u062a\u0627 \u0631\u0648\u0634\u0646/\u062e\u0627\u0645\u0648\u0634 \u0634\u0648\u062f\u061b \u0628\u0631\u0627\u06cc \u062a\u0648\u0636\u06cc\u062d \u0648 \u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u0631\u0648\u06cc \u2699\ufe0f." % CAT_TITLE[cat], rows


def v_on(uid):
    rows = [[Button.inline("\u2705 " + f["title"], "f:" + k)] for k, f in FEATS.items() if is_on(uid, k)]
    rows.append(BACK_MAIN)
    return ("\u26a1 <b>\u0642\u0627\u0628\u0644\u06cc\u062a\u200c\u0647\u0627\u06cc \u0631\u0648\u0634\u0646</b>" if len(rows) > 1 else "\u0647\u06cc\u0686 \u0642\u0627\u0628\u0644\u06cc\u062a\u06cc \u0631\u0648\u0634\u0646 \u0646\u06cc\u0633\u062a."), rows


def v_feat(uid, key, note=""):
    f = FEATS[key]
    on = is_on(uid, key)
    t = []
    if note:
        t.append(note + "\n")
    t.append("<b>%s</b>" % esc(f["title"]))
    t.append(esc(f["desc"]))
    t.append("")
    t.append("\u0648\u0636\u0639\u06cc\u062a: " + ("\u2705 \u0631\u0648\u0634\u0646" if on else "\u23f9 \u062e\u0627\u0645\u0648\u0634"))
    if key in GROUP_FEATS and not S[uid]["mg"]:
        t.append("\u26a0\ufe0f \u0647\u0646\u0648\u0632 \u00ab\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u00bb \u0646\u062f\u0627\u0631\u06cc (\u0627\u0628\u0632\u0627\u0631\u0647\u0627 \u2190 \u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u060c \u06cc\u0627 \u062f\u0627\u062e\u0644 \u06af\u0631\u0648\u0647 \u0628\u0646\u0648\u06cc\u0633 <code>.manage</code>).")
    rows = [[Button.inline("\u23f9 \u062e\u0627\u0645\u0648\u0634 \u06a9\u0631\u062f\u0646" if on else "\u2705 \u0631\u0648\u0634\u0646 \u06a9\u0631\u062f\u0646", "t:%s:f" % key)]]
    for i, p in enumerate(f["params"]):
        val = get_p(uid, key, p["n"])
        if p["t"] in ("text", "int"):
            t.append("\u2022 %s: <code>%s</code>" % (esc(p["l"]), esc(show_val(p, val))))
            rows.append([Button.inline("\u270f\ufe0f " + p["l"], "pe:%s:%d" % (key, i))])
        elif p["t"] == "one":
            t.append("\u2022 %s: <code>%s</code>" % (esc(p["l"]), esc(show_val(p, val))))
            rows.append([Button.inline("\u270f\ufe0f " + p["l"], "pe:%s:%d" % (key, i)),
                         Button.inline("\U0001f5d1", "px:%s:%d" % (key, i))])
        elif p["t"] == "choice":
            t.append("\u2022 %s: <b>%s</b>" % (esc(p["l"]), esc(show_val(p, val))))
            btns = [Button.inline(("\u2714 " if val == v else "") + lab, "pc:%s:%d:%d" % (key, i, j))
                    for j, (v, lab) in enumerate(p["o"])]
            for st in range(0, len(btns), 3):
                rows.append(btns[st:st + 3])
        elif p["t"] == "list":
            items = val or []
            t.append("\u2022 %s (%s):" % (esc(p["l"]), fa(len(items))))
            for j, it in enumerate(items[:12]):
                t.append("   %s) %s" % (fa(j + 1), esc(fmt_item(p["k"], it))))
            rows.append([Button.inline("\u2795 \u0627\u0641\u0632\u0648\u062f\u0646", "la:%s:%d" % (key, i)),
                         Button.inline("\U0001f9f9 \u067e\u0627\u06a9\u200c\u06a9\u0631\u062f\u0646 \u0647\u0645\u0647", "lc:%s:%d" % (key, i))])
            dels = [Button.inline("\U0001f5d1 %s" % fa(j + 1), "ld:%s:%d:%d" % (key, i, j)) for j in range(min(len(items), 12))]
            for s in range(0, len(dels), 4):
                rows.append(dels[s:s + 4])
    rows.append([Button.inline("\u2b05 \u0628\u0627\u0632\u06af\u0634\u062a", "c:" + f["cat"])])
    return "\n".join(t), rows


def v_prompt(uid, key, idx, mode, err=""):
    p = FEATS[key]["params"][idx]
    t = []
    if err:
        t.append(err + "\n")
    t.append("\u270f\ufe0f <b>%s</b>" % esc(p["l"]))
    if p.get("h"):
        t.append(esc(p["h"]))
    if p["t"] == "int":
        t.append("\u06cc\u06a9 \u0639\u062f\u062f \u0628\u06cc\u0646 %s \u062a\u0627 %s \u0628\u0641\u0631\u0633\u062a." % (fa(p["lo"]), fa(p["hi"])))
    t.append("\n\u0645\u0642\u062f\u0627\u0631 \u0631\u0627 \u0647\u0645\u06cc\u0646\u200c\u062c\u0627 \u0628\u0641\u0631\u0633\u062a. (\u0627\u0646\u0635\u0631\u0627\u0641: \u062f\u06a9\u0645\u0647\u200c\u06cc \u0632\u06cc\u0631)")
    return "\n".join(t), [[Button.inline("\u21a9 \u0627\u0646\u0635\u0631\u0627\u0641", "f:" + key)]]


#
def norm_ref(s):
    s = s.strip().translate(EN_DIGITS)
    s = re.sub(r"^(https?://)?(t\.me|telegram\.me)/", "", s)
    return s.lstrip("@").split("?")[0].strip("/")


async def resolve(rt, ref):
    ref = norm_ref(ref)
    if ref.startswith("+") or ref.startswith("joinchat"):
        raise ValueError("invite")
    if re.fullmatch(r"-?\d+", ref):
        ref = int(ref)
    return await rt.client.get_entity(ref)


def fwd_cycle(rules, s, d):
    edges = collections.defaultdict(set)
    for r in rules:
        edges[r["s"]].add(r["d"])
    edges[s].add(d)
    seen, stack = set(), [d]
    while stack:
        x = stack.pop()
        if x == s:
            return True
        if x in seen:
            continue
        seen.add(x)
        stack.extend(edges.get(x, ()))
    return False


async def parse_item(rt, kind, txt, sp=None):
    """\u0628\u0627\u0632\u06af\u0634\u062a: (\u0622\u06cc\u062a\u0645, \u067e\u06cc\u0627\u0645 \u062e\u0637\u0627)"""
    try:
        if kind == "text":
            if not txt or len(txt) > 200:
                return None, "\u274c \u0645\u062a\u0646 \u0646\u0627\u0645\u0639\u062a\u0628\u0631 \u0627\u0633\u062a (\u062d\u062f\u0627\u06a9\u062b\u0631 \u06f2\u06f0\u06f0 \u0646\u0648\u06cc\u0633\u0647)."
            return txt, None
        if kind == "kv":
            k, _, v = txt.partition("=")
            if not k.strip() or not v.strip():
                return None, "\u274c \u0628\u0647 \u0634\u06a9\u0644 \u00ab\u06a9\u0644\u0645\u0647=\u067e\u0627\u0633\u062e\u00bb \u0628\u0641\u0631\u0633\u062a."
            return k.strip() + "=" + v.strip(), None
        if kind == "user":
            ref = norm_ref(txt)
            if re.fullmatch(r"\d+", ref):
                try:
                    e = await rt.client.get_entity(int(ref))
                except Exception:
                    return {"id": int(ref), "n": ref, "u": None}, None
            else:
                e = await resolve(rt, ref)
            if not isinstance(e, types.User):
                return None, "\u274c \u0627\u06cc\u0646 \u06cc\u06a9 \u06a9\u0627\u0631\u0628\u0631 \u0646\u06cc\u0633\u062a."
            return {"id": e.id, "n": uname(e), "u": e.username}, None
        if kind == "chat":
            e = await resolve(rt, txt)
            if isinstance(e, types.User):
                return None, "\u274c \u0627\u06cc\u0646 \u06cc\u06a9 \u06a9\u0627\u0631\u0628\u0631 \u0627\u0633\u062a\u061b \u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0644\u06cc\u0646\u06a9 \u06a9\u0627\u0646\u0627\u0644/\u06af\u0631\u0648\u0647 \u0628\u0641\u0631\u0633\u062a."
            if sp and sp.get("admin") and not (getattr(e, "creator", False) or getattr(e, "admin_rights", None)):
                return None, "\u274c \u0628\u0627\u06cc\u062f \u0627\u062f\u0645\u06cc\u0646 \u0622\u0646 \u06a9\u0627\u0646\u0627\u0644 \u0628\u0627\u0634\u06cc."
            return {"id": utils.get_peer_id(e), "n": uname(e), "u": getattr(e, "username", None)}, None
        if kind == "sched":
            parts = [x.strip() for x in txt.split("|", 2)]
            mins = parts[1].translate(EN_DIGITS) if len(parts) == 3 else ""
            if len(parts) != 3 or not mins.isdigit() or not parts[2]:
                return None, "\u274c \u0628\u0647 \u0634\u06a9\u0644 \u00ab\u0686\u062a | \u062f\u0642\u06cc\u0642\u0647 | \u0645\u062a\u0646\u00bb \u0628\u0641\u0631\u0633\u062a."
            if int(mins) < 10:
                return None, "\u274c \u062d\u062f\u0627\u0642\u0644 \u0641\u0627\u0635\u0644\u0647 \u06f1\u06f0 \u062f\u0642\u06cc\u0642\u0647 \u0627\u0633\u062a."
            e = await resolve(rt, parts[0])
            return {"j": secrets.token_hex(3), "id": utils.get_peer_id(e), "n": uname(e),
                    "u": getattr(e, "username", None), "m": int(mins), "t": parts[2]}, None
        if kind == "click":
            parts = [x.strip() for x in txt.split("|", 1)]
            if len(parts) != 2 or not parts[1]:
                return None, "\u274c \u0628\u0647 \u0634\u06a9\u0644 \u00ab\u0686\u062a | \u0645\u062a\u0646 \u062f\u06a9\u0645\u0647\u00bb \u0628\u0641\u0631\u0633\u062a."
            e = await resolve(rt, parts[0])
            return {"id": utils.get_peer_id(e), "n": uname(e), "u": getattr(e, "username", None), "b": parts[1]}, None
        if kind == "fwd":
            parts = [x.strip() for x in re.split(">|\u279c|\u2190", txt)]
            if len(parts) != 2 or not parts[0] or not parts[1]:
                return None, "\u274c \u0628\u0647 \u0634\u06a9\u0644 \u00ab\u0645\u0628\u062f\u0623 > \u0645\u0642\u0635\u062f\u00bb \u0628\u0641\u0631\u0633\u062a."
            a, b = await resolve(rt, parts[0]), await resolve(rt, parts[1])
            s, d = utils.get_peer_id(a), utils.get_peer_id(b)
            if s == d or fwd_cycle(get_p(rt.uid, "fwd", "rules") or [], s, d):
                return None, "\u274c \u0627\u06cc\u0646 \u0642\u0627\u0646\u0648\u0646 \u06cc\u06a9 \u062d\u0644\u0642\u0647 \u0645\u06cc\u200c\u0633\u0627\u0632\u062f."
            return {"s": s, "sn": uname(a), "su": getattr(a, "username", None),
                    "d": d, "dn": uname(b), "du": getattr(b, "username", None)}, None
    except ValueError as e:
        if "invite" in str(e):
            return None, "\u274c \u0644\u06cc\u0646\u06a9 \u062f\u0639\u0648\u062a \u062e\u0635\u0648\u0635\u06cc \u0642\u0627\u0628\u0644 \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u0646\u06cc\u0633\u062a\u061b \u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0622\u06cc\u062f\u06cc \u0628\u0641\u0631\u0633\u062a."
        return None, "\u274c \u067e\u06cc\u062f\u0627 \u0646\u0634\u062f. \u06cc\u0648\u0632\u0631\u0646\u06cc\u0645/\u0622\u06cc\u062f\u06cc \u0631\u0627 \u062f\u0631\u0633\u062a \u0628\u0641\u0631\u0633\u062a."
    except errors.FloodWaitError as e:
        return None, "\u274c \u062a\u0644\u06af\u0631\u0627\u0645 \u0645\u062d\u062f\u0648\u062f\u06cc\u062a \u0645\u0648\u0642\u062a \u06af\u0630\u0627\u0634\u062a\u061b %s \u062b\u0627\u0646\u06cc\u0647 \u0628\u0639\u062f \u062f\u0648\u0628\u0627\u0631\u0647 \u062a\u0644\u0627\u0634 \u06a9\u0646." % fa(e.seconds)
    except Exception as e:
        log.info("parse_item failed: %s", e)
        return None, "\u274c \u067e\u06cc\u062f\u0627 \u0646\u0634\u062f. (\u0628\u0631\u0627\u06cc \u0622\u06cc\u062f\u06cc \u0639\u062f\u062f\u06cc\u060c \u0628\u0627\u06cc\u062f \u0642\u0628\u0644\u0627\u064b \u0628\u0627 \u0622\u0646 \u0686\u062a \u062f\u0627\u0634\u062a\u0647 \u0628\u0627\u0634\u06cc\u061b \u0628\u0647\u062a\u0631 \u0627\u0633\u062a \u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u0628\u062f\u0647\u06cc.)"
    return None, "\u274c \u0646\u0648\u0639 \u0646\u0627\u0645\u0639\u062a\u0628\u0631"


#
async def v_action(uid, name, arg="0", note=""):
    rt = RTS.get(uid)
    back = [Button.inline("\u2b05 \u0628\u0627\u0632\u06af\u0634\u062a", "c:tools")]
    if not rt:
        return "\U0001f534 \u062d\u0633\u0627\u0628\u062a \u0645\u062a\u0635\u0644 \u0646\u06cc\u0633\u062a.", [back]
    head = (note + "\n\n") if note else ""
    if name == "st":
        ping = await measure_ping(rt.client)
        rt.ping = ping
        n_cache = DB.one("SELECT COUNT(*) FROM cache WHERE uid=?", (uid,))[0]
        txt = ("\U0001f4ca <b>\u0648\u0636\u0639\u06cc\u062a</b>\n\n\U0001f464 %s\n\U0001f7e2 \u0622\u0646\u0644\u0627\u06cc\u0646\n\u23f1 \u0645\u062f\u062a \u0641\u0639\u0627\u0644\u06cc\u062a: %s \u062f\u0642\u06cc\u0642\u0647\n\U0001f4f6 \u067e\u06cc\u0646\u06af: %s ms\n\U0001f527 \u0642\u0627\u0628\u0644\u06cc\u062a \u0641\u0639\u0627\u0644: %s \u0627\u0632 %s\n"
               "\U0001f465 \u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc: %s\n\U0001f4be \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc \u062f\u0631 \u062d\u0627\u0641\u0638\u0647: %s") % (
            esc(uname(rt.me)), fa(int((time.time() - rt.started) / 60)), fa(ping), fa(count_on(uid)), fa(len(FEATS)),
            fa(len(S[uid]["mg"])), fa(n_cache))
        return head + txt, [[Button.inline("\U0001f504 \u062a\u0627\u0632\u0647\u200c\u0633\u0627\u0632\u06cc", "a:st:0")], back]
    if name == "ch":
        page = int(arg) if arg.isdigit() else 0
        ds = await rt.client.get_dialogs(limit=300)
        chats = [d for d in ds if (d.is_channel or d.is_group) and not getattr(d.entity, "creator", False)]
        per = 8
        pg = chats[page * per:(page + 1) * per]
        rows = [[Button.inline("\U0001f6aa " + (d.name or "?")[:30], "a:lv:%d" % d.id)] for d in pg]
        nav = []
        if page > 0:
            nav.append(Button.inline("\u25c0\ufe0f \u0642\u0628\u0644\u06cc", "a:ch:%d" % (page - 1)))
        if (page + 1) * per < len(chats):
            nav.append(Button.inline("\u0628\u0639\u062f\u06cc \u25b6\ufe0f", "a:ch:%d" % (page + 1)))
        if nav:
            rows.append(nav)
        rows.append(back)
        return head + "\U0001f6aa <b>\u06a9\u0627\u0646\u0627\u0644\u200c\u0647\u0627 \u0648 \u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u062a\u0648</b> (%s)\n\u0631\u0648\u06cc \u0647\u0631\u06a9\u062f\u0627\u0645 \u0628\u0632\u0646\u06cc\u060c \u0628\u0639\u062f \u0627\u0632 \u062a\u0623\u06cc\u06cc\u062f \u0627\u0632 \u0622\u0646 \u062e\u0627\u0631\u062c \u0645\u06cc\u200c\u0634\u0648\u06cc." % fa(len(chats)), rows
    if name == "lv":
        try:
            e = await rt.client.get_entity(int(arg))
            title = uname(e)
        except Exception:
            title = arg
        return "\u0627\u0632 \u00ab%s\u00bb \u062e\u0627\u0631\u062c \u0634\u0648\u0645\u061f" % esc(title), [[Button.inline("\u2705 \u0628\u0644\u0647\u060c \u062e\u0627\u0631\u062c \u0634\u0648", "a:lv2:" + arg),
                                                      Button.inline("\u21a9 \u0646\u0647", "a:ch:0")]]
    if name == "ses":
        r = await rt.client(functions.account.GetAuthorizationsRequest())
        lines, rows = ["\U0001f511 <b>\u0646\u0634\u0633\u062a\u200c\u0647\u0627\u06cc \u0641\u0639\u0627\u0644 \u062d\u0633\u0627\u0628</b>\n"], []
        for i, a in enumerate(r.authorizations):
            when = a.date_active.strftime("%Y-%m-%d %H:%M") if a.date_active else ""
            lines.append("%s %s %s \u2014 %s %s" % ("\u2705" if a.current else "\u25ab\ufe0f", esc(a.device_model), esc(a.app_name),
                                                  esc(a.country or ""), when))
            if not a.current:
                rows.append([Button.inline("\U0001f6ab \u0627\u062e\u0631\u0627\u062c: %s" % (a.device_model or "?")[:24], "a:ks:%d" % a.hash)])
        lines.append("\n\u2705 = \u0647\u0645\u06cc\u0646 \u0631\u0628\u0627\u062a")
        if rows:
            rows.append([Button.inline("\U0001f6ab \u0627\u062e\u0631\u0627\u062c \u0647\u0645\u0647 \u0628\u0647\u200c\u062c\u0632 \u0631\u0628\u0627\u062a", "a:ksall:0")])
        rows.append(back)
        return head + "\n".join(lines), rows
    if name == "mg":
        mg = S[uid]["mg"]
        lines = ["\U0001f465 <b>\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc</b>",
                 "\u0642\u0627\u0628\u0644\u06cc\u062a\u200c\u0647\u0627\u06cc \u06af\u0631\u0648\u0647\u06cc (\u062e\u0648\u0634\u200c\u0622\u0645\u062f\u060c \u0642\u0641\u0644 \u0644\u06cc\u0646\u06a9/\u0641\u0648\u0631\u0648\u0627\u0631\u062f\u060c \u0633\u06a9\u0648\u062a \u06a9\u0627\u0631\u0628\u0631\u0627\u0646) \u0641\u0642\u0637 \u062f\u0631 \u0627\u06cc\u0646 \u06af\u0631\u0648\u0647\u200c\u0647\u0627 \u06a9\u0627\u0631 \u0645\u06cc\u200c\u06a9\u0646\u0646\u062f.",
                 "\u062f\u0627\u062e\u0644 \u06af\u0631\u0648\u0647 \u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u06cc \u0628\u0646\u0648\u06cc\u0633\u06cc <code>.manage</code> \u0647\u0645.\n"]
        rows = []
        for i, g in enumerate(mg):
            lines.append("%s) %s" % (fa(i + 1), esc(g.get("n"))))
            rows.append([Button.inline("\U0001f5d1 \u062d\u0630\u0641: %s" % (g.get("n") or "?")[:28], "a:mgd:%d" % i)])
        rows.insert(0, [Button.inline("\u2795 \u0627\u0641\u0632\u0648\u062f\u0646 \u06af\u0631\u0648\u0647", "a:mga:0")])
        rows.append(back)
        return head + "\n".join(lines), rows
    if name == "d24":
        since = int(time.time()) - 86400
        n = DB.one("SELECT COUNT(*) FROM cache WHERE uid=? AND out=1 AND date>?", (uid, since))[0]
        if not is_on(uid, "track"):
            return "\u0627\u0648\u0644 \u0642\u0627\u0628\u0644\u06cc\u062a \u00ab\u0631\u062f\u06cc\u0627\u0628 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u00bb \u0631\u0627 \u0631\u0648\u0634\u0646 \u06a9\u0646 \u062a\u0627 \u067e\u06cc\u0627\u0645\u200c\u0647\u0627\u06cc\u062a \u062b\u0628\u062a \u0634\u0648\u0646\u062f.", [back]
        return ("\U0001f9f9 %s \u067e\u06cc\u0627\u0645 \u0627\u0632 \u06f2\u06f4 \u0633\u0627\u0639\u062a \u0627\u062e\u06cc\u0631 \u062b\u0628\u062a \u0634\u062f\u0647 \u0627\u0633\u062a. \u0647\u0645\u0647 \u0628\u0631\u0627\u06cc \u0647\u0645\u0647\u200c\u06cc \u0637\u0631\u0641\u200c\u0647\u0627 \u062d\u0630\u0641 \u0634\u0648\u0646\u062f\u061f" % fa(n)), [
            [Button.inline("\u2705 \u0628\u0644\u0647\u060c \u062d\u0630\u0641 \u06a9\u0646", "a:d24y:0"), Button.inline("\u21a9 \u0646\u0647", "c:tools")]]
    return "\u061f", [back]


async def do_action(uid, name, arg):
    """\u0627\u062c\u0631\u0627\u06cc \u0627\u06a9\u0634\u0646\u200c\u0647\u0627\u06cc\u06cc \u06a9\u0647 \u062a\u063a\u06cc\u06cc\u0631 \u0645\u06cc\u200c\u062f\u0647\u0646\u062f. \u062e\u0631\u0648\u062c\u06cc: (\u0646\u0645\u0627, \u0647\u0634\u062f\u0627\u0631)"""
    rt = RTS.get(uid)
    if not rt:
        return None, "\u062d\u0633\u0627\u0628\u062a \u0645\u062a\u0635\u0644 \u0646\u06cc\u0633\u062a"
    if name == "lv2":
        try:
            await rt.client.delete_dialog(int(arg))
            note = "\u2705 \u062e\u0627\u0631\u062c \u0634\u062f\u06cc."
        except Exception as e:
            note = "\u274c \u0646\u0634\u062f: %s" % type(e).__name__
        return await v_action(uid, "ch", "0", note), None
    if name == "ks":
        ok = await kick_auth(rt, int(arg))
        return await v_action(uid, "ses", "0", "\u2705 \u0627\u062e\u0631\u0627\u062c \u0634\u062f." if ok else ""), None
    if name == "ksall":
        try:
            await rt.client(functions.auth.ResetAuthorizationsRequest())
            note = "\u2705 \u0647\u0645\u0647\u200c\u06cc \u0646\u0634\u0633\u062a\u200c\u0647\u0627\u06cc \u062f\u06cc\u06af\u0631 \u0628\u0633\u062a\u0647 \u0634\u062f."
        except errors.FreshResetAuthorisationForbiddenError:
            note = "\u26a0\ufe0f \u0631\u0628\u0627\u062a \u0647\u0646\u0648\u0632 \u06f2\u06f4 \u0633\u0627\u0639\u062a \u0627\u0632 \u0648\u0631\u0648\u062f\u0634 \u0646\u06af\u0630\u0634\u062a\u0647\u061b \u062a\u0644\u06af\u0631\u0627\u0645 \u0627\u062c\u0627\u0632\u0647 \u0646\u0645\u06cc\u200c\u062f\u0647\u062f."
        return await v_action(uid, "ses", "0", note), None
    if name == "d24y":
        rows = DB.all("SELECT chat_id,msg_id FROM cache WHERE uid=? AND out=1 AND date>?", (uid, int(time.time()) - 86400))
        by = collections.defaultdict(list)
        for cid, mid in rows:
            by[cid].append(mid)
        done = 0
        for cid, ids in by.items():
            for s in range(0, len(ids), 100):
                try:
                    await rt.client.delete_messages(cid, ids[s:s + 100], revoke=True)
                    done += len(ids[s:s + 100])
                except Exception as e:
                    log.warning("d24 delete failed: %s", e)
        DB.q("DELETE FROM cache WHERE uid=? AND out=1", (uid,))
        txt, btn = v_cat(uid, "tools")
        return ("\u2705 %s \u067e\u06cc\u0627\u0645 \u062d\u0630\u0641 \u0634\u062f.\n\n" % fa(done) + txt, btn), None
    if name == "clr":
        for (p,) in DB.all("SELECT path FROM cache WHERE uid=? AND path IS NOT NULL", (uid,)):
            try:
                os.remove(p)
            except Exception:
                pass
        DB.q("DELETE FROM cache WHERE uid=?", (uid,))
        txt, btn = v_cat(uid, "tools")
        return ("\u2705 \u062d\u0627\u0641\u0638\u0647\u200c\u06cc \u067e\u06cc\u0627\u0645\u200c\u0647\u0627 \u067e\u0627\u06a9 \u0634\u062f.\n\n" + txt, btn), None
    if name == "mgd":
        mg = S[uid]["mg"]
        if arg.isdigit() and int(arg) < len(mg):
            mg.pop(int(arg))
            save_settings(uid)
        return await v_action(uid, "mg", "0"), None
    return None, None


#
def code_kind(sent):
    n = type(sent.type).__name__
    if "App" in n:
        return "app"
    if "Sms" in n:
        return "sms"
    if "Call" in n:
        return "call"
    return "other"


def login_view(L, note=""):
    kinds = {
        "app": "\U0001f514 \u06a9\u062f \u0628\u0647 <b>\u0628\u0631\u0646\u0627\u0645\u0647\u200c\u06cc \u062a\u0644\u06af\u0631\u0627\u0645 \u0647\u0645\u06cc\u0646 \u0634\u0645\u0627\u0631\u0647</b> \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0634\u062f (\u0686\u062a \u00abTelegram\u00bb \u0631\u0648\u06cc \u062f\u0633\u062a\u06af\u0627\u0647 \u062f\u06cc\u06af\u0631) \u2014 \u0646\u0647 \u0627\u06cc\u0646\u062c\u0627\u060c \u0646\u0647 \u067e\u06cc\u0627\u0645\u06a9.",
        "sms": "\U0001f4e9 \u06a9\u062f \u0628\u0627 <b>\u067e\u06cc\u0627\u0645\u06a9</b> \u0628\u0631\u0627\u06cc\u062a \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0634\u062f.",
        "call": "\U0001f4de \u06a9\u062f \u0628\u0627 <b>\u062a\u0645\u0627\u0633 \u062a\u0644\u0641\u0646\u06cc</b> \u0627\u0639\u0644\u0627\u0645 \u0645\u06cc\u200c\u0634\u0648\u062f.",
        "other": "\U0001f4e8 \u06a9\u062f \u0628\u0631\u0627\u06cc\u062a \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0634\u062f.",
    }
    n = len(L["code"])
    shown = " ".join(["\u25cf"] * n + ["\u25cb"] * max(0, L["len"] - n))
    t = []
    if note:
        t.append(note + "\n")
    t.append("\U0001f522 <b>\u06a9\u062f \u0648\u0631\u0648\u062f \u0631\u0627 \u0648\u0627\u0631\u062f \u06a9\u0646\u06cc\u062f</b>\n")
    t.append("\u062a\u0644\u06af\u0631\u0627\u0645 \u06cc\u06a9 \u06a9\u062f \u0648\u0631\u0648\u062f \u0628\u0647 \u062d\u0633\u0627\u0628 \u0634\u0645\u0627 \u0641\u0631\u0633\u062a\u0627\u062f. \u06a9\u062f \u0631\u0627 \u0628\u0627 \u062f\u06a9\u0645\u0647\u200c\u0647\u0627\u06cc \u0632\u06cc\u0631 \u0648\u0627\u0631\u062f \u06a9\u0646\u06cc\u062f \u0648 \u2705 \u0631\u0627 \u0628\u0632\u0646\u06cc\u062f.\n")
    t.append(kinds.get(L.get("kind"), kinds["other"]) + "\n")
    t.append("\u06a9\u062f: %s\n" % shown)
    t.append("\U0001f512 \u06a9\u062f \u0631\u0627 \u0647\u0631\u06af\u0632 \u062f\u0631 \u0686\u062a \u062a\u0627\u06cc\u067e \u0646\u06a9\u0646 (\u062a\u0644\u06af\u0631\u0627\u0645 \u0622\u0646 \u0631\u0627 \u0628\u0627\u0637\u0644 \u0645\u06cc\u200c\u06a9\u0646\u062f). \u0628\u0627 \u062f\u06a9\u0645\u0647\u200c\u0647\u0627 \u0648\u0627\u0631\u062f \u06a9\u0646.")
    rows = [[Button.inline(str(d), "k:%d" % d) for d in (1, 2, 3)],
            [Button.inline(str(d), "k:%d" % d) for d in (4, 5, 6)],
            [Button.inline(str(d), "k:%d" % d) for d in (7, 8, 9)],
            [Button.inline("\u232b \u067e\u0627\u06a9", "k:del"), Button.inline("0", "k:0"), Button.inline("\u2705 \u062a\u0623\u06cc\u06cc\u062f", "k:ok")],
            [Button.inline("\U0001f504 \u06a9\u062f \u0646\u06cc\u0648\u0645\u062f\u061f \u062f\u0648\u0628\u0627\u0631\u0647 \u0628\u0641\u0631\u0633\u062a", "k:re")],
            [Button.inline("\u274c \u0627\u0646\u0635\u0631\u0627\u0641", "k:x")]]
    return "\n".join(t), rows


async def safe_edit(uid, mid, text, **kw):
    """Edit a bot message; if Telegram refuses (old/reply-keyboard message), send a new one. Returns message id."""
    try:
        await BOT.edit_message(uid, mid, text, **kw)
        return mid
    except errors.MessageNotModifiedError:
        return mid
    except Exception as e:
        log.info("edit failed (%s), sending new message", type(e).__name__)
        m = await BOT.send_message(uid, text, **kw)
        return getattr(m, "id", mid)


async def edit_login(uid, note=""):
    L = LOGIN.get(uid)
    if not L:
        return
    txt, rows = login_view(L, note)
    L["mid"] = await safe_edit(uid, L["mid"], txt, buttons=rows, parse_mode="html", link_preview=False)


async def cancel_login(uid):
    L = LOGIN.pop(uid, None)
    if L:
        try:
            await L["client"].disconnect()
        except Exception:
            pass


async def login_start(uid, phone):
    now = time.time()
    if now - LAST_LOGIN.get(uid, 0) < 20:
        await BOT.send_message(uid, "\u23f3 \u0686\u0646\u062f \u062b\u0627\u0646\u06cc\u0647 \u0635\u0628\u0631 \u06a9\u0646 \u0648 \u062f\u0648\u0628\u0627\u0631\u0647 \u062a\u0644\u0627\u0634 \u06a9\u0646.")
        return
    LAST_LOGIN[uid] = now
    await cancel_login(uid)
    try:
        tmp = await BOT.send_message(uid, "\u23f3", buttons=Button.clear())
        await BOT.delete_messages(uid, [tmp.id])
    except Exception:
        pass
    wait = await BOT.send_message(uid, "\u23f3 \u062f\u0631 \u062d\u0627\u0644 \u062f\u0631\u062e\u0648\u0627\u0633\u062a \u06a9\u062f \u0627\u0632 \u062a\u0644\u06af\u0631\u0627\u0645 ...")
    client = make_client(StringSession())
    try:
        await client.connect()
        sent = await client.send_code_request(phone)
    except errors.PhoneNumberInvalidError:
        return await _login_fail(uid, client, wait.id, "\u274c \u0634\u0645\u0627\u0631\u0647 \u0646\u0627\u0645\u0639\u062a\u0628\u0631 \u0627\u0633\u062a.")
    except errors.PhoneNumberBannedError:
        return await _login_fail(uid, client, wait.id, "\u274c \u0627\u06cc\u0646 \u0634\u0645\u0627\u0631\u0647 \u062f\u0631 \u062a\u0644\u06af\u0631\u0627\u0645 \u0645\u0633\u062f\u0648\u062f \u0627\u0633\u062a.")
    except errors.FloodWaitError as e:
        return await _login_fail(uid, client, wait.id, "\u23f3 \u062a\u0644\u06af\u0631\u0627\u0645 \u0645\u062d\u062f\u0648\u062f\u06cc\u062a \u0645\u0648\u0642\u062a \u06af\u0630\u0627\u0634\u062a\u061b %s \u062b\u0627\u0646\u06cc\u0647 \u0628\u0639\u062f \u062f\u0648\u0628\u0627\u0631\u0647 \u062a\u0644\u0627\u0634 \u06a9\u0646." % fa(e.seconds))
    except errors.ApiIdInvalidError:
        await notify(OWNER_ID, "\u274c API_ID/API_HASH \u0646\u0627\u0645\u0639\u062a\u0628\u0631 \u0627\u0633\u062a. \u062f\u0631 config.json \u062f\u0631\u0633\u062a\u0634\u0627\u0646 \u06a9\u0646.")
        return await _login_fail(uid, client, wait.id, "\u274c \u0645\u0634\u06a9\u0644 \u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u0631\u0628\u0627\u062a\u061b \u0628\u0647 \u0645\u062f\u06cc\u0631 \u062e\u0628\u0631 \u062f\u0627\u062f\u0647 \u0634\u062f.")
    except Exception as e:
        log.exception("send_code failed")
        return await _login_fail(uid, client, wait.id, "\u274c \u0627\u062a\u0635\u0627\u0644 \u0628\u0647 \u062a\u0644\u06af\u0631\u0627\u0645 \u0646\u0627\u0645\u0648\u0641\u0642 \u0628\u0648\u062f (%s). \u0641\u06cc\u0644\u062a\u0631\u0634\u06a9\u0646 \u0631\u0627 \u0686\u06a9 \u06a9\u0646." % type(e).__name__)
    ln = getattr(sent.type, "length", None) or 5
    LOGIN[uid] = dict(client=client, phone=phone, hash=sent.phone_code_hash, code="", stage="code", t=now,
                      sent=now, len=int(ln), mid=wait.id, kind=code_kind(sent), pw_tries=0)
    await edit_login(uid)


async def _login_fail(uid, client, mid, text):
    try:
        await client.disconnect()
    except Exception:
        pass
    await safe_edit(uid, mid, text + "\n\n\u062f\u0648\u0628\u0627\u0631\u0647 /start \u0628\u0632\u0646.")


async def login_key(ev, data):
    uid = ev.sender_id
    L = LOGIN.get(uid)
    if not L or L["stage"] != "code":
        return await ev.answer("\u0627\u06cc\u0646 \u0645\u0631\u062d\u0644\u0647 \u062a\u0645\u0627\u0645 \u0634\u062f\u0647\u061b /start \u0628\u0632\u0646.", alert=True)
    L["mid"] = ev.message_id
    k = data[2:]
    if k.isdigit():
        if len(L["code"]) < 8:
            L["code"] += k
        await ev.answer()
        await edit_login(uid)
        if len(L["code"]) >= L["len"]:
            await login_submit(uid)
        return
    if k == "del":
        L["code"] = L["code"][:-1]
        await ev.answer()
        return await edit_login(uid)
    if k == "x":
        await cancel_login(uid)
        await ev.answer()
        return await ev.edit("\u274c \u0648\u0631\u0648\u062f \u0644\u063a\u0648 \u0634\u062f. \u0628\u0631\u0627\u06cc \u0634\u0631\u0648\u0639 \u062f\u0648\u0628\u0627\u0631\u0647 /start \u0628\u0632\u0646.")
    if k == "ok":
        if len(L["code"]) < 4:
            return await ev.answer("\u06a9\u062f \u0631\u0627 \u06a9\u0627\u0645\u0644 \u0648\u0627\u0631\u062f \u06a9\u0646.", alert=True)
        await ev.answer()
        return await login_submit(uid)
    if k == "re":
        wait = 60 - (time.time() - L["sent"])
        if wait > 0:
            return await ev.answer("%s \u062b\u0627\u0646\u06cc\u0647 \u062f\u06cc\u06af\u0631 \u0635\u0628\u0631 \u06a9\u0646." % fa(int(wait) + 1), alert=True)
        try:
            sent = await L["client"].send_code_request(L["phone"])
            if getattr(sent, "phone_code_hash", None):
                L["hash"] = sent.phone_code_hash
            L["kind"] = code_kind(sent)
            L["len"] = int(getattr(sent.type, "length", None) or L["len"])
            L["sent"] = time.time()
            L["code"] = ""
            await ev.answer("\u06a9\u062f \u062f\u0648\u0628\u0627\u0631\u0647 \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0634\u062f.")
            await edit_login(uid, "\U0001f504 \u06a9\u062f \u062c\u062f\u06cc\u062f \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0634\u062f.")
        except errors.FloodWaitError as e:
            await ev.answer("\u062a\u0644\u06af\u0631\u0627\u0645 \u0645\u062d\u062f\u0648\u062f\u06cc\u062a \u06af\u0630\u0627\u0634\u062a\u061b %s \u062b\u0627\u0646\u06cc\u0647 \u0628\u0639\u062f." % fa(e.seconds), alert=True)
        except Exception as e:
            log.warning("resend failed: %s", e)
            await ev.answer("\u0627\u0631\u0633\u0627\u0644 \u062f\u0648\u0628\u0627\u0631\u0647 \u0645\u0645\u06a9\u0646 \u0646\u0634\u062f. /start \u0628\u0632\u0646.", alert=True)


async def login_submit(uid):
    L = LOGIN.get(uid)
    if not L:
        return
    code = L["code"]
    try:
        await L["client"].sign_in(phone=L["phone"], code=code, phone_code_hash=L["hash"])
    except errors.SessionPasswordNeededError:
        L["stage"] = "password"
        L["code"] = ""
        L["mid"] = await safe_edit(uid, L["mid"],
                               "\U0001f511 <b>\u0631\u0645\u0632 \u062f\u0648\u0645\u0631\u062d\u0644\u0647\u200c\u0627\u06cc</b>\n\n\u062d\u0633\u0627\u0628\u062a \u0631\u0645\u0632 \u062f\u0648\u0645\u0631\u062d\u0644\u0647\u200c\u0627\u06cc \u062f\u0627\u0631\u062f. \u0631\u0645\u0632\u062a \u0631\u0627 \u0647\u0645\u06cc\u0646\u200c\u062c\u0627 \u0628\u0641\u0631\u0633\u062a "
                               "(\u067e\u06cc\u0627\u0645\u062a \u0641\u0648\u0631\u0627\u064b \u067e\u0627\u06a9 \u0645\u06cc\u200c\u0634\u0648\u062f \u0648 \u062c\u0627\u06cc\u06cc \u0630\u062e\u06cc\u0631\u0647 \u0646\u0645\u06cc\u200c\u0634\u0648\u062f).\n\n\u0627\u0646\u0635\u0631\u0627\u0641: /cancel",
                               parse_mode="html", buttons=None)
        return
    except errors.PhoneCodeInvalidError:
        L["code"] = ""
        return await edit_login(uid, "\u274c \u06a9\u062f \u0627\u0634\u062a\u0628\u0627\u0647 \u0628\u0648\u062f\u061b \u062f\u0648\u0628\u0627\u0631\u0647 \u0648\u0627\u0631\u062f \u06a9\u0646.")
    except (errors.PhoneCodeExpiredError, getattr(errors, "PhoneCodeEmptyError", errors.PhoneCodeInvalidError)):
        L["code"] = ""
        L["sent"] = 0
        return await edit_login(uid, "\u231b \u06a9\u062f \u0645\u0646\u0642\u0636\u06cc \u0634\u062f. \u062f\u06a9\u0645\u0647\u200c\u06cc \u00ab\u062f\u0648\u0628\u0627\u0631\u0647 \u0628\u0641\u0631\u0633\u062a\u00bb \u0631\u0627 \u0628\u0632\u0646.")
    except errors.FloodWaitError as e:
        L["code"] = ""
        return await edit_login(uid, "\u23f3 \u0645\u062d\u062f\u0648\u062f\u06cc\u062a \u0645\u0648\u0642\u062a \u062a\u0644\u06af\u0631\u0627\u0645\u061b %s \u062b\u0627\u0646\u06cc\u0647 \u0628\u0639\u062f \u062a\u0644\u0627\u0634 \u06a9\u0646." % fa(e.seconds))
    except Exception as e:
        log.exception("sign_in failed")
        await cancel_login(uid)
        return await BOT.send_message(uid, "\u274c \u0648\u0631\u0648\u062f \u0646\u0627\u0645\u0648\u0641\u0642 \u0628\u0648\u062f (%s). \u062f\u0648\u0628\u0627\u0631\u0647 /start \u0628\u0632\u0646." % type(e).__name__)
    await login_finish(uid)


async def login_password(ev, L):
    uid = ev.sender_id
    pw = ev.raw_text or ""
    try:
        await ev.delete()
    except Exception:
        pass
    try:
        await L["client"].sign_in(password=pw)
    except errors.PasswordHashInvalidError:
        L["pw_tries"] += 1
        if L["pw_tries"] >= 5:
            await cancel_login(uid)
            return await BOT.send_message(uid, "\u274c \u0631\u0645\u0632 \u0686\u0646\u062f \u0628\u0627\u0631 \u0627\u0634\u062a\u0628\u0627\u0647 \u0628\u0648\u062f. \u0648\u0631\u0648\u062f \u0644\u063a\u0648 \u0634\u062f\u061b /start \u0628\u0632\u0646.")
        return await BOT.send_message(uid, "\u274c \u0631\u0645\u0632 \u0627\u0634\u062a\u0628\u0627\u0647 \u0627\u0633\u062a\u061b \u062f\u0648\u0628\u0627\u0631\u0647 \u0628\u0641\u0631\u0633\u062a (%s \u0627\u0632 \u06f5)." % fa(L["pw_tries"]))
    except errors.FloodWaitError as e:
        return await BOT.send_message(uid, "\u23f3 %s \u062b\u0627\u0646\u06cc\u0647 \u0628\u0639\u062f \u062f\u0648\u0628\u0627\u0631\u0647 \u062a\u0644\u0627\u0634 \u06a9\u0646." % fa(e.seconds))
    except Exception as e:
        log.exception("2fa failed")
        await cancel_login(uid)
        return await BOT.send_message(uid, "\u274c \u0648\u0631\u0648\u062f \u0646\u0627\u0645\u0648\u0641\u0642 \u0628\u0648\u062f (%s)." % type(e).__name__)
    await login_finish(uid)


async def login_finish(uid):
    L = LOGIN.get(uid)
    client = L["client"]
    me = await client.get_me()
    if me.id != uid:
        try:
            await client.log_out()
        except Exception:
            pass
        LOGIN.pop(uid, None)
        return await BOT.send_message(uid, "\u274c \u0634\u0645\u0627\u0631\u0647\u200c\u0627\u06cc \u06a9\u0647 \u0648\u0627\u0631\u062f \u0634\u062f \u0628\u0627 \u0647\u0645\u06cc\u0646 \u062d\u0633\u0627\u0628 \u062a\u0644\u06af\u0631\u0627\u0645 \u06cc\u06a9\u06cc \u0646\u06cc\u0633\u062a. \u0648\u0631\u0648\u062f \u0644\u063a\u0648 \u0634\u062f.")
    sess = enc(client.session.save())
    old = DB.one("SELECT settings FROM users WHERE id=?", (uid,))
    await stop_rt(uid)
    if old:
        DB.q("UPDATE users SET phone=?, name=?, username=?, session=?, status='active', last_seen=? WHERE id=?",
             (L["phone"], uname(me), me.username, sess, int(time.time()), uid))
    else:
        DB.q("INSERT INTO users(id,phone,name,username,session,status,settings,created,last_seen) VALUES(?,?,?,?,?,'active','{}',?,?)",
             (uid, L["phone"], uname(me), me.username, sess, int(time.time()), int(time.time())))
        load_settings(uid, "{}")
    if uid not in S:
        load_settings(uid, old[0] if old else "{}")
    LOGIN.pop(uid, None)
    fr = int(float(kv_get(uid, "frozen", 0) or 0))
    if fr > 0:
        bill_get(uid)
        DB.q("UPDATE bill SET exp=?, warned=0 WHERE uid=?", (int(time.time()) + fr, uid))
        kv_del(uid, "frozen")
    granted = False
    if not is_free(uid):
        granted = grant_test(uid)
        if left_sec(uid) <= 0:
            DB.q("UPDATE users SET status='expired' WHERE id=?", (uid,))
            try:
                await client.disconnect()
            except Exception:
                pass
            wtxt, wrows = v_wallet(uid, "\u2705 \u0648\u0627\u0631\u062f \u0634\u062f\u06cc\u060c \u0648\u0644\u06cc \u0632\u0645\u0627\u0646 \u0633\u0644\u0641\u062a \u062a\u0645\u0627\u0645 \u0634\u062f\u0647 \u0627\u0633\u062a. \u0628\u0631\u0627\u06cc \u0631\u0648\u0634\u0646 \u0634\u062f\u0646 \u0633\u06a9\u0647 \u0628\u062e\u0631.")
            return await BOT.send_message(uid, wtxt, buttons=wrows, parse_mode="html")
    await start_rt(uid, client)
    try:
        await safe_edit(uid, L["mid"], "\u2705 <b>\u0648\u0627\u0631\u062f \u0634\u062f\u06cc!</b> \u06cc\u0648\u0632\u0631\u0628\u0627\u062a \u0631\u0648\u0634\u0646 \u0634\u062f.", parse_mode="html")
    except Exception:
        pass
    if granted:
        await BOT.send_message(uid, "\U0001f381 <b>\u062a\u0633\u062a \u0631\u0627\u06cc\u06af\u0627\u0646 \u0641\u0639\u0627\u0644 \u0634\u062f:</b> %s\n\u0628\u0639\u062f \u0627\u0632 \u0622\u0646 \u0647\u0631 \U0001fa99 \u0633\u06a9\u0647 = \u06f1 \u0633\u0627\u0639\u062a (\u062f\u06a9\u0645\u0647\u200c\u06cc \u00ab\u0633\u06a9\u0647 \u0648 \u0627\u0634\u062a\u0631\u0627\u06a9\u00bb)." % fmt_left(left_sec(uid)),
                               parse_mode="html")
    txt, rows = v_main(uid)
    await BOT.send_message(uid, txt, buttons=rows, parse_mode="html")


async def notify_down(uid):
    await notify(uid, "\U0001f4e1 <b>\u06cc\u0648\u0632\u0631\u0628\u0627\u062a \u0634\u0645\u0627 \u0642\u0637\u0639 \u0634\u062f</b>\n\n\u0628\u0647 \u0627\u062d\u062a\u0645\u0627\u0644 \u0632\u06cc\u0627\u062f \u0646\u0634\u0633\u062a \u062a\u0644\u06af\u0631\u0627\u0645 \u0622\u0646 \u0628\u0633\u062a\u0647 \u06cc\u0627 \u0645\u0646\u0642\u0636\u06cc \u0634\u062f\u0647 \u0627\u0633\u062a.\n"
                      "\u0628\u0631\u0627\u06cc \u0648\u0635\u0644 \u06a9\u0631\u062f\u0646 \u062f\u0648\u0628\u0627\u0631\u0647 \u0631\u0648\u06cc \u062f\u06a9\u0645\u0647\u200c\u06cc \u0632\u06cc\u0631 \u0628\u0632\u0646\u061b \u06cc\u06a9 \u06a9\u062f \u0648\u0631\u0648\u062f \u062a\u0627\u0632\u0647 \u0628\u0631\u0627\u06cc\u062a \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f.",
                 buttons=[[Button.inline("\U0001f504 \u0648\u0631\u0648\u062f \u062f\u0648\u0628\u0627\u0631\u0647", "rl")]])


#
async def cmd_start(ev):
    uid = ev.sender_id
    row = DB.one("SELECT status FROM users WHERE id=?", (uid,))
    if row and row[0] == "active" and uid in RTS:
        txt, rows = v_main(uid)
        return await ev.respond(txt, buttons=rows, parse_mode="html")
    if row and row[0] == "expired":
        txt, rows = v_wallet(uid, "\u26d4 \u0632\u0645\u0627\u0646 \u0633\u0644\u0641 \u062a\u0648 \u062a\u0645\u0627\u0645 \u0634\u062f\u0647 \u0627\u0633\u062a.")
        return await ev.respond(txt, buttons=rows, parse_mode="html")
    if row and row[0] == "down":
        return await notify_down(uid)
    if row and row[0] == "off":
        return await ev.respond("\u26d4 \u062d\u0633\u0627\u0628 \u0634\u0645\u0627 \u062a\u0648\u0633\u0637 \u0645\u062f\u06cc\u0631 \u063a\u06cc\u0631\u0641\u0639\u0627\u0644 \u0634\u062f\u0647 \u0627\u0633\u062a.")
    if not row and DB.one("SELECT COUNT(*) FROM users")[0] >= MAX_USERS:
        return await ev.respond("\u0638\u0631\u0641\u06cc\u062a \u0631\u0628\u0627\u062a \u067e\u0631 \u0627\u0633\u062a. \u0628\u0639\u062f\u0627\u064b \u062f\u0648\u0628\u0627\u0631\u0647 \u0627\u0645\u062a\u062d\u0627\u0646 \u06a9\u0646.")
    await ev.respond(START_TEXT, parse_mode="html",
                     buttons=[Button.request_phone("\U0001f4f1 \u0627\u0631\u0633\u0627\u0644 \u0634\u0645\u0627\u0631\u0647\u200c\u06cc \u0645\u0646 \u0648 \u0648\u0631\u0648\u062f", resize=True, single_use=True)])


async def on_contact(ev):
    uid = ev.sender_id
    c = ev.message.contact
    if getattr(c, "user_id", None) != uid:
        return await ev.respond("\u274c \u0641\u0642\u0637 \u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u06cc \u0634\u0645\u0627\u0631\u0647\u200c\u06cc <b>\u062e\u0648\u062f\u062a</b> \u0631\u0627 \u0628\u0641\u0631\u0633\u062a\u06cc (\u0628\u0627 \u062f\u06a9\u0645\u0647\u200c\u06cc \u0627\u0631\u0633\u0627\u0644 \u0634\u0645\u0627\u0631\u0647).", parse_mode="html")
    row = DB.one("SELECT status FROM users WHERE id=?", (uid,))
    if row and row[0] == "off":
        return await ev.respond("\u26d4 \u062d\u0633\u0627\u0628 \u0634\u0645\u0627 \u062a\u0648\u0633\u0637 \u0645\u062f\u06cc\u0631 \u063a\u06cc\u0631\u0641\u0639\u0627\u0644 \u0634\u062f\u0647 \u0627\u0633\u062a.")
    if not row and DB.one("SELECT COUNT(*) FROM users")[0] >= MAX_USERS:
        return await ev.respond("\u0638\u0631\u0641\u06cc\u062a \u0631\u0628\u0627\u062a \u067e\u0631 \u0627\u0633\u062a.")
    phone = "+" + (c.phone_number or "").lstrip("+")
    await login_start(uid, phone)


async def on_owner(ev, cmd, arg):
    if cmd == "/stats":
        total = DB.one("SELECT COUNT(*) FROM users")[0]
        down = DB.one("SELECT COUNT(*) FROM users WHERE status='down'")[0]
        use = collections.Counter()
        for u in S:
            for k in FEATS:
                if is_on(u, k):
                    use[k] += 1
        top = "\n".join("\u2022 %s: %s" % (FEATS[k]["title"], fa(n)) for k, n in use.most_common(8)) or "\u2014"
        return await ev.respond("\U0001f4c8 <b>\u0622\u0645\u0627\u0631</b>\n\n\u06a9\u0627\u0631\u0628\u0631\u0627\u0646: %s\n\u062f\u0631 \u062d\u0627\u0644 \u0627\u062c\u0631\u0627: %s\n\u0642\u0637\u0639\u200c\u0634\u062f\u0647: %s\n\n<b>\u067e\u0631\u06a9\u0627\u0631\u0628\u0631\u062f\u062a\u0631\u06cc\u0646\u200c\u0647\u0627:</b>\n%s" % (
            fa(total), fa(len(RTS)), fa(down), esc(top)), parse_mode="html")
    if cmd == "/broadcast" and arg:
        n = 0
        for (u,) in DB.all("SELECT id FROM users"):
            if await notify(u, esc(arg)):
                n += 1
            await asyncio.sleep(0.1)
        return await ev.respond("\u2705 \u0628\u0631\u0627\u06cc %s \u0646\u0641\u0631 \u0627\u0631\u0633\u0627\u0644 \u0634\u062f." % fa(n))
    if cmd in ("/kick", "/revive") and arg.strip().isdigit():
        u = int(arg.strip())
        if cmd == "/kick":
            DB.q("UPDATE users SET status='off' WHERE id=?", (u,))
            await stop_rt(u)
            return await ev.respond("\u26d4 \u06a9\u0627\u0631\u0628\u0631 %s \u063a\u06cc\u0631\u0641\u0639\u0627\u0644 \u0634\u062f." % u)
        DB.q("UPDATE users SET status='down' WHERE id=?", (u,))
        await notify_down(u)
        return await ev.respond("\u267b\ufe0f \u0628\u0647 \u06a9\u0627\u0631\u0628\u0631 %s \u067e\u06cc\u0627\u0645 \u0648\u0631\u0648\u062f \u062f\u0648\u0628\u0627\u0631\u0647 \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0634\u062f." % u)
    if cmd == "/games":
        gg = game_groups()
        return await ev.respond("\U0001f3ae \u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0628\u0627\u0632\u06cc: %s\n\n\u0628\u0631\u0627\u06cc \u0627\u0641\u0632\u0648\u062f\u0646: \u0631\u0628\u0627\u062a \u0631\u0627 \u062f\u0631 \u06af\u0631\u0648\u0647 \u0627\u062f\u0645\u06cc\u0646 \u06a9\u0646 \u0648 \u062f\u0627\u062e\u0644 \u0647\u0645\u0627\u0646 \u06af\u0631\u0648\u0647 <code>/setgame</code> \u0628\u0641\u0631\u0633\u062a."
                                % (("<code>%s</code>" % "</code>, <code>".join(str(x) for x in gg)) if gg else "\u0647\u06cc\u0686"), parse_mode="html")
    if cmd == "/update":
        text = arg or ("\U0001f527 <b>\u062f\u0631 \u062d\u0627\u0644 \u0628\u0647\u200c\u0631\u0648\u0632\u0631\u0633\u0627\u0646\u06cc \u0633\u0631\u0648\u06cc\u0633\u200c\u0647\u0627 \u0647\u0633\u062a\u06cc\u0645</b>\n\nSelf Speed \u0628\u0631\u0627\u06cc \u0627\u0631\u062a\u0642\u0627 \u0686\u0646\u062f \u0633\u0627\u0639\u062a \u062e\u0627\u0645\u0648\u0634 \u0645\u06cc\u200c\u0634\u0648\u062f. "
                       "\u0628\u0639\u062f \u0627\u0632 \u0627\u062a\u0645\u0627\u0645\u060c \u0628\u0647 \u0647\u0645\u06cc\u0646 \u0631\u0628\u0627\u062a \u067e\u06cc\u0627\u0645 \u0645\u06cc\u200c\u062f\u0647\u06cc\u0645 \u062a\u0627 \u062f\u0648\u0628\u0627\u0631\u0647 \u0648\u0627\u0631\u062f \u0634\u0648\u06cc\u061b \u0647\u0645\u0647\u200c\u06cc \u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u0648 \u0645\u0648\u062c\u0648\u062f\u06cc\u200c\u0627\u062a \u062d\u0641\u0638 \u0645\u06cc\u200c\u0634\u0648\u062f. \U0001f64f")
        ok = bad = 0
        for (u,) in DB.all("SELECT id FROM users"):
            if await notify(u, text):
                ok += 1
            else:
                bad += 1
            await asyncio.sleep(0.05)
        return await ev.respond("\u2705 \u0628\u0631\u0627\u06cc %s \u06a9\u0627\u0631\u0628\u0631 \u0627\u0631\u0633\u0627\u0644 \u0634\u062f (%s \u0646\u0627\u0645\u0648\u0641\u0642).\n\u062d\u0627\u0644\u0627 /backup \u0628\u0632\u0646 \u0648 \u0641\u0627\u06cc\u0644 \u0631\u0627 \u0646\u06af\u0647 \u062f\u0627\u0631." % (fa(ok), fa(bad)))
    if cmd == "/backup":
        buf, n = make_backup(full=(arg.strip().lower() == "full"))
        await BOT.send_file(OWNER_ID, buf, caption="\U0001f4be \u0628\u06a9\u0627\u067e %s \u06a9\u0627\u0631\u0628\u0631%s\n\u0631\u0648\u06cc \u0631\u0628\u0627\u062a \u062c\u062f\u06cc\u062f \u0647\u0645\u06cc\u0646 \u0641\u0627\u06cc\u0644 \u0631\u0627 \u0628\u0641\u0631\u0633\u062a\u061b \u0628\u0639\u062f /relogin \u0628\u0632\u0646." % (
            fa(n), " (\u0628\u0627 \u0646\u0634\u0633\u062a\u200c\u0647\u0627)" if arg.strip().lower() == "full" else ""))
        return
    if cmd == "/relogin":
        ok = bad = 0
        for (u,) in DB.all("SELECT id FROM users WHERE status='down'"):
            try:
                await BOT.send_message(u, "\U0001f504 <b>\u0633\u0631\u0648\u06cc\u0633\u200c\u0647\u0627\u06cc Self Speed \u0627\u0631\u062a\u0642\u0627 \u06cc\u0627\u0641\u062a!</b>\n\n\u0628\u0631\u0627\u06cc \u0627\u062f\u0627\u0645\u0647\u060c \u062f\u0648\u0628\u0627\u0631\u0647 \u0648\u0627\u0631\u062f \u0634\u0648. "
                                          "\u0647\u0645\u0647\u200c\u06cc \u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u0648 \u0645\u0648\u062c\u0648\u062f\u06cc\u200c\u0627\u062a \u062d\u0641\u0638 \u0634\u062f\u0647 \u0627\u0633\u062a.",
                                       buttons=[[Button.inline("\U0001f511 \u0648\u0631\u0648\u062f \u062f\u0648\u0628\u0627\u0631\u0647", "rl")]], parse_mode="html")
                ok += 1
            except Exception as e:
                bad += 1
                log.info("relogin notice failed for %s: %s", u, e)
            await asyncio.sleep(0.05)
        return await ev.respond("\u2705 \u067e\u06cc\u0627\u0645 \u0648\u0631\u0648\u062f \u062f\u0648\u0628\u0627\u0631\u0647 \u0628\u0631\u0627\u06cc %s \u06a9\u0627\u0631\u0628\u0631 \u0631\u0641\u062a (%s \u0646\u0627\u0645\u0648\u0641\u0642\u061b \u0627\u0648\u0646\u200c\u0647\u0627 \u0628\u0627\u06cc\u062f \u06cc\u06a9\u200c\u0628\u0627\u0631 /start \u0628\u0632\u0646\u0646)." % (fa(ok), fa(bad)))
    if cmd == "/errors":
        if not ERRS:
            return await ev.respond("\u2705 \u062e\u0637\u0627\u06cc\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647.")
        return await ev.respond("<b>\u0622\u062e\u0631\u06cc\u0646 \u062e\u0637\u0627\u0647\u0627:</b>\n\n" + "\n\n".join("<code>%s</code>" % esc(e[-450:]) for e in list(ERRS)[-6:]),
                                parse_mode="html")
    if cmd == "/prices":
        lines = ["\U0001fa99 <b>\u0628\u0633\u062a\u0647\u200c\u0647\u0627\u06cc \u0633\u06a9\u0647</b>"] + ["\u2022 %s \u0633\u06a9\u0647 = %s \u062a\u0648\u0645\u0627\u0646" % (fa(c), money(p)) for c, p in get_packs()]
        lines.append("\n\U0001f4b3 \u06a9\u0627\u0631\u062a: %s" % esc(kv_get(0, "card", "\u062b\u0628\u062a \u0646\u0634\u062f\u0647 (/setcard)")))
        lines.append("\U0001f381 \u062a\u0633\u062a \u0631\u0627\u06cc\u06af\u0627\u0646: %s" % fmt_left(test_sec()))
        lines.append("\U0001f3a1 \u06af\u0631\u062f\u0648\u0646\u0647: %s" % ("\u0631\u0648\u0634\u0646" if wheel_on() else "\u062e\u0627\u0645\u0648\u0634"))
        lines.append("\U0001f310 \u0645\u06cc\u0646\u06cc\u200c\u0627\u067e: %s" % (webapp_url() or "\u062a\u0646\u0638\u06cc\u0645 \u0646\u0634\u062f\u0647"))
        return await ev.respond("\n".join(lines), parse_mode="html")
    a = arg.translate(EN_DIGITS).replace(",", " ").split()
    if cmd == "/setprice":
        if len(a) == 2 and a[0].isdigit() and a[1].isdigit() and int(a[0]) > 0:
            packs = dict(get_packs())
            packs[int(a[0])] = int(a[1])
            set_packs(packs)
            return await ev.respond("\u2705 %s \u0633\u06a9\u0647 = %s \u062a\u0648\u0645\u0627\u0646 \u062b\u0628\u062a \u0634\u062f." % (fa(a[0]), money(a[1])))
        return await ev.respond("\u0645\u062b\u0627\u0644: <code>/setprice 5 20000</code> (\u06f5 \u0633\u06a9\u0647 = \u06f2\u06f0\u06f0\u06f0\u06f0 \u062a\u0648\u0645\u0627\u0646)", parse_mode="html")
    if cmd == "/delprice":
        packs = dict(get_packs())
        if len(a) == 1 and a[0].isdigit() and int(a[0]) in packs and len(packs) > 1:
            packs.pop(int(a[0]))
            set_packs(packs)
            return await ev.respond("\U0001f5d1 \u062d\u0630\u0641 \u0634\u062f.")
        return await ev.respond("\u0645\u062b\u0627\u0644: <code>/delprice 5</code> (\u062d\u062f\u0627\u0642\u0644 \u06cc\u06a9 \u0628\u0633\u062a\u0647 \u0628\u0627\u06cc\u062f \u0628\u0645\u0627\u0646\u062f)", parse_mode="html")
    if cmd == "/setcard":
        kv_set(0, "card", arg)
        return await ev.respond("\u2705 \u0630\u062e\u06cc\u0631\u0647 \u0634\u062f.")
    if cmd == "/gift":
        try:
            u, n = int(a[0]), float(a[1])
        except Exception:
            return await ev.respond("\u0645\u062b\u0627\u0644: <code>/gift 123456 3</code> (\u06f3 \u0633\u06a9\u0647 \u0628\u0647 \u06a9\u0627\u0631\u0628\u0631)", parse_mode="html")
        if not DB.one("SELECT 1 FROM users WHERE id=?", (u,)):
            return await ev.respond("\u0627\u06cc\u0646 \u06a9\u0627\u0631\u0628\u0631 \u067e\u06cc\u062f\u0627 \u0646\u0634\u062f.")
        add_time(u, int(n * COIN_SEC))
        await notify(u, "\U0001f381 \u0645\u062f\u06cc\u0631 <b>%s \u0633\u0627\u0639\u062a</b> \u0628\u0647 \u0633\u0644\u0641\u062a \u0627\u0636\u0627\u0641\u0647 \u06a9\u0631\u062f.\n\u23f3 \u0632\u0645\u0627\u0646 \u0628\u0627\u0642\u06cc\u200c\u0645\u0627\u0646\u062f\u0647: <b>%s</b>" % (fa(n), fmt_left(left_sec(u))))
        await resume_user(u)
        return await ev.respond("\u2705 \u0627\u0646\u062c\u0627\u0645 \u0634\u062f. \u0632\u0645\u0627\u0646 \u06a9\u0627\u0631\u0628\u0631: %s" % fmt_left(left_sec(u)))
    if cmd == "/test":
        try:
            h = float(a[0])
            assert 0 <= h <= 720
        except Exception:
            return await ev.respond("\u0645\u062b\u0627\u0644: <code>/test 1</code> (\u0633\u0627\u0639\u062a \u062a\u0633\u062a \u0631\u0627\u06cc\u06af\u0627\u0646\u061b \u06f0 \u06cc\u0639\u0646\u06cc \u0628\u062f\u0648\u0646 \u062a\u0633\u062a)", parse_mode="html")
        kv_set(0, "test_h", h)
        return await ev.respond("\u2705 \u062a\u0633\u062a \u0631\u0627\u06cc\u06af\u0627\u0646: %s" % fmt_left(test_sec()))
    if cmd == "/wheel":
        if a and a[0].lower() in ("on", "off"):
            kv_set(0, "wheel", "1" if a[0].lower() == "on" else "0")
            return await ev.respond("\u2705 \u06af\u0631\u062f\u0648\u0646\u0647 %s \u0634\u062f." % ("\u0631\u0648\u0634\u0646" if a[0].lower() == "on" else "\u062e\u0627\u0645\u0648\u0634"))
        return await ev.respond("\u0645\u062b\u0627\u0644: /wheel on  \u06cc\u0627  /wheel off")
    if cmd == "/seturl":
        kv_set(0, "url", arg.strip())
        return await ev.respond("\u2705 \u0630\u062e\u06cc\u0631\u0647 \u0634\u062f\u061b \u0628\u0639\u062f \u0627\u0632 \u0631\u06cc\u200c\u0627\u0633\u062a\u0627\u0631\u062a \u0631\u0628\u0627\u062a\u060c \u062f\u06a9\u0645\u0647\u200c\u06cc \u0645\u0646\u0648 \u0647\u0645 \u062a\u0646\u0638\u06cc\u0645 \u0645\u06cc\u200c\u0634\u0648\u062f.")
    if cmd == "/user":
        try:
            u = int(a[0])
        except Exception:
            return await ev.respond("\u0645\u062b\u0627\u0644: /user 123456")
        r = DB.one("SELECT name, username, status FROM users WHERE id=?", (u,))
        if not r:
            return await ev.respond("\u067e\u06cc\u062f\u0627 \u0646\u0634\u062f.")
        return await ev.respond("\U0001f464 %s @%s\n\u0648\u0636\u0639\u06cc\u062a: %s\n\u23f3 \u0632\u0645\u0627\u0646: %s\n\u062f\u0631 \u062d\u0627\u0644 \u0627\u062c\u0631\u0627: %s" % (
            esc(r[0] or ""), r[1] or "\u2014", r[2], fmt_left(left_sec(u)), "\u0628\u0644\u0647" if u in RTS else "\u062e\u06cc\u0631"), parse_mode="html")
    return await ev.respond(
        "\u062f\u0633\u062a\u0648\u0631\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631:\n/stats  /broadcast \u0645\u062a\u0646  /kick \u0622\u06cc\u062f\u06cc  /revive \u0622\u06cc\u062f\u06cc  /user \u0622\u06cc\u062f\u06cc\n"
        "/prices  /setprice \u0633\u06a9\u0647 \u0642\u06cc\u0645\u062a  /delprice \u0633\u06a9\u0647  /setcard \u0645\u062a\u0646\n/gift \u0622\u06cc\u062f\u06cc \u0633\u06a9\u0647  /test \u0633\u0627\u0639\u062a  /wheel on|off  /seturl \u0622\u062f\u0631\u0633  /errors\n"
        "/update (\u067e\u06cc\u0627\u0645 \u0628\u0647\u200c\u0631\u0648\u0632\u0631\u0633\u0627\u0646\u06cc)  /backup  /relogin  /games")


async def on_cmd(ev, text):
    uid = ev.sender_id
    cmd, _, arg = text.partition(" ")
    cmd = cmd.split("@")[0].lower()
    if cmd == "/start":
        return await cmd_start(ev)
    if cmd in ("/panel", "/menu"):
        if uid in RTS:
            txt, rows = v_main(uid)
            return await ev.respond(txt, buttons=rows, parse_mode="html")
        return await cmd_start(ev)
    if cmd == "/help":
        return await ev.respond(HELP_PANEL, parse_mode="html")
    if cmd == "/cancel":
        PEND.pop(uid, None)
        await cancel_login(uid)
        return await ev.respond("\u21a9\ufe0f \u0644\u063a\u0648 \u0634\u062f. /panel", buttons=Button.clear())
    if cmd == "/logout":
        return await ev.respond("\u0645\u0637\u0645\u0626\u0646\u06cc \u0645\u06cc\u200c\u062e\u0648\u0627\u0647\u06cc \u062e\u0627\u0631\u062c \u0634\u0648\u06cc\u061f \u0646\u0634\u0633\u062a \u06a9\u0627\u0645\u0644\u0627\u064b \u067e\u0627\u06a9 \u0645\u06cc\u200c\u0634\u0648\u062f.",
                                buttons=[[Button.inline("\u2705 \u0628\u0644\u0647\u060c \u062e\u0631\u0648\u062c", "lo2"), Button.inline("\u21a9 \u0646\u0647", "m")]])
    if cmd in ("/coins", "/wallet", "/app"):
        if DB.one("SELECT 1 FROM users WHERE id=?", (uid,)):
            txt, rows = v_wallet(uid)
            return await ev.respond(txt, buttons=rows, parse_mode="html")
        return await cmd_start(ev)
    if uid == OWNER_ID and cmd == "/admin":
        t, rows = v_admin()
        return await ev.respond(t, buttons=rows, parse_mode="html")
    if uid == OWNER_ID and cmd in ("/stats", "/broadcast", "/kick", "/revive", "/prices", "/setprice",
                                   "/delprice", "/setcard", "/gift", "/test", "/wheel", "/seturl", "/user", "/errors", "/update",
                                   "/backup", "/relogin", "/games"):
        return await on_owner(ev, cmd, arg.strip())


async def on_msg(ev):
    if not ev.is_private:
        try:
            return await on_group(ev)
        except Exception:
            log.exception("on_group failed")
            await report_error("on_group")
            return
    try:
        uid = ev.sender_id
        if DB.one("SELECT 1 FROM users WHERE id=?", (uid,)):
            try:
                sn = await ev.get_sender()
                ah = getattr(sn, "access_hash", None)
                if ah and str(kv_get(uid, "ah", "")) != str(ah):
                    kv_set(uid, "ah", ah)
            except Exception:
                pass
        if uid == OWNER_ID and getattr(ev.message, "document", None) is not None:
            if await restore_from(ev):
                return
        if ev.message.contact:
            return await on_contact(ev)
        text = ev.raw_text or ""
        pp = PEND.get(uid)
        if pp and pp.get("kind") == "adm" and uid == OWNER_ID and not text.startswith("/"):
            return await admin_input(ev, pp)
        if pp and pp.get("kind") == "pay" and not text.startswith("/"):
            return await receive_receipt(ev, pp)
        if text.startswith("/"):
            return await on_cmd(ev, text)
        L = LOGIN.get(uid)
        if L and L["stage"] == "password":
            return await login_password(ev, L)
        if uid in PEND:
            return await handle_input(ev)
        if DB.one("SELECT 1 FROM users WHERE id=?", (uid,)):
            return await ev.respond("\u0628\u0631\u0627\u06cc \u0628\u0627\u0632 \u06a9\u0631\u062f\u0646 \u067e\u0646\u0644 /panel \u0631\u0627 \u0628\u0632\u0646.")
        return await ev.respond("\u0628\u0631\u0627\u06cc \u0634\u0631\u0648\u0639 /start \u0631\u0627 \u0628\u0632\u0646.")
    except Exception:
        log.exception("on_msg failed")
        await report_error("on_msg")
        try:
            await ev.respond("\u26a0\ufe0f \u062e\u0637\u0627\u06cc \u062f\u0627\u062e\u0644\u06cc. \u062f\u0648\u0628\u0627\u0631\u0647 \u0627\u0645\u062a\u062d\u0627\u0646 \u06a9\u0646.")
        except Exception:
            pass


async def handle_input(ev):
    uid = ev.sender_id
    p = PEND.get(uid)
    rt = RTS.get(uid)
    txt = (ev.raw_text or "").strip()
    try:
        await ev.delete()
    except Exception:
        pass
    if not rt:
        PEND.pop(uid, None)
        return await ev.respond("\u062d\u0633\u0627\u0628\u062a \u0645\u062a\u0635\u0644 \u0646\u06cc\u0633\u062a. /start")
    kind = p["kind"]
    err, note, key = "", "", p.get("key")
    if kind == "p":
        sp = FEATS[key]["params"][p["idx"]]
        if sp["t"] == "text":
            if not txt or len(txt) > 500:
                err = "\u274c \u0645\u062a\u0646 \u0646\u0627\u0645\u0639\u062a\u0628\u0631 \u0627\u0633\u062a."
            else:
                set_p(uid, key, sp["n"], txt)
        elif sp["t"] == "int":
            v = txt.translate(EN_DIGITS)
            if not v.isdigit() or not (sp["lo"] <= int(v) <= sp["hi"]):
                err = "\u274c \u0639\u062f\u062f\u06cc \u0628\u06cc\u0646 %s \u062a\u0627 %s \u0628\u0641\u0631\u0633\u062a." % (fa(sp["lo"]), fa(sp["hi"]))
            else:
                set_p(uid, key, sp["n"], int(v))
        elif sp["t"] == "one":
            item, err = await parse_item(rt, sp["k"], txt, sp)
            if not err:
                set_p(uid, key, sp["n"], item)
        if not err:
            note = "\u2705 \u0630\u062e\u06cc\u0631\u0647 \u0634\u062f."
            rt.last_name = rt.last_bio = None
            rt.last["clock"] = 0
    elif kind == "la":
        sp = FEATS[key]["params"][p["idx"]]
        lst = get_p(uid, key, sp["n"]) or []
        if len(lst) >= sp["mx"]:
            err = "\u274c \u062d\u062f\u0627\u06a9\u062b\u0631 %s \u0645\u0648\u0631\u062f \u0645\u062c\u0627\u0632 \u0627\u0633\u062a." % fa(sp["mx"])
        else:
            item, err = await parse_item(rt, sp["k"], txt, sp)
            if not err:
                lst.append(item)
                set_p(uid, key, sp["n"], lst)
                note = "\u2705 \u0627\u0636\u0627\u0641\u0647 \u0634\u062f."
    elif kind == "mg":
        item, err = await parse_item(rt, "chat", txt)
        if not err:
            if any(g["id"] == item["id"] for g in S[uid]["mg"]):
                err = "\u0627\u06cc\u0646 \u06af\u0631\u0648\u0647 \u0627\u0632 \u0642\u0628\u0644 \u0647\u0633\u062a."
            else:
                S[uid]["mg"].append(item)
                save_settings(uid)
                note = "\u2705 \u0627\u0636\u0627\u0641\u0647 \u0634\u062f."
    if err:
        if kind == "mg":
            view = ("%s\n\n\u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0644\u06cc\u0646\u06a9 \u06af\u0631\u0648\u0647 \u0631\u0627 \u0628\u0641\u0631\u0633\u062a." % err, [[Button.inline("\u21a9 \u0627\u0646\u0635\u0631\u0627\u0641", "a:mg:0")]])
        else:
            view = v_prompt(uid, key, p["idx"], kind, err)
    else:
        PEND.pop(uid, None)
        view = await v_action(uid, "mg", "0", note) if kind == "mg" else v_feat(uid, key, note)
    try:
        await BOT.edit_message(uid, p["mid"], view[0], buttons=view[1], parse_mode="html", link_preview=False)
    except errors.MessageNotModifiedError:
        pass


#
async def do_toggle(uid, key):
    rt = RTS.get(uid)
    if not rt:
        return "\u062d\u0633\u0627\u0628\u062a \u0645\u062a\u0635\u0644 \u0646\u06cc\u0633\u062a\u061b /start \u0628\u0632\u0646."
    f = FEATS[key]
    new = not is_on(uid, key)
    if new:
        for pn in f["need"]:
            if not get_p(uid, key, pn):
                return "\u0627\u0648\u0644 \u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u0627\u06cc\u0646 \u0642\u0627\u0628\u0644\u06cc\u062a \u0631\u0627 \u06a9\u0627\u0645\u0644 \u06a9\u0646 (\u062f\u06a9\u0645\u0647\u200c\u06cc \u2699\ufe0f)."
    set_on(uid, key, new)
    try:
        await on_toggle(rt, key, new)
    except AUTH_DEAD as e:
        await session_dead(rt, e)
    except Exception:
        log.exception("on_toggle failed")
    if new and key in GROUP_FEATS and not S[uid]["mg"]:
        return "\u0631\u0648\u0634\u0646 \u0634\u062f\u061b \u0648\u0644\u06cc \u0647\u0646\u0648\u0632 \u00ab\u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc\u00bb \u0646\u062f\u0627\u0631\u06cc (\u0627\u0628\u0632\u0627\u0631\u0647\u0627 \u2190 \u06af\u0631\u0648\u0647\u200c\u0647\u0627\u06cc \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc)."
    return None


async def on_cb(ev):
    uid = ev.sender_id
    try:
        data = ev.data.decode()
        if data.startswith("k:"):
            return await login_key(ev, data)
        if data.startswith("bg:"):
            _, op_, cid_ = data.split(":")
            return await game_cb(ev, op_, int(cid_))
        if data.startswith("ad:"):
            if uid != OWNER_ID:
                return await ev.answer("\u0641\u0642\u0637 \u0645\u062f\u06cc\u0631", alert=True)
            return await admin_cb(ev, data[3:])
        if data[:4] in ("pok:", "pno:"):
            if uid != OWNER_ID:
                return await ev.answer("\u0641\u0642\u0637 \u0645\u062f\u06cc\u0631", alert=True)
            return await pay_decide(ev, data.startswith("pok:"), int(data[4:]))
        row = DB.one("SELECT status FROM users WHERE id=?", (uid,))
        if not row:
            return await ev.answer("\u0627\u0648\u0644 /start \u0628\u0632\u0646.", alert=True)
        parts = data.split(":")
        op = parts[0]
        view, alert = None, None
        if op == "x":
            await ev.answer()
            return await ev.delete()
        if op == "rl":
            r = DB.one("SELECT phone FROM users WHERE id=?", (uid,))
            await ev.answer()
            return await login_start(uid, r[0])
        if op == "wc":
            return await ev.answer("\u06a9\u0627\u0631\u062a \u0645\u0648\u062c\u0648\u062f\u06cc \u0641\u0642\u0637 \u062a\u0648\u06cc \u06af\u0631\u0648\u0647 \u0628\u0627\u0632\u06cc \u0627\u0633\u062a\u061b \u0622\u0646\u062c\u0627 \u0628\u0646\u0648\u06cc\u0633: \u0645\u0648\u062c\u0648\u062f\u06cc", alert=True)
        if op == "w":
            PEND.pop(uid, None)
            view = v_wallet(uid)
        elif op == "wb":
            packs = dict(get_packs())
            coins = int(parts[1])
            if coins not in packs:
                return await ev.answer("\u0627\u06cc\u0646 \u0628\u0633\u062a\u0647 \u062f\u06cc\u06af\u0631 \u0648\u062c\u0648\u062f \u0646\u062f\u0627\u0631\u062f.", alert=True)
            PEND[uid] = dict(kind="pay", coins=coins, price=packs[coins], mid=ev.message_id, t=time.time())
            card = kv_get(0, "card", "") or "\u0647\u0646\u0648\u0632 \u0634\u0645\u0627\u0631\u0647 \u06a9\u0627\u0631\u062a \u062b\u0628\u062a \u0646\u0634\u062f\u0647\u061b \u0628\u0647 \u0645\u062f\u06cc\u0631 \u067e\u06cc\u0627\u0645 \u0628\u062f\u0647."
            view = ("\U0001f4b3 <b>\u062e\u0631\u06cc\u062f %s \u0633\u06a9\u0647</b>\n\n\u0645\u0628\u0644\u063a: <b>%s \u062a\u0648\u0645\u0627\u0646</b>\n\u06a9\u0627\u0631\u062a\u200c\u0628\u0647\u200c\u06a9\u0627\u0631\u062a \u0628\u0647:\n<code>%s</code>\n\n"
                    "\u0628\u0639\u062f \u0627\u0632 \u067e\u0631\u062f\u0627\u062e\u062a\u060c <b>\u0639\u06a9\u0633 \u0631\u0633\u06cc\u062f</b> \u0631\u0627 \u0647\u0645\u06cc\u0646\u200c\u062c\u0627 \u0628\u0641\u0631\u0633\u062a. \u0628\u0639\u062f \u0627\u0632 \u062a\u0623\u06cc\u06cc\u062f \u0645\u062f\u06cc\u0631 \u0633\u06a9\u0647 \u0627\u0636\u0627\u0641\u0647 \u0648 \u0633\u0644\u0641\u062a \u0631\u0648\u0634\u0646 \u0645\u06cc\u200c\u0634\u0648\u062f." % (
                        fa(coins), money(packs[coins]), esc(card)),
                    [[Button.inline("\u21a9 \u0627\u0646\u0635\u0631\u0627\u0641", "w")]])
        elif op == "m":
            view = v_main(uid)
        elif op == "c":
            view = v_cat(uid, parts[1])
        elif op == "on":
            view = v_on(uid)
        elif op == "hlp":
            view = (HELP_PANEL, [BACK_MAIN])
        elif op == "f":
            PEND.pop(uid, None)
            view = v_feat(uid, parts[1])
        elif op == "t":
            alert = await do_toggle(uid, parts[1])
            view = v_feat(uid, parts[1]) if parts[2] == "f" else v_cat(uid, FEATS[parts[1]]["cat"])
        elif op == "pe":
            key, idx = parts[1], int(parts[2])
            PEND[uid] = dict(kind="p", key=key, idx=idx, mid=ev.message_id, t=time.time())
            view = v_prompt(uid, key, idx, "p")
        elif op == "px":
            key, idx = parts[1], int(parts[2])
            set_p(uid, key, FEATS[key]["params"][idx]["n"], None)
            if is_on(uid, key) and key in FEATS and FEATS[key]["need"]:
                set_on(uid, key, False)
            view = v_feat(uid, key, "\U0001f5d1 \u067e\u0627\u06a9 \u0634\u062f.")
        elif op == "pc":
            key, idx, j = parts[1], int(parts[2]), int(parts[3])
            sp = FEATS[key]["params"][idx]
            set_p(uid, key, sp["n"], sp["o"][j][0])
            rt = RTS.get(uid)
            if rt:
                rt.last_name = rt.last_bio = None
                rt.last["clock"] = 0
            view = v_feat(uid, key)
        elif op == "la":
            key, idx = parts[1], int(parts[2])
            PEND[uid] = dict(kind="la", key=key, idx=idx, mid=ev.message_id, t=time.time())
            view = v_prompt(uid, key, idx, "la")
        elif op == "ld":
            key, idx, j = parts[1], int(parts[2]), int(parts[3])
            sp = FEATS[key]["params"][idx]
            lst = get_p(uid, key, sp["n"]) or []
            if j < len(lst):
                lst.pop(j)
                set_p(uid, key, sp["n"], lst)
            if not lst and is_on(uid, key) and sp["n"] in FEATS[key]["need"]:
                set_on(uid, key, False)
            view = v_feat(uid, key)
        elif op == "lc":
            key, idx = parts[1], int(parts[2])
            sp = FEATS[key]["params"][idx]
            set_p(uid, key, sp["n"], [])
            if is_on(uid, key) and sp["n"] in FEATS[key]["need"]:
                set_on(uid, key, False)
            view = v_feat(uid, key, "\U0001f9f9 \u067e\u0627\u06a9 \u0634\u062f.")
        elif op == "a":
            name, arg = parts[1], (parts[2] if len(parts) > 2 else "0")
            if name == "mga":
                PEND[uid] = dict(kind="mg", mid=ev.message_id, t=time.time())
                view = ("\u2795 <b>\u0627\u0641\u0632\u0648\u062f\u0646 \u06af\u0631\u0648\u0647</b>\n\n\u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0644\u06cc\u0646\u06a9 \u06af\u0631\u0648\u0647 \u0631\u0627 \u0628\u0641\u0631\u0633\u062a (\u06cc\u0627 \u062f\u0627\u062e\u0644 \u062e\u0648\u062f \u06af\u0631\u0648\u0647 \u0628\u0646\u0648\u06cc\u0633 <code>.manage</code>).",
                        [[Button.inline("\u21a9 \u0627\u0646\u0635\u0631\u0627\u0641", "a:mg:0")]])
            elif name in ("lv2", "ks", "ksall", "d24y", "clr", "mgd"):
                view, alert = await do_action(uid, name, arg)
            else:
                view = await v_action(uid, name, arg)
        elif op == "al":
            rt = RTS.get(uid)
            h = int(parts[2])
            if rt and parts[1] == "ok":
                known = set(json.loads(kv_get(uid, "auth_known", "[]")))
                known.add(h)
                kv_set(uid, "auth_known", json.dumps(sorted(known)))
                rt.pend_auth.pop(h, None)
                await ev.answer("\u2705 \u062a\u0623\u06cc\u06cc\u062f \u0634\u062f")
                return await ev.edit("\u2705 \u0627\u06cc\u0646 \u0648\u0631\u0648\u062f \u0631\u0627 \u062a\u0623\u06cc\u06cc\u062f \u06a9\u0631\u062f\u06cc.")
            if rt and parts[1] == "kick":
                await ev.answer()
                await kick_auth(rt, h)
                return await ev.edit("\U0001f6ab \u0628\u0631\u0631\u0633\u06cc \u0634\u062f.")
        elif op == "lo":
            view = ("\u0645\u0637\u0645\u0626\u0646\u06cc \u0645\u06cc\u200c\u062e\u0648\u0627\u0647\u06cc \u062e\u0627\u0631\u062c \u0634\u0648\u06cc\u061f \u0646\u0634\u0633\u062a \u06a9\u0627\u0645\u0644\u0627\u064b \u067e\u0627\u06a9 \u0645\u06cc\u200c\u0634\u0648\u062f \u0648 \u0642\u0627\u0628\u0644\u06cc\u062a\u200c\u0647\u0627 \u062e\u0627\u0645\u0648\u0634 \u0645\u06cc\u200c\u0634\u0648\u0646\u062f.",
                    [[Button.inline("\u2705 \u0628\u0644\u0647\u060c \u062e\u0631\u0648\u062c", "lo2"), Button.inline("\u21a9 \u0646\u0647", "m")]])
        elif op == "lo2":
            await ev.answer()
            return await do_logout(uid, ev)
        if view is None:
            return await ev.answer(alert or "")
        await ev.answer(alert or "", alert=bool(alert))
        try:
            await ev.edit(view[0], buttons=view[1], parse_mode="html", link_preview=False)
        except errors.MessageNotModifiedError:
            pass
    except AUTH_DEAD:
        await ev.answer("\u062d\u0633\u0627\u0628\u062a \u0642\u0637\u0639 \u0634\u062f\u0647\u061b /start \u0628\u0632\u0646.", alert=True)
    except Exception:
        log.exception("on_cb failed")
        await report_error("on_cb")
        try:
            await ev.answer("\u26a0\ufe0f \u062e\u0637\u0627\u06cc \u062f\u0627\u062e\u0644\u06cc", alert=True)
        except Exception:
            pass


async def do_logout(uid, ev=None):
    rt = RTS.get(uid)
    if rt:
        try:
            await rt.client.log_out()
        except Exception:
            pass
        await stop_rt(uid)
    for (p,) in DB.all("SELECT path FROM cache WHERE uid=? AND path IS NOT NULL", (uid,)):
        try:
            os.remove(p)
        except Exception:
            pass
    for t in ("users", "cache", "kv"):
        DB.q("DELETE FROM %s WHERE %s=?" % (t, "id" if t == "users" else "uid"), (uid,))
    S.pop(uid, None)
    PEND.pop(uid, None)
    msg = "\u2705 \u062e\u0627\u0631\u062c \u0634\u062f\u06cc \u0648 \u0646\u0634\u0633\u062a \u0648 \u062f\u0627\u062f\u0647\u200c\u0647\u0627\u06cc\u062a \u06a9\u0627\u0645\u0644 \u067e\u0627\u06a9 \u0634\u062f. \u0647\u0631 \u0648\u0642\u062a \u062e\u0648\u0627\u0633\u062a\u06cc \u0628\u0627 /start \u0628\u0631\u06af\u0631\u062f."
    if ev:
        try:
            return await ev.edit(msg)
        except Exception:
            pass
    await BOT.send_message(uid, msg)


#
def purge_cache():
    now = int(time.time())
    for (p,) in DB.all("SELECT path FROM cache WHERE out=0 AND date<? AND path IS NOT NULL", (now - 48 * 3600,)):
        try:
            os.remove(p)
        except Exception:
            pass
    DB.q("DELETE FROM cache WHERE (out=0 AND date<?) OR (out=1 AND date<?)", (now - 48 * 3600, now - 24 * 3600))


async def ensure_running():
    for (uid,) in DB.all("SELECT id FROM users WHERE status='active'"):
        if uid in RTS:
            continue
        try:
            if uid not in S:
                load_settings(uid, DB.one("SELECT settings FROM users WHERE id=?", (uid,))[0])
            if not is_free(uid):
                if bill_row(uid) is None:
                    grant_test(uid)
                elif left_sec(uid) <= 0:
                    DB.q("UPDATE users SET status='expired' WHERE id=?", (uid,))
                    await notify(uid, "\u26d4 <b>\u0633\u0644\u0641 \u0634\u0645\u0627 \u0642\u0637\u0639 \u0634\u062f</b>\n\n\u0632\u0645\u0627\u0646 \u0633\u0644\u0641\u062a \u062a\u0645\u0627\u0645 \u0634\u062f\u0647 \u0627\u0633\u062a. \u0628\u0631\u0627\u06cc \u0631\u0648\u0634\u0646 \u0634\u062f\u0646 \u0633\u06a9\u0647 \u0628\u062e\u0631.",
                                 buttons=buy_rows())
                    continue
            await start_rt(uid)
        except (SessionDead,) + AUTH_DEAD:
            DB.q("UPDATE users SET status='down' WHERE id=?", (uid,))
            await notify_down(uid)
        except Exception as e:
            log.warning("start failed for %s: %s", uid, e)
        await asyncio.sleep(0.5)


async def housekeeping():
    n = 0
    while True:
        try:
            await ensure_running()
            now = time.time()
            for uid in [u for u, L in LOGIN.items() if now - L["t"] > 900]:
                await cancel_login(uid)
            for uid in [u for u, p in PEND.items() if now - p["t"] > 1800]:
                PEND.pop(uid, None)
            if n % 2 == 0:
                purge_cache()
        except Exception:
            log.exception("housekeeping failed")
        n += 1
        await asyncio.sleep(300)



# ============================================================================
#
# ============================================================================
COIN_SEC = 3600
WHEEL = [("\u067e\u0648\u0686 \U0001f605", 0, 30), ("\u06f1\u06f5 \u062f\u0642\u06cc\u0642\u0647", 15, 25), ("\u06f3\u06f0 \u062f\u0642\u06cc\u0642\u0647", 30, 20), ("\u06f1 \u0633\u06a9\u0647", 60, 15), ("\u06f2 \u0633\u06a9\u0647", 120, 7),
         ("\u06f3 \u0633\u06a9\u0647", 180, 3)]
WHEEL_GAP = 24 * 3600
DEFAULT_PACKS = {1: 5000, 5: 22000, 24: 100000}


def is_free(uid):
    return bool(OWNER_ID) and uid == OWNER_ID


def bill_get(uid):
    DB.q("INSERT OR IGNORE INTO bill(uid) VALUES(?)", (uid,))
    r = DB.one("SELECT exp, test_used, wheel_ts, warned FROM bill WHERE uid=?", (uid,))
    return dict(exp=r[0], test=r[1], wheel=r[2], warned=r[3])


def bill_row(uid):
    r = DB.one("SELECT exp, test_used, wheel_ts, warned FROM bill WHERE uid=?", (uid,))
    return dict(exp=r[0], test=r[1], wheel=r[2], warned=r[3]) if r else None


def left_sec(uid):
    if is_free(uid):
        return 10 ** 9
    b = bill_row(uid)
    return max(0, int(b["exp"] - time.time())) if b else 0


def add_time(uid, sec):
    b = bill_get(uid)
    new = int(max(b["exp"], time.time()) + sec)
    DB.q("UPDATE bill SET exp=?, warned=0 WHERE uid=?", (new, uid))
    return new


def test_sec():
    try:
        return int(float(kv_get(0, "test_h", "1")) * 3600)
    except Exception:
        return 3600


def grant_test(uid):
    b = bill_get(uid)
    if b["test"]:
        return False
    add_time(uid, test_sec())
    DB.q("UPDATE bill SET test_used=1 WHERE uid=?", (uid,))
    return True


def fmt_left(sec):
    if sec >= 10 ** 8:
        return "\u0646\u0627\u0645\u062d\u062f\u0648\u062f"
    h, m = sec // 3600, (sec % 3600) // 60
    parts = []
    if h >= 24:
        parts.append("%s \u0631\u0648\u0632" % fa(h // 24))
        h %= 24
    if h:
        parts.append("%s \u0633\u0627\u0639\u062a" % fa(h))
    if m or not parts:
        parts.append("%s \u062f\u0642\u06cc\u0642\u0647" % fa(m))
    return " \u0648 ".join(parts)


def get_packs():
    try:
        d = json.loads(kv_get(0, "packs") or "null")
    except Exception:
        d = None
    if not isinstance(d, dict) or not d:
        d = {str(k): v for k, v in DEFAULT_PACKS.items()}
    return sorted((int(k), int(v)) for k, v in d.items())


def set_packs(d):
    kv_set(0, "packs", json.dumps({str(k): int(v) for k, v in d.items()}))


def money(n):
    return fa("{:,}".format(int(n)))


def wheel_on():
    return kv_get(0, "wheel", "1") != "0"


def webapp_url():
    u = (os.environ.get("WEBAPP_URL") or kv_get(0, "url", "") or "").strip()
    if not u:
        d = (os.environ.get("RAILWAY_PUBLIC_DOMAIN") or "").strip()
        if d:
            u = d
    if u and not u.startswith("http"):
        u = "https://" + u
    return u.rstrip("/")


WEB_OK = [True]


def webapp_rows():
    if not WEB_OK[0]:
        return []
    try:
        u = webapp_url()
        if u.startswith("https://"):
            return [[types.KeyboardButtonWebView("\U0001f3a1 \u0645\u06cc\u0646\u06cc\u200c\u0627\u067e \u0648 \u06af\u0631\u062f\u0648\u0646\u0647 \u0634\u0627\u0646\u0633", u + "/")]]
    except Exception as e:
        WEB_OK[0] = False
        log.warning("web app button disabled: %s", e)
    return []


def _has_web(buttons):
    try:
        rows = buttons if isinstance(buttons, list) else [buttons]
        return any(isinstance(b, types.KeyboardButtonWebView)
                   for r_ in rows for b in (r_ if isinstance(r_, list) else [r_]))
    except Exception:
        return False


def _strip_web(buttons):
    try:
        rows = buttons if isinstance(buttons, list) else [buttons]
        out = []
        for r_ in rows:
            r2 = [b for b in (r_ if isinstance(r_, list) else [r_]) if not isinstance(b, types.KeyboardButtonWebView)]
            if r2:
                out.append(r2)
        return out or None
    except Exception:
        return None


def guard_client(client):
    """\u0627\u06af\u0631 \u062a\u0644\u06af\u0631\u0627\u0645 \u062f\u06a9\u0645\u0647\u200c\u06cc \u0645\u06cc\u0646\u06cc\u200c\u0627\u067e \u0631\u0627 \u0631\u062f \u06a9\u0631\u062f\u060c \u0647\u0645\u0627\u0646 \u067e\u06cc\u0627\u0645 \u0628\u062f\u0648\u0646 \u0622\u0646 \u062f\u06a9\u0645\u0647 \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f (\u0631\u0628\u0627\u062a \u0647\u0631\u06af\u0632 \u062e\u0631\u0627\u0628 \u0646\u0645\u06cc\u200c\u0634\u0648\u062f)"""
    for name in ("send_message", "edit_message"):
        def make(orig):
            async def w(*a, **k):
                try:
                    return await orig(*a, **k)
                except errors.RPCError as e:
                    if _has_web(k.get("buttons")):
                        WEB_OK[0] = False
                        log.warning("web app button rejected by Telegram (%s) - disabled", type(e).__name__)
                        k["buttons"] = _strip_web(k["buttons"])
                        return await orig(*a, **k)
                    raise
            return w
        setattr(client, name, make(getattr(client, name)))


def buy_rows():
    return [[Button.inline("\U0001fa99 \u062e\u0631\u06cc\u062f \u0633\u06a9\u0647", "w")]] + webapp_rows()


def v_wallet(uid, note=""):
    t = []
    if note:
        t.append(note + "\n")
    t.append("\U0001fa99 <b>\u0633\u06a9\u0647 \u0648 \u0627\u0634\u062a\u0631\u0627\u06a9</b>\n")
    t.append("\u0647\u0631 \u0633\u06a9\u0647 = <b>\u06f1 \u0633\u0627\u0639\u062a</b> \u0631\u0648\u0634\u0646\u200c\u0628\u0648\u062f\u0646 \u0633\u0644\u0641. \u0648\u0642\u062a\u06cc \u0632\u0645\u0627\u0646\u062a \u062a\u0645\u0627\u0645 \u0634\u0648\u062f \u0633\u0644\u0641 \u062e\u0648\u062f\u06a9\u0627\u0631 \u0642\u0637\u0639 \u0645\u06cc\u200c\u0634\u0648\u062f \u0648 \u0628\u0631\u0627\u06cc\u062a \u067e\u06cc\u0627\u0645 \u0645\u06cc\u200c\u0622\u06cc\u062f.")
    t.append("\u23f3 \u0632\u0645\u0627\u0646 \u0628\u0627\u0642\u06cc\u200c\u0645\u0627\u0646\u062f\u0647: <b>%s</b>\n" % fmt_left(left_sec(uid)))
    rows = []
    for coins, price in get_packs():
        rows.append([Button.inline("\U0001fa99 %s \u0633\u06a9\u0647 \u2014 %s \u062a\u0648\u0645\u0627\u0646" % (fa(coins), money(price)), "wb:%d" % coins)])
    rows.extend(webapp_rows())
    rows.append(BACK_MAIN)
    return "\n".join(t), rows


async def receive_receipt(ev, p):
    uid = ev.sender_id
    if not (ev.message.media or (ev.raw_text or "").strip()):
        return
    cur = DB.q("INSERT INTO pay(uid,coins,price,status,ts) VALUES(?,?,?,'wait',?)",
               (uid, p["coins"], p["price"], int(time.time())))
    pid = cur.lastrowid
    PEND.pop(uid, None)
    try:
        await BOT.forward_messages(OWNER_ID, ev.message)
    except Exception as e:
        log.info("forward receipt failed: %s", e)
    name = esc(ev.sender.first_name) if getattr(ev, "sender", None) is not None and getattr(ev.sender, "first_name", None) else ""
    await BOT.send_message(OWNER_ID, "\U0001f4b3 <b>\u062f\u0631\u062e\u0648\u0627\u0633\u062a \u067e\u0631\u062f\u0627\u062e\u062a #%d</b>\n\u06a9\u0627\u0631\u0628\u0631: %s <code>%d</code>\n\U0001fa99 %s \u0633\u06a9\u0647 \u2014 %s \u062a\u0648\u0645\u0627\u0646" % (
        pid, name, uid, fa(p["coins"]), money(p["price"])), parse_mode="html",
        buttons=[[Button.inline("\u2705 \u062a\u0623\u06cc\u06cc\u062f", "pok:%d" % pid), Button.inline("\u274c \u0631\u062f", "pno:%d" % pid)]])
    await ev.respond("\u2705 \u0631\u0633\u06cc\u062f \u062f\u0631\u06cc\u0627\u0641\u062a \u0634\u062f. \u0628\u0639\u062f \u0627\u0632 \u062a\u0623\u06cc\u06cc\u062f \u0645\u062f\u06cc\u0631\u060c \u0633\u06a9\u0647\u200c\u0627\u062a \u0627\u0636\u0627\u0641\u0647 \u0648 \u0633\u0644\u0641\u062a \u0631\u0648\u0634\u0646 \u0645\u06cc\u200c\u0634\u0648\u062f.")


async def pay_decide(ev, ok, pid):
    r = DB.one("SELECT uid, coins, price, status FROM pay WHERE id=?", (pid,))
    if not r or r[3] != "wait":
        return await ev.answer("\u0627\u06cc\u0646 \u062f\u0631\u062e\u0648\u0627\u0633\u062a \u0642\u0628\u0644\u0627\u064b \u0628\u0631\u0631\u0633\u06cc \u0634\u062f\u0647.", alert=True)
    u, coins = r[0], r[1]
    DB.q("UPDATE pay SET status=? WHERE id=?", ("ok" if ok else "no", pid))
    if ok:
        add_time(u, coins * COIN_SEC)
        await notify(u, "\u2705 <b>\u067e\u0631\u062f\u0627\u062e\u062a \u062a\u0623\u06cc\u06cc\u062f \u0634\u062f</b>\n\U0001fa99 %s \u0633\u06a9\u0647 \u0627\u0636\u0627\u0641\u0647 \u0634\u062f.\n\u23f3 \u0632\u0645\u0627\u0646 \u0628\u0627\u0642\u06cc\u200c\u0645\u0627\u0646\u062f\u0647: <b>%s</b>" % (
            fa(coins), fmt_left(left_sec(u))))
        await resume_user(u)
    else:
        await notify(u, "\u274c \u067e\u0631\u062f\u0627\u062e\u062a \u0634\u0645\u0627 \u062a\u0623\u06cc\u06cc\u062f \u0646\u0634\u062f. \u0627\u06af\u0631 \u0627\u0634\u062a\u0628\u0627\u0647 \u0634\u062f\u0647 \u0628\u0627 \u0645\u062f\u06cc\u0631 \u062f\u0631 \u062a\u0645\u0627\u0633 \u0628\u0627\u0634.")
    await ev.answer("\u0627\u0646\u062c\u0627\u0645 \u0634\u062f")
    try:
        await ev.edit("%s \u062f\u0631\u062e\u0648\u0627\u0633\u062a #%d: %s" % ("\u2705" if ok else "\u274c", pid, "\u062a\u0623\u06cc\u06cc\u062f \u0634\u062f" if ok else "\u0631\u062f \u0634\u062f"))
    except Exception:
        pass


async def resume_user(uid):
    row = DB.one("SELECT status FROM users WHERE id=?", (uid,))
    if not row or row[0] != "expired" or uid in RTS:
        return False
    if uid not in S:
        load_settings(uid, DB.one("SELECT settings FROM users WHERE id=?", (uid,))[0])
    try:
        DB.q("UPDATE users SET status='active' WHERE id=?", (uid,))
        await start_rt(uid)
    except (SessionDead,) + AUTH_DEAD:
        DB.q("UPDATE users SET status='down' WHERE id=?", (uid,))
        await notify_down(uid)
        return False
    except Exception as e:
        log.warning("resume failed for %s: %s", uid, e)
        return False
    await notify(uid, "\U0001f7e2 <b>\u0633\u0644\u0641 \u0634\u0645\u0627 \u062f\u0648\u0628\u0627\u0631\u0647 \u0631\u0648\u0634\u0646 \u0634\u062f.</b>", buttons=[[Button.inline("\U0001f39b \u067e\u0646\u0644", "m")]])
    return True


async def restore_profile(rt):
    uid = rt.uid
    try:
        if is_on(uid, "cname"):
            base = get_p(uid, "cname", "base")
            if base:
                await rt.client(functions.account.UpdateProfileRequest(first_name=base))
        if is_on(uid, "cbio") or is_on(uid, "brot"):
            await rt.client(functions.account.UpdateProfileRequest(about=kv_get(uid, "orig_bio", "") or ""))
    except Exception as e:
        log.info("restore profile failed for %s: %s", uid, e)


async def expire_user(uid):
    rt = RTS.get(uid)
    DB.q("UPDATE users SET status='expired' WHERE id=?", (uid,))
    try:
        await notify(uid, "\u26d4 <b>\u0633\u0644\u0641 \u0634\u0645\u0627 \u0642\u0637\u0639 \u0634\u062f</b>\n\n\u0632\u0645\u0627\u0646 \u0633\u0644\u0641\u062a \u062a\u0645\u0627\u0645 \u0634\u062f. \u0628\u0631\u0627\u06cc \u0631\u0648\u0634\u0646 \u0634\u062f\u0646 \u062f\u0648\u0628\u0627\u0631\u0647 \u0633\u06a9\u0647 \u0628\u062e\u0631\u061b "
                          "\u0628\u0639\u062f \u0627\u0632 \u062a\u0623\u06cc\u06cc\u062f \u067e\u0631\u062f\u0627\u062e\u062a\u060c \u0633\u0644\u0641 \u062e\u0648\u062f\u06a9\u0627\u0631 \u0631\u0648\u0634\u0646 \u0645\u06cc\u200c\u0634\u0648\u062f (\u0646\u06cc\u0627\u0632\u06cc \u0628\u0647 \u0648\u0631\u0648\u062f \u062f\u0648\u0628\u0627\u0631\u0647 \u0646\u06cc\u0633\u062a).",
                     buttons=buy_rows())
    except Exception:
        log.exception("expire notice failed")
    try:
        if rt:
            await restore_profile(rt)
        await stop_rt(uid)
    except Exception:
        log.exception("expire stop failed")


async def billing_loop():
    while True:
        try:
            now = time.time()
            for uid in list(RTS):
                try:
                    if is_free(uid):
                        continue
                    b = bill_row(uid)
                    if b is None:
                        grant_test(uid)
                        continue
                    if b["exp"] <= now:
                        await expire_user(uid)
                    elif b["exp"] - now < 600 and not b["warned"]:
                        DB.q("UPDATE bill SET warned=1 WHERE uid=?", (uid,))
                        await notify(uid, "\u23f3 \u0641\u0642\u0637 <b>%s</b> \u0627\u0632 \u0632\u0645\u0627\u0646 \u0633\u0644\u0641\u062a \u0645\u0627\u0646\u062f\u0647. \u0628\u0631\u0627\u06cc \u062a\u0645\u062f\u06cc\u062f \u0633\u06a9\u0647 \u0628\u062e\u0631." % fmt_left(int(b["exp"] - now)),
                                     buttons=buy_rows())
                except Exception:
                    log.exception("billing step failed for %s", uid)
        except Exception:
            log.exception("billing loop failed")
        await asyncio.sleep(30)


#
WEB_HTML = "<!doctype html>\n<html lang=\"fa\" dir=\"rtl\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no\">\n<title>Self Speed</title>\n<script src=\"https://telegram.org/js/telegram-web-app.js\"></script>\n<style>\n:root{--bg:#0e1117;--card:#171c26;--card2:#1f2633;--tx:#eef2f8;--mut:#8b96a8;--acc:#2f9bff;--acc2:#7c5cff;--ok:#27c281;--bad:#ff5a67;--line:#2a3344}\n*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}\nhtml,body{overflow-x:hidden;max-width:100vw}\nbody{margin:0;background:var(--bg);color:var(--tx);font-family:Tahoma,Vazirmatn,system-ui,sans-serif;font-size:15px;padding-bottom:84px;min-height:100vh}\n.top{padding:18px 16px 8px;display:flex;align-items:center;gap:10px}\n.logo{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,var(--acc),var(--acc2));display:grid;place-items:center;font-size:22px}\n.top b{font-size:18px}.top small{display:block;color:var(--mut);font-size:12px}\n.wrap{padding:8px 16px}\n.card{overflow:hidden;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px;margin:10px 0}\n.big{font-size:26px;font-weight:700;letter-spacing:.5px}\n.row{display:flex;gap:10px;flex-wrap:wrap}\n.pill{background:var(--card2);border-radius:12px;padding:10px 12px;flex:1;min-width:120px}\n.pill small{display:block;color:var(--mut);font-size:12px;margin-bottom:4px}\n.ok{color:var(--ok)}.bad{color:var(--bad)}.mut{color:var(--mut)}\nbutton{font:inherit;border:0;border-radius:12px;padding:11px 14px;background:var(--acc);color:#fff;cursor:pointer}\nbutton.sec{background:var(--card2);color:var(--tx)}\nbutton.full{width:100%}\nbutton:disabled{opacity:.5}\n.tabs{position:fixed;bottom:0;left:0;right:0;display:flex;background:var(--card);border-top:1px solid var(--line);padding:6px 6px calc(6px + env(safe-area-inset-bottom))}\n.tabs div{flex:1;text-align:center;padding:8px 0;border-radius:10px;color:var(--mut);font-size:12px}\n.tabs div span{display:block;font-size:20px}\n.tabs div.on{color:var(--tx);background:var(--card2)}\n.cat{font-weight:700;margin:16px 4px 6px}\n.feat{display:flex;align-items:center;justify-content:space-between;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:6px 0}\n.feat .n{flex:1;padding-left:8px}\n.sw{width:46px;height:26px;border-radius:13px;background:var(--card2);position:relative;flex:none;border:1px solid var(--line)}\n.sw i{position:absolute;top:2px;right:2px;width:20px;height:20px;border-radius:50%;background:var(--mut);transition:.2s}\n.sw.on{background:var(--ok)}.sw.on i{right:22px;background:#fff}\n.sheet{position:fixed;inset:0;background:#000a;display:none;align-items:flex-end;z-index:9}\n.sheet.show{display:flex}\n.sheet .in{background:var(--card);width:100%;max-height:88vh;overflow:auto;border-radius:22px 22px 0 0;padding:16px}\ninput[type=text],input[type=number],textarea{width:100%;background:var(--card2);border:1px solid var(--line);color:var(--tx);border-radius:12px;padding:11px;font:inherit;margin:6px 0}\n.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}\n.chip{padding:8px 12px;border-radius:20px;background:var(--card2);border:1px solid var(--line)}\n.chip.on{background:var(--acc);border-color:var(--acc)}\n.li{display:flex;justify-content:space-between;align-items:center;background:var(--card2);border-radius:10px;padding:8px 10px;margin:4px 0;font-size:13px}\n.wheelbox{position:relative;width:min(86vw,340px);margin:14px auto}\n.wheelbox canvas{width:100%;height:auto;display:block;transition:transform 5s cubic-bezier(.12,.7,.1,1)}\n.ptr{position:absolute;top:-10px;left:50%;margin-left:-14px;width:0;height:0;border-left:14px solid transparent;border-right:14px solid transparent;border-top:26px solid #fff;filter:drop-shadow(0 2px 3px #0008);z-index:2}\n.hub{position:absolute;top:50%;left:50%;width:54px;height:54px;margin:-27px;border-radius:50%;background:var(--bg);border:4px solid #fff;display:grid;place-items:center;font-size:22px}\n.toast{position:fixed;top:14px;left:50%;transform:translateX(-50%);background:#000d;color:#fff;padding:10px 16px;border-radius:12px;z-index:20;display:none;max-width:90vw;text-align:center}\n.pack{display:flex;justify-content:space-between;align-items:center}\n.av{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--acc2),var(--acc));display:grid;place-items:center;position:relative;overflow:hidden;flex:none}\n.av img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}\n</style>\n</head>\n<body>\n<div class=\"top\"><div class=\"logo\">&#9889;</div><div><b>Self Speed</b><small id=\"who\">...</small></div></div>\n<div class=\"wrap\" id=\"view\"></div>\n<div class=\"tabs\" id=\"tabs\"></div>\n<div class=\"sheet\" id=\"sheet\"><div class=\"in\" id=\"sheetin\"></div></div>\n<div class=\"toast\" id=\"toast\"></div>\n<script>\nvar tg = window.Telegram && window.Telegram.WebApp;\nif (tg) { try { tg.ready(); tg.expand(); } catch (e) {} }\nvar INIT = tg ? tg.initData : \"\";\nvar ST = null, CATS = null, TAB = \"home\", rot = 0, spinning = false;\nvar TABS = [[\"home\", \"&#127968;\", \"\u0648\u0636\u0639\u06cc\u062a\"], [\"feat\", \"&#9881;&#65039;\", \"\u0642\u0627\u0628\u0644\u06cc\u062a\u200c\u0647\u0627\"], [\"wheel\", \"&#127905;\", \"\u06af\u0631\u062f\u0648\u0646\u0647\"], [\"board\", \"&#127942;\", \"\u0644\u06cc\u062f\u0631\u0628\u0648\u0631\u062f\"], [\"coin\", \"&#129689;\", \"\u0633\u06a9\u0647\"]];\n\nfunction $(id) { return document.getElementById(id); }\nfunction esc(s) { return String(s == null ? \"\" : s).replace(/&/g, \"&amp;\").replace(/</g, \"&lt;\").replace(/>/g, \"&gt;\").replace(/\"/g, \"&quot;\"); }\nfunction fa(n) { return String(n).replace(/[0-9]/g, function (d) { return \"\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9\"[d]; }); }\nfunction ft(s) {\n  if (s >= 100000000) return \"\u0646\u0627\u0645\u062d\u062f\u0648\u062f\";\n  var d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60), p = [];\n  if (d) p.push(fa(d) + \" \u0631\u0648\u0632\");\n  if (h) p.push(fa(h) + \" \u0633\u0627\u0639\u062a\");\n  if (m || !p.length) p.push(fa(m) + \" \u062f\u0642\u06cc\u0642\u0647\");\n  return p.join(\" \u0648 \");\n}\nfunction toast(t) { var e = $(\"toast\"); e.textContent = t; e.style.display = \"block\"; setTimeout(function () { e.style.display = \"none\"; }, 2600); }\nfunction hap(k) { try { tg.HapticFeedback.notificationOccurred(k || \"success\"); } catch (e) {} }\n\nasync function api(op, data) {\n  var body = JSON.stringify(Object.assign({ op: op }, data || {}));\n  try {\n    var r = await fetch(\"/api\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\", \"X-Init\": INIT }, body: body });\n    return await r.json();\n  } catch (e) { return { ok: false, err: \"\u0627\u0631\u062a\u0628\u0627\u0637 \u0628\u0627 \u0633\u0631\u0648\u0631 \u0628\u0631\u0642\u0631\u0627\u0631 \u0646\u0634\u062f\" }; }\n}\n\nasync function load() {\n  var r = await api(\"state\");\n  if (!r.ok) { $(\"view\").innerHTML = '<div class=\"card bad\">' + esc(r.err || \"\u062e\u0637\u0627\") + '<br><span class=\"mut\">\u0645\u06cc\u0646\u06cc\u200c\u0627\u067e \u0631\u0627 \u0627\u0632 \u062f\u0627\u062e\u0644 \u0631\u0628\u0627\u062a \u0628\u0627\u0632 \u06a9\u0646.</span></div>'; return; }\n  ST = r; $(\"who\").textContent = r.name || \"\";\n  render();\n}\n\nfunction renderTabs() {\n  $(\"tabs\").innerHTML = TABS.map(function (t) {\n    return '<div class=\"' + (t[0] === TAB ? \"on\" : \"\") + '\" onclick=\"go(\\'' + t[0] + '\\')\"><span>' + t[1] + \"</span>\" + t[2] + \"</div>\";\n  }).join(\"\");\n}\nfunction go(t) { TAB = t; render(); }\n\nfunction render() {\n  renderTabs();\n  if (!ST) return;\n  if (!ST.reg) { $(\"view\").innerHTML = '<div class=\"card\">\u0647\u0646\u0648\u0632 \u062f\u0631 \u0631\u0628\u0627\u062a \u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u0646\u06a9\u0631\u062f\u0647\u200c\u0627\u06cc. \u0628\u0647 \u0631\u0628\u0627\u062a \u0628\u0631\u06af\u0631\u062f \u0648 /start \u0628\u0632\u0646.</div>'; return; }\n  if (TAB === \"home\") home(); else if (TAB === \"feat\") feats(); else if (TAB === \"wheel\") wheel(); else if (TAB === \"board\") board(); else coin();\n}\n\nfunction statusLine() {\n  if (ST.active) return '<span class=\"ok\">&#9679; \u0631\u0648\u0634\u0646</span>';\n  if (ST.status === \"expired\") return '<span class=\"bad\">&#9679; \u0632\u0645\u0627\u0646 \u062a\u0645\u0627\u0645 \u0634\u062f\u0647</span>';\n  if (ST.status === \"down\") return '<span class=\"bad\">&#9679; \u0642\u0637\u0639 (\u0646\u06cc\u0627\u0632 \u0628\u0647 \u0648\u0631\u0648\u062f \u062f\u0648\u0628\u0627\u0631\u0647)</span>';\n  return '<span class=\"bad\">&#9679; \u062e\u0627\u0645\u0648\u0634</span>';\n}\n\nfunction home() {\n  $(\"view\").innerHTML =\n    '<div class=\"card\"><div class=\"mut\">\u0648\u0636\u0639\u06cc\u062a \u0633\u0644\u0641</div><div class=\"big\">' + statusLine() + '</div></div>' +\n    '<div class=\"row\"><div class=\"pill\"><small>&#9203; \u0632\u0645\u0627\u0646 \u0628\u0627\u0642\u06cc\u200c\u0645\u0627\u0646\u062f\u0647</small><b>' + ft(ST.left) + '</b></div>' +\n    '<div class=\"pill\"><small>&#128246; \u067e\u06cc\u0646\u06af \u0633\u0644\u0641</small><b id=\"pg\">' + (ST.ping ? fa(ST.ping) + \" ms\" : \"\u2014\") + '</b></div></div>' +\n    '<div class=\"row\" style=\"margin-top:10px\"><div class=\"pill\"><small>&#128295; \u0642\u0627\u0628\u0644\u06cc\u062a\u200c\u0647\u0627\u06cc \u0631\u0648\u0634\u0646</small><b>' + fa(ST.on) + \" \u0627\u0632 \" + fa(ST.total) + '</b></div>' +\n    '<div class=\"pill\"><small>&#127881; \u06af\u0631\u062f\u0648\u0646\u0647\u200c\u06cc \u0627\u0645\u0631\u0648\u0632</small><b>' + (ST.wheel.can ? \"\u0622\u0645\u0627\u062f\u0647\" : (ST.wheel.enabled ? \"\u0628\u0639\u062f\u0627\u064b\" : \"\u063a\u06cc\u0631\u0641\u0639\u0627\u0644\")) + '</b></div></div>' +\n    '<div class=\"card\"><button class=\"full sec\" onclick=\"doPing()\">&#127955; \u0627\u0646\u062f\u0627\u0632\u0647\u200c\u06af\u06cc\u0631\u06cc \u067e\u06cc\u0646\u06af \u0633\u0644\u0641</button></div>' +\n    (ST.active ? \"\" : '<div class=\"card bad\">\u0633\u0644\u0641 \u0634\u0645\u0627 \u0627\u0644\u0627\u0646 \u0631\u0648\u0634\u0646 \u0646\u06cc\u0633\u062a. \u0628\u0631\u0627\u06cc \u0631\u0648\u0634\u0646 \u0634\u062f\u0646 \u062f\u0631 \u062a\u0628 \u00ab\u0633\u06a9\u0647\u00bb \u0633\u06a9\u0647 \u0628\u062e\u0631.</div>');\n}\nasync function sendCard() {\n  var r = await api(\"sendcard\");\n  toast(r.ok ? (r.msg || \"\u0627\u0631\u0633\u0627\u0644 \u0634\u062f\") : (r.err || \"\u062e\u0637\u0627\"));\n}\nfunction avatar(u, name) {\n  var ini = esc((name || \"?\").trim().charAt(0));\n  return '<span class=\"av\"><b>' + ini + '</b><img src=\"/av/' + u + '.jpg\" onerror=\"this.remove()\"></span>';\n}\nasync function board() {\n  $(\"view\").innerHTML = '<div class=\"card mut\">\u062f\u0631 \u062d\u0627\u0644 \u0628\u0627\u0631\u06af\u0630\u0627\u0631\u06cc ...</div>';\n  var r = await api(\"board\");\n  if (!r.ok) { $(\"view\").innerHTML = '<div class=\"card bad\">' + esc(r.err || \"\u062e\u0637\u0627\") + \"</div>\"; return; }\n  var med = [\"&#129351;\", \"&#129352;\", \"&#129353;\"], h = '<div class=\"card\" style=\"text-align:center\"><b style=\"font-size:18px\">&#127942; \u0644\u06cc\u062f\u0631\u0628\u0648\u0631\u062f \u06f1\u06f0 \u0646\u0641\u0631 \u0628\u0631\u062a\u0631</b><div class=\"mut\" style=\"font-size:12px\">\u0628\u0631 \u0627\u0633\u0627\u0633 \u0633\u0648\u062f \u0633\u06a9\u0647 \u062f\u0631 \u0634\u0631\u0637\u200c\u0628\u0646\u062f\u06cc \u06af\u0631\u0648\u0647</div></div>';\n  if (!r.top.length) h += '<div class=\"card mut\">\u0647\u0646\u0648\u0632 \u0628\u0627\u0632\u06cc\u200c\u0627\u06cc \u0627\u0646\u062c\u0627\u0645 \u0646\u0634\u062f\u0647. \u062a\u0648\u06cc \u06af\u0631\u0648\u0647 \u0628\u0627\u0632\u06cc \u0628\u0646\u0648\u06cc\u0633: \u0634\u0631\u0637 \u06f3</div>';\n  r.top.forEach(function (p) {\n    h += '<div class=\"feat\"><div style=\"display:flex;align-items:center;gap:10px;flex:1\">' +\n      '<b style=\"width:28px;text-align:center\">' + (p.rank <= 3 ? med[p.rank - 1] : fa(p.rank)) + \"</b>\" + avatar(p.uid, p.name) +\n      '<div><div>' + esc(p.name) + '</div><div class=\"mut\" style=\"font-size:12px\">' + fa(p.wins) + \" \u0628\u0631\u062f \u0627\u0632 \" + fa(p.games) + \" \u0628\u0627\u0632\u06cc</div></div></div>\" +\n      '<b dir=\"ltr\" class=\"' + (p.net >= 0 ? \"ok\" : \"bad\") + '\">' + (p.net >= 0 ? \"+\" : \"-\") + fa(Math.abs(p.net)) + \" &#129689;</b></div>\";\n  });\n  if (r.me) h += '<div class=\"card\">\u0631\u062a\u0628\u0647\u200c\u06cc \u062a\u0648: <b>' + fa(r.me.rank) + \"</b> \u2014 \u0633\u0648\u062f: <b>\" + fa(r.me.net) + \"</b> \u0633\u06a9\u0647 \u2014 \" + fa(r.me.wins) + \" \u0628\u0631\u062f \u0627\u0632 \" + fa(r.me.games) + \" \u0628\u0627\u0632\u06cc</div>\";\n  $(\"view\").innerHTML = h;\n}\nasync function doPing() {\n  var r = await api(\"ping\");\n  if (r.ok) { ST.ping = r.ping; var e = $(\"pg\"); if (e) e.textContent = fa(r.ping) + \" ms\"; toast(\"\u067e\u06cc\u0646\u06af \u0633\u0644\u0641: \" + fa(r.ping) + \" ms\"); }\n  else toast(r.err || \"\u062e\u0637\u0627\");\n}\n\nasync function feats() {\n  if (!CATS) { var r = await api(\"cats\"); if (!r.ok) { toast(r.err || \"\u062e\u0637\u0627\"); return; } CATS = r.cats; }\n  var h = \"\";\n  CATS.forEach(function (c) {\n    h += '<div class=\"cat\">' + esc(c.title) + \"</div>\";\n    c.items.forEach(function (f) {\n      h += '<div class=\"feat\"><div class=\"n\" onclick=\"openFeat(\\'' + f.k + '\\')\">' + esc(f.t) + '<div class=\"mut\" style=\"font-size:12px\">\u062a\u0646\u0638\u06cc\u0645\u0627\u062a &#8250;</div></div>' +\n        '<div class=\"sw ' + (f.on ? \"on\" : \"\") + '\" onclick=\"tog(\\'' + f.k + '\\')\"><i></i></div></div>';\n    });\n  });\n  $(\"view\").innerHTML = h;\n}\nasync function tog(k) {\n  var r = await api(\"toggle\", { k: k });\n  if (r.msg) toast(r.msg);\n  if (!r.ok) { toast(r.err || \"\u062e\u0637\u0627\"); return; }\n  CATS.forEach(function (c) { c.items.forEach(function (f) { if (f.k === k) f.on = r.on; }); });\n  ST.on = r.count; hap();\n  if (TAB === \"feat\") feats();\n  if ($(\"sheet\").classList.contains(\"show\")) showFeat(r.feat);\n}\nasync function openFeat(k) {\n  var r = await api(\"feat\", { k: k });\n  if (!r.ok) { toast(r.err || \"\u062e\u0637\u0627\"); return; }\n  showFeat(r.feat);\n}\nfunction closeSheet() { $(\"sheet\").classList.remove(\"show\"); }\n$(\"sheet\").onclick = function (e) { if (e.target === $(\"sheet\")) closeSheet(); };\n\nfunction showFeat(f) {\n  var h = \"<b style=\\\"font-size:17px\\\">\" + esc(f.title) + \"</b><p class=\\\"mut\\\">\" + esc(f.desc) + \"</p>\" +\n    '<div class=\"feat\"><div class=\"n\">' + (f.on ? \"\u0631\u0648\u0634\u0646\" : \"\u062e\u0627\u0645\u0648\u0634\") + '</div><div class=\"sw ' + (f.on ? \"on\" : \"\") + '\" onclick=\"tog(\\'' + f.k + '\\')\"><i></i></div></div>';\n  f.params.forEach(function (p) {\n    h += '<div class=\"card\"><b>' + esc(p.l) + \"</b>\";\n    if (p.h) h += '<div class=\"mut\" style=\"font-size:12px\">' + esc(p.h) + \"</div>\";\n    if (p.t === \"text\") h += '<input type=\"text\" id=\"p' + p.i + '\" value=\"' + esc(p.v) + '\"><button onclick=\"saveP(\\'' + f.k + \"',\" + p.i + ')\">\u0630\u062e\u06cc\u0631\u0647</button>';\n    else if (p.t === \"int\") h += '<input type=\"number\" id=\"p' + p.i + '\" value=\"' + esc(p.v) + '\" min=\"' + p.lo + '\" max=\"' + p.hi + '\"><button onclick=\"saveP(\\'' + f.k + \"',\" + p.i + ')\">\u0630\u062e\u06cc\u0631\u0647</button>';\n    else if (p.t === \"choice\") {\n      h += '<div class=\"chips\">';\n      p.o.forEach(function (o, j) { h += '<div class=\"chip ' + (o[0] === p.v ? \"on\" : \"\") + '\" onclick=\"chooseP(\\'' + f.k + \"',\" + p.i + \",\" + j + ')\">' + esc(o[1]) + \"</div>\"; });\n      h += \"</div>\";\n    } else if (p.t === \"one\") {\n      h += '<div class=\"mut\">\u0641\u0639\u0644\u06cc: ' + esc(p.v) + '</div><input type=\"text\" id=\"p' + p.i + '\" placeholder=\"\u06cc\u0648\u0632\u0631\u0646\u06cc\u0645 \u06cc\u0627 \u0644\u06cc\u0646\u06a9\"><div class=\"row\"><button onclick=\"saveP(\\'' + f.k + \"',\" + p.i + ')\">\u0630\u062e\u06cc\u0631\u0647</button><button class=\"sec\" onclick=\"clearP(\\'' + f.k + \"',\" + p.i + ')\">\u067e\u0627\u06a9 \u06a9\u0631\u062f\u0646</button></div>';\n    } else if (p.t === \"list\") {\n      p.items.forEach(function (it, j) { h += '<div class=\"li\"><span>' + esc(it) + '</span><button class=\"sec\" onclick=\"delItem(\\'' + f.k + \"',\" + p.i + \",\" + j + ')\">&#128465;</button></div>'; });\n      h += '<input type=\"text\" id=\"p' + p.i + '\" placeholder=\"\u0645\u0648\u0631\u062f \u062c\u062f\u06cc\u062f\"><div class=\"row\"><button onclick=\"addItem(\\'' + f.k + \"',\" + p.i + ')\">&#10133; \u0627\u0641\u0632\u0648\u062f\u0646</button>' +\n        (p.items.length ? '<button class=\"sec\" onclick=\"clearList(\\'' + f.k + \"',\" + p.i + ')\">\u067e\u0627\u06a9 \u06a9\u0631\u062f\u0646 \u0647\u0645\u0647</button>' : \"\") + \"</div>\";\n    }\n    h += \"</div>\";\n  });\n  h += '<button class=\"sec full\" onclick=\"closeSheet()\">\u0628\u0633\u062a\u0646</button>';\n  $(\"sheetin\").innerHTML = h; $(\"sheet\").classList.add(\"show\");\n}\nasync function after(r) {\n  if (!r.ok) { toast(r.err || \"\u062e\u0637\u0627\"); hap(\"error\"); return; }\n  if (r.msg) toast(r.msg);\n  showFeat(r.feat); hap();\n  CATS = null;\n}\nfunction val(i) { var e = $(\"p\" + i); return e ? e.value : \"\"; }\nasync function saveP(k, i) { after(await api(\"setp\", { k: k, i: i, v: val(i) })); }\nasync function chooseP(k, i, j) { after(await api(\"setp\", { k: k, i: i, j: j })); }\nasync function clearP(k, i) { after(await api(\"clearp\", { k: k, i: i })); }\nasync function addItem(k, i) { after(await api(\"ladd\", { k: k, i: i, v: val(i) })); }\nasync function delItem(k, i, j) { after(await api(\"ldel\", { k: k, i: i, j: j })); }\nasync function clearList(k, i) { after(await api(\"lclr\", { k: k, i: i })); }\n\n/* ---------- wheel ---------- */\nvar COLORS = [\"#2f9bff\", \"#7c5cff\", \"#27c281\", \"#ff9f43\", \"#ff5a67\", \"#19c3d6\"];\nfunction drawWheel(prizes) {\n  var c = $(\"wc\"), x = c.getContext(\"2d\"), n = prizes.length, R = c.width / 2, a = 2 * Math.PI / n;\n  x.clearRect(0, 0, c.width, c.height);\n  for (var i = 0; i < n; i++) {\n    x.beginPath(); x.moveTo(R, R);\n    x.arc(R, R, R - 4, -Math.PI / 2 + i * a, -Math.PI / 2 + (i + 1) * a);\n    x.closePath(); x.fillStyle = COLORS[i % COLORS.length]; x.fill();\n    x.lineWidth = 3; x.strokeStyle = \"#fff\"; x.stroke();\n    x.save(); x.translate(R, R); x.rotate(-Math.PI / 2 + (i + 0.5) * a);\n    x.fillStyle = \"#fff\"; x.font = \"bold 24px Tahoma\"; x.textAlign = \"right\";\n    x.fillText(prizes[i], R - 22, 8); x.restore();\n  }\n}\nfunction wheel() {\n  var w = ST.wheel;\n  var info;\n  if (!w.enabled) info = '<span class=\"bad\">\u06af\u0631\u062f\u0648\u0646\u0647 \u0641\u0639\u0644\u0627\u064b \u063a\u06cc\u0631\u0641\u0639\u0627\u0644 \u0627\u0633\u062a.</span>';\n  else if (!ST.active) info = '<span class=\"bad\">\u06af\u0631\u062f\u0648\u0646\u0647 \u0641\u0642\u0637 \u0648\u0642\u062a\u06cc \u0633\u0644\u0641\u062a \u0631\u0648\u0634\u0646 \u0627\u0633\u062a \u06a9\u0627\u0631 \u0645\u06cc\u200c\u06a9\u0646\u062f.</span>';\n  else if (w.can) info = '<span class=\"ok\">\u0627\u0645\u0631\u0648\u0632 \u06cc\u06a9 \u0634\u0627\u0646\u0633 \u062f\u0627\u0631\u06cc!</span>';\n  else info = '<span class=\"mut\">\u0634\u0627\u0646\u0633 \u0628\u0639\u062f\u06cc: ' + ft(Math.max(0, w.next - Math.floor(Date.now() / 1000))) + \" \u062f\u06cc\u06af\u0631</span>\";\n  $(\"view\").innerHTML = '<div class=\"card\" style=\"text-align:center\"><b style=\"font-size:18px\">&#127905; \u06af\u0631\u062f\u0648\u0646\u0647\u200c\u06cc \u0634\u0627\u0646\u0633</b><div>' + info + \"</div>\" +\n    '<div class=\"wheelbox\"><div class=\"ptr\"></div><canvas id=\"wc\" width=\"680\" height=\"680\" style=\"transform:rotate(' + rot + 'deg)\"></canvas><div class=\"hub\">&#9889;</div></div>' +\n    '<button class=\"full\" id=\"spin\" ' + (w.can && !spinning ? \"\" : \"disabled\") + ' onclick=\"spin()\">\u0628\u0686\u0631\u062e\u0648\u0646!</button>' +\n    '<p class=\"mut\" style=\"font-size:12px\">\u0647\u0631 \u06f2\u06f4 \u0633\u0627\u0639\u062a \u06cc\u06a9\u200c\u0628\u0627\u0631\u061b \u062c\u0627\u06cc\u0632\u0647\u200c\u0647\u0627 \u0628\u0647 \u0632\u0645\u0627\u0646 \u0633\u0644\u0641\u062a \u0627\u0636\u0627\u0641\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f.</p></div>';\n  drawWheel(w.prizes);\n}\nasync function spin() {\n  if (spinning) return; spinning = true; $(\"spin\").disabled = true;\n  var r = await api(\"wheel\");\n  if (!r.ok) { spinning = false; toast(r.err || \"\u062e\u0637\u0627\"); hap(\"error\"); load(); return; }\n  var n = ST.wheel.prizes.length, seg = 360 / n;\n  rot = Math.ceil(rot / 360) * 360 + 360 * 6 + (360 - (r.idx + 0.5) * seg);\n  var c = $(\"wc\"); c.style.transform = \"rotate(\" + rot + \"deg)\";\n  setTimeout(function () {\n    spinning = false; hap();\n    toast(r.min > 0 ? \"\U0001f389 \u0628\u0631\u0646\u062f\u0647 \u0634\u062f\u06cc: \" + r.label : \"\u0627\u06cc\u0646 \u0628\u0627\u0631 \u067e\u0648\u0686 \u0628\u0648\u062f\u060c \u0641\u0631\u062f\u0627 \u062f\u0648\u0628\u0627\u0631\u0647!\");\n    load();\n  }, 5300);\n}\n\n/* ---------- coins ---------- */\nfunction coin() {\n  var h = '<div class=\"card\"><div class=\"mut\">\u0632\u0645\u0627\u0646 \u0628\u0627\u0642\u06cc\u200c\u0645\u0627\u0646\u062f\u0647</div><div class=\"big\">' + ft(ST.left) + '</div><div class=\"mut\" style=\"font-size:12px\">\u0647\u0631 \u0633\u06a9\u0647 = \u06f1 \u0633\u0627\u0639\u062a \u0631\u0648\u0634\u0646 \u0628\u0648\u062f\u0646 \u0633\u0644\u0641</div></div><div class=\"cat\">\u0628\u0633\u062a\u0647\u200c\u0647\u0627\u06cc \u0633\u06a9\u0647</div>';\n  ST.packs.forEach(function (p) {\n    h += '<div class=\"card pack\"><div><b>&#129689; ' + fa(p[0]) + ' \u0633\u06a9\u0647</b><div class=\"mut\" style=\"font-size:12px\">' + fa(p[0]) + \" \u0633\u0627\u0639\u062a</div></div><b>\" + fa(p[1].toLocaleString(\"en-US\")) + \" \u062a\u0648\u0645\u0627\u0646</b></div>\";\n  });\n  h += '<div class=\"card\"><div>\u0628\u0631\u0627\u06cc \u062e\u0631\u06cc\u062f\u060c \u062f\u0631 \u0631\u0628\u0627\u062a \u0631\u0648\u06cc \u00ab\U0001fa99 \u0633\u06a9\u0647 \u0648 \u0627\u0634\u062a\u0631\u0627\u06a9\u00bb \u0628\u0632\u0646\u060c \u0628\u0633\u062a\u0647 \u0631\u0627 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646 \u0648 \u0631\u0633\u06cc\u062f \u0631\u0627 \u0628\u0641\u0631\u0633\u062a.</div></div>';\n  if (tg) h += '<button class=\"full\" onclick=\"tg.close()\">\u0628\u0627\u0632\u06af\u0634\u062a \u0628\u0647 \u0631\u0628\u0627\u062a</button>';\n  $(\"view\").innerHTML = h;\n}\nload();\nsetInterval(function () { if (ST && ST.left > 0 && ST.left < 100000000) { ST.left -= 30; if (TAB === \"home\" || TAB === \"coin\") render(); } }, 30000);\n</script>\n</body>\n</html>\n"


def check_init(init):
    """\u0627\u0639\u062a\u0628\u0627\u0631\u0633\u0646\u062c\u06cc initData \u062a\u0644\u06af\u0631\u0627\u0645\u061b \u062f\u0631 \u0635\u0648\u0631\u062a \u062f\u0631\u0633\u062a \u0628\u0648\u062f\u0646 \u0622\u06cc\u062f\u06cc \u06a9\u0627\u0631\u0628\u0631 \u0631\u0627 \u0628\u0631\u0645\u06cc\u200c\u06af\u0631\u062f\u0627\u0646\u062f"""
    try:
        from urllib.parse import parse_qsl
        d = dict(parse_qsl(init, keep_blank_values=True))
        h = d.pop("hash", None)
        if not h:
            return None
        chk = "\n".join("%s=%s" % (k, d[k]) for k in sorted(d))
        sk = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(sk, chk.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, h):
            return None
        if time.time() - int(d.get("auth_date", "0")) > 86400:
            return None
        return int(json.loads(d["user"])["id"])
    except Exception:
        return None


def feat_json(uid, key):
    f = FEATS[key]
    ps = []
    for i, p in enumerate(f["params"]):
        val = get_p(uid, key, p["n"])
        d = dict(i=i, l=p["l"], t=p["t"], h=p.get("h", ""))
        if p["t"] == "text":
            d["v"] = val or ""
        elif p["t"] == "int":
            d.update(v=val, lo=p["lo"], hi=p["hi"])
        elif p["t"] == "choice":
            d.update(v=val, o=[[a, b] for a, b in p["o"]])
        elif p["t"] == "one":
            d["v"] = show_val(p, val)
        elif p["t"] == "list":
            d["items"] = [fmt_item(p["k"], x) for x in (val or [])]
        ps.append(d)
    return dict(k=key, title=f["title"], desc=f["desc"], on=is_on(uid, key), params=ps)


async def api_call(uid, q):
    op = q.get("op")
    row = DB.one("SELECT status, name FROM users WHERE id=?", (uid,))
    rt = RTS.get(uid)
    if op == "state":
        if not row:
            return dict(ok=True, reg=False, name="")
        now = time.time()
        b = bill_get(uid)
        nxt = int(b["wheel"] + WHEEL_GAP)
        return dict(ok=True, reg=True, name=row[1] or "", status=row[0], active=bool(rt), left=left_sec(uid),
                    free=is_free(uid), ping=rt.ping if rt else None, on=count_on(uid) if uid in S else 0,
                    total=len(FEATS), packs=[[c, p] for c, p in get_packs()],
                    wheel=dict(enabled=wheel_on(), next=nxt, prizes=[w[0] for w in WHEEL],
                               can=bool(rt) and wheel_on() and left_sec(uid) > 0 and now >= nxt))
    if not row:
        return dict(ok=False, err="\u0647\u0646\u0648\u0632 \u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u0646\u06a9\u0631\u062f\u0647\u200c\u0627\u06cc\u061b \u062f\u0631 \u0631\u0628\u0627\u062a /start \u0628\u0632\u0646.")
    if op == "cats":
        cats = []
        for ck, title in CATS:
            items = [dict(k=k, t=f["title"], on=is_on(uid, k)) for k, f in FEATS.items() if f["cat"] == ck]
            if items:
                cats.append(dict(title=title, items=items))
        return dict(ok=True, cats=cats)
    if op == "board":
        top, idx = board(10)
        me = idx.get(uid)
        return dict(ok=True, top=top, me=dict(rank=me[0], net=me[1], wins=me[2], games=me[3]) if me else None)
    if op == "sendcard":
        return dict(ok=False, err="\u06a9\u0627\u0631\u062a \u0645\u0648\u062c\u0648\u062f\u06cc \u0641\u0642\u0637 \u062a\u0648\u06cc \u06af\u0631\u0648\u0647 \u0628\u0627\u0632\u06cc \u0641\u0631\u0633\u062a\u0627\u062f\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f (\u0628\u0646\u0648\u06cc\u0633: \u0645\u0648\u062c\u0648\u062f\u06cc).")
    if op == "wheel":
        if not wheel_on():
            return dict(ok=False, err="\u06af\u0631\u062f\u0648\u0646\u0647 \u0641\u0639\u0644\u0627\u064b \u063a\u06cc\u0631\u0641\u0639\u0627\u0644 \u0627\u0633\u062a.")
        if not rt or left_sec(uid) <= 0:
            return dict(ok=False, err="\u06af\u0631\u062f\u0648\u0646\u0647 \u0641\u0642\u0637 \u0648\u0642\u062a\u06cc \u0633\u0644\u0641\u062a \u0631\u0648\u0634\u0646 \u0627\u0633\u062a \u06a9\u0627\u0631 \u0645\u06cc\u200c\u06a9\u0646\u062f.")
        b = bill_get(uid)
        now = time.time()
        if now < b["wheel"] + WHEEL_GAP:
            return dict(ok=False, err="\u0647\u0646\u0648\u0632 \u0632\u0645\u0627\u0646 \u0634\u0627\u0646\u0633 \u0628\u0639\u062f\u06cc \u0646\u0631\u0633\u06cc\u062f\u0647.")
        DB.q("UPDATE bill SET wheel_ts=? WHERE uid=?", (int(now), uid))
        idx = random.choices(range(len(WHEEL)), weights=[w[2] for w in WHEEL])[0]
        label, mins = WHEEL[idx][0], WHEEL[idx][1]
        if mins:
            add_time(uid, mins * 60)
        return dict(ok=True, idx=idx, label=label, min=mins)
    if not rt:
        return dict(ok=False, err="\u0633\u0644\u0641 \u0627\u0644\u0627\u0646 \u0631\u0648\u0634\u0646 \u0646\u06cc\u0633\u062a\u061b \u0627\u06af\u0631 \u0632\u0645\u0627\u0646\u062a \u062a\u0645\u0627\u0645 \u0634\u062f\u0647 \u0633\u06a9\u0647 \u0628\u062e\u0631.")
    if op == "ping":
        ms = await measure_ping(rt.client)
        rt.ping = ms
        return dict(ok=True, ping=ms)
    key = q.get("k")
    if key not in FEATS:
        return dict(ok=False, err="\u0642\u0627\u0628\u0644\u06cc\u062a \u0646\u0627\u0645\u0639\u062a\u0628\u0631")
    if op == "feat":
        return dict(ok=True, feat=feat_json(uid, key))
    if op == "toggle":
        msg = await do_toggle(uid, key)
        return dict(ok=True, on=is_on(uid, key), count=count_on(uid), msg=msg or "", feat=feat_json(uid, key))
    try:
        i = int(q.get("i", -1))
    except Exception:
        i = -1
    params = FEATS[key]["params"]
    if not 0 <= i < len(params):
        return dict(ok=False, err="\u067e\u0627\u0631\u0627\u0645\u062a\u0631 \u0646\u0627\u0645\u0639\u062a\u0628\u0631")
    sp = params[i]
    txt = str(q.get("v") if q.get("v") is not None else "").strip()
    err, msg = "", "\u2705 \u0630\u062e\u06cc\u0631\u0647 \u0634\u062f."
    if op == "setp":
        t = sp["t"]
        if t == "text":
            if not txt or len(txt) > 500:
                err = "\u0645\u062a\u0646 \u0646\u0627\u0645\u0639\u062a\u0628\u0631 \u0627\u0633\u062a."
            else:
                set_p(uid, key, sp["n"], txt)
        elif t == "int":
            v = txt.translate(EN_DIGITS)
            if not v.isdigit() or not (sp["lo"] <= int(v) <= sp["hi"]):
                err = "\u0639\u062f\u062f\u06cc \u0628\u06cc\u0646 %s \u062a\u0627 %s \u0628\u0641\u0631\u0633\u062a." % (sp["lo"], sp["hi"])
            else:
                set_p(uid, key, sp["n"], int(v))
        elif t == "choice":
            try:
                j = int(q.get("j", -1))
            except Exception:
                j = -1
            if 0 <= j < len(sp["o"]):
                set_p(uid, key, sp["n"], sp["o"][j][0])
            else:
                err = "\u06af\u0632\u06cc\u0646\u0647\u200c\u06cc \u0646\u0627\u0645\u0639\u062a\u0628\u0631"
        elif t == "one":
            item, err = await parse_item(rt, sp["k"], txt, sp)
            if not err:
                set_p(uid, key, sp["n"], item)
        else:
            err = "\u0627\u06cc\u0646 \u0628\u062e\u0634 \u0631\u0627 \u0627\u0632 \u062f\u0627\u062e\u0644 \u0631\u0628\u0627\u062a \u062a\u0646\u0638\u06cc\u0645 \u06a9\u0646."
        if not err:
            rt.last_name = rt.last_bio = None
            rt.last["clock"] = 0
    elif op == "clearp" and sp["t"] == "one":
        set_p(uid, key, sp["n"], None)
        if is_on(uid, key) and FEATS[key]["need"]:
            set_on(uid, key, False)
        msg = "\U0001f5d1 \u067e\u0627\u06a9 \u0634\u062f."
    elif op == "ladd" and sp["t"] == "list":
        lst = get_p(uid, key, sp["n"]) or []
        if len(lst) >= sp["mx"]:
            err = "\u062d\u062f\u0627\u06a9\u062b\u0631 %s \u0645\u0648\u0631\u062f \u0645\u062c\u0627\u0632 \u0627\u0633\u062a." % sp["mx"]
        else:
            item, err = await parse_item(rt, sp["k"], txt, sp)
            if not err:
                lst.append(item)
                set_p(uid, key, sp["n"], lst)
                msg = "\u2705 \u0627\u0636\u0627\u0641\u0647 \u0634\u062f."
    elif op == "ldel" and sp["t"] == "list":
        lst = get_p(uid, key, sp["n"]) or []
        try:
            j = int(q.get("j", -1))
        except Exception:
            j = -1
        if 0 <= j < len(lst):
            lst.pop(j)
            set_p(uid, key, sp["n"], lst)
        if not lst and is_on(uid, key) and sp["n"] in FEATS[key]["need"]:
            set_on(uid, key, False)
        msg = "\U0001f5d1 \u062d\u0630\u0641 \u0634\u062f."
    elif op == "lclr" and sp["t"] == "list":
        set_p(uid, key, sp["n"], [])
        if is_on(uid, key) and sp["n"] in FEATS[key]["need"]:
            set_on(uid, key, False)
        msg = "\U0001f9f9 \u067e\u0627\u06a9 \u0634\u062f."
    else:
        err = "\u062f\u0633\u062a\u0648\u0631 \u0646\u0627\u0645\u0639\u062a\u0628\u0631"
    if err:
        return dict(ok=False, err=err)
    return dict(ok=True, msg=msg, feat=feat_json(uid, key))


async def _http(writer, code, ctype, body, extra=""):
    if isinstance(body, str):
        body = body.encode("utf-8")
    head = ("HTTP/1.1 %s\r\nContent-Type: %s\r\nContent-Length: %d\r\nCache-Control: no-store\r\n"
            "Connection: close\r\n%s\r\n" % (code, ctype, len(body), extra)).encode("latin-1")
    writer.write(head + body)
    await writer.drain()


async def web_conn(reader, writer):
    try:
        raw = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 15)
        lines = raw.decode("latin-1").split("\r\n")
        method, path = lines[0].split(" ")[:2]
        hd = {}
        for ln in lines[1:]:
            if ":" in ln:
                k, v = ln.split(":", 1)
                hd[k.strip().lower()] = v.strip()
        n = int(hd.get("content-length") or 0)
        if n > 65536:
            return await _http(writer, "413 Payload Too Large", "text/plain", "too large")
        body = await asyncio.wait_for(reader.readexactly(n), 15) if n else b""
        path = path.split("?")[0]
        if method == "GET" and path in ("/", "/index.html"):
            await _http(writer, "200 OK", "text/html; charset=utf-8", WEB_HTML)
        elif method == "GET" and path.startswith("/av/"):
            try:
                au = int(path[4:].split(".")[0])
            except Exception:
                au = 0
            ap = await get_avatar(au) if DB.one("SELECT 1 FROM users WHERE id=?", (au,)) else None
            if ap and os.path.exists(ap):
                with open(ap, "rb") as fh:
                    await _http(writer, "200 OK", "image/jpeg", fh.read())
            else:
                await _http(writer, "404 Not Found", "text/plain", "no")
        elif method == "GET" and path == "/health":
            await _http(writer, "200 OK", "text/plain", "ok")
        elif method == "POST" and path == "/api":
            uid = check_init(hd.get("x-init", ""))
            if uid is None:
                res = dict(ok=False, err="\u0627\u0639\u062a\u0628\u0627\u0631\u0633\u0646\u062c\u06cc \u0646\u0627\u0645\u0648\u0641\u0642\u061b \u0645\u06cc\u0646\u06cc\u200c\u0627\u067e \u0631\u0627 \u0627\u0632 \u062f\u0627\u062e\u0644 \u0631\u0628\u0627\u062a \u0628\u0627\u0632 \u06a9\u0646.")
            else:
                try:
                    res = await api_call(uid, json.loads(body.decode("utf-8") or "{}"))
                except AUTH_DEAD:
                    res = dict(ok=False, err="\u062d\u0633\u0627\u0628\u062a \u0642\u0637\u0639 \u0634\u062f\u0647\u061b \u062f\u0631 \u0631\u0628\u0627\u062a /start \u0628\u0632\u0646.")
                except Exception:
                    log.exception("api failed")
                    res = dict(ok=False, err="\u062e\u0637\u0627\u06cc \u062f\u0627\u062e\u0644\u06cc")
            await _http(writer, "200 OK", "application/json; charset=utf-8", json.dumps(res, ensure_ascii=False))
        else:
            await _http(writer, "404 Not Found", "text/plain", "not found")
    except Exception:
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass



def v_admin():
    pend = DB.one("SELECT COUNT(*) FROM pay WHERE status='wait'")[0]
    packs = "\n".join("\u2022 %s \u0633\u06a9\u0647 = %s \u062a\u0648\u0645\u0627\u0646" % (fa(c), money(p)) for c, p in get_packs())
    t = ("\U0001f6e0 <b>\u0645\u062f\u06cc\u0631\u06cc\u062a Self Speed</b>\n\n\U0001f4b3 \u06a9\u0627\u0631\u062a: <code>%s</code>\n\n\U0001fa99 \u0628\u0633\u062a\u0647\u200c\u0647\u0627:\n%s\n\n\U0001f381 \u062a\u0633\u062a \u0631\u0627\u06cc\u06af\u0627\u0646: %s\n\U0001f3a1 \u06af\u0631\u062f\u0648\u0646\u0647: %s\n\U0001f310 \u0645\u06cc\u0646\u06cc\u200c\u0627\u067e: %s" % (
        esc(kv_get(0, "card", "") or "\u062b\u0628\u062a \u0646\u0634\u062f\u0647"), packs, fmt_left(test_sec()), "\u0631\u0648\u0634\u0646" if wheel_on() else "\u062e\u0627\u0645\u0648\u0634",
        webapp_url() or "\u062a\u0646\u0638\u06cc\u0645 \u0646\u0634\u062f\u0647"))
    rows = [[Button.inline("\U0001f4b3 \u0634\u0645\u0627\u0631\u0647 \u06a9\u0627\u0631\u062a", "ad:card"), Button.inline("\U0001fa99 \u0642\u06cc\u0645\u062a\u200c\u0647\u0627", "ad:price")],
            [Button.inline("\U0001f381 \u0645\u062f\u062a \u062a\u0633\u062a", "ad:test"), Button.inline("\U0001f3a1 \u06af\u0631\u062f\u0648\u0646\u0647 %s" % ("\u2705" if wheel_on() else "\u26d4"), "ad:wheel")],
            [Button.inline("\U0001f9fe \u062f\u0631\u062e\u0648\u0627\u0633\u062a\u200c\u0647\u0627\u06cc \u067e\u0631\u062f\u0627\u062e\u062a (%s)" % fa(pend), "ad:pays")],
            [Button.inline("\U0001f465 \u06a9\u0627\u0631\u0628\u0631\u0627\u0646", "ad:users"), Button.inline("\U0001f41e \u062e\u0637\u0627\u0647\u0627", "ad:err")]]
    return t, rows


ADMIN_BACK = [[Button.inline("\u2b05 \u0645\u062f\u06cc\u0631\u06cc\u062a", "ad:home")]]


async def admin_cb(ev, what):
    uid = ev.sender_id
    PEND.pop(uid, None)
    if what == "home":
        view = v_admin()
    elif what == "wheel":
        kv_set(0, "wheel", "0" if wheel_on() else "1")
        view = v_admin()
    elif what in ("card", "price", "test"):
        PEND[uid] = dict(kind="adm", what=what, mid=ev.message_id, t=time.time())
        txt = {"card": "\U0001f4b3 <b>\u0634\u0645\u0627\u0631\u0647 \u06a9\u0627\u0631\u062a</b> (\u0648 \u0627\u06af\u0631 \u062e\u0648\u0627\u0633\u062a\u06cc \u0646\u0627\u0645 \u0635\u0627\u062d\u0628 \u06a9\u0627\u0631\u062a) \u0631\u0627 \u0628\u0641\u0631\u0633\u062a.\n\u0645\u062b\u0627\u0644: <code>6037 9911 2233 4455 - \u0639\u0644\u06cc \u0627\u062d\u0645\u062f\u06cc</code>",
               "price": "\U0001fa99 <b>\u0642\u06cc\u0645\u062a \u0628\u0633\u062a\u0647</b> \u0631\u0627 \u0628\u0647 \u0627\u06cc\u0646 \u0634\u06a9\u0644 \u0628\u0641\u0631\u0633\u062a: <code>\u062a\u0639\u062f\u0627\u062f\u200c\u0633\u06a9\u0647 \u0642\u06cc\u0645\u062a\u200c\u0628\u0647\u200c\u062a\u0648\u0645\u0627\u0646</code>\n\u0645\u062b\u0627\u0644: <code>5 20000</code> \u06cc\u0639\u0646\u06cc \u06f5 \u0633\u06a9\u0647 = \u06f2\u06f0\u06f0\u06f0\u06f0 \u062a\u0648\u0645\u0627\u0646\n"
                        "(\u0628\u0631\u0627\u06cc \u062d\u0630\u0641 \u06cc\u06a9 \u0628\u0633\u062a\u0647: <code>5 0</code>)",
               "test": "\U0001f381 \u0645\u062f\u062a <b>\u062a\u0633\u062a \u0631\u0627\u06cc\u06af\u0627\u0646</b> \u0631\u0627 \u0628\u0647 \u0633\u0627\u0639\u062a \u0628\u0641\u0631\u0633\u062a. \u0645\u062b\u0627\u0644: <code>1</code> \u06cc\u0627 <code>0.5</code> (\u0646\u06cc\u0645 \u0633\u0627\u0639\u062a). <code>0</code> \u06cc\u0639\u0646\u06cc \u0628\u062f\u0648\u0646 \u062a\u0633\u062a."}[what]
        view = (txt, ADMIN_BACK)
    elif what == "pays":
        rs = DB.all("SELECT id, uid, coins, price FROM pay WHERE status='wait' ORDER BY id LIMIT 10")
        if not rs:
            view = ("\U0001f9fe \u062f\u0631\u062e\u0648\u0627\u0633\u062a \u067e\u0631\u062f\u0627\u062e\u062a \u062f\u0631 \u0627\u0646\u062a\u0638\u0627\u0631\u06cc \u0646\u06cc\u0633\u062a.", ADMIN_BACK)
        else:
            lines, rows = ["\U0001f9fe <b>\u062f\u0631\u062e\u0648\u0627\u0633\u062a\u200c\u0647\u0627\u06cc \u062f\u0631 \u0627\u0646\u062a\u0638\u0627\u0631</b>\n"], []
            for pid, u, coins, price in rs:
                lines.append("#%d \u2014 <code>%d</code> \u2014 %s \u0633\u06a9\u0647 \u2014 %s \u062a\u0648\u0645\u0627\u0646" % (pid, u, fa(coins), money(price)))
                rows.append([Button.inline("\u2705 \u062a\u0623\u06cc\u06cc\u062f #%d" % pid, "pok:%d" % pid), Button.inline("\u274c \u0631\u062f #%d" % pid, "pno:%d" % pid)])
            view = ("\n".join(lines), rows + ADMIN_BACK)
    elif what == "users":
        rs = DB.all("SELECT id, name, status FROM users ORDER BY created DESC LIMIT 25")
        lines = ["\U0001f465 <b>\u06a9\u0627\u0631\u0628\u0631\u0627\u0646</b> (%s)\n" % fa(DB.one("SELECT COUNT(*) FROM users")[0])]
        for u, name, st in rs:
            lines.append("%s <code>%d</code> %s \u2014 %s" % ("\U0001f7e2" if u in RTS else "\u26aa", u, esc(name or ""), fmt_left(left_sec(u))))
        view = ("\n".join(lines), ADMIN_BACK)
    elif what == "err":
        view = ("<b>\u0622\u062e\u0631\u06cc\u0646 \u062e\u0637\u0627\u0647\u0627:</b>\n\n" + ("\n\n".join("<code>%s</code>" % esc(e[-400:]) for e in list(ERRS)[-6:]) or "\u2705 \u062e\u0637\u0627\u06cc\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647."), ADMIN_BACK)
    else:
        return await ev.answer()
    await ev.edit(view[0], buttons=view[1], parse_mode="html")


async def admin_input(ev, p):
    uid = ev.sender_id
    text = (ev.raw_text or "").strip()
    what = p["what"]
    a = text.translate(EN_DIGITS).replace(",", " ").split()
    err = ""
    if what == "card":
        if len(text) < 8:
            err = "\u0634\u0645\u0627\u0631\u0647 \u06a9\u0627\u0631\u062a \u06a9\u0648\u062a\u0627\u0647 \u0627\u0633\u062a."
        else:
            kv_set(0, "card", text)
    elif what == "price":
        if len(a) == 2 and a[0].isdigit() and a[1].isdigit() and int(a[0]) > 0:
            packs = dict(get_packs())
            if int(a[1]) == 0:
                if len(packs) > 1:
                    packs.pop(int(a[0]), None)
                else:
                    err = "\u062d\u062f\u0627\u0642\u0644 \u06cc\u06a9 \u0628\u0633\u062a\u0647 \u0628\u0627\u06cc\u062f \u0628\u0645\u0627\u0646\u062f."
            else:
                packs[int(a[0])] = int(a[1])
            if not err:
                set_packs(packs)
        else:
            err = "\u0628\u0647 \u0634\u06a9\u0644 \u00ab\u062a\u0639\u062f\u0627\u062f \u0642\u06cc\u0645\u062a\u00bb \u0628\u0641\u0631\u0633\u062a\u061b \u0645\u062b\u0644: 5 20000"
    elif what == "test":
        try:
            h = float(a[0])
            assert 0 <= h <= 720
            kv_set(0, "test_h", h)
        except Exception:
            err = "\u06cc\u06a9 \u0639\u062f\u062f (\u0633\u0627\u0639\u062a) \u0628\u0641\u0631\u0633\u062a\u061b \u0645\u062b\u0644 1"
    if err:
        return await ev.respond("\u274c " + err)
    PEND.pop(uid, None)
    await ev.respond("\u2705 \u0630\u062e\u06cc\u0631\u0647 \u0634\u062f.")
    t, rows = v_admin()
    await ev.respond(t, buttons=rows, parse_mode="html")


# ============================================================================
#
# ============================================================================
LAST_REPORT = [0]


async def report_error(where):
    try:
        import traceback
        if time.time() - LAST_REPORT[0] < 20 or not OWNER_ID or BOT is None:
            return
        LAST_REPORT[0] = time.time()
        await BOT.send_message(OWNER_ID, "\U0001f41e <b>\u062e\u0637\u0627 \u062f\u0631 %s</b>\n<code>%s</code>" % (where, esc(traceback.format_exc()[-900:])),
                               parse_mode="html")
    except Exception:
        pass


def _asset(name):
    for d in (BASE, os.getcwd()):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


AV_DIR = os.path.join(DATA, "avatars")
try:
    os.makedirs(AV_DIR, exist_ok=True)
except Exception:
    pass


def _shape(t):
    try:
        import arabic_reshaper
        try:
            from bidi.algorithm import get_display
        except Exception:
            from bidi import get_display
        return get_display(arabic_reshaper.reshape(t))
    except Exception:
        return t


def _clean(t):
    t = "".join(ch for ch in str(t or "") if ord(ch) < 0x2000 or 0xFB00 <= ord(ch) <= 0xFEFF)
    return " ".join(t.split()) or "-"


def _put(d, ImageFont, cx, cy, text, maxw, size, fill=(255, 255, 255), stroke=(15, 5, 35), minsize=14, clean=True):
    t = _shape(_clean(text) if clean else text)
    fp = _asset("font.ttf")
    while True:
        f = ImageFont.truetype(fp, size, layout_engine=ImageFont.Layout.BASIC)
        if d.textlength(t, font=f) <= maxw or size <= minsize:
            break
        size -= 2
    d.text((cx, cy), t, font=f, fill=fill, anchor="mm", stroke_width=2, stroke_fill=stroke)


def _circle(Image, ImageDraw, ImageOps, ImageFont, path, diam, initial=""):
    if path:
        try:
            im = ImageOps.fit(Image.open(path).convert("RGB"), (diam, diam))
        except Exception:
            im = None
    else:
        im = None
    if im is None:
        im = Image.new("RGB", (diam, diam), (70, 40, 140))
        dd = ImageDraw.Draw(im)
        _put(dd, ImageFont, diam // 2, diam // 2, initial or "?", diam, int(diam * 0.55), clean=True, stroke=(30, 10, 70))
    big = Image.new("L", (diam * 4, diam * 4), 0)
    ImageDraw.Draw(big).ellipse((0, 0, diam * 4 - 1, diam * 4 - 1), fill=255)
    mask = big.resize((diam, diam), Image.LANCZOS)
    out = Image.new("RGBA", (diam, diam))
    out.paste(im, (0, 0))
    out.putalpha(mask)
    return out


def _pil():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
        if _asset("font.ttf"):
            return Image, ImageDraw, ImageFont, ImageOps
    except Exception as e:
        log.info("pillow unavailable: %s", e)
    return None


def _coins_txt(sec):
    if sec >= 10 ** 8:
        return "\u0646\u0627\u0645\u062d\u062f\u0648\u062f"
    v = "%.1f" % (sec / float(COIN_SEC))
    v = v[:-2] if v.endswith(".0") else v.replace(".", "\u066b")
    return "%s \u0633\u06a9\u0647" % fa(v)


def _jpeg(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=88)
    buf.seek(0)
    buf.name = "card.jpg"
    return buf


def _render_card(uid, name, avatar):
    P = _pil()
    base = _asset("card.jpg")
    if not P or not base:
        return None
    Image, ImageDraw, ImageFont, ImageOps = P
    im = Image.open(base).convert("RGB")
    d = ImageDraw.Draw(im)
    if avatar:
        c = _circle(Image, ImageDraw, ImageOps, ImageFont, avatar, 302)
        im.paste(c, (338 - 151, 300 - 151), c)
    _put(d, ImageFont, 898, 340, "%s  \u2022  ID %s" % (_clean(name), uid), 470, 36, clean=False)
    sec = left_sec(uid)
    _put(d, ImageFont, 772, 432, fmt_left(sec), 250, 36, fill=(255, 226, 140))
    _put(d, ImageFont, 772, 534, _coins_txt(sec), 250, 40, fill=(255, 226, 140))
    return _jpeg(im)


def _render_end(w, l, stake, dw, dl, wav, lav):
    P = _pil()
    base = _asset("end.jpg")
    if not P or not base:
        return None
    Image, ImageDraw, ImageFont, ImageOps = P
    im = Image.open(base).convert("RGB")
    d = ImageDraw.Draw(im)
    for (cx, cy, nm, av) in ((291, 320, w[1], wav), (1077, 318, l[1], lav)):
        c = _circle(Image, ImageDraw, ImageOps, ImageFont, av, 186, _clean(nm)[:1])
        im.paste(c, (cx - 93, cy - 93), c)
    _put(d, ImageFont, 290, 441, w[1], 165, 28)
    _put(d, ImageFont, 1072, 441, l[1], 165, 28)
    _put(d, ImageFont, 290, 580, "\u0628\u0631\u0646\u062f\u0647", 300, 40, fill=(255, 215, 110))
    _put(d, ImageFont, 290, 620, "%s \u0633\u06a9\u0647 \u0633\u0648\u062f" % fa(stake), 300, 34, fill=(120, 255, 160))
    _put(d, ImageFont, 1062, 580, "\u0628\u0627\u0632\u0646\u062f\u0647", 300, 40, fill=(255, 120, 120))
    _put(d, ImageFont, 1062, 620, "%s \u0633\u06a9\u0647 \u0636\u0631\u0631" % fa(stake), 300, 34, fill=(255, 150, 150))
    _put(d, ImageFont, 675, 425, "\u062c\u0627\u06cc\u0632\u0647\u200c\u06cc \u0628\u0631\u0646\u062f\u0647", 300, 34)
    _put(d, ImageFont, 675, 480, "%s \u0633\u06a9\u0647" % fa(stake), 300, 60, fill=(255, 215, 110))
    _put(d, ImageFont, 675, 585, "\u062a\u0627\u0633: %s \u062f\u0631 \u0628\u0631\u0627\u0628\u0631 %s" % (fa(dw), fa(dl)), 300, 30)
    return _jpeg(im)


async def get_avatar(uid):
    p = os.path.join(AV_DIR, "%d.jpg" % uid)
    try:
        if os.path.exists(p) and time.time() - os.path.getmtime(p) < 6 * 3600:
            return p
        if os.path.exists(p + ".none") and time.time() - os.path.getmtime(p + ".none") < 3600:
            return None
    except Exception:
        pass
    for cl, who in ((BOT, uid), (RTS[uid].client if uid in RTS else None, "me")):
        if cl is None:
            continue
        try:
            r = await cl.download_profile_photo(who, file=p, download_big=False)
            if r:
                return p
        except Exception as e:
            log.info("avatar fetch failed for %s: %s", uid, type(e).__name__)
    try:
        open(p + ".none", "w").close()
    except Exception:
        pass
    return None


def _uname_of(uid):
    r = DB.one("SELECT name FROM users WHERE id=?", (uid,))
    return (r[0] if r and r[0] else "\u06a9\u0627\u0631\u0628\u0631")


async def make_card(uid):
    av = await get_avatar(uid)
    return await asyncio.get_event_loop().run_in_executor(None, _render_card, uid, _uname_of(uid), av)


async def send_card_to(chat, uid, reply_to=None):
    img = None
    try:
        img = await make_card(uid)
    except Exception:
        log.exception("card render failed")
    sec = left_sec(uid)
    cap = "\U0001faaa <b>%s</b>\n\u23f3 \u0632\u0645\u0627\u0646 \u0628\u0627\u0642\u06cc\u200c\u0645\u0627\u0646\u062f\u0647: <b>%s</b>\n\U0001fa99 \u0633\u06a9\u0647: <b>%s</b>" % (esc(_uname_of(uid)), fmt_left(sec), _coins_txt(sec))
    if img is not None:
        return await BOT.send_file(chat, img, caption=cap, parse_mode="html", reply_to=reply_to)
    return await BOT.send_message(chat, cap, parse_mode="html", reply_to=reply_to)


#
CH = {}
CH_ID = [0]


def game_groups():
    try:
        return [int(x) for x in json.loads(kv_get(0, "gg") or "[]")]
    except Exception:
        return []


def can_play(uid, stake):
    return (not is_free(uid)) and bool(DB.one("SELECT 1 FROM users WHERE id=?", (uid,))) and left_sec(uid) >= stake * COIN_SEC + 60


def board(limit=10):
    net, wins, games = {}, {}, {}
    for w, l, st in DB.all("SELECT w, l, stake FROM game"):
        net[w] = net.get(w, 0) + st
        net[l] = net.get(l, 0) - st
        wins[w] = wins.get(w, 0) + 1
        games[w] = games.get(w, 0) + 1
        games[l] = games.get(l, 0) + 1
    order = sorted(net, key=lambda u: (-net[u], -wins.get(u, 0), u))
    return [dict(rank=i + 1, uid=u, name=_uname_of(u), net=net[u], wins=wins.get(u, 0), games=games.get(u, 0))
            for i, u in enumerate(order)][:limit], {u: (i + 1, net[u], wins.get(u, 0), games.get(u, 0)) for i, u in enumerate(order)}


GAME_HELP = ("\U0001f3ae <b>\u0628\u0627\u0632\u06cc \u0634\u0631\u0637\u200c\u0628\u0646\u062f\u06cc Self Speed</b>\n\n"
             "\u2022 <code>\u0634\u0631\u0637 3</code> \u2190 \u0634\u0631\u0637 \u06f3 \u0633\u06a9\u0647\u200c\u0627\u06cc \u0645\u06cc\u200c\u0628\u0646\u062f\u06cc \u0648 \u0645\u0646\u062a\u0638\u0631 \u062d\u0631\u06cc\u0641 \u0645\u06cc\u200c\u0645\u0627\u0646\u06cc\n"
             "\u2022 \u062d\u0631\u06cc\u0641 \u0631\u0648\u06cc \u00ab\u2694\ufe0f \u0642\u0628\u0648\u0644\u00bb \u0645\u06cc\u200c\u0632\u0646\u062f\u061b \u0647\u0631 \u062f\u0648 \u062a\u0627\u0633 \u0645\u06cc\u200c\u0627\u0646\u062f\u0627\u0632\u0646\u062f\u060c \u062a\u0627\u0633 \u0628\u0632\u0631\u06af\u200c\u062a\u0631 \u0628\u0631\u0646\u062f\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f\n"
             "\u2022 \u0633\u06a9\u0647\u200c\u06cc \u0634\u0631\u0637 \u0627\u0632 \u0628\u0627\u0632\u0646\u062f\u0647 \u06a9\u0645 \u0648 \u0628\u0647 \u0628\u0631\u0646\u062f\u0647 \u0627\u0636\u0627\u0641\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f (\u0647\u0631 \u0633\u06a9\u0647 = \u06f1 \u0633\u0627\u0639\u062a \u0633\u0644\u0641)\n"
             "\u2022 <code>\u0645\u0648\u062c\u0648\u062f\u06cc</code> \u2190 \u06a9\u0627\u0631\u062a \u0645\u0648\u062c\u0648\u062f\u06cc \u062a\u0648\n\u2022 <code>\u0644\u06cc\u062f\u0631\u0628\u0648\u0631\u062f</code> \u2190 \u0628\u0631\u062a\u0631\u06cc\u0646\u200c\u0647\u0627\n\n"
             "\u0634\u0631\u0637: \u062f\u0627\u0634\u062a\u0646 \u062d\u0633\u0627\u0628 \u0641\u0639\u0627\u0644 \u062f\u0631 \u0631\u0628\u0627\u062a \u0648 \u0633\u06a9\u0647\u200c\u06cc \u06a9\u0627\u0641\u06cc.")


async def on_group(ev):
    chat = ev.chat_id
    text = (ev.raw_text or "").strip().translate(EN_DIGITS)
    if not text:
        return
    parts = text.split()
    cmd = parts[0].lower().lstrip("/").split("@")[0]
    uid = ev.sender_id
    if uid == OWNER_ID and cmd in ("setgame", "unsetgame"):
        gg = game_groups()
        if cmd == "setgame" and chat not in gg:
            gg.append(chat)
        if cmd == "unsetgame" and chat in gg:
            gg.remove(chat)
        kv_set(0, "gg", json.dumps(gg))
        return await ev.respond("\u2705 \u0627\u06cc\u0646 \u06af\u0631\u0648\u0647 %s \u0634\u062f." % ("\u06af\u0631\u0648\u0647 \u0628\u0627\u0632\u06cc" if cmd == "setgame" else "\u0627\u0632 \u0628\u0627\u0632\u06cc \u062e\u0627\u0631\u062c"))
    if chat not in game_groups():
        return
    if cmd in ("\u0645\u0648\u062c\u0648\u062f\u06cc", "bal", "balance", "\u06a9\u06cc\u0641", "wallet"):
        if not DB.one("SELECT 1 FROM users WHERE id=?", (uid,)):
            return await ev.respond("\u0627\u0648\u0644 \u062f\u0627\u062e\u0644 \u0631\u0628\u0627\u062a (\u067e\u06cc\u0648\u06cc) \u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u06a9\u0646 \U0001f339")
        return await send_card_to(chat, uid, reply_to=ev.id)
    if cmd in ("\u0634\u0631\u0637", "bet"):
        return await new_bet(ev, parts)
    if cmd in ("\u0644\u06cc\u062f\u0631\u0628\u0648\u0631\u062f", "top", "\u0628\u0631\u062a\u0631\u06cc\u0646", "\u062c\u062f\u0648\u0644"):
        top, _ = board(10)
        if not top:
            return await ev.respond("\u0647\u0646\u0648\u0632 \u0628\u0627\u0632\u06cc\u200c\u0627\u06cc \u0627\u0646\u062c\u0627\u0645 \u0646\u0634\u062f\u0647.")
        med = ["\U0001f947", "\U0001f948", "\U0001f949"]
        lines = ["\U0001f3c6 <b>\u0644\u06cc\u062f\u0631\u0628\u0648\u0631\u062f Self Speed</b>\n"]
        for r in top:
            lines.append("%s %s \u2014 %s%s \u0633\u06a9\u0647 (%s \u0628\u0631\u062f)" % (med[r["rank"] - 1] if r["rank"] <= 3 else fa(r["rank"]) + ".", esc(r["name"]),
                                                       "+" if r["net"] >= 0 else "-", fa(abs(r["net"])), fa(r["wins"])))
        return await ev.respond("\n".join(lines), parse_mode="html")
    if cmd in ("\u0631\u0627\u0647\u0646\u0645\u0627", "\u0628\u0627\u0632\u06cc", "help"):
        return await ev.respond(GAME_HELP, parse_mode="html")


async def new_bet(ev, parts):
    uid, chat = ev.sender_id, ev.chat_id
    try:
        stake = int(parts[1])
        assert 1 <= stake <= 100
    except Exception:
        return await ev.respond("\u0645\u062b\u0627\u0644: <code>\u0634\u0631\u0637 3</code> (\u06f1 \u062a\u0627 \u06f1\u06f0\u06f0 \u0633\u06a9\u0647)", parse_mode="html")
    if not DB.one("SELECT 1 FROM users WHERE id=?", (uid,)):
        return await ev.respond("\u0627\u0648\u0644 \u062f\u0627\u062e\u0644 \u0631\u0628\u0627\u062a (\u067e\u06cc\u0648\u06cc) \u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u06a9\u0646 \U0001f339")
    if not can_play(uid, stake):
        return await ev.respond("\U0001fa99 \u0633\u06a9\u0647\u200c\u06cc \u06a9\u0627\u0641\u06cc \u0628\u0631\u0627\u06cc \u0627\u06cc\u0646 \u0634\u0631\u0637 \u0646\u062f\u0627\u0631\u06cc. \u0628\u0627 \u00ab\u0645\u0648\u062c\u0648\u062f\u06cc\u00bb \u0628\u0628\u06cc\u0646 \u0686\u0642\u062f\u0631 \u062f\u0627\u0631\u06cc.")
    for cid, c in list(CH.items()):
        if c["creator"] == uid:
            CH.pop(cid, None)
    CH_ID[0] += 1
    cid = CH_ID[0]
    name = _uname_of(uid)
    m = await BOT.send_message(chat, "\u2694\ufe0f <b>%s</b> \u0631\u0648\u06cc <b>%s \u0633\u06a9\u0647</b> \u0634\u0631\u0637 \u0628\u0633\u062a!\n\u06a9\u06cc \u062d\u0627\u0636\u0631\u0647 \u0628\u0627\u0647\u0627\u0634 \u0628\u062c\u0646\u06af\u0647\u061f" % (esc(name), fa(stake)),
                               parse_mode="html", reply_to=ev.id,
                               buttons=[[Button.inline("\u2694\ufe0f \u0642\u0628\u0648\u0644 \u0645\u06cc\u200c\u06a9\u0646\u0645", "bg:a:%d" % cid), Button.inline("\u2716 \u0644\u063a\u0648", "bg:c:%d" % cid)]])
    CH[cid] = dict(chat=chat, creator=uid, stake=stake, t=time.time(), mid=getattr(m, "id", None))


async def _roll(chat):
    try:
        m = await BOT.send_file(chat, types.InputMediaDice("\U0001f3b2"))
        v = getattr(getattr(m, "media", None), "value", None)
        return int(v) if v else random.randint(1, 6)
    except Exception:
        return random.randint(1, 6)


async def game_cb(ev, op, cid):
    uid = ev.sender_id
    ch = CH.get(cid)
    if not ch or time.time() - ch["t"] > 600:
        CH.pop(cid, None)
        try:
            await ev.edit("\u231b \u0627\u06cc\u0646 \u0634\u0631\u0637 \u0645\u0646\u0642\u0636\u06cc \u0634\u062f\u0647.", buttons=None)
        except Exception:
            pass
        return await ev.answer("\u0645\u0646\u0642\u0636\u06cc \u0634\u062f")
    if op == "c":
        if uid not in (ch["creator"], OWNER_ID):
            return await ev.answer("\u0641\u0642\u0637 \u0633\u0627\u0632\u0646\u062f\u0647\u200c\u06cc \u0634\u0631\u0637 \u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u062f \u0644\u063a\u0648 \u06a9\u0646\u062f.", alert=True)
        CH.pop(cid, None)
        await ev.answer("\u0644\u063a\u0648 \u0634\u062f")
        return await ev.edit("\u2716 \u0634\u0631\u0637 \u0644\u063a\u0648 \u0634\u062f.", buttons=None)
    if uid == ch["creator"]:
        return await ev.answer("\u0646\u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u06cc \u0628\u0627 \u062e\u0648\u062f\u062a \u0628\u0627\u0632\u06cc \u06a9\u0646\u06cc \U0001f604", alert=True)
    if not DB.one("SELECT 1 FROM users WHERE id=?", (uid,)):
        return await ev.answer("\u0627\u0648\u0644 \u062f\u0627\u062e\u0644 \u0631\u0628\u0627\u062a (\u067e\u06cc\u0648\u06cc) \u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u06a9\u0646.", alert=True)
    if not can_play(uid, ch["stake"]):
        return await ev.answer("\U0001fa99 \u0633\u06a9\u0647\u200c\u06cc \u06a9\u0627\u0641\u06cc \u0646\u062f\u0627\u0631\u06cc.", alert=True)
    if not can_play(ch["creator"], ch["stake"]):
        CH.pop(cid, None)
        await ev.answer("\u0633\u0627\u0632\u0646\u062f\u0647 \u062f\u06cc\u06af\u0631 \u0633\u06a9\u0647\u200c\u06cc \u06a9\u0627\u0641\u06cc \u0646\u062f\u0627\u0631\u062f")
        return await ev.edit("\u26a0\ufe0f \u0633\u0627\u0632\u0646\u062f\u0647\u200c\u06cc \u0634\u0631\u0637 \u062f\u06cc\u06af\u0631 \u0633\u06a9\u0647\u200c\u06cc \u06a9\u0627\u0641\u06cc \u0646\u062f\u0627\u0631\u062f\u061b \u0634\u0631\u0637 \u0644\u063a\u0648 \u0634\u062f.", buttons=None)
    CH.pop(cid, None)
    await ev.answer("\u0628\u0627\u0632\u06cc \u0634\u0631\u0648\u0639 \u0634\u062f!")
    await play_game(ev, ch, uid)


async def play_game(ev, ch, p2):
    chat, p1, stake = ch["chat"], ch["creator"], ch["stake"]
    n1, n2 = _uname_of(p1), _uname_of(p2)
    await ev.edit("\U0001f3b2 <b>%s</b>  \u2694\ufe0f  <b>%s</b>\n\u0634\u0631\u0637: %s \u0633\u06a9\u0647 \u2014 \u062a\u0627\u0633\u200c\u0647\u0627 \u0645\u06cc\u200c\u0627\u0641\u062a\u0646\u062f ..." % (esc(n1), esc(n2), fa(stake)), parse_mode="html", buttons=None)
    d1 = d2 = 0
    for _ in range(3):
        d1 = await _roll(chat)
        d2 = await _roll(chat)
        if d1 != d2:
            break
    if d1 == d2:
        d1 += 0
        winner = secrets.choice([p1, p2])
    else:
        winner = p1 if d1 > d2 else p2
    loser = p2 if winner == p1 else p1
    dw, dl = (d1, d2) if winner == p1 else (d2, d1)
    await asyncio.sleep(3.5)
    if not (can_play(p1, stake) and can_play(p2, stake)):
        return await BOT.send_message(chat, "\u26a0\ufe0f \u0628\u0627\u0632\u06cc \u0644\u063a\u0648 \u0634\u062f\u061b \u06cc\u06a9\u06cc \u0627\u0632 \u0628\u0627\u0632\u06cc\u06a9\u0646\u200c\u0647\u0627 \u062f\u06cc\u06af\u0631 \u0633\u06a9\u0647\u200c\u06cc \u06a9\u0627\u0641\u06cc \u0646\u062f\u0627\u0634\u062a.")
    add_time(winner, stake * COIN_SEC)
    add_time(loser, -stake * COIN_SEC)
    DB.q("INSERT INTO game(chat,w,l,stake,ts) VALUES(?,?,?,?,?)", (chat, winner, loser, stake, int(time.time())))
    wn, ln = _uname_of(winner), _uname_of(loser)
    cap = "\U0001f3c1 <b>\u067e\u0627\u06cc\u0627\u0646 \u0628\u0627\u0632\u06cc</b>\n\U0001f3c6 \u0628\u0631\u0646\u062f\u0647: <b>%s</b> (+%s \u0633\u06a9\u0647)\n\U0001f494 \u0628\u0627\u0632\u0646\u062f\u0647: <b>%s</b> (-%s \u0633\u06a9\u0647)\n\U0001f3b2 %s \u062f\u0631 \u0628\u0631\u0627\u0628\u0631 %s" % (
        esc(wn), fa(stake), esc(ln), fa(stake), fa(dw), fa(dl))
    img = None
    try:
        wav, lav = await get_avatar(winner), await get_avatar(loser)
        img = await asyncio.get_event_loop().run_in_executor(None, _render_end, (winner, wn), (loser, ln), stake, dw, dl, wav, lav)
    except Exception:
        log.exception("end card failed")
    if img is not None:
        await BOT.send_file(chat, img, caption=cap, parse_mode="html")
    else:
        await BOT.send_message(chat, cap, parse_mode="html")
    await notify(winner, "\U0001f3c6 \u062f\u0631 \u0634\u0631\u0637\u200c\u0628\u0646\u062f\u06cc \u0628\u0631\u062f\u06cc! +%s \u0633\u06a9\u0647\n\u23f3 \u0632\u0645\u0627\u0646 \u0641\u0639\u0644\u06cc: <b>%s</b>" % (fa(stake), fmt_left(left_sec(winner))))
    await notify(loser, "\U0001f494 \u062f\u0631 \u0634\u0631\u0637\u200c\u0628\u0646\u062f\u06cc \u0628\u0627\u062e\u062a\u06cc: -%s \u0633\u06a9\u0647\n\u23f3 \u0632\u0645\u0627\u0646 \u0641\u0639\u0644\u06cc: <b>%s</b>" % (fa(stake), fmt_left(left_sec(loser))))


#
def make_backup(full=False):
    now = time.time()
    users = []
    for (uid, phone, name, username, session, status, settings, created) in DB.all(
            "SELECT id,phone,name,username,session,status,settings,created FROM users"):
        kv = {k: v for k, v in DB.all("SELECT k, v FROM kv WHERE uid=?", (uid,)) if not k.startswith(("w:", "dnd:"))}
        b = bill_row(uid)
        u = dict(id=uid, phone=phone, name=name, username=username, status=status, settings=settings, created=created,
                 kv=kv, left=max(0, int(b["exp"] - now)) if b else 0, test=b["test"] if b else 0, wheel=b["wheel_ts"] if False else (b["wheel"] if b else 0))
        if full:
            u["session"] = session
        users.append(u)
    data = dict(v=1, time=int(now), users=users,
                glob={k: v for k, v in DB.all("SELECT k, v FROM kv WHERE uid=0")},
                pay=[list(r) for r in DB.all("SELECT id,uid,coins,price,status,ts FROM pay")],
                game=[list(r) for r in DB.all("SELECT id,chat,w,l,stake,ts FROM game")])
    buf = io.BytesIO(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    buf.name = "selfspeed_backup_%s.json" % time.strftime("%Y%m%d_%H%M")
    buf.seek(0)
    return buf, len(users)


def import_backup(d):
    now = int(time.time())
    n = 0
    for u in d.get("users", []):
        uid = int(u["id"])
        full = bool(u.get("session"))
        status = u.get("status") or "down"
        if not full and status != "off":
            status = "down"
        DB.q("INSERT OR REPLACE INTO users(id,phone,name,username,session,status,settings,created,last_seen) VALUES(?,?,?,?,?,?,?,?,?)",
             (uid, u.get("phone"), u.get("name"), u.get("username"), u["session"] if full else enc(""), status,
              u.get("settings") or "{}", u.get("created") or now, now))
        for k, v in (u.get("kv") or {}).items():
            DB.q("INSERT OR REPLACE INTO kv(uid,k,v) VALUES(?,?,?)", (uid, k, v))
        left = int(u.get("left") or 0)
        DB.q("INSERT OR REPLACE INTO bill(uid,exp,test_used,wheel_ts,warned) VALUES(?,?,?,?,0)",
             (uid, (now + left) if full else 0, int(u.get("test") or 0), int(u.get("wheel") or 0)))
        if not full and left > 0:
            kv_set(uid, "frozen", left)
        ah = (u.get("kv") or {}).get("ah")
        if ah and BOT is not None:
            try:
                BOT.session.process_entities([types.User(id=uid, access_hash=int(ah), first_name=u.get("name") or "U")])
            except Exception as e:
                log.info("peer seed failed for %s: %s", uid, e)
        n += 1
    for k, v in (d.get("glob") or {}).items():
        DB.q("INSERT OR REPLACE INTO kv(uid,k,v) VALUES(0,?,?)", (k, v))
    for r in d.get("pay", []):
        DB.q("INSERT OR REPLACE INTO pay(id,uid,coins,price,status,ts) VALUES(?,?,?,?,?,?)", tuple(r))
    for r in d.get("game", []):
        DB.q("INSERT OR REPLACE INTO game(id,chat,w,l,stake,ts) VALUES(?,?,?,?,?,?)", tuple(r))
    return n


async def restore_from(ev):
    f = ev.message.file
    if not f or not (f.name or "").lower().endswith(".json"):
        return False
    raw = await ev.message.download_media(file=bytes)
    try:
        d = json.loads(raw.decode("utf-8"))
        assert isinstance(d.get("users"), list)
    except Exception:
        await ev.respond("\u274c \u0627\u06cc\u0646 \u0641\u0627\u06cc\u0644 \u0628\u06a9\u0627\u067e Self Speed \u0646\u06cc\u0633\u062a.")
        return True
    n = import_backup(d)
    await ev.respond("\u2705 <b>%s \u06a9\u0627\u0631\u0628\u0631</b> \u0628\u0627\u0632\u06cc\u0627\u0628\u06cc \u0634\u062f (\u062a\u0646\u0638\u06cc\u0645\u0627\u062a\u060c \u0645\u0648\u062c\u0648\u062f\u06cc \u0648 \u0628\u0627\u0632\u06cc\u200c\u0647\u0627).\n\u062d\u0627\u0644\u0627 <code>/relogin</code> \u0628\u0632\u0646 \u062a\u0627 \u0628\u0647 \u0647\u0645\u0647 \u067e\u06cc\u0627\u0645 \u00ab\u0648\u0631\u0648\u062f \u062f\u0648\u0628\u0627\u0631\u0647\u00bb \u0628\u0631\u0648\u062f." % fa(n),
                     parse_mode="html")
    return True



async def main():
    global BOT, DB
    load_config()
    init_key()
    if ON_SERVER and not HAS_VOLUME:
        log.warning("NO VOLUME: data is lost on every deploy")
    if ON_SERVER and not (os.environ.get("SECRET_KEY") or "").strip():
        log.warning("SECRET_KEY not set: a random key is stored next to the database")
    DB = Database(os.path.join(DATA, "selfsaz.db"))
    for (uid, raw) in DB.all("SELECT id, settings FROM users"):
        load_settings(uid, raw)
    BOT = make_client(os.path.join(DATA, "bot"))
    guard_client(BOT)
    await BOT.start(bot_token=BOT_TOKEN)
    BOT.add_event_handler(on_msg, events.NewMessage(incoming=True))
    BOT.add_event_handler(on_cb, events.CallbackQuery())
    me = await BOT.get_me()
    n_users = DB.one("SELECT COUNT(*) FROM users")[0]
    print("\n\u2705 \u0631\u0628\u0627\u062a \u0631\u0648\u0634\u0646 \u0634\u062f:  @%s  (\u06a9\u0627\u0631\u0628\u0631\u0627\u0646: %d)" % (me.username, n_users))
    if not ON_SERVER:
        print("   \u062d\u0627\u0644\u0627 \u062f\u0631 \u062a\u0644\u06af\u0631\u0627\u0645 \u0628\u0631\u0648 \u0628\u0647 \u0631\u0628\u0627\u062a \u0648 /start \u0628\u0632\u0646.")
        print("   (\u0627\u06cc\u0646 \u0635\u0641\u062d\u0647 \u0631\u0627 \u0628\u0627\u0632 \u0646\u06af\u0647 \u062f\u0627\u0631\u061b \u0628\u0627 \u0628\u0633\u062a\u0646\u0634 \u0631\u0628\u0627\u062a \u062e\u0627\u0645\u0648\u0634 \u0645\u06cc\u200c\u0634\u0648\u062f.)\n")
    asyncio.create_task(housekeeping())
    asyncio.create_task(billing_loop())
    port = int(os.environ.get("PORT") or (8080 if ON_SERVER else 0))
    if port:
        try:
            await asyncio.start_server(web_conn, "0.0.0.0", port)
            log.info("web app listening on %s", port)
        except Exception as e:
            log.warning("web server failed: %s", e)
    wu = webapp_url()
    if wu.startswith("https://"):
        try:
            await BOT(functions.bots.SetBotMenuButtonRequest(
                user_id=types.InputUserEmpty(), button=types.BotMenuButton("\U0001f3a1 Self Speed", wu + "/")))
        except Exception as e:
            log.info("menu button skipped: %s", e)
    if ON_SERVER:
        text = "\u2705 \u0631\u0628\u0627\u062a \u0631\u0648\u06cc \u0633\u0631\u0648\u0631 \u0631\u0648\u0634\u0646 \u0634\u062f. \u06a9\u0627\u0631\u0628\u0631\u0627\u0646: %s" % fa(n_users)
        if not HAS_VOLUME:
            text += ("\n\n\u26a0\ufe0f <b>Volume \u0646\u062f\u0627\u0631\u06cc!</b> \u0628\u0627 \u0647\u0631 Deploy \u0647\u0645\u0647\u200c\u06cc \u06a9\u0627\u0631\u0628\u0631\u0627\u0646 \u0648 \u062a\u0646\u0638\u06cc\u0645\u0627\u062a\u0634\u0627\u0646 \u067e\u0627\u06a9 \u0645\u06cc\u200c\u0634\u0648\u062f. "
                     "\u062f\u0631 \u0631\u06cc\u0644\u0648\u06cc \u06cc\u06a9 Volume \u0628\u0627 \u0645\u0633\u06cc\u0631 /data \u0628\u0633\u0627\u0632 \u0648 \u0645\u062a\u063a\u06cc\u0631 DATA_DIR=/data \u0628\u06af\u0630\u0627\u0631.")
        if not (os.environ.get("SECRET_KEY") or "").strip():
            text += "\n\n\u26a0\ufe0f \u0645\u062a\u063a\u06cc\u0631 SECRET_KEY \u0646\u062f\u0627\u0631\u06cc\u061b \u0628\u0647\u062a\u0631 \u0627\u0633\u062a \u06cc\u06a9 \u0631\u0645\u0632 \u0637\u0648\u0644\u0627\u0646\u06cc \u0628\u0631\u0627\u06cc\u0634 \u0628\u06af\u0630\u0627\u0631\u06cc."
        if not wu:
            text += ("\n\n\u2139\ufe0f \u0622\u062f\u0631\u0633 \u0645\u06cc\u0646\u06cc\u200c\u0627\u067e \u062a\u0646\u0638\u06cc\u0645 \u0646\u06cc\u0633\u062a: \u062f\u0631 \u0631\u06cc\u0644\u0648\u06cc Settings \u2190 Networking \u2190 Generate Domain \u0628\u0632\u0646 "
                     "(\u0648 PORT=8080 \u0631\u0627 \u062f\u0631 Variables \u0628\u06af\u0630\u0627\u0631)\u060c \u06cc\u0627 \u0628\u0627 /seturl \u0622\u062f\u0631\u0633 \u0631\u0627 \u0628\u062f\u0647.")
        try:
            await BOT.send_message(OWNER_ID, text, parse_mode="html")
        except Exception as e:
            log.info("owner notice skipped: %s", e)
    await BOT.run_until_disconnected()


def _run():
    try:
        import signal
        signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    except Exception:
        pass
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\u062e\u0627\u0645\u0648\u0634 \u0634\u062f.")
    except SystemExit:
        raise
    except BaseException:
        import traceback
        traceback.print_exc()
        if ON_SERVER:
            sys.exit(1)
        print("\n\u274c \u062e\u0637\u0627! \u0645\u062a\u0646 \u0628\u0627\u0644\u0627 \u0631\u0627 \u0628\u0631\u0627\u06cc \u0645\u0646 \u0628\u0641\u0631\u0633\u062a.")
    if not ON_SERVER:
        try:
            input("\n\u0628\u0631\u0627\u06cc \u0628\u0633\u062a\u0646\u060c Enter \u0628\u0632\u0646 ...")
        except Exception:
            pass


# ---- RUN ----
_run()
