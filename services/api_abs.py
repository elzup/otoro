
from abc import ABCMeta, abstractmethod


class WrapperAPI(metaclass=ABCMeta):
    @abstractmethod
    def buy_order(self, ):
        pass
