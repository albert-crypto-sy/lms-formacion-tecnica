import streamlit as st, sqlite3, hashlib, secrets, json, uuid, io
from pathlib import Path
from datetime import date, datetime
import qrcode
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
st.set_page_config(page_title='LMS Tecnico',page_icon='🎓',layout='wide')
BASE=Path(__file__).parent; DATA=BASE/'data'; UP=DATA/'uploads'; DATA.mkdir(exist_ok=True);UP.mkdir(exist_ok=True);DB=DATA/'lms.db'
def cn():
 c=sqlite3.connect(DB,check_same_thread=False);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
def one(q,a=()):
 with cn() as c:return c.execute(q,a).fetchone()
def all(q,a=()):
 with cn() as c:return c.execute(q,a).fetchall()
def run(q,a=()):
 with cn() as c:c.execute(q,a);c.commit()
def hp(p):
 s=secrets.token_bytes(16);return (s+hashlib.pbkdf2_hmac('sha256',p.encode(),s,200000)).hex()
def vp(p,h):
 try:r=bytes.fromhex(h);return secrets.compare_digest(r[16:],hashlib.pbkdf2_hmac('sha256',p.encode(),r[:16],200000))
 except:return False
def save(f):
 if not f:return None
 n=uuid.uuid4().hex+Path(f.name).suffix.lower();(UP/n).write_bytes(f.getbuffer());return n
