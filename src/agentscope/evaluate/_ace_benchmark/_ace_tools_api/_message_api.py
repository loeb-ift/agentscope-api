# -*- coding: utf-8 -*-
"""The Message API in the ACEBench evaluation."""
from datetime import datetime

from ._shared_state import SharedState


class MessageApi(SharedState):
    """The message Api in the ACEBench evaluation."""

    tool_functions: list[str] = [
        "send_message",
        "delete_message",
        "view_messages_between_users",
        "search_messages",
        "get_all_message_times_with_ids",
        "get_latest_message_id",
        "get_earliest_message_id",
    ]

    def __init__(self, share_state: dict) -> None:
        """Initialize the MessageApi with shared state."""
        super().__init__(share_state)

        # 設置六個用戶
        self.max_capacity = 6
        self.user_list: dict[str, dict[str, str | int]] = {
            "Eve": {
                "user_id": "USR100",
                "phone_number": "123-456-7890",
                "occupation": "Software Engineer",
            },
            "Frank": {
                "user_id": "USR101",
                "phone_number": "234-567-8901",
                "occupation": "Data Scientist",
            },
            "Grace": {
                "user_id": "USR102",
                "phone_number": "345-678-9012",
                "occupation": "Product Manager",
            },
            "Helen": {
                "user_id": "USR103",
                "phone_number": "456-789-0123",
                "occupation": "UX Designer",
            },
            "Isaac": {
                "user_id": "USR104",
                "phone_number": "567-890-1234",
                "occupation": "DevOps Engineer",
            },
            "Jack": {
                "user_id": "USR105",
                "phone_number": "678-901-2345",
                "occupation": "Marketing Specialist",
            },
        }

        # 設置六個用戶之間的短信記錄
        # 信息1和reminder配合  信息2和food配合
        self.inbox: dict[int, dict[str, str | int]] = {
            1: {
                "sender_id": "USR100",
                "receiver_id": "USR101",
                "message": "Hey Frank, don't forget about our meeting on "
                "2024-06-11 at 4 PM in Conference Room 1.",
                "time": "2024-06-09",
            },
            2: {
                "sender_id": "USR101",
                "receiver_id": "USR102",
                "message": """你能幫我點一個\"瑪格麗特披薩\"的外賣嗎,商家是達美樂。""",
                "time": "2024-03-09",
            },
            3: {
                "sender_id": "USR102",
                "receiver_id": "USR103",
                "message": "幫我查一些喜茶有哪些奶茶外賣，買一杯便宜些的奶茶。"
                "買完以後記得回覆我,回覆的內容是（已經買好了）",
                "time": "2023-12-05",
            },
            4: {
                "sender_id": "USR103",
                "receiver_id": "USR102",
                "message": "No problem Helen, I can assist you.",
                "time": "2024-09-09",
            },
            5: {
                "sender_id": "USR104",
                "receiver_id": "USR105",
                "message": "Isaac, are you available for a call?",
                "time": "2024-06-06",
            },
            6: {
                "sender_id": "USR105",
                "receiver_id": "USR104",
                "message": "Yes Jack, let's do it in 30 minutes.",
                "time": "2024-01-15",
            },
        }

        self.message_id_counter: int = 6

    def get_state_dict(self) -> dict:
        """Get the current state dict of the MessageApi."""

        # To avoid the error in ACEBench dataset
        inbox_state = {}
        for key, value in self.inbox.items():
            inbox_state[str(key)] = value

        return {
            "MessageApi": {
                "inbox": inbox_state,
            },
        }

    def send_message(
        self,
        sender_name: str,
        receiver_name: str,
        message: str,
    ) -> dict[str, bool | str]:
        """將一條消息從一個用戶發送給另一個用戶。

        Args:
            sender_name (`str`):
                發送消息的用戶姓名。
            receiver_name (`str`):
                接收消息的用戶姓名。
            message (`str`):
                要發送的消息內容。
        """
        if not self.logged_in:
            return {"status": False, "message": "device未登錄，無法發送短信"}

        if not self.wifi:
            return {"status": False, "message": "wifi關閉，此時不能發送信息"}

        if len(self.inbox) >= self.max_capacity:
            return {
                "status": False,
                "message": "內存容量不夠了，你需要詢問user刪除哪一條短信。",
            }

        # 驗證發送者和接收者是否存在
        if (
            sender_name not in self.user_list
            or receiver_name not in self.user_list
        ):
            return {"status": False, "message": "發送者或接收者不存在"}

        sender_id = self.user_list[sender_name]["user_id"]
        receiver_id = self.user_list[receiver_name]["user_id"]

        # 將短信添加到inbox
        self.message_id_counter += 1
        self.inbox[self.message_id_counter] = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "message": message,
        }

        return {"status": True, "message": f"短信成功發送給{receiver_name}。"}

    def delete_message(self, message_id: int) -> dict[str, bool | str]:
        """根據消息 ID 刪除一條消息。

        Args:
            message_id (`int`):
                要刪除的消息的 ID。
        """
        if not self.logged_in:
            return {"status": False, "message": "device未登錄，無法刪除短信"}
        if message_id not in self.inbox:
            return {"status": False, "message": "短信ID不存在"}

        del self.inbox[message_id]
        return {"status": True, "message": f"短信ID {message_id} 已成功刪除。"}

    def view_messages_between_users(
        self,
        sender_name: str,
        receiver_name: str,
    ) -> dict:
        """獲取特定用戶發送給另一個用戶的所有消息。

        Args:
            sender_name (`str`):
                發送消息的用戶姓名。
            receiver_name (`str`):
                接收消息的用戶姓名。
        """
        if not self.logged_in:
            return {
                "status": False,
                "message": "device未登錄，無法查看短信信息",
            }

        if sender_name not in self.user_list:
            return {"status": False, "message": "發送者不存在"}

        if receiver_name not in self.user_list:
            return {"status": False, "message": "接收者不存在"}

        sender_id = self.user_list[sender_name]["user_id"]
        receiver_id = self.user_list[receiver_name]["user_id"]
        messages_between_users = []

        # 遍歷 inbox，找出 sender_id 發送給 receiver_id 的短信
        for msg_id, msg_data in self.inbox.items():
            if (
                msg_data["sender_id"] == sender_id
                and msg_data["receiver_id"] == receiver_id
            ):
                messages_between_users.append(
                    {
                        "id": msg_id,
                        "sender": sender_name,
                        "receiver": receiver_name,
                        "message": msg_data["message"],
                    },
                )

        if not messages_between_users:
            return {"status": False, "message": "沒有找到相關的短信記錄"}

        return {"status": True, "messages": messages_between_users}

    def search_messages(
        self,
        user_name: str,
        keyword: str,
    ) -> dict:
        """搜索特定用戶消息中包含特定關鍵字的消息。

        Args:
            user_name (`str`):
                要搜索消息的用戶姓名。
            keyword (`str`):
                要在消息中搜索的關鍵字。
        """
        if user_name not in self.user_list:
            return {"status": False, "message": "用戶不存在"}

        user_id = self.user_list[user_name]["user_id"]
        matched_messages = []

        # 遍歷 inbox，找到發送或接收中包含關鍵詞的消息
        for msg_id, msg_data in self.inbox.items():
            if (
                user_id in (msg_data["sender_id"], msg_data["receiver_id"])
                and keyword.lower() in msg_data["message"].lower()
            ):
                matched_messages.append(
                    {
                        "id": msg_id,
                        "sender_id": msg_data["sender_id"],
                        "receiver_id": msg_data["receiver_id"],
                        "message": msg_data["message"],
                    },
                )

        if not matched_messages:
            return {"status": False, "message": "沒有找到包含關鍵詞的短信"}

        return {"status": True, "messages": matched_messages}

    def get_all_message_times_with_ids(
        self,
    ) -> dict:
        """獲取所有短信的時間以及對應的短信編號。"""
        if not self.logged_in:
            return {
                "status": False,
                "message": "device未登錄，獲取所有短信的時間以及對應的短信編號。",
            }
        message_times_with_ids = {
            msg_id: msg_data["time"] for msg_id, msg_data in self.inbox.items()
        }
        return message_times_with_ids

    def get_latest_message_id(self) -> dict:
        """獲取最近發送的消息的 ID。"""
        if not self.logged_in:
            return {
                "status": False,
                "message": "device未登錄，無法獲取最新發送的短信ID。",
            }
        if not self.inbox:
            return {"status": False, "message": "短信記錄為空"}

        # 遍歷所有短信，找出時間最新的短信
        latest_message_id = None
        latest_time = None

        for message_id, message_data in self.inbox.items():
            message_time = datetime.strptime(
                str(message_data["time"]),
                "%Y-%m-%d",
            )
            if latest_time is None or message_time > latest_time:
                latest_time = message_time
                latest_message_id = message_id

        return {
            "status": True,
            "message": f"最新的短信ID是 {latest_message_id}",
            "message_id": latest_message_id,
        }

    def get_earliest_message_id(self) -> dict:
        """獲取最早發送的消息的 ID。"""
        if not self.logged_in:
            return {
                "status": False,
                "message": "device未登錄，無法獲取最早發送的短信ID",
            }
        if not self.inbox:
            return {"status": False, "message": "短信記錄為空"}

        # 遍歷所有短信，找出時間最早的短信
        earliest_message_id = None
        earliest_time = None

        for message_id, message_data in self.inbox.items():
            message_time = datetime.strptime(
                str(message_data["time"]),
                "%Y-%m-%d",
            )
            if earliest_time is None or message_time < earliest_time:
                earliest_time = message_time
                earliest_message_id = message_id

        return {
            "status": True,
            "message": f"最早的短信ID是 {earliest_message_id}",
            "message_id": earliest_message_id,
        }
