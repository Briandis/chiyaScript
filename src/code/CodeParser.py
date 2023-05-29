from typing import List


class StringMatch:

    def __init__(self, data: str):
        self.data = data
        """ 存储的字符串 """
        self.index = 0
        """ 当前判断的下标 """

    def reset(self):
        """ 重置 """
        self.index = 0

    def match(self, next_string):
        """
        判断下一个字符符不符合
        :param next_string: 下一个字符串
        :return: 是前缀，完全匹配
        """
        if self.data is None or len(self.data) == 0:
            return True, True
        for char in next_string:
            if self.data[self.index] == char:
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

    def __init__(self, status, start, end, need_escape=True, need_in_pairs=False):
        """
        构造方法
        :param status: 状态
        :param start: 开始字符
        :param end: 结束字符
        :param need_escape: 需要转义
        :param need_in_pairs: 不需要转义
        """
        self.start = start
        """ 开始 """
        self.end = end
        """ 结束 """
        self.status = status
        """ 状态 """
        self.need_escape = need_escape
        """ 需要转义 """
        self.need_in_pairs = need_in_pairs
        """ 需要成对 """


class MatchFactor:
    def __init__(self, factor: Factor):
        self.factor: Factor = factor
        """ 因子 """
        self.start_match = StringMatch(self.factor.start)
        """ 开始匹配 """
        self.end_match = StringMatch(self.factor.end)
        """ 结尾匹配 """
        self.cache = ""
        """ 缓存中间字符 """
        self.escape = False
        """ 转义字符状态 """
        self.end_index = -1
        """ 最终停止的字符位置 """

    def prefix_start(self, next_char):
        """
        判断该字符串是不是前缀，
        :param next_char: 下一个字符
        :return: True/False
        """
        similar, equal = self.start_match.match(next_char)
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
    def __init__(self, match_factor: MatchFactor):
        self.start = match_factor.factor.start
        """ 开始 """
        self.end = match_factor.factor.end
        """ 结束 """
        self.data = match_factor.cache
        """ 内容 """
        self.type = match_factor.factor.status
        """ 类型 """
        self.end_index = match_factor.end_index
        """ 源文件字符位置 """


class CombinationFactor:

    def __init__(self):
        self.data: List[Factor] = []
        """ 全部因子信息 """

    def add_factor(self, status, start, end=None):
        """
        添加因子
        :param status:状态
        :param start: 开始
        :param end: 结束
        """
        self.data.append(Factor(status, start, end))

    def to_match_factor(self) -> List[MatchFactor]:
        """
        制造一批匹配因子
        :return: 复制的因子列表
        """
        out_list = []
        for factor in self.data:
            out_list.append(MatchFactor(Factor(factor.status, factor.start, factor.end)))
        return out_list


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

    def add_combination(self, token_type: str, start: str, end: str):
        """
        添加组合token
        :param token_type:
        :param start:开始
        :param end: 结束
        """
        self.factor.add_factor(token_type, start, end)

    def switch_token(self, index, source_code):
        # 符合的因子
        satisfy_factor = []
        # 判断起始因子队列
        judge_start_list = self.factor.to_match_factor()
        # 下一次待判断因子
        next_start_list = []
        # 判断结束因子队列
        judge_end_list = []
        # 下一次待判断因子
        next_end_list = []
        while index < len(source_code):
            now_char = source_code[index]

            for token in judge_start_list:
                similar, equal = token.prefix_start(now_char)
                # 前缀相同则放入符合因子中
                if equal:
                    if token.factor.end is None:
                        token.end_index = index
                        satisfy_factor.append(token)
                    else:
                        next_end_list.append(token)
                # 相似则需要进一步判断
                elif similar:
                    next_start_list.append(token)
            for token in judge_end_list:
                similar, equal = token.prefix_end(now_char)
                # 前缀相同则放入符合因子中
                if equal:
                    token.end_index = index
                    satisfy_factor.append(token)
                # 相似则需要进一步判断
                elif similar:
                    next_end_list.append(token)
            # 队列交换操作
            judge_start_list, next_start_list = next_start_list, []
            judge_end_list, next_end_list = next_end_list, []
            # print("当前字符 ->", now_char)
            # print("起始队列", judge_start_list)
            # print("结束队列", judge_end_list)
            # print("符合因子", satisfy_factor)
            if len(judge_start_list) == 0 and len(judge_end_list) == 0:
                break
            index += 1
        # 排序，起始标识进行升序
        for i in range(len(satisfy_factor)):
            for j in range(i, len(satisfy_factor)):
                if len(satisfy_factor[i].factor.start) > len(satisfy_factor[j].factor.start):
                    satisfy_factor[i], satisfy_factor[j] = satisfy_factor[j], satisfy_factor[i]
        # for token in satisfy_factor:
        #     print(token.factor.status, token.end_index, token.factor.start, token.factor.end, token.cache)
        return satisfy_factor

    def to_token(self, source_code) -> List[Token]:
        token_list = []
        now_index = 0
        any_token = ""
        while now_index < len(source_code):
            find_token = self.switch_token(now_index, source_code)
            if len(find_token) == 0:
                any_token += source_code[now_index]
            else:
                if any_token != "":
                    match_factor = MatchFactor(Factor("any", None, None))
                    match_factor.cache = any_token
                    match_factor.end_index = now_index - 1
                    token_list.append(Token(match_factor))
                    any_token = ""
                last_token = find_token[-1]
                token_list.append(Token(last_token))
                now_index = last_token.end_index
            now_index += 1
        if any_token != "":
            match_factor = MatchFactor(Factor("any", None, None))
            match_factor.cache = any_token
            match_factor.end_index = now_index - 1
            token_list.append(Token(match_factor))
        return token_list


class LexicalFactor:
    def __init__(self, data=None, *token_type, ):
        """
        词法
        :param token_type: token类型
        :param data: token的值
        """
        self.type = []
        """ token类型 """
        self.data = data
        """ token的值 """
        self.type.extend(token_type)


class AbstractSyntaxTree:

    def __init__(self, status):
        self._syntax: List[LexicalFactor] = []
        """ 语法结构 """
        self.status = status
        """ 自身类型 """

    def add_lexical(self, *lexical_list):
        """
        添加语法
        :param lexical_list:
        :return:
        """
        for lexical in lexical_list:
            self._syntax.append(lexical)


a = AbstractSyntaxTree("attribute")
a.add_lexical(LexicalFactor(None, "any", "attribute"), LexicalFactor(".", None), LexicalFactor("any", "any"))