def refresh():st.rerun()
def init():
 with cn() as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY,company TEXT,logo TEXT);CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,company TEXT,email TEXT UNIQUE,phone TEXT,password TEXT,role TEXT);CREATE TABLE IF NOT EXISTS modules(id INTEGER PRIMARY KEY,title TEXT,synopsis TEXT,logo TEXT,attachment TEXT,pass_score INTEGER);CREATE TABLE IF NOT EXISTS trainers(id INTEGER PRIMARY KEY,name TEXT,email TEXT,phone TEXT);CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY,token TEXT UNIQUE,training_date TEXT,location TEXT,mode TEXT,comments TEXT,other_modules TEXT,trainer_ids TEXT,module_ids TEXT);CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY,module_id INTEGER,text TEXT,options TEXT,correct INTEGER);CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY,user_id INTEGER,session_id INTEGER,registered_at TEXT,UNIQUE(user_id,session_id));CREATE TABLE IF NOT EXISTS results(id INTEGER PRIMARY KEY,user_id INTEGER,session_id INTEGER,module_id INTEGER,score INTEGER,passed INTEGER,completed_at TEXT,UNIQUE(user_id,session_id,module_id));""")
  c.execute("INSERT OR IGNORE INTO settings VALUES(1,'Empresa Formadora',NULL)")
  e=st.secrets.get('ADMIN_EMAIL','admin@local.test').lower();p=st.secrets.get('ADMIN_PASSWORD','Admin123!')
  if not c.execute('SELECT 1 FROM users WHERE email=?',(e,)).fetchone():c.execute('INSERT INTO users(name,company,email,phone,password,role) VALUES(?,?,?,?,?,?)',('Administrador','',e,'',hp(p),'admin'))
init();S=one('SELECT * FROM settings WHERE id=1')
st.markdown('<style>.block-container{max-width:1200px}.hero{background:linear-gradient(135deg,#10213d,#1769e0);color:white;padding:28px;border-radius:22px;margin-bottom:22px}.stButton button,.stDownloadButton button{border-radius:10px;font-weight:700}</style>',unsafe_allow_html=True)
if S['logo'] and (UP/S['logo']).exists():st.sidebar.image(str(UP/S['logo']),width=130)
st.sidebar.title(S['company'])
def current():return one('SELECT * FROM users WHERE id=?',(st.session_state.get('uid',-1),))
def diploma(r):
 u=one('SELECT * FROM users WHERE id=?',(r['user_id'],));m=one('SELECT * FROM modules WHERE id=?',(r['module_id'],));s=one('SELECT * FROM sessions WHERE id=?',(r['session_id'],));b=io.BytesIO();c=canvas.Canvas(b,pagesize=landscape(A4));w,h=landscape(A4);c.setLineWidth(7);c.rect(22,22,w-44,h-44)
 for name,x in [(S['logo'],55),(m['logo'],w-205)]:
  if name and (UP/name).exists():
   try:c.drawImage(ImageReader(str(UP/name)),x,h-130,150,75,preserveAspectRatio=True,mask='auto')
   except:pass
 c.setFont('Helvetica-Bold',30);c.drawCentredString(w/2,h-120,'DIPLOMA DE FORMACION');c.setFont('Helvetica',16);c.drawCentredString(w/2,h-170,'Se certifica que');c.setFont('Helvetica-Bold',27);c.drawCentredString(w/2,h-215,u['name']);c.setFont('Helvetica',16);c.drawCentredString(w/2,h-258,'ha completado y superado la formacion');c.setFont('Helvetica-Bold',23);c.drawCentredString(w/2,h-300,m['title']);c.setFont('Helvetica',14);c.drawCentredString(w/2,h-342,f"{s['training_date']} - {s['location']}");c.drawCentredString(w/2,78,f"{S['company']} - Resultado {r['score']}%");c.save();return b.getvalue()
# Registro desde QR
token=st.query_params.get('join')
if token and not current():
 s=one('SELECT * FROM sessions WHERE token=?',(token,));
 if not s:st.error('Sesion no encontrada');st.stop()
 st.markdown(f"<div class='hero'><h1>Registro de asistencia</h1><p>{s['training_date']} · {s['location']} · {s['mode']}</p></div>",unsafe_allow_html=True)
 new=st.radio('Cuenta',['Soy nuevo','Ya tengo cuenta'],horizontal=True)
 with st.form('join'):
  name=st.text_input('Nombre');company=st.text_input('Empresa');email=st.text_input('Email');phone=st.text_input('Telefono');pwd=st.text_input('Contrasena',type='password');ok=st.form_submit_button('Confirmar asistencia',type='primary')
 if ok:
  u=one('SELECT * FROM users WHERE email=?',(email.lower().strip(),))
  if u and not vp(pwd,u['password']):st.error('Contrasena incorrecta')
  elif not u and (new!='Soy nuevo' or not name or len(pwd)<8):st.error('Completa el alta y usa una contrasena de 8 caracteres')
  else:
   if not u:run('INSERT INTO users(name,company,email,phone,password,role) VALUES(?,?,?,?,?,?)',(name,company,email.lower().strip(),phone,hp(pwd),'student'));u=one('SELECT * FROM users WHERE email=?',(email.lower().strip(),))
   run('INSERT OR IGNORE INTO attendance(user_id,session_id,registered_at) VALUES(?,?,?)',(u['id'],s['id'],datetime.now().isoformat()));st.session_state.uid=u['id'];st.query_params.clear();refresh()
 st.stop()
u=current()
if not u:
 st.markdown("<div class='hero'><h1>LMS Tecnico Industrial</h1><p>Asistencia QR, evaluaciones y diplomas.</p></div>",unsafe_allow_html=True)
 with st.form('login'):
  e=st.text_input('Email');p=st.text_input('Contrasena',type='password');ok=st.form_submit_button('Entrar',type='primary')
 if ok:
  x=one('SELECT * FROM users WHERE email=?',(e.lower().strip(),))
  if x and vp(p,x['password']):st.session_state.uid=x['id'];refresh()
  else:st.error('Credenciales incorrectas')
 st.stop()
if st.sidebar.button('Cerrar sesion'):st.session_state.clear();refresh()
if u['role']=='student':
 st.markdown(f"<div class='hero'><h1>Hola, {u['name']}</h1><p>Completa tus tests y descarga los diplomas.</p></div>",unsafe_allow_html=True)
 for s in all('SELECT s.* FROM sessions s JOIN attendance a ON a.session_id=s.id WHERE a.user_id=?',(u['id'],)):
  with st.container(border=True):
   st.subheader(f"{s['training_date']} · {s['location']}")
   for mid in json.loads(s['module_ids']):
    m=one('SELECT * FROM modules WHERE id=?',(mid,));r=one('SELECT * FROM results WHERE user_id=? AND session_id=? AND module_id=?',(u['id'],s['id'],mid))
    if not m:continue
    st.write(f"**{m['title']}**")
    if r and r['passed']:st.success(f"Superado: {r['score']}%");st.download_button('Descargar diploma',diploma(r),f"diploma-{m['title']}.pdf",'application/pdf',key=f"d{r['id']}")
    elif st.button('Iniciar test',key=f"t{s['id']}-{mid}"):st.session_state.test=(s['id'],mid);refresh()
 if st.session_state.get('test'):
  sid,mid=st.session_state.test;m=one('SELECT * FROM modules WHERE id=?',(mid,));qs=all('SELECT * FROM questions WHERE module_id=?',(mid,));st.header('Test: '+m['title'])
  with st.form('test'):
   ans={q['id']:st.radio(q['text'],json.loads(q['options']),index=None,key=f"q{q['id']}") for q in qs};ok=st.form_submit_button('Enviar',type='primary')
  if ok and all(v is not None for v in ans.values()):
   score=round(sum(json.loads(q['options']).index(ans[q['id']])==q['correct'] for q in qs)*100/len(qs)) if qs else 100;passed=int(score>=m['pass_score']);run('INSERT INTO results(user_id,session_id,module_id,score,passed,completed_at) VALUES(?,?,?,?,?,?) ON CONFLICT(user_id,session_id,module_id) DO UPDATE SET score=max(score,excluded.score),passed=max(passed,excluded.passed)',(u['id'],sid,mid,score,passed,datetime.now().isoformat()));del st.session_state.test;refresh()
 st.stop()
# Administracion
st.markdown("<div class='hero'><h1>Administracion LMS</h1><p>Gestion integral de la formacion.</p></div>",unsafe_allow_html=True)
a,b,c,d,e=st.tabs(['Modulos','Formadores','Sesiones y QR','Tests','Configuracion'])
with a:
 with st.form('mod',clear_on_submit=True):
  title=st.text_input('Titulo');syn=st.text_area('Sinopsis');score=st.number_input('Nota minima',0,100,70);logo=st.file_uploader('Logo',type=['png','jpg','jpeg']);att=st.file_uploader('Adjunto');ok=st.form_submit_button('Crear',type='primary')
 if ok and title:run('INSERT INTO modules(title,synopsis,logo,attachment,pass_score) VALUES(?,?,?,?,?)',(title,syn,save(logo),save(att),score));refresh()
 st.dataframe([dict(x) for x in all('SELECT id,title,synopsis,pass_score FROM modules')],use_container_width=True,hide_index=True)
with b:
 with st.form('trainer',clear_on_submit=True):
  n=st.text_input('Nombre');em=st.text_input('Email');ph=st.text_input('Telefono');ok=st.form_submit_button('Guardar')
 if ok and n:run('INSERT INTO trainers(name,email,phone) VALUES(?,?,?)',(n,em,ph));refresh()
 st.dataframe([dict(x) for x in all('SELECT * FROM trainers')],use_container_width=True,hide_index=True)
with c:
 ts=all('SELECT * FROM trainers');ms=all('SELECT * FROM modules');tm={x['name']:x['id'] for x in ts};mm={x['title']:x['id'] for x in ms}
 with st.form('session',clear_on_submit=True):
  dt=st.date_input('Fecha',date.today());loc=st.text_input('Ubicacion');mode=st.selectbox('Tipologia',['Presencial','Online','Hibrida']);t=st.multiselect('Formadores',list(tm));m=st.multiselect('Modulos',list(mm));other=st.text_input('Otros');com=st.text_area('Comentarios');ok=st.form_submit_button('Crear sesion')
 if ok and loc:run('INSERT INTO sessions VALUES(NULL,?,?,?,?,?,?,?,?)',(uuid.uuid4().hex,dt.isoformat(),loc,mode,com,other,json.dumps([tm[x] for x in t]),json.dumps([mm[x] for x in m])));refresh()
 base=st.secrets.get('APP_URL','http://localhost:8501').rstrip('/')
 for s in all('SELECT * FROM sessions ORDER BY training_date DESC'):
  with st.container(border=True):
   url=f"{base}/?join={s['token']}";im=qrcode.make(url);buf=io.BytesIO();im.save(buf,'PNG');x,y=st.columns([3,1]);x.subheader(f"{s['training_date']} · {s['location']}");x.code(url);x.download_button('Descargar QR',buf.getvalue(),f"qr-{s['id']}.png",'image/png',key=f"qr{s['id']}");y.image(buf.getvalue())
with d:
 ms=all('SELECT * FROM modules');mm={x['title']:x['id'] for x in ms}
 if ms:
  with st.form('question',clear_on_submit=True):
   mn=st.selectbox('Modulo',list(mm));q=st.text_area('Pregunta');o1=st.text_input('Opcion A');o2=st.text_input('Opcion B');o3=st.text_input('Opcion C');cor=st.selectbox('Correcta',['A','B','C']);ok=st.form_submit_button('Anadir')
  if ok and q and o1 and o2 and o3:run('INSERT INTO questions(module_id,text,options,correct) VALUES(?,?,?,?)',(mm[mn],q,json.dumps([o1,o2,o3]),['A','B','C'].index(cor)));refresh()
 st.dataframe([dict(x) for x in all('SELECT q.id,m.title modulo,q.text pregunta FROM questions q JOIN modules m ON m.id=q.module_id')],use_container_width=True)
with e:
 with st.form('config'):
  company=st.text_input('Empresa',S['company']);logo=st.file_uploader('Logo corporativo',type=['png','jpg','jpeg']);name=st.text_input('Administrador',u['name']);email=st.text_input('Email',u['email']);pwd=st.text_input('Nueva contrasena',type='password');ok=st.form_submit_button('Guardar')
 if ok:
  run('UPDATE settings SET company=?,logo=? WHERE id=1',(company,save(logo) or S['logo']));run('UPDATE users SET name=?,email=? WHERE id=?',(name,email.lower(),u['id']))
  if pwd and len(pwd)>=8:run('UPDATE users SET password=? WHERE id=?',(hp(pwd),u['id']))
  refresh()
 st.warning('SQLite y los archivos locales de Community Cloud pueden perderse tras reinicios o redespliegues. Para produccion conviene PostgreSQL/Supabase y almacenamiento de objetos.')
 st.download_button('Copia de seguridad SQLite',DB.read_bytes(),'lms.db','application/octet-stream')
