import time
from typing import List


class IterativeMatch:
    """ 迭代匹配 """

    def __init__(self, data):
        """
        可迭代对象构建
        :param data:可迭代对象
        """
        self.data = data
        """ 迭代数据 """
        self.index = 0
        """ 当前判断的下标 """

    def reset(self):
        """ 重置 """
        self.index = 0

    def match(self, next_data):
        """
        对迭代序列进行迭代
        :param next_data: 下一个迭代的数据
        :return: 是前缀，完全匹配
        """
        if self.data is None or len(self.data) == 0:
            return True, True

        for data in next_data:
            if self.data[self.index] == data:
                self.index += 1
            else:
                self.reset()
                return False, False
        is_equal = False
        if len(self.data) == self.index:
            is_equal = True
            self.reset()
        return True, is_equal


class Factor:

    def __init__(self, status, start, end, need_escape=False, next_parser=None, self_mark=None):
        """
        构造方法
        :param status: 状态
        :param start: 开始字符
        :param end: 结束字符
        :param need_escape: 需要转义
        :param next_parser: 匹配后解析
        :param self_mark:自身标记
        """
        self.start = start
        """ 开始 """
        self.end = end
        """ 结束 """
        self.status = status
        """ 状态 """
        self.need_escape = need_escape
        """ 需要转义 """
        self.next_parser = next_parser
        """ 下一层解析 """
        self.self_mark = self_mark
        """ 自身标记 """


class MatchFactor:
    def __init__(self, factor: Factor):
        self.factor: Factor = factor
        """ 因子 """
        self.start_match = IterativeMatch(self.factor.start)
        """ 开始匹配 """
        self.end_match = IterativeMatch(self.factor.end)
        """ 结尾匹配 """
        self.cache = ""
        """ 缓存中间字符 """
        self.escape = False
        """ 转义字符状态 """
        self.end_index = -1
        """ 最终停止的字符位置 """
        self.next_flag = False

    def reset(self):
        """ 重置 """
        self.start_match.reset()
        self.start_match.reset()
        self.cache = ""
        self.escape = False
        self.end_index = -1
        self.next_flag = False

    def prefix(self, next_char):
        """
        匹配字符
        :param next_char:下一个匹配字符
        :return: True/False
        """
        if self.next_flag:
            return self.prefix_end(next_char)
        return self.prefix_start(next_char)

    def prefix_start(self, next_char):
        """
        判断该字符串是不是前缀，
        :param next_char: 下一个字符
        :return: True/False
        """
        similar, equal = self.start_match.match(next_char)
        if equal:
            self.next_flag = True
            equal = self.factor.end is None
        return similar, equal

    def prefix_end(self, next_char):
        """
        判断该字符串是不是前缀，
        :param next_char: 下一个字符
        :return: True/False
        """
        if self.factor.end is None:
            return False, True
        # 转义字符
        if self.factor.need_escape:
            if self.escape:
                escape_char = f'\\{next_char}'
                if escape_char == "\\\\":
                    self.cache += f'\\'
                elif escape_char == "\\n":
                    self.cache += f'\n'
                elif escape_char == "\\t":
                    self.cache += f'\t'
                else:
                    self.cache += escape_char
                self.escape = False
                return True, False
            if next_char == "\\" and not self.escape:
                self.escape = True
                return True, False

        self.cache += next_char
        similar, equal = self.end_match.match(next_char)
        if equal:
            self.cache = self.cache[0:len(self.cache) - len(self.factor.end)]
        return True, equal


class Token:

    @staticmethod
    def start_type(any_type, data, index):
        token = Token()
        token.end_index = index
        token.start = data
        token.type = any_type
        return token

    @staticmethod
    def end_type(any_type, data, index):
        token = Token()
        token.end_index = index
        token.end = data
        token.type = any_type
        return token

    @staticmethod
    def any_token(any_type, data, index):
        token = Token()
        token.end_index = index
        token.data = data
        token.type = any_type
        return token

    def __init__(self, match_factor: MatchFactor = None):
        self.type = None
        """ 类型 """
        self.token_tree = []
        """ Token树 """
        self.start = None
        """ 开始 """
        self.end = None
        """ 结束 """
        self.data = ""
        """ 内容 """
        self.type = None
        """ 类型 """
        self.end_index = None
        """ 源文件字符位置 """

        if match_factor is not None:
            self.start = match_factor.factor.start
            self.end = match_factor.factor.end
            self.data = match_factor.cache
            self.type = match_factor.factor.status
            self.end_index = match_factor.end_index

    def add_tree(self, token):
        """
        添加树
        :param token: Token节点
        """
        self.token_tree.append(token)


