# Basic School Management App in Tkinter
import sqlite3
import os
import datetime
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import json
import requests

DB_PATH = os.path.join(os.path.dirname(__file__), 'school.db')
LAST_USER_FILE = os.path.join(os.path.dirname(__file__), 'last_user.txt')
DEFAULT_W, DEFAULT_H = 500, 400
MASTER_USER = 'master'
MASTER_PASS = 'master'

CADASTRO_COLUMNS = [
    'matricula', 'data_matricula', 'nome', 'data_nascimento', 'idade',
    'responsavel', 'cpf', 'rg', 'tel_principal', 'tel_recado', 'cep',
    'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'email',
    'instagram', 'turma_id', 'curso_id', 'material_id', 'vencimento', 'valor_id'
]

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS turmas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        horario TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS cursos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS materiais(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        valor REAL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS valores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT,
        valor REAL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS estoque(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        quantidade INTEGER
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS cadastro(
        matricula INTEGER PRIMARY KEY AUTOINCREMENT,
        data_matricula TEXT,
        nome TEXT,
        data_nascimento TEXT,
        idade INTEGER,
        responsavel TEXT,
        cpf TEXT,
        rg TEXT,
        tel_principal TEXT,
        tel_recado TEXT,
        cep TEXT,
        logradouro TEXT,
        numero TEXT,
        complemento TEXT,
        bairro TEXT,
        cidade TEXT,
        email TEXT,
        instagram TEXT,
        turma_id INTEGER,
        curso_id INTEGER,
        material_id INTEGER,
        vencimento TEXT,
        valor_id INTEGER
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS financeiro(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula INTEGER,
        valor REAL,
        vencimento TEXT,
        forma_pagamento TEXT,
        anexo TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        table_name TEXT,
        record_id TEXT,
        timestamp TEXT
    )''')
    cur.execute("INSERT OR IGNORE INTO users(username, password) VALUES (?, ?)", (MASTER_USER, MASTER_PASS))
    conn.commit()
    conn.close()

# --- Helper Functions ---
def save_last_user(username):
    with open(LAST_USER_FILE, 'w') as f:
        f.write(username)


def load_last_user():
    if os.path.exists(LAST_USER_FILE):
        with open(LAST_USER_FILE) as f:
            return f.read().strip()
    return ''


def is_master(username):
    return username == MASTER_USER


def cep_lookup(cep, street_var, bairro_var, cidade_var):
    try:
        r = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
        if r.status_code == 200:
            data = r.json()
            street_var.set(data.get('logradouro', ''))
            bairro_var.set(data.get('bairro', ''))
            cidade_var.set(data.get('localidade', ''))
    except Exception as e:
        messagebox.showerror('Erro', f'Falha ao consultar CEP: {e}')


def apply_mask(entry, pattern):
    digits = ''.join(filter(str.isdigit, entry.get()))
    result = ''
    di = 0
    for ch in pattern:
        if ch == '#':
            if di < len(digits):
                result += digits[di]
                di += 1
            else:
                break
        else:
            if di < len(digits):
                result += ch
            else:
                break
    entry.delete(0, END)
    entry.insert(0, result)
    entry.icursor(len(result))


def mask_date(entry):
    apply_mask(entry, '##/##/####')


def mask_cpf(entry):
    apply_mask(entry, '###.###.###-##')


def mask_phone(entry):
    apply_mask(entry, '(##) #####-####')


def mask_cep(entry):
    apply_mask(entry, '#####-###')


def center_window(win, w=DEFAULT_W, h=DEFAULT_H):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def make_fullscreen(win):
    win.update_idletasks()
    win.attributes('-fullscreen', True)


def apply_apple_style(win):
    style = ttk.Style(win)
    try:
        style.theme_use('clam')
    except Exception:
        pass
    default_font = ('Helvetica', 12)
    style.configure('.', font=default_font, background='white')
    style.configure('TButton', padding=6, background='#e0e0e0')
    # Quote font family so Tk can parse names with spaces like "Helvetica"
    win.option_add('*Font', '{Helvetica} 12')
    win.configure(bg='white')


def log_action(user, action, table_name, record_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''INSERT INTO logs(username, action, table_name, record_id, timestamp)
                   VALUES(?,?,?,?,?)''', (
        user, action, table_name, str(record_id), datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


# --- GUI Classes ---
class LoginWindow(Tk):
    def __init__(self):
        super().__init__()
        self.title('Login')
        apply_apple_style(self)
        make_fullscreen(self)
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.confirm_exit)

        last_user = load_last_user()

        Label(self, text='Bem-vindo!').pack(pady=5)
        Label(self, text='Usuário').pack()
        self.user_var = StringVar(value=last_user)
        Entry(self, textvariable=self.user_var).pack()

        Label(self, text='Senha').pack()
        self.pass_var = StringVar()
        self.pass_entry = Entry(self, textvariable=self.pass_var, show='*')
        self.pass_entry.pack()
        self.pass_entry.bind('<Return>', lambda e: self.login())

        Button(self, text='Entrar', command=self.login).pack(pady=5)
        Button(self, text='Esqueci a senha', command=self.recover).pack()

    def login(self):
        user = self.user_var.get().strip()
        pwd = self.pass_var.get().strip()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT password FROM users WHERE username=?', (user,))
        row = cur.fetchone()
        conn.close()
        if row and row[0] == pwd:
            save_last_user(user)
            self.destroy()
            app = MainApp(user)
            app.mainloop()
        else:
            messagebox.showerror('Erro', 'Usuário ou senha inválidos')

    def recover(self):
        RecoveryWindow()

    def confirm_exit(self):
        if messagebox.askyesno('Sair', 'Deseja realmente sair?'):
            self.destroy()


class MainApp(Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title('Sistema Escolar')
        apply_apple_style(self)
        make_fullscreen(self)
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        Label(self, text=f'Usuário logado: {self.user}').pack(anchor='e')
        Button(self, text='Bloquear', command=self.lock, width=10).pack(anchor='e')

        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True)

        self.cadastro_tab = CadastroTab(nb, self.user)
        nb.add(self.cadastro_tab, text='Cadastro')

        self.matriculas_tab = MatriculasTab(nb, self.user)
        nb.add(self.matriculas_tab, text='Matrículas')

        self.turmas_tab = CrudTab(nb, 'turmas', self.user, (('nome', 'Nome'), ('horario', 'Horário')))
        nb.add(self.turmas_tab, text='Turmas')

        self.cursos_tab = CrudTab(nb, 'cursos', self.user, (('nome', 'Nome'),))
        nb.add(self.cursos_tab, text='Cursos')

        self.materiais_tab = CrudTab(nb, 'materiais', self.user, (('nome', 'Nome'), ('valor', 'Valor')))
        nb.add(self.materiais_tab, text='Materiais didáticos')

        self.valores_tab = CrudTab(nb, 'valores', self.user, (('descricao', 'Descrição'), ('valor', 'Valor')))
        nb.add(self.valores_tab, text='Valores')

        self.estoque_tab = CrudTab(nb, 'estoque', self.user, (('nome', 'Nome'), ('quantidade', 'Qtd')))
        nb.add(self.estoque_tab, text='Estoque')

        self.financeiro_tab = FinanceiroTab(nb, self.user)
        nb.add(self.financeiro_tab, text='Financeiro')

        self.users_tab = UsersTab(nb, self.user)
        nb.add(self.users_tab, text='Gerenciamento de Usuários')

        self.logs_tab = LogsTab(nb)
        nb.add(self.logs_tab, text='Logs')

    def lock(self):
        self.destroy()
        LoginWindow().mainloop()

    def on_close(self):
        if messagebox.askyesno('Sair', 'Deseja realmente sair?'):
            self.destroy()


class CadastroTab(Frame):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user
        self.build_form()

    def build_form(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT id, nome FROM turmas')
        turmas = cur.fetchall()
        cur.execute('SELECT id, nome FROM cursos')
        cursos = cur.fetchall()
        cur.execute('SELECT id, nome FROM materiais')
        mats = cur.fetchall()
        cur.execute('SELECT id, descricao FROM valores')
        valores = cur.fetchall()
        conn.close()

        row = 0
        Label(self, text='Nome completo').grid(row=row, column=0, sticky=W)
        self.nome_var = StringVar()
        Entry(self, textvariable=self.nome_var, width=40).grid(row=row, column=1)
        row += 1

        self.resp_var = StringVar()
        self.resp_chk = IntVar()
        Checkbutton(self, text='Responsável é o mesmo', variable=self.resp_chk, command=self.sync_resp).grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.resp_var, width=40).grid(row=row, column=1)
        row += 1

        Label(self, text='Data de nascimento (dd/mm/aaaa)').grid(row=row, column=0, sticky=W)
        self.nasc_var = StringVar()
        self.nasc_entry = Entry(self, textvariable=self.nasc_var)
        self.nasc_entry.grid(row=row, column=1)
        self.nasc_entry.bind('<KeyRelease>', lambda e: (mask_date(self.nasc_entry), self.update_age()))
        row += 1

        Label(self, text='Idade').grid(row=row, column=0, sticky=W)
        self.idade_var = StringVar()
        Entry(self, textvariable=self.idade_var, state='readonly').grid(row=row, column=1)
        row += 1

        Label(self, text='CPF').grid(row=row, column=0, sticky=W)
        self.cpf_var = StringVar()
        self.cpf_entry = Entry(self, textvariable=self.cpf_var)
        self.cpf_entry.grid(row=row, column=1)
        self.cpf_entry.bind('<KeyRelease>', lambda e: mask_cpf(self.cpf_entry))
        row += 1

        Label(self, text='Telefone principal').grid(row=row, column=0, sticky=W)
        self.tel_var = StringVar()
        self.tel_entry = Entry(self, textvariable=self.tel_var)
        self.tel_entry.grid(row=row, column=1)
        self.tel_entry.bind('<KeyRelease>', lambda e: mask_phone(self.tel_entry))
        row += 1

        Label(self, text='Telefone recado').grid(row=row, column=0, sticky=W)
        self.tel2_var = StringVar()
        self.tel2_entry = Entry(self, textvariable=self.tel2_var)
        self.tel2_entry.grid(row=row, column=1)
        self.tel2_entry.bind('<KeyRelease>', lambda e: mask_phone(self.tel2_entry))
        row += 1

        Label(self, text='CEP').grid(row=row, column=0, sticky=W)
        self.cep_var = StringVar()
        self.cep_entry = Entry(self, textvariable=self.cep_var)
        self.cep_entry.grid(row=row, column=1)
        self.cep_entry.bind('<KeyRelease>', lambda e: mask_cep(self.cep_entry))
        Button(self, text='Buscar', command=lambda: cep_lookup(self.cep_var.get(), self.log_var, self.bairro_var, self.cidade_var)).grid(row=row, column=2)
        row += 1

        Label(self, text='Logradouro').grid(row=row, column=0, sticky=W)
        self.log_var = StringVar()
        Entry(self, textvariable=self.log_var, width=40).grid(row=row, column=1)
        row += 1

        Label(self, text='Número').grid(row=row, column=0, sticky=W)
        self.num_var = StringVar()
        Entry(self, textvariable=self.num_var).grid(row=row, column=1)
        row += 1

        Label(self, text='Complemento').grid(row=row, column=0, sticky=W)
        self.comp_var = StringVar()
        Entry(self, textvariable=self.comp_var).grid(row=row, column=1)
        row += 1

        Label(self, text='Bairro').grid(row=row, column=0, sticky=W)
        self.bairro_var = StringVar()
        Entry(self, textvariable=self.bairro_var).grid(row=row, column=1)
        row += 1

        Label(self, text='Cidade').grid(row=row, column=0, sticky=W)
        self.cidade_var = StringVar()
        Entry(self, textvariable=self.cidade_var).grid(row=row, column=1)
        row += 1

        Label(self, text='E-mail').grid(row=row, column=0, sticky=W)
        self.email_var = StringVar()
        Entry(self, textvariable=self.email_var, width=40).grid(row=row, column=1)
        row += 1

        Label(self, text='Instagram').grid(row=row, column=0, sticky=W)
        self.inst_var = StringVar()
        Entry(self, textvariable=self.inst_var, width=40).grid(row=row, column=1)
        row += 1

        Label(self, text='Turma').grid(row=row, column=0, sticky=W)
        self.turma_var = StringVar()
        ttk.Combobox(self, textvariable=self.turma_var, values=[f'{t[0]} - {t[1]}' for t in turmas]).grid(row=row, column=1)
        row += 1

        Label(self, text='Curso').grid(row=row, column=0, sticky=W)
        self.curso_var = StringVar()
        ttk.Combobox(self, textvariable=self.curso_var, values=[f'{c[0]} - {c[1]}' for c in cursos]).grid(row=row, column=1)
        row += 1

        Label(self, text='Material didático').grid(row=row, column=0, sticky=W)
        self.mat_var = StringVar()
        ttk.Combobox(self, textvariable=self.mat_var, values=[f'{m[0]} - {m[1]}' for m in mats]).grid(row=row, column=1)
        row += 1

        Label(self, text='Valor').grid(row=row, column=0, sticky=W)
        self.valor_var = StringVar()
        ttk.Combobox(self, textvariable=self.valor_var, values=[f'{v[0]} - {v[1]}' for v in valores]).grid(row=row, column=1)
        row += 1

        Button(self, text='Salvar', command=self.save).grid(row=row, column=1, pady=10)

    def sync_resp(self):
        if self.resp_chk.get():
            self.resp_var.set(self.nome_var.get())
        else:
            self.resp_var.set('')

    def update_age(self):
        self.idade_var.set(str(self.calc_idade(self.nasc_var.get())))

    def calc_idade(self, nasc):
        try:
            d = datetime.datetime.strptime(nasc, '%d/%m/%Y').date()
            today = datetime.date.today()
            return today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        except ValueError:
            return 0

    def save(self):
        idade = self.calc_idade(self.nasc_var.get())
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('''INSERT INTO cadastro(
            data_matricula, nome, data_nascimento, idade, responsavel, cpf, rg,
            tel_principal, tel_recado, cep, logradouro, numero, complemento,
            bairro, cidade, email, instagram, turma_id, curso_id, material_id,
            valor_id)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                datetime.date.today().isoformat(),
                self.nome_var.get(),
                self.nasc_var.get(),
                idade,
                self.resp_var.get(),
                self.cpf_var.get(),
                '',  # rg not implemented
                self.tel_var.get(),
                self.tel2_var.get(),
                self.cep_var.get(),
                self.log_var.get(),
                self.num_var.get(),
                self.comp_var.get(),
                self.bairro_var.get(),
                self.cidade_var.get(),
                self.email_var.get(),
                self.inst_var.get(),
                self.get_id(self.turma_var.get()),
                self.get_id(self.curso_var.get()),
                self.get_id(self.mat_var.get()),
                self.get_id(self.valor_var.get())
        ))
        conn.commit()
        record_id = cur.lastrowid
        conn.close()
        log_action(self.user, 'add', 'cadastro', record_id)
        messagebox.showinfo('Sucesso', 'Cadastro salvo')
        self.clear()
        self.master.master.matriculas_tab.refresh()

    def get_id(self, value):
        if not value:
            return None
        return int(value.split(' - ')[0])

    def clear(self):
        for var in [self.nome_var, self.resp_var, self.nasc_var, self.cpf_var,
                    self.tel_var, self.tel2_var, self.cep_var, self.log_var,
                    self.num_var, self.comp_var, self.bairro_var,
                    self.cidade_var, self.email_var, self.inst_var,
                    self.turma_var, self.curso_var, self.mat_var,
                    self.valor_var, self.idade_var]:
            var.set('')
        self.resp_chk.set(0)


class MatriculasTab(Frame):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user
        self.tree = ttk.Treeview(self, columns=('matricula', 'nome', 'turma', 'curso'))
        self.tree.heading('#0', text='ID')
        self.tree.heading('matricula', text='Matrícula')
        self.tree.heading('nome', text='Nome')
        self.tree.heading('turma', text='Turma')
        self.tree.heading('curso', text='Curso')
        self.tree.column('#0', width=30)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', self.open_details)
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('''SELECT c.matricula, c.nome, t.nome, s.nome
            FROM cadastro c LEFT JOIN turmas t ON c.turma_id=t.id
            LEFT JOIN cursos s ON c.curso_id=s.id''')
        for row in cur.fetchall():
            self.tree.insert('', 'end', text=row[0], values=row)
        conn.close()

    def open_details(self, event):
        item = self.tree.selection()[0]
        matricula = self.tree.item(item, 'text')
        DetailWindow(matricula, self.user)


class DetailWindow(Toplevel):
    def __init__(self, matricula, user):
        super().__init__()
        self.title(f'Detalhes {matricula}')
        apply_apple_style(self)
        make_fullscreen(self)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT * FROM cadastro WHERE matricula=?', (matricula,))
        data = cur.fetchone()
        conn.close()
        for i, (col, val) in enumerate(zip(CADASTRO_COLUMNS, data)):
            Label(self, text=col.replace('_', ' ').title()+':').grid(row=i, column=0, sticky=W)
            Entry(self, state='readonly', width=40, readonlybackground='white',
                  fg='black',
                  textvariable=StringVar(value='' if val is None else str(val))).grid(row=i, column=1)
        Button(self, text='Editar', command=lambda: self.edit(matricula, user)).grid(row=len(CADASTRO_COLUMNS), column=1, pady=10)

    def edit(self, matricula, user):
        if not is_master(user):
            messagebox.showerror('Erro', 'Acesso negado')
            return
        EditWindow(matricula, user)


class EditWindow(Toplevel):
    def __init__(self, matricula, user):
        super().__init__()
        self.title('Editar Cadastro')
        apply_apple_style(self)
        make_fullscreen(self)
        self.matricula = matricula
        self.user = user
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT * FROM cadastro WHERE matricula=?', (matricula,))
        data = cur.fetchone()
        conn.close()
        self.vars = {}
        for i, (col, val) in enumerate(zip(CADASTRO_COLUMNS[1:], data[1:])):
            Label(self, text=col.replace('_', ' ').title()+':').grid(row=i, column=0, sticky=W)
            var = StringVar(value='' if val is None else str(val))
            ent = Entry(self, textvariable=var)
            ent.grid(row=i, column=1)
            if col == 'data_nascimento':
                ent.bind('<KeyRelease>', lambda e, w=ent: mask_date(w))
            elif col in ('cpf',):
                ent.bind('<KeyRelease>', lambda e, w=ent: mask_cpf(w))
            elif col in ('tel_principal', 'tel_recado'):
                ent.bind('<KeyRelease>', lambda e, w=ent: mask_phone(w))
            elif col == 'cep':
                ent.bind('<KeyRelease>', lambda e, w=ent: mask_cep(w))
            self.vars[col] = var
        Button(self, text='Salvar', command=self.save).grid(row=len(self.vars)+1, column=1, pady=10)

    def save(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cols = ', '.join([f"{c}=?" for c in self.vars.keys()])
        values = [v.get() for v in self.vars.values()] + [self.matricula]
        cur.execute(f'UPDATE cadastro SET {cols} WHERE matricula=?', values)
        conn.commit()
        conn.close()
        messagebox.showinfo('Sucesso', 'Atualizado')
        log_action(self.user, 'edit', 'cadastro', self.matricula)
        self.destroy()


class CrudTab(Frame):
    def __init__(self, master, table, user, fields):
        super().__init__(master)
        self.table = table
        self.user = user
        self.fields = fields
        self.build()

    def build(self):
        self.entries = {}
        row = 0
        for name, label in self.fields:
            Label(self, text=label).grid(row=row, column=0, sticky=W)
            var = StringVar()
            Entry(self, textvariable=var).grid(row=row, column=1)
            self.entries[name] = var
            row += 1
        Button(self, text='Adicionar', command=self.add).grid(row=row, column=0, pady=10)
        Button(self, text='Atualizar Lista', command=self.refresh).grid(row=row, column=1)
        self.tree = ttk.Treeview(self, columns=[f[0] for f in self.fields], show='headings')
        for f in self.fields:
            self.tree.heading(f[0], text=f[1])
        self.tree.grid(row=row+1, column=0, columnspan=2, sticky='nsew')
        self.refresh()

    def add(self):
        if not is_master(self.user):
            messagebox.showerror('Erro', 'Acesso negado')
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cols = ','.join(self.entries.keys())
        vals = [v.get() for v in self.entries.values()]
        placeholders = ','.join(['?'] * len(vals))
        cur.execute(f'INSERT INTO {self.table}({cols}) VALUES ({placeholders})', vals)
        conn.commit()
        record_id = cur.lastrowid
        conn.close()
        log_action(self.user, 'add', self.table, record_id)
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(f'SELECT rowid, * FROM {self.table}')
        for row in cur.fetchall():
            self.tree.insert('', 'end', text=row[0], values=row[1:])
        conn.close()


class FinanceiroTab(Frame):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user
        self.build()

    def build(self):
        Label(self, text='Matrícula').grid(row=0, column=0)
        self.matric_var = StringVar()
        Entry(self, textvariable=self.matric_var).grid(row=0, column=1)
        Label(self, text='Valor').grid(row=1, column=0)
        self.val_var = StringVar()
        Entry(self, textvariable=self.val_var).grid(row=1, column=1)
        Label(self, text='Vencimento').grid(row=2, column=0)
        self.venc_var = StringVar()
        Entry(self, textvariable=self.venc_var).grid(row=2, column=1)
        Label(self, text='Forma de pagamento').grid(row=3, column=0)
        self.forma_var = StringVar()
        Entry(self, textvariable=self.forma_var).grid(row=3, column=1)
        Button(self, text='Anexar Arquivo', command=self.attach).grid(row=4, column=0)
        self.anexo_var = StringVar()
        Entry(self, textvariable=self.anexo_var, state='readonly').grid(row=4, column=1)
        Button(self, text='Salvar', command=self.save).grid(row=5, column=1)
        self.tree = ttk.Treeview(self, columns=('matric', 'valor', 'venc', 'forma', 'anexo'))
        for col in ('matric', 'valor', 'venc', 'forma', 'anexo'):
            self.tree.heading(col, text=col)
        self.tree.grid(row=6, column=0, columnspan=2)
        self.refresh()

    def attach(self):
        f = filedialog.askopenfilename()
        if f:
            self.anexo_var.set(f)

    def save(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('''INSERT INTO financeiro(matricula, valor, vencimento, forma_pagamento, anexo)
            VALUES(?,?,?,?,?)''', (
            self.matric_var.get(),
            self.val_var.get(),
            self.venc_var.get(),
            self.forma_var.get(),
            self.anexo_var.get()
        ))
        conn.commit()
        record_id = cur.lastrowid
        conn.close()
        log_action(self.user, 'add', 'financeiro', record_id)
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT matricula, valor, vencimento, forma_pagamento, anexo FROM financeiro')
        for row in cur.fetchall():
            self.tree.insert('', 'end', values=row)
        conn.close()


class UsersTab(Frame):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user
        self.build()

    def build(self):
        Label(self, text='Usuário').grid(row=0, column=0)
        self.user_var = StringVar()
        Entry(self, textvariable=self.user_var).grid(row=0, column=1)
        Label(self, text='Senha').grid(row=1, column=0)
        self.pass_var = StringVar()
        Entry(self, textvariable=self.pass_var).grid(row=1, column=1)
        Button(self, text='Adicionar', command=self.add).grid(row=2, column=1)
        self.tree = ttk.Treeview(self, columns=('user',))
        self.tree.heading('user', text='Usuário')
        self.tree.grid(row=3, column=0, columnspan=2)
        self.refresh()

    def add(self):
        if not is_master(self.user):
            messagebox.showerror('Erro', 'Acesso negado')
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('INSERT INTO users(username, password) VALUES (?, ?)', (self.user_var.get(), self.pass_var.get()))
        conn.commit()
        conn.close()
        log_action(self.user, 'add', 'users', self.user_var.get())
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT username FROM users')
        for row in cur.fetchall():
            self.tree.insert('', 'end', values=row)
        conn.close()


class RecoveryWindow(Toplevel):
    def __init__(self):
        super().__init__()
        self.title('Recuperar Senha')
        apply_apple_style(self)
        make_fullscreen(self)
        Label(self, text='Usuário').pack()
        self.user_var = StringVar()
        Entry(self, textvariable=self.user_var).pack()
        Label(self, text='Código master').pack()
        self.code_var = StringVar()
        Entry(self, textvariable=self.code_var, show='*').pack()
        Label(self, text='Nova senha').pack()
        self.pass_var = StringVar()
        Entry(self, textvariable=self.pass_var, show='*').pack()
        Button(self, text='Confirmar', command=self.reset).pack(pady=10)

    def reset(self):
        if self.code_var.get() != '587707':
            messagebox.showerror('Erro', 'Código inválido')
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('UPDATE users SET password=? WHERE username=?', (self.pass_var.get(), self.user_var.get()))
        if cur.rowcount:
            conn.commit()
            messagebox.showinfo('Sucesso', 'Senha atualizada')
            self.destroy()
        else:
            messagebox.showerror('Erro', 'Usuário não encontrado')
        conn.close()


class LogsTab(Frame):
    def __init__(self, master):
        super().__init__(master)
        Label(self, text='Filtrar por usuário').grid(row=0, column=0)
        self.filter_var = StringVar()
        Entry(self, textvariable=self.filter_var).grid(row=0, column=1)
        Button(self, text='Buscar', command=self.refresh).grid(row=0, column=2)
        self.tree = ttk.Treeview(self, columns=('user','action','table','record','time'))
        for c, l in zip(('user','action','table','record','time'), ['Usuário','Ação','Tabela','Registro','Data']):
            self.tree.heading(c, text=l)
        self.tree.grid(row=1, column=0, columnspan=3, sticky='nsew')
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        if self.filter_var.get():
            cur.execute('SELECT username, action, table_name, record_id, timestamp FROM logs WHERE username=?', (self.filter_var.get(),))
        else:
            cur.execute('SELECT username, action, table_name, record_id, timestamp FROM logs')
        for row in cur.fetchall():
            self.tree.insert('', 'end', values=row)
        conn.close()


if __name__ == '__main__':
    init_db()
    LoginWindow().mainloop()
