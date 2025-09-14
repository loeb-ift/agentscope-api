# -*- coding: utf-8 -*-
# type: ignore
# pylint: disable=too-many-lines
# pylint: disable=too-many-statements
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
# pylint: disable=too-many-return-statements
"""The travel API for the ACEBench simulation tools in AgentScope."""

from datetime import datetime, timedelta


class TravelApi:
    """旅行預訂系統類。

    提供航班查詢、用戶認證、預訂管理等功能的旅行系統。
    支持直飛和中轉航班查詢、航班預訂、預訂修改和取消等功能。
    """

    tool_functions: list[str] = [
        "get_user_details",
        "get_flight_details",
        "get_reservation_details",
        "reserve_flight",
        "cancel_reservation",
        "modify_flight",
    ]

    def __init__(self) -> None:
        """初始化旅行系統。

        設置用戶檔案和航班信息，包含用戶信息、航班數據和預訂記錄。
        """
        # 初始化用戶信息
        self.users = {
            "user1": {
                "user_name": "Eve",
                "password": "password123",
                "cash_balance": 2000.0,
                "bank_balance": 50000.0,
                "membership_level": "regular",
            },
            "user2": {
                "user_name": "Frank",
                "password": "password456",
                "cash_balance": 8000.0,
                "bank_balance": 8000.0,
                "membership_level": "silver",
            },
            "user3": {
                "user_name": "Grace",
                "password": "password789",
                "cash_balance": 1000.0,
                "bank_balance": 5000.0,
                "membership_level": "gold",
            },
        }

        # 初始化航班信息
        self.flights = [
            {
                "flight_no": "CA1234",
                "origin": "北京",
                "destination": "上海",
                "depart_time": "2024-07-15 08:00:00",
                "arrival_time": "2024-07-15 10:30:00",
                "status": "available",
                "seats_available": 5,
                "economy_price": 1200,
                "business_price": 3000,
            },
            {
                "flight_no": "MU5678",
                "origin": "上海",
                "destination": "北京",
                "depart_time": "2024-07-16 09:00:00",
                "arrival_time": "2024-07-16 11:30:00",
                "status": "available",
                "seats_available": 3,
                "economy_price": 1900,
                "business_price": 3000,
            },
            {
                "flight_no": "CZ4321",
                "origin": "上海",
                "destination": "北京",
                "depart_time": "2024-07-16 20:00:00",
                "arrival_time": "2024-07-16 22:00:00",
                "status": "available",
                "seats_available": 8,
                "economy_price": 2500,
                "business_price": 4000,
            },
            {
                "flight_no": "CZ4352",
                "origin": "上海",
                "destination": "北京",
                "depart_time": "2024-07-17 20:00:00",
                "arrival_time": "2024-07-17 22:00:00",
                "status": "available",
                "seats_available": 8,
                "economy_price": 1600,
                "business_price": 2500,
            },
            {
                "flight_no": "MU3561",
                "origin": "北京",
                "destination": "南京",
                "depart_time": "2024-07-18 08:00:00",
                "arrival_time": "2024-07-18 10:00:00",
                "status": "available",
                "seats_available": 8,
                "economy_price": 1500,
                "business_price": 4000,
            },
            {
                "flight_no": "MU1566",
                "origin": "北京",
                "destination": "南京",
                "depart_time": "2024-07-18 20:00:00",
                "arrival_time": "2024-07-18 22:00:00",
                "status": "available",
                "seats_available": 8,
                "economy_price": 1500,
                "business_price": 4000,
            },
            {
                "flight_no": "CZ1765",
                "origin": "南京",
                "destination": "深圳",
                "depart_time": "2024-07-17 20:30:00",
                "arrival_time": "2024-07-17 22:00:00",
                "status": "available",
                "seats_available": 8,
                "economy_price": 1500,
                "business_price": 2500,
            },
            {
                "flight_no": "CZ1765",
                "origin": "南京",
                "destination": "深圳",
                "depart_time": "2024-07-18 12:30:00",
                "arrival_time": "2024-07-18 15:00:00",
                "status": "available",
                "seats_available": 8,
                "economy_price": 1500,
                "business_price": 2500,
            },
            {
                "flight_no": "MH1765",
                "origin": "廈門",
                "destination": "成都",
                "depart_time": "2024-07-17 12:30:00",
                "arrival_time": "2024-07-17 15:00:00",
                "status": "available",
                "seats_available": 8,
                "economy_price": 1500,
                "business_price": 2500,
            },
            {
                "flight_no": "MH2616",
                "origin": "成都",
                "destination": "廈門",
                "depart_time": "2024-07-18 18:30:00",
                "arrival_time": "2024-07-18 21:00:00",
                "status": "available",
                "seats_available": 8,
                "economy_price": 1500,
                "business_price": 2500,
            },
            {
                "flight_no": "MH2616",
                "origin": "成都",
                "destination": "福州",
                "depart_time": "2024-07-16 18:30:00",
                "arrival_time": "2024-07-16 21:00:00",
                "status": "available",
                "seats_available": 8,
                "economy_price": 1500,
                "business_price": 2500,
            },
        ]

        # 初始化預訂列表
        self.reservations = [
            {
                "reservation_id": "res_1",
                "user_id": "user1",
                "flight_no": "CA1234",
                "payment_method": "bank",
                "cabin": "經濟艙",
                "baggage": 1,
                "origin": "北京",
                "destination": "上海",
            },
            {
                "reservation_id": "res_2",
                "user_id": "user1",
                "flight_no": "MU5678",
                "payment_method": "bank",
                "cabin": "商務艙",
                "baggage": 1,
                "origin": "上海",
                "destination": "北京",
            },
            {
                "reservation_id": "res_3",
                "user_id": "user2",
                "flight_no": "MH1765",
                "payment_method": "bank",
                "cabin": "商務艙",
                "baggage": 1,
                "origin": "廈門",
                "destination": "成都",
            },
            {
                "reservation_id": "res_4",
                "user_id": "user2",
                "flight_no": "MU2616",
                "payment_method": "bank",
                "cabin": "商務艙",
                "baggage": 1,
                "origin": "成都",
                "destination": "廈門",
            },
        ]

    def get_state_dict(self) -> dict:
        """獲取當前TravelApi的狀態字典。"""
        return {
            "Travel": {
                "users": self.users,
                "reservations": self.reservations,
            },
        }

    # 根据出发地和到达地查询航班

    def get_flight_details(
        self,
        origin: str = None,
        destination: str = None,
    ) -> list[dict] | str:
        """根據出發地和目的地查詢航班的基本信息。

        Args:
            origin (str, optional): 出發地城市名稱。默認為None。
            destination (str, optional): 目的地城市名稱。默認為None。

        Returns:
            list[dict] | str: 符合條件的航班列表或無航班的提示信息。
        """
        flights = self.flights

        # 過濾出發地
        if origin:
            flights = [
                flight for flight in flights if flight["origin"] == origin
            ]

        # 過濾目的地
        if destination:
            flights = [
                flight
                for flight in flights
                if flight["destination"] == destination
            ]
        if len(flights) == 0:
            return "沒有符合條件的直達航班"
        # 返回查詢結果
        return [
            {
                "flight_no": flight["flight_no"],
                "origin": flight["origin"],
                "destination": flight["destination"],
                "depart_time": flight["depart_time"],
                "arrival_time": flight["arrival_time"],
                "status": flight["status"],
                "seats_available": flight["seats_available"],
                "economy_price": flight["economy_price"],
                "business_price": flight["business_price"],
            }
            for flight in flights
        ]

    def get_user_details(self, user_id: str, password: str) -> dict:
        """根據用戶名和密碼查詢用戶信息。

        Args:
            user_id (str): 用戶ID。
            password (str): 用戶密碼。

        Returns:
            dict: 用戶信息字典（不包含密碼）或錯誤信息。
        """
        user = self.users.get(user_id)
        if user and user["password"] == password:
            return {
                key: value for key, value in user.items() if key != "password"
            }
        return {"status": "error", "message": "用戶名或密碼不正確"}

    def get_reservation_details(
        self,
        reservation_id: str = None,
        user_id: str = None,
    ) -> list[dict] | dict:
        """根據預訂ID或用戶ID查詢預訂信息，包括對應航班的基本信息。

        Args:
            reservation_id (str, optional): 預訂ID。默認為None。
            user_id (str, optional): 用戶ID。默認為None。

        Returns:
            `list[dict] | dict`:
                詳細預訂信息列表或錯誤信息字典。
        """
        # 根據預訂ID或用戶ID篩選預訂信息
        if reservation_id:
            reservations = [
                reservation
                for reservation in self.reservations
                if reservation["reservation_id"] == reservation_id
            ]
        elif user_id:
            reservations = [
                reservation
                for reservation in self.reservations
                if reservation["user_id"] == user_id
            ]
        else:
            return {"status": "error", "message": "請提供有效的預訂ID或用戶ID"}

        # 對每個預訂，附加航班信息
        detailed_reservations = []
        for reservation in reservations:
            flight_info = next(
                (
                    flight
                    for flight in self.flights
                    if flight["flight_no"] == reservation["flight_no"]
                ),
                None,
            )
            detailed_reservation = {**reservation, "flight_info": flight_info}
            detailed_reservations.append(detailed_reservation)

        return detailed_reservations

    def authenticate_user(self, user_id: str, password: str) -> dict:
        """驗證用戶身份。

        Args:
            user_id (str): 用戶ID。
            password (str): 用戶密碼。

        Returns:
            `dict`:
                用戶信息字典或錯誤信息字典。
        """
        user = self.users.get(user_id)
        if user and user["password"] == password:
            return user
        return {"status": "error", "message": "用戶名或密碼不正確"}

    def get_baggage_allowance(
        self,
        membership_level: str,
        cabin_class: str,
    ) -> int:
        """獲取用戶基於會員等級和艙位的免費托運行李限額。

        Args:
            membership_level (str): 會員等級 ("regular", "silver", "gold")。
            cabin_class (str): 艙位 ("基礎經濟艙", "經濟艙", "商務艙")。

        Returns:
            int: 免費托運行李數量。
        """
        allowance = {
            "regular": {"經濟艙": 1, "商務艙": 2},
            "silver": {"經濟艙": 2, "商務艙": 3},
            "gold": {"經濟艙": 3, "商務艙": 3},
        }
        return allowance.get(membership_level, {}).get(cabin_class, 0)

    def find_transfer_flights(
        self,
        origin_city: str,
        transfer_city: str,
        destination_city: str,
    ) -> list[dict] | str:
        """查找從出發城市到目的地城市的中轉航班。

        確保第一班航班降落時間早於第二班航班起飛時間。

        Args:
            origin_city (str): 出發城市。
            transfer_city (str): 中轉城市。
            destination_city (str): 到達城市。

        Returns:
            list[dict] | str:
                滿足條件的中轉航班列表，每個航班包含兩段航程的信息，或無航班提示。
        """
        # 獲取從出發城市到中轉城市的航班
        first_leg_flights: list[dict] = [
            flight
            for flight in self.flights
            if flight["origin"] == origin_city
            and flight["destination"] == transfer_city
            and flight["status"] == "available"
        ]

        # 獲取從中轉城市到目的地城市的航班
        second_leg_flights = [
            flight
            for flight in self.flights
            if flight["origin"] == transfer_city
            and flight["destination"] == destination_city
            and flight["status"] == "available"
        ]

        # 存儲符合條件的中轉航班
        transfer_flights = []

        # 遍歷第一段航班和第二段航班，查找符合時間條件的組合
        for first_flight in first_leg_flights:
            first_arrival = datetime.strptime(
                first_flight["arrival_time"],
                "%Y-%m-%d %H:%M:%S",
            )

            for second_flight in second_leg_flights:
                second_departure = datetime.strptime(
                    str(second_flight["depart_time"]),
                    "%Y-%m-%d %H:%M:%S",
                )

                # 檢查第一班航班降落時間早於第二班航班起飛時間
                if first_arrival < second_departure:
                    transfer_flights.append(
                        {
                            "first_leg": first_flight,
                            "second_leg": second_flight,
                        },
                    )

        # 返回符合條件的中轉航班列表
        if transfer_flights:
            return transfer_flights
        else:
            return "未找到符合條件的中轉航班。"

    def calculate_baggage_fee(
        self,
        membership_level: str,
        cabin_class: str,
        baggage_count: int,
    ) -> float:
        """計算行李費用。

        Args:
            membership_level (str): 會員等級。
            cabin_class (str): 艙位等級。
            baggage_count (int): 行李數量。

        Returns:
            float: 額外行李費用。
        """
        free_baggage = {
            "regular": {"經濟艙": 1, "商務艙": 2},
            "silver": {"經濟艙": 2, "商務艙": 3},
            "gold": {"經濟艙": 3, "商務艙": 3},
        }
        free_limit = free_baggage[membership_level][cabin_class]
        additional_baggage = max(baggage_count - free_limit, 0)
        return additional_baggage * 50

    def update_balance(
        self,
        user: dict,
        payment_method: str,
        amount: float,
    ) -> bool:
        """更新用戶的餘額。

        Args:
            user (dict): 用戶信息字典。
            payment_method (str): 支付方式（"cash" 或 "bank"）。
            amount (float): 更新金額（正數表示增加，負數表示減少）。

        Returns:
            bool: 如果餘額充足且更新成功，返回 True，否則返回 False。
        """
        if payment_method == "cash":
            if user["cash_balance"] + amount < 0:
                return False  # 餘額不足
            user["cash_balance"] += amount
        elif payment_method == "bank":
            if user["bank_balance"] + amount < 0:
                return False  # 余额不足
            user["bank_balance"] += amount
        return True

    def reserve_flight(
        self,
        user_id: str,
        password: str,
        flight_no: str,
        cabin: str,
        payment_method: str,
        baggage_count: int,
    ) -> str:
        """預訂航班。

        Args:
            user_id (str): 用戶ID。
            password (str): 用戶密碼。
            flight_no (str): 航班號。
            cabin (str): 艙位等級。
            payment_method (str): 支付方式。
            baggage_count (int): 行李數量。

        Returns:
            str: 預訂結果信息。
        """
        user = self.authenticate_user(user_id, password)
        if not user:
            return "認證失敗，請檢查用戶ID和密碼。"

        # 檢查航班和座位
        flight = next(
            (
                f
                for f in self.flights
                if f["flight_no"] == flight_no and f["status"] == "available"
            ),
            None,
        )

        # 計算航班價格
        price: int = (
            flight["economy_price"]
            if cabin == "經濟艙"
            else flight["business_price"]
        )
        total_cost = price

        # 計算行李費用
        baggage_fee = self.calculate_baggage_fee(
            user["membership_level"],
            cabin,
            baggage_count,
        )
        total_cost += baggage_fee

        # 檢查支付方式
        if payment_method not in ["cash", "bank"]:
            return "支付方式無效"

        # 更新預定後的餘額
        if payment_method == "cash":
            if total_cost > self.users.get(user_id)["cash_balance"]:
                return "cash餘額不足，請考慮換一種支付方式"
            self.users.get(user_id)["cash_balance"] -= total_cost
        else:
            if total_cost > self.users.get(user_id)["bank_balance"]:
                return "bank餘額不足，請考慮換一種支付方式"
            self.users.get(user_id)["bank_balance"] -= total_cost

        # 更新航班信息並生成預訂
        flight["seats_available"] -= 1
        reservation_id = f"res_{len(self.reservations) + 1}"
        reservation = {
            "reservation_id": reservation_id,
            "user_id": user_id,
            "flight_no": flight_no,
            "payment_method": payment_method,
            "cabin": cabin,
            "baggage": baggage_count,
        }
        self.reservations.append(reservation)

        return f"預訂成功，預訂號：{reservation_id}，" f"總費用：{total_cost}元（包含行李費用）。"

    def modify_flight(
        self,
        user_id: str,
        reservation_id: str,
        new_flight_no: str = None,
        new_cabin: str = None,
        add_baggage: int = 0,
        new_payment_method: str = None,
    ) -> str:
        """修改航班預訂，包括更改航班、艙位和行李。

        Args:
            user_id (str): 用戶ID。
            reservation_id (str): 預訂ID。
            new_flight_no (str, optional): 新的航班號。默認為None。
            new_cabin (str, optional): 新的艙位。默認為None。
            add_baggage (int, optional): 新增托運行李的數量。默認為0。
            new_payment_method (str, optional): 新的付款方式。默認為None。

        Returns:
            str: 修改結果信息。
        """
        # 獲取對應的預訂
        reservation = next(
            (
                r
                for r in self.reservations
                if r["reservation_id"] == reservation_id
                and r["user_id"] == user_id
            ),
            None,
        )
        if not reservation:
            return "預訂未找到或用戶ID不匹配。"

        # 檢查當前預訂的航班信息
        current_flight = next(
            (
                f
                for f in self.flights
                if f["flight_no"] == reservation["flight_no"]
            ),
            None,
        )
        if not current_flight:
            return "航班信息未找到。"

        # 獲取原始支付方式或新提供的支付方式
        payment_method = (
            new_payment_method
            if new_payment_method
            else reservation["payment_method"]
        )
        user = self.users[user_id]
        if not user:
            return "用户信息未找到。"

        # 存储处理结果
        result_messages = []

        if new_flight_no and new_flight_no != reservation["flight_no"]:
            # 更新航班号（若提供）但必须匹配出发地和目的地
            new_flight = next(
                (f for f in self.flights if f["flight_no"] == new_flight_no),
                None,
            )
            if (
                new_flight
                and new_flight["origin"] == current_flight["origin"]
                and new_flight["destination"] == current_flight["destination"]
            ):
                reservation["flight_no"] = new_flight_no
                result_messages.append("航班号已更改。")
            else:
                return "航班更改失敗：新的航班號無效或目的地不匹配。"

        # 更新艙位（若提供）並計算價格差價
        if new_cabin and new_cabin != reservation.get("cabin"):
            price_difference = self.calculate_price_difference(
                current_flight,
                reservation["cabin"],
                new_cabin,
            )
            reservation["cabin"] = new_cabin
            if price_difference > 0:
                # 扣除差價
                if self.update_balance(
                    user,
                    payment_method,
                    -price_difference,
                ):
                    result_messages.append(
                        f"艙位更改成功。已支付差價: {price_difference}。",
                    )
                else:
                    result_messages.append("餘額不足，無法支付艙位差價。")
            elif price_difference < 0:
                # 退款
                self.update_balance(user, payment_method, -price_difference)
                result_messages.append(f"艙位更改成功。已退款差價: {-price_difference}。")

        # 增加托運行李，檢查免費限額和計算費用
        if add_baggage > 0:
            membership = user["membership_level"]
            max_free_baggage = self.get_baggage_allowance(
                membership,
                reservation["cabin"],
            )
            current_baggage = reservation.get("baggage", 0)
            total_baggage = current_baggage + add_baggage
            extra_baggage = max(0, total_baggage - max_free_baggage)
            baggage_cost = extra_baggage * 50
            if baggage_cost > 0:
                # 扣除行李費用
                if self.update_balance(user, payment_method, -baggage_cost):
                    result_messages.append(
                        f"行李已增加。需支付額外費用: {baggage_cost}。",
                    )
                else:
                    result_messages.append("餘額不足，無法支付額外行李費用。")
            reservation["baggage"] = total_baggage

        # 返回最終結果
        if not result_messages:
            result_messages.append("修改完成，無需額外費用。")
        return " ".join(result_messages)

    def cancel_reservation(
        self,
        user_id: str,
        reservation_id: str,
        reason: str,
    ) -> str:
        """取消預訂。

        Args:
            user_id (str): 用戶ID。
            reservation_id (str): 預訂ID。
            reason (str): 取消原因。

        Returns:
            str: 取消結果信息。
        """
        # 設置默認當前時間為 2024年7月14日早上6點
        current_time = datetime(2024, 7, 14, 6, 0, 0)

        # 驗證用戶和預訂是否存在
        user = self.users.get(user_id, None)
        if not user:
            return "用戶ID無效。"

        reservation = next(
            (
                r
                for r in self.reservations
                if r["reservation_id"] == reservation_id
                and r["user_id"] == user_id
            ),
            None,
        )
        if not reservation:
            return "預訂ID無效或與該用戶無關。"

        # 檢查航班信息是否存在
        flight = next(
            (
                f
                for f in self.flights
                if f["flight_no"] == reservation["flight_no"]
            ),
            None,
        )
        if not flight:
            return "航班信息無效。"

        # 檢查航班是否已起飛
        depart_time = datetime.strptime(
            flight["depart_time"],
            "%Y-%m-%d %H:%M:%S",
        )
        if current_time > depart_time:
            return "航段已使用，無法取消。"

        # 計算距離出發時間
        time_until_departure = depart_time - current_time
        cancel_fee = 0
        refund_amount = 0

        # 獲取航班價格
        flight_price = (
            flight["economy_price"]
            if reservation["cabin"] == "經濟艙"
            else flight["business_price"]
        )

        # 取消政策及退款計算
        if reason == "航空公司取消航班":
            # 航空公司取消航班，全額退款
            refund_amount = flight_price
            self.process_refund(user, refund_amount)
            return f"航班已取消，您的預訂將被免費取消，已退款{refund_amount}元。"

        elif time_until_departure > timedelta(days=1):
            # 離出發時間超過24小時免費取消
            refund_amount = flight_price
            self.process_refund(user, refund_amount)
            return f"距離出發時間超過24小時，免費取消成功，已退款{refund_amount}元。"

        else:
            # 若不符合免費取消條件，可根據需求設置取消费
            cancel_fee = flight_price * 0.1  # 假設取消费為票價的10%
            refund_amount = flight_price - cancel_fee
            self.process_refund(user, refund_amount)
            return f"距離出發時間不足24小時，已扣除取消费{cancel_fee}元，退款{refund_amount}元。"

    def process_refund(self, user: dict, amount: float) -> str:
        """將退款金額添加到用戶的現金餘額中。

        Args:
            user (dict): 用戶信息字典。
            amount (float): 退款金額。
        """
        user["cash_balance"] += amount
        return f"已成功處理退款，{user['user_name']}的現金餘額增加了{amount}元。"

    def calculate_price_difference(
        self,
        flight: dict,
        old_cabin: str,
        new_cabin: str,
    ) -> float:
        """計算艙位價格差異。

        Args:
            flight (dict): 航班信息字典。
            old_cabin (str): 原艙位等級。
            new_cabin (str): 新艙位等級。

        Returns:
            float: 價格差異（正數表示需支付差價，負數表示退款）。
        """
        cabin_prices = {
            "經濟艙": flight["economy_price"],
            "商務艙": flight["business_price"],
        }
        old_price = cabin_prices.get(old_cabin, 0)
        new_price = cabin_prices.get(new_cabin, 0)
        return new_price - old_price
