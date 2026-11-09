from aiogram import Dispatcher

from app.context import BotContext
from app.handlers import callbacks, common, counterparties, documents, uploads
from app.middleware import AccessMiddleware


def create_dispatcher(ctx: BotContext):
    dispatcher = Dispatcher(ctx=ctx)
    access = AccessMiddleware()
    dispatcher.message.outer_middleware(access)
    dispatcher.callback_query.outer_middleware(access)
    # Commands and uploads take precedence over text input states.
    dispatcher.include_routers(
        common.router,
        documents.router,
        callbacks.router,
        uploads.router,
        counterparties.router,
    )
    return dispatcher
