# -*- coding: utf-8 -*-
"""The reminder API in ACEBench simulation tools."""
from datetime import datetime

from ._shared_state import SharedState


class ReminderApi(SharedState):
    """The reminder Api in the ACEBench evaluation."""

    tool_functions: list[str] = [
        "view_reminder_by_title",
        "add_reminder",
        "delete_reminder",
        "view_all_reminders",
        "mark_as_notified",
        "search_reminders",
    ]

    def __init__(self, share_state: dict) -> None:
        """Initialize the Reminder Api in the ACEBench evaluation."""
        super().__init__(share_state)

        self.max_capacity = 6
        self.reminder_list: dict[
            int,
            dict,
        ] = {
            1: {
                "reminder_id": 1001,
                "title": "Doctor's Appointment",
                "description": "Visit Dr. Smith for a checkup.",
                "time": "2024-07-15 09:30",
                "notified": False,
            },
            2: {
                "reminder_id": 1002,
                "title": "Team Meeting",
                "description": "Monthly project review with the team.",
                "time": "2024-07-17 11:00",
                "notified": False,
            },
            3: {
                "reminder_id": 1003,
                "title": "To-do list",
                "description": '首先幫Frank在"盒馬生鮮"點外賣，'
                '需要定兩個"生鮮大禮包"，再發短信告訴Frank：'
                '"購買商品的價格是()元"。要把括號換成實際金額，'
                "保留一位小數。",
                "time": "2024-07-16 11:00",
                "notified": False,
            },
        }
        self.reminder_id_counter: int = 3

    def get_state_dict(self) -> dict:
        """Get the current state dict of the ReminderApi."""
        return {
            "ReminderApi": {
                "reminder_list": self.reminder_list,
            },
        }

    def _check_capacity(self) -> bool:
        """檢查備忘錄容量是否已滿。"""
        return len(self.reminder_list) >= self.max_capacity

    def view_reminder_by_title(
        self,
        title: str,
    ) -> dict[str, str | bool | dict[str, str | bool | datetime]]:
        """根據提醒的標題查看特定的提醒。

        Args:
            title (str): 提醒的標題。

        Returns:
            dict[str, str | bool | dict[str, str | bool | datetime]]:
                包含查找狀態和提醒詳情的字典。
        """
        if not self.logged_in:
            return {"status": False, "message": "device未登錄，無法查看提醒"}
        for reminder in self.reminder_list.values():
            if reminder["title"] == title:
                return {"status": True, "reminder": reminder}

        return {"status": False, "message": f"沒有找到標題為 '{title}' 的提醒"}

    def add_reminder(
        self,
        title: str,
        description: str,
        time: datetime,
    ) -> dict[str, bool | str]:
        """添加一個新的提醒。

        Args:
            title (str): 提醒標題。
            description (str): 提醒描述。
            time (datetime): 提醒時間, 一定遵循格式"YYYY-MM-DD HH:MM"。

        Returns:
            dict[str, bool | str]: 包含添加狀態和結果的字典。
        """
        if not self.logged_in:
            return {
                "status": False,
                "message": "device未登錄，無法添加一個新的提醒",
            }
        if self._check_capacity():
            return {"status": False, "message": "提醒容量已滿，無法添加新的提醒"}

        self.reminder_id_counter += 1
        reminder_id = self.reminder_id_counter
        self.reminder_list[reminder_id] = {
            "reminder_id": reminder_id,
            "title": title,
            "description": description,
            "time": time,
            "notified": False,
        }
        return {"status": True, "message": f"提醒 '{title}' 已成功添加"}

    def delete_reminder(self, reminder_id: int) -> dict[str, bool | str]:
        """刪除指定的提醒。

        Args:
            reminder_id (int): 要刪除的提醒ID。

        Returns:
            dict[str, bool | str]: 包含刪除狀態和結果的字典。
        """
        if not self.logged_in:
            return {"status": False, "message": "device未登錄，無法刪除指定的提醒"}
        if reminder_id not in self.reminder_list:
            return {"status": False, "message": "提醒ID不存在"}

        del self.reminder_list[reminder_id]
        return {"status": True, "message": f"提醒ID {reminder_id} 已成功刪除"}

    def view_all_reminders(
        self,
    ) -> dict:
        """查看所有的提醒。

        Returns:
            dict:
                包含所有提醒的字典列表。
        """
        if not self.reminder_list:
            return {"status": False, "message": "沒有任何提醒"}

        reminders = []
        for reminder in self.reminder_list.values():
            reminders.append(
                {
                    "title": reminder["title"],
                    "description": reminder["description"],
                    "time": reminder["time"],
                    "notified": reminder["notified"],
                },
            )
        return {"status": True, "reminders": reminders}

    def mark_as_notified(
        self,
        reminder_id: int,
    ) -> dict[str, bool | str]:
        """標記提醒為已通知。

        Args:
            reminder_id (int): 要標記為已通知的提醒ID。

        Returns:
            dict[str, bool | str]:: 包含操作結果的字典。
        """
        if reminder_id not in self.reminder_list:
            return {"status": False, "message": "提醒ID不存在"}

        self.reminder_list[reminder_id]["notified"] = True
        return {"status": True, "message": f"提醒ID {reminder_id} 已標記為已通知"}

    def search_reminders(
        self,
        keyword: str,
    ) -> dict:
        """根據關鍵詞搜索提醒。

        Args:
            keyword (str): 搜索關鍵詞。

        Returns:
            `dict`:
                包含匹配提醒的字典列表。
        """
        matched_reminders = []

        for reminder in self.reminder_list.values():
            if (
                keyword.lower() in reminder["title"].lower()
                or keyword.lower() in reminder["description"].lower()
            ):
                matched_reminders.append(
                    {
                        "title": reminder["title"],
                        "description": reminder["description"],
                        "time": reminder["time"].strftime("%Y-%m-%d %H:%M"),
                    },
                )

        if not matched_reminders:
            return {"status": False, "message": "沒有找到包含該關鍵詞的提醒"}

        return {"status": True, "reminders": matched_reminders}
