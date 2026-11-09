"""Exercise real router/filter/middleware wiring without contacting Telegram."""

import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

from aiogram import Bot
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from app.config import Settings
from app.context import BotContext
from app.factory import create_dispatcher
from app.models.invoice import Invoice
from app.ui.views import show


class DispatcherTests(unittest.IsolatedAsyncioTestCase):
    async def test_commands_access_and_callbacks_use_injected_context(self):
        store = Mock()
        store.get.return_value = (Invoice(), "draft")
        ctx = BotContext(Settings(allowed_user_ids=frozenset({123})), store)
        dp = create_dispatcher(ctx)
        bot = Bot("123:TEST")
        bot.session.make_request = AsyncMock(return_value=True)

        def message(text, user_id=123):
            return Message(
                message_id=1,
                date=datetime.now(timezone.utc),
                chat=Chat(id=123, type="private"),
                from_user=User(id=user_id, is_bot=False, first_name="Test"),
                text=text,
            )

        try:
            await dp.feed_update(bot, Update(update_id=1, message=message("/show 4")))
            store.get.assert_called_once_with(123, 4)
            sent = bot.session.make_request.call_args.args[1]
            self.assertIn("Nakladnoy #4", sent.text)
            self.assertIsNotNone(sent.reply_markup)
            store.get.reset_mock()
            await dp.feed_update(bot, Update(update_id=2, message=message("/show 4", 999)))
            store.get.assert_not_called()
            await dp.feed_update(
                bot,
                Update(
                    update_id=3,
                    callback_query=CallbackQuery(
                        id="test",
                        from_user=User(id=123, is_bot=False, first_name="Test"),
                        chat_instance="test",
                        message=message("Card"),
                        data="inv:back:4",
                    ),
                ),
            )
            store.get.assert_called_with(123, 4)
        finally:
            await dp.storage.close()
            await bot.session.close()

    async def test_photo_card_has_reply_and_party_picker(self):
        from types import SimpleNamespace

        store = Mock()
        store.get.return_value = (Invoice(supplier="Test"), "draft")
        store.parties.return_value = [{"id": 8, "name": "Korxona"}]
        ctx = BotContext(Settings(), store)
        m = SimpleNamespace(message_id=17, from_user=SimpleNamespace(id=123), answer=AsyncMock())
        await show(m, 4, selecting=True, reply_to=True, ctx=ctx)
        args, kwargs = m.answer.call_args
        self.assertIn("Kontragent: Test", args[0])
        self.assertEqual(kwargs["reply_parameters"].message_id, 17)
        rows = kwargs["reply_markup"].inline_keyboard
        self.assertEqual(rows[0][0].text, "Korxona")
        self.assertEqual(rows[-2][0].text, "🔎 Qidirish")
