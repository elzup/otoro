from logic import buy_judge_channelbreakout
import unittest


class TestStringMethods(unittest.TestCase):

    def test_buy(self):
        data = [
            [0, 10, 13, 9, 11],
            [1, 11, 14, 11, 13],
            [2, 13, 14, 15, 11],
            [3, 10, 13, 9, 17],
            [4, 17, 17, 9, 11],
            [5, 11, 13, 9, 11]
        ]
        self.assertTrue(buy_judge_channelbreakout(3, 3, data[:3]))


if __name__ == '__main__':
    unittest.main()
