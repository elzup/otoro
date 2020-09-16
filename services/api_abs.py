
from abc import ABCMeta, abstractmethod
from typing import Literal, Tuple


class WrapperAPI(metaclass=ABCMeta):
    @abstractmethod
    def buy_order(self, amount) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def sell_order(self, amount) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def get_open_orders(self) -> list:
        pass

    @abstractmethod
    def get_position(self) -> Literal["none", "long", "shor"]:
        pass

    @abstractmethod
    def get_mycoin(self) -> float:
        pass

    @abstractmethod
    def get_balance_interest(self) -> float:
        pass

    @abstractmethod
    def get_ask(self) -> float:
        pass

    @abstractmethod
    def get_bid(self) -> float:
        pass

    @abstractmethod
    def get_order_status(self, id) -> Literal["COMP", "NEW", "EXPIRE"]:
        pass
