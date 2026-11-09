import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
import test_domain
import bot


class FlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_choose_preserves_original_and_uses_clicker_owner(self):
        inv = test_domain.InvoiceTests().sample()
        m = SimpleNamespace(answer=AsyncMock())
        cb = SimpleNamespace(data='inv:choose:4:8',from_user=SimpleNamespace(id=123),message=m,answer=AsyncMock())
        state = SimpleNamespace(clear=AsyncMock())
        store = Mock()
        store.get.return_value = (inv,'approved')
        store.party.return_value = {'name':'1C nomi','inn':'123456789','contract':'Договор № 5'}
        with patch.object(bot,'store',store), patch.object(bot,'show',new_callable=AsyncMock) as show:
            await bot.invoice_action(cb,state)
        store.party.assert_called_once_with(123,8)
        args = store.update.call_args.args
        self.assertEqual(args[:2],(123,4))
        self.assertEqual(args[2].source_supplier,'Test')
        self.assertEqual(args[2].supplier_inn,'123456789')
        self.assertEqual(args[2].contract,'Договор № 5')
        show.assert_awaited_once_with(m,4,123)

    async def test_invalid_new_party_keeps_prompt(self):
        m = SimpleNamespace(text='bad input',answer=AsyncMock())
        state = SimpleNamespace(get_data=AsyncMock(return_value={'doc_id':4}),clear=AsyncMock())
        with patch.object(bot,'store') as store:
            await bot.party_new(m,state)
        store.save_party.assert_not_called()
        state.clear.assert_not_awaited()
        m.answer.assert_awaited_once()

    async def test_new_party_is_saved_and_assigned(self):
        inv = test_domain.InvoiceTests().sample()
        m = SimpleNamespace(text='123456789; Korxona; Договор № 9',from_user=SimpleNamespace(id=123),answer=AsyncMock())
        state = SimpleNamespace(get_data=AsyncMock(return_value={'doc_id':4}),clear=AsyncMock())
        store = Mock()
        store.get.return_value = (inv,'draft')
        store.save_party.return_value = {'name':'Korxona','inn':'123456789','contract':'Договор № 9'}
        with patch.object(bot,'store',store), patch.object(bot,'show',new_callable=AsyncMock):
            await bot.party_new(m,state)
        store.save_party.assert_called_once_with(123,'Korxona','123456789','Договор № 9')
        self.assertEqual(store.update.call_args.args[2].supplier,'Korxona')
        state.clear.assert_awaited_once()
