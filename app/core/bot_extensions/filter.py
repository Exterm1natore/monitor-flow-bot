import json
from bot.filter import FilterBase


class ChatTypeFilter(FilterBase):
    def __init__(self, *chat_types):
        super(ChatTypeFilter, self).__init__()
        self.chat_types = chat_types

    def filter(self, event):
        chat = event.data.get("chat")
        if not chat or "type" not in chat:
            return False
        return chat["type"] in self.chat_types


class CallbackActionFilter(FilterBase):
    def __init__(self, expected_action: str):
        super(CallbackActionFilter, self).__init__()
        self.expected_action = expected_action

    def filter(self, event):
        callback_data = event.data.get("callbackData")
        if not callback_data:
            return False

        try:
            payload = json.loads(callback_data)
        except (ValueError, TypeError):
            return False

        return payload.get("action") == self.expected_action
