from aiogram.fsm.state import State, StatesGroup


class PartyFlow(StatesGroup):
    search = State()
    new = State()
