import unittest
import numpy as np
from logic import buy_judge_channelbreakout, buy_judge_channelbreakout_i, buy_judge_channelbreakout_ic, sell_judge_channelbreakout_i, sell_judge_channelbreakout_ic

data = np.array([
    [0, 10, 13, 5, 11],
    [1, 11, 14, 11, 13],
    [2, 13, 14, 10, 11],
    [3, 10, 13, 9, 16],
    [4, 16, 17, 9, 11],  # high
    [5, 11, 13, 7, 15]  # low
])


class TestStringMethods(unittest.TestCase):

    def test_buy(self):
        self.assertTrue(buy_judge_channelbreakout_i(4, 3, data))
        self.assertFalse(buy_judge_channelbreakout_i(5, 3, data))

    def test_sell(self):
        self.assertTrue(sell_judge_channelbreakout_i(5, 5, data))
        self.assertFalse(sell_judge_channelbreakout_i(3, 4, data))

    def test_not_fill(self):
        self.assertFalse(buy_judge_channelbreakout_i(3, 5, data))

    def test_mergin_buy(self):
        data = np.array([
            [0, 10, 13, 10, 11],
            [1, 11, 20, 11, 13],
            [2, 13, 18, 10, 11],
        ])
        self.assertTrue(buy_judge_channelbreakout_ic(2, 3, data, 0.2))
        self.assertFalse(buy_judge_channelbreakout_ic(2, 3, data, 0.1))

    def test_mergin_sell(self):
        data = np.array([
            [0, 10, 13, 10, 11],
            [1, 11, 20, 11, 13],
            [2, 13, 14, 12, 11],
        ])
        self.assertTrue(sell_judge_channelbreakout_ic(2, 3, data, 0.21))
        self.assertFalse(sell_judge_channelbreakout_ic(2, 3, data, 0.19))


if __name__ == '__main__':
    unittest.main()
