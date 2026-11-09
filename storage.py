import json
import psycopg
from psycopg.rows import dict_row
from domain import Invoice


class Store:
    def __init__(self, url):
        self.url = url

    def connect(self):
        return psycopg.connect(self.url, row_factory=dict_row, connect_timeout=10)

    def init(self):
        with self.connect() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS invoices (
              id BIGSERIAL PRIMARY KEY, owner BIGINT NOT NULL,
              digest TEXT NOT NULL, data JSONB NOT NULL,
              status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved')),
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              UNIQUE(owner,digest))''')
            conn.execute('''CREATE TABLE IF NOT EXISTS counterparties (
              id BIGSERIAL PRIMARY KEY, owner BIGINT NOT NULL,
              name TEXT NOT NULL, inn TEXT NOT NULL DEFAULT '', contract TEXT NOT NULL DEFAULT '',
              UNIQUE(owner,name))''')

    def save_party(self, owner, name, inn, contract):
        with self.connect() as conn:
            return conn.execute('''INSERT INTO counterparties(owner,name,inn,contract) VALUES(%s,%s,%s,%s)
              ON CONFLICT(owner,name) DO UPDATE SET inn=EXCLUDED.inn,contract=EXCLUDED.contract
              RETURNING *''', (owner,name,inn,contract)).fetchone()

    def parties(self, owner, query='', page=0):
        with self.connect() as conn:
            # Search literal user text, not LIKE wildcards.
            return conn.execute('''SELECT * FROM counterparties WHERE owner=%s
              AND (strpos(lower(name),lower(%s))>0 OR strpos(inn,%s)>0)
              ORDER BY id LIMIT 6 OFFSET %s''', (owner,query,query,page*5)).fetchall()

    def party(self, owner, party_id):
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM counterparties WHERE owner=%s AND id=%s', (owner,party_id)).fetchone()
        if not row:
            raise ValueError('Kontragent topilmadi')
        return row

    def seed_parties(self, owner):
        # Only the exact known 1C record from the supplied screenshot is prefilled.
        with self.connect() as conn:
            conn.execute('''INSERT INTO counterparties(owner,name,inn,contract)
              VALUES(%s,%s,%s,%s) ON CONFLICT(owner,name) DO NOTHING''',
              (owner,'Элмуродов Сарвар (снабженец)','121233663','Договор № 01.07 от 01.07.2026г.'))

    def add(self, owner, digest, invoice):
        with self.connect() as conn:
            row = conn.execute('''INSERT INTO invoices(owner,digest,data) VALUES(%s,%s,%s::jsonb)
              ON CONFLICT(owner,digest) DO NOTHING RETURNING id''',
              (owner, digest, invoice.model_dump_json())).fetchone()
            if row:
                return row['id'], False
            return conn.execute('SELECT id FROM invoices WHERE owner=%s AND digest=%s',
                                (owner,digest)).fetchone()['id'], True

    def get(self, owner, doc_id):
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM invoices WHERE owner=%s AND id=%s', (owner,doc_id)).fetchone()
        if not row:
            raise ValueError('Hujjat topilmadi')
        return Invoice.model_validate(row['data']), row['status']

    def update(self, owner, doc_id, inv):
        with self.connect() as conn:
            conn.execute("UPDATE invoices SET data=%s::jsonb,status='draft' WHERE owner=%s AND id=%s",
                         (inv.model_dump_json(),owner,doc_id))

    def approve(self, owner, doc_id):
        with self.connect() as conn:
            conn.execute("UPDATE invoices SET status='approved' WHERE owner=%s AND id=%s", (owner,doc_id))

    def approved(self, owner, day):
        with self.connect() as conn:
            rows = conn.execute("SELECT id,data FROM invoices WHERE owner=%s AND status='approved' AND data->>'document_date'=%s ORDER BY id", (owner,day)).fetchall()
        return [(r['id'],Invoice.model_validate(r['data'])) for r in rows]

    def recent(self, owner):
        with self.connect() as conn:
            return conn.execute('SELECT id,status,data FROM invoices WHERE owner=%s ORDER BY id DESC LIMIT 10', (owner,)).fetchall()