class CombinationFactor:

    def __init__(self):
        self.data: List[Factor] = []
        """ 全部因子信息 """
        self.cache: List[MatchFactor] = []
        """ 匹配器缓存 """

    def add_factor(self, status, start, end=None, next_parser=None, self_mark=None, need_escape=False):
        """
        添加因子
        :param status:状态
        :param start: 开始
        :param end: 结束
        :param next_parser:下一层解析
        :param self_mark:自身标记
        :param need_escape:需要转义处理
        """
        self.data.append(Factor(status, start, end, need_escape, next_parser=next_parser, self_mark=self_mark))

    def clear_cache(self):
        """ 清除缓存 """
        self.cache = []

    def to_match_factor(self) -> List[MatchFactor]:
        """
        制造一批匹配因子
        :return: 复制的因子列表
        """
        if not self.cache:
            self.cache = []
            for factor in self.data:
                self.cache.append(MatchFactor(factor))
        else:
            for match_factor in self.cache:
                match_factor.reset()
        return self.cache


class CodeParser:
    def __init__(self):
        self.factor = CombinationFactor()
        """ 因子 """

    def add_token(self, token_type: str, *args: str):
        """
        注册单个token类型
        :param token_type:token类型
        :param args: token
        """
        for token in args:
            self.factor.add_factor(token_type, token)

    def add_combination(self, token_type: str, start: str, end: str, next_parser=None, self_mark=None, need_escape=False):
        """
        添加组合token
        :param token_type:
        :param start:开始
        :param end: 结束
        :param next_parser:匹配后下一层解析
        :param self_mark: 自身标记
        :param need_escape: 需要转义匹配
        """
        self.factor.add_factor(token_type, start, end, next_parser, self_mark, need_escape)

    def switch_token(self, index, source_code):
        # 符合的因子
        satisfy_factor = []
        # 判断起始因子队列
        judge_start_list = self.factor.to_match_factor()
        # 下一次待判断因子
        next_start_list = []
        while index < len(source_code):
            now_char = source_code[index]
            for match in judge_start_list:
                similar, equal = match.prefix(now_char)
                # 前缀相同则放入符合因子中
                if equal:
                    match.end_index = index
                    satisfy_factor.append(match)
                # 相似则需要进一步判断
                elif similar:
                    next_start_list.append(match)
            # 队列交换操作
            judge_start_list, next_start_list = next_start_list, []
            if not judge_start_list:
                break
            index += 1
        # 排序，起始标识进行升序
        satisfy_factor.sort(key=lambda x: x.factor.start)
        return satisfy_factor

    def to_token(self, source_code, any_type="any", skip_type=None) -> List[Token]:
        """
        将代码解析成token
        :param source_code:源码
        :param any_type: 未识别类型
        :param skip_type: 跳过的类型
        :return: token列表
        """
        if skip_type:
            if isinstance(skip_type, str):
                skip_type = {skip_type}
            else:
                skip_type = set(skip_type)
        else:
            skip_type = set()

        token_list = []
        now_index = 0
        any_token = ""
        while now_index < len(source_code):
            find_token = self.switch_token(now_index, source_code)
            if len(find_token) == 0:
                any_token += source_code[now_index]
            else:
                if any_token != "":
                    token_list.append(Token.any_token(any_type, any_token, now_index - 1))
                    any_token = ""

                last_token = find_token[-1]
                if last_token.factor.status not in skip_type:
                    # 缓存结尾下标，防止递归解析时，信息丢失
                    end_index = last_token.end_index
                    # 如果需要递归解析
                    if last_token.factor.next_parser is not None:
                        # 先进性计算，递归解析中会将当前状态信息重置
                        start_index = end_index - len(last_token.cache) - 1
                        self_mark = last_token.factor.status
                        # 如果有自身类型，则装配自身类型
                        if last_token.factor.self_mark:
                            self_mark = last_token.factor.self_mark
                        # 进行递归解析
                        temp_token_list = last_token.factor.next_parser.to_token(last_token.cache, last_token.factor.status, skip_type)
                        # 此处计算的是起始坐标
                        token_list.append(Token.start_type(self_mark, last_token.factor.start, start_index))
                        for token in temp_token_list:
                            token.end_index = start_index + token.end_index + 1
                        token_list.extend(temp_token_list)
                        token_list.append(Token.end_type(self_mark, last_token.factor.end, end_index))

                    else:
                        token_list.append(Token(last_token))
                    now_index = end_index

            now_index += 1
        if any_token != "":
            token_list.append(Token.any_token(any_type, any_token, now_index - 1))
        return token_list
