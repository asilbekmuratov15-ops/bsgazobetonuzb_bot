import unittest
from datetime import date
from decimal import Decimal
from domain import Invoice, Item, problems, export_csv


class InvoiceTests(unittest.TestCase):
    def sample(self):
        return Invoice(document_date=date(2026,11,3),supplier='Test',warehouse='Ombor',contract='Shartnoma',total=720000,items=[
            Item(name='A4',unit='blok',quantity=2,price=250000,amount=500000),
            Item(name='Daftar',unit='sht',quantity=4,price=35000,amount=140000),
            Item(name='Papka',unit='sht',quantity=2,price=40000,amount=80000)])

    def test_total(self):
        inv = self.sample()
        self.assertEqual(problems(inv),[])
        inv.items[0].amount = Decimal('50')
        self.assertEqual(len(problems(inv)),2)
        with self.assertRaises(ValueError):
            export_csv([(1,inv)])

    def test_csv(self):
        inv = self.sample()
        inv.items[0].name = '=BAD;"test"'
        raw = export_csv([(1,inv)])
        self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
        import csv, io
        rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'))
        self.assertEqual(len(rows),4)
        self.assertIn("'=BAD;\"test\"",rows[1])
        self.assertEqual(rows[1][-1],'720000')

    def test_missing(self):
        self.assertTrue(problems(Invoice()))


if __name__ == '__main__':
    unittest.main()
