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
