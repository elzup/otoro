from logic import buy_judge_channelbreakout, buy_judge_channelbreakout_i, sell_judge_channelbreakout, sell_judge_channelbreakout_i
import unittest
import numpy as np

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


if __name__ == '__main__':
    unittest.main()
