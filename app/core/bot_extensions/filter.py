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
