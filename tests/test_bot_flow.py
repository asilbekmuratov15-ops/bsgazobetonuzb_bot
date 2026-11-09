import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import test_domain

from app.config import Settings
from app.context import BotContext
from app.handlers import callbacks, counterparties, uploads


class FlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_uses_injected_groq_and_shows_photo_card(self):
        import io

        # A real tiny PNG is used to exercise MIME validation before the OCR mock.
        from PIL import Image

        image = Image.new("RGB", (1, 1))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        png = buffer.getvalue()
        inv = test_domain.InvoiceTests().sample()
        store = Mock()
        store.add.return_value = (4, False)
        ctx = BotContext(Settings(groq_api_key="test-key"), store)
        m = SimpleNamespace(
            photo=[SimpleNamespace(file_size=len(png))],
            from_user=SimpleNamespace(id=123),
            answer=AsyncMock(),
        )

        async def download(obj, destination):
            destination.write(png)

        bot = SimpleNamespace(download=AsyncMock(side_effect=download))
        state = SimpleNamespace(clear=AsyncMock())
        with (
            patch.object(uploads, "extract", new_callable=AsyncMock, return_value=inv) as extract,
            patch.object(uploads, "show", new_callable=AsyncMock) as show,
        ):
            await uploads.image_cmd(m, bot, state, ctx)
        extract.assert_awaited_once_with(png, "image/png", "test-key", ctx.settings.groq_model)
        self.assertEqual(store.add.call_args.args[2].source_supplier, "Test")
        show.assert_awaited_once_with(m, 4, selecting=True, reply_to=True, ctx=ctx)

    async def test_choose_preserves_original_and_uses_clicker_owner(self):
        inv = test_domain.InvoiceTests().sample()
        m = SimpleNamespace(answer=AsyncMock())
        cb = SimpleNamespace(
            data="inv:choose:4:8", from_user=SimpleNamespace(id=123), message=m, answer=AsyncMock()
        )
        state = SimpleNamespace(clear=AsyncMock())
        store = Mock()
        store.get.return_value = (inv, "approved")
        store.party.return_value = {
            "name": "1C nomi",
            "inn": "123456789",
            "contract": "Договор № 5",
        }
        ctx = BotContext(Settings(), store)
        with patch.object(callbacks, "show", new_callable=AsyncMock) as show:
            await callbacks.invoice_action(cb, state, ctx)
        store.party.assert_called_once_with(123, 8)
        args = store.update.call_args.args
        self.assertEqual(args[:2], (123, 4))
        self.assertEqual(args[2].source_supplier, "Test")
        self.assertEqual(args[2].supplier_inn, "123456789")
        self.assertEqual(args[2].contract, "Договор № 5")
        show.assert_awaited_once_with(m, 4, 123, ctx=ctx)

    async def test_invalid_new_party_keeps_prompt(self):
        m = SimpleNamespace(text="bad input", answer=AsyncMock())
        state = SimpleNamespace(get_data=AsyncMock(return_value={"doc_id": 4}), clear=AsyncMock())
        store = Mock()
        ctx = BotContext(Settings(), store)
        with patch.object(counterparties, "show", new_callable=AsyncMock):
            await counterparties.party_new(m, state, ctx)
        store.save_party.assert_not_called()
        state.clear.assert_not_awaited()
        m.answer.assert_awaited_once()

    async def test_new_party_is_saved_and_assigned(self):
        inv = test_domain.InvoiceTests().sample()
        m = SimpleNamespace(
            text="123456789; Korxona; Договор № 9",
            from_user=SimpleNamespace(id=123),
            answer=AsyncMock(),
        )
        state = SimpleNamespace(get_data=AsyncMock(return_value={"doc_id": 4}), clear=AsyncMock())
        store = Mock()
        store.get.return_value = (inv, "draft")
        store.save_party.return_value = {
            "name": "Korxona",
            "inn": "123456789",
            "contract": "Договор № 9",
        }
        ctx = BotContext(Settings(), store)
        with patch.object(counterparties, "show", new_callable=AsyncMock):
            await counterparties.party_new(m, state, ctx)
        store.save_party.assert_called_once_with(123, "Korxona", "123456789", "Договор № 9")
        self.assertEqual(store.update.call_args.args[2].supplier, "Korxona")
        state.clear.assert_awaited_once()
