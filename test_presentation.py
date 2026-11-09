import unittest
from decimal import Decimal
import test_domain
from presentation import summary, number, chunks, actions, party_buttons


class PresentationTests(unittest.TestCase):
    def test_readable_summary(self):
        inv = test_domain.InvoiceTests().sample()
        inv.source_supplier = 'Qog‘ozdagi nom'
        inv.supplier_inn = '121233663'
        text = summary(4,inv,'draft')
        self.assertIn('Nakladnoy #4 · 📝 qoralama',text)
        self.assertIn('03.11.2026',text)
        self.assertIn('2 blok × 250 000 = 500 000',text)
        self.assertIn('720 000 UZS (qog‘oz bilan mos)',text)
        self.assertIn('Qog‘ozdagi nom',text)
        self.assertNotIn('"items":',text)
        inv.items[0].amount = Decimal('1')
        self.assertIn('(tekshirish kerak)',summary(4,inv,'draft'))

    def test_unknowns_and_telegram_limits(self):
        from domain import Invoice
        self.assertIn('Jami: —',summary(1,Invoice(),'draft'))
        self.assertEqual(number(Decimal('0.00')),'0')
        self.assertEqual(number(Decimal('1234.50')),'1 234.5')
        for part in chunks('😀'*5000):
            self.assertLessEqual(len(part.encode('utf-16-le'))//2,4096)

    def test_buttons(self):
        rows = party_buttons(4,[{'id':8,'name':'Korxona'}],page=1,has_next=True).inline_keyboard
        self.assertEqual(rows[0][0].callback_data,'inv:choose:4:8')
        self.assertEqual(rows[-1][0].callback_data,'inv:back:4')
        self.assertEqual(actions(4,True).inline_keyboard[-1][0].callback_data,'inv:csv:4')
