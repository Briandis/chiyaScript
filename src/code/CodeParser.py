import time
from typing import List, Dict


class MatchRule:

    def __init__(self, data: str, need_match=False, ignore_case=False):
        self.data = data
        """ 匹配的字符 """
        self.need_match: bool = need_match
        """ 需要进行匹配 """
        self.ignore_case: bool = ignore_case
        """ 忽略大小写 """
        self.length: int = len(data)
        """ 长度 """


class IndexTree:
    class _TreeNode:
        def __init__(self):
            """ 节点 """
            self.children: Dict[str, IndexTree._TreeNode] = {}
            """ 子节点 """
            self.end = []
            """ 包含 """
            self.need_match: List[IndexTree._TreeNode] = []

        def add(self, key):
            """
            添加索引的信息
            :param key:索引的key
            :return: 当前这个key的节点
            """
            if key not in self.children:
                self.children[key] = IndexTree._TreeNode()
            return self.children[key]

    def __init__(self):
        self.root: IndexTree._TreeNode = self._TreeNode()
        """ 根节点 """
        self.match_node = self.root
        """ 当前匹配节点 """

    def reset(self):
        self.match_node = self.root

    @staticmethod
    def _to_match_rule(data: str, need_match=False, ignore_case=False):
        if isinstance(data, str):
            return MatchRule(data, need_match, ignore_case)
        return data

    @staticmethod
    def create_index(key, start_node: _TreeNode, match_rule: MatchRule):
        node_list = set()
        node_list.add(start_node)
        for now_char in match_rule.data:
            next_node = set()
            # 忽略大小写情况，对所有路径进行添加
            for now_node in node_list:
                if match_rule.ignore_case:
                    next_node.add(now_node.add(now_char.lower()))
                    next_node.add(now_node.add(now_char.upper()))
                else:
                    next_node.add(now_node.add(now_char))
            node_list = next_node

        for now_node in node_list:
            now_node.end.append(key)
        return node_list

    def add(self, key, start_data: MatchRule | str):
        """
        添加
        :param key:唯一标识
        :param start_data: 数据
        """
        start_data = self._to_match_rule(start_data)
        self.create_index(key, self.root, start_data)

    def match(self, now_char):
        """
        迭代匹配
        :param now_char:当前字符
        """
        is_match = now_char in self.match_node.children
        result = []
        if is_match:
            self.match_node = self.match_node.children[now_char]
            result = self.match_node.end
        return result, not is_match or not self.match_node.children


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

    def match(self, next_data, context=None):
        """
        对迭代序列进行迭代
        :param next_data: 下一个迭代的数据
        :param context: 上下文
        :return: 是前缀，完全匹配
        """
        if context:
            if context.small_start:
                temp_flag, is_eq = context.small_start.match(next_data)
                if not temp_flag:
                    context.small_start.reset()
                if is_eq:
                    context.small_start.reset()
                    context.start_count += 1
            if context.small_end:
                temp_flag, is_eq = context.small_end.match(next_data)
                if not temp_flag:
                    context.small_end.reset()
                if is_eq:
                    context.small_end.reset()
                    context.end_count += 1

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


class TokenRule:

    def __init__(self, status, start, end, need_escape=False, next_parser=None, self_mark=None, count_start=None, count_end=None, next_all_match=False):
        """
        构造方法
        :param status: 状态
        :param start: 开始字符
        :param end: 结束字符
        :param need_escape: 需要转义
        :param next_parser: 匹配后解析
        :param self_mark:自身标记
        :param count_start: 计数开始
        :param count_end: 计数结束
        :param next_all_match: 下一层全部重新解析
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
        self.count_start = count_start
        """ 计数开始 """
        self.count_end = count_end
        """ 计数结束 """
        self.next_all_match = next_all_match
        """ 下一层全部重新解析 """


class MatchToken:
    def __init__(self, token_rule: TokenRule):
        self.token_rule: TokenRule = token_rule
        """ 因子 """
        self.end_match = IterativeMatch(self.token_rule.end)
        """ 结尾匹配 """
        self.cache = ""
        """ 缓存中间字符 """
        self.escape = False
        """ 转义字符状态 """
        self.end_index = -1
        """ 最终停止的字符位置 """
        self.start_count = 0
        """ 开始的计数 """
        self.end_count = 0
        """ 结尾的计数 """
        self.small_start = None
        self.small_end = None
        if self.token_rule.count_start:
            self.small_start = IterativeMatch(self.token_rule.count_start)
        if self.token_rule.count_end:
            self.small_end = IterativeMatch(self.token_rule.count_end)

    def prefix_end(self, next_char):
        """
        判断该字符串是不是前缀，
        :param next_char: 下一个字符
        :return: True/False
        """
        if self.token_rule.end is None:
            return False, True
        # 转义字符
        if self.token_rule.need_escape:
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
        similar, equal = self.end_match.match(next_char, self)
        equal = equal and self.start_count == self.end_count
        if equal:
            self.cache = self.cache[0:len(self.cache) - len(self.token_rule.end)]
        return True, equal


class MatchResult:

    def __init__(self, token_rule: TokenRule, end_index: int, data: str = ""):
        self.token_rule = token_rule
        self.end_index = end_index
        self.data = data


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

    @staticmethod
    def create(token_type: str, token_start: str | None = None, token_data: str | None = "", token_end: str | None = None):
        """
        创建token
        :param token_type:token类型
        :param token_start: 左侧字符
        :param token_data: 右侧字符
        :param token_end: 结束字符
        :return: token
        """
        token = Token()
        token.type = token_type
        token.start = token_start
        token.data = f'{token_data}'
        token.end = token_end
        return token

    def __init__(self, match_factor: MatchResult = None):
        self.type = None
        """ 类型 """
        self.token_tree: List[Token] = []
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
        self.line_start = None
        """ 源文件出现的起始行 """
        self.line_end = None
        """ 源文件出现的结束行 """

        if match_factor is not None:
            self.start = match_factor.token_rule.start
            self.end = match_factor.token_rule.end
            self.data = match_factor.data
            self.type = match_factor.token_rule.status
            self.end_index = match_factor.end_index

    def add_tree(self, token):
        """
        添加树
        :param token: Token节点
        """
        self.token_tree.append(token)

    def create_tree(self, token_type: str, token_start: str | None = None, token_data: str | None = "", token_end: str | None = None):
        """
        直接往token树中添加新token
        :param token_type:token类型
        :param token_start: 左侧字符
        :param token_data: 右侧字符
        :param token_end: 结束字符
        """
        self.token_tree.append(Token.create(token_type, token_start, token_data, token_end))


class ParserMatch:

    def __init__(self):
        self.data: List[TokenRule] = []
        """ 全部因子信息 """
        self.index_tree = IndexTree()
        """ 前缀匹配索引 """
        self.match_index = {}
        """ 后缀匹配器索引 """

    def add_rule(self, status, start, end=None, next_parser=None, self_mark=None, need_escape=False, count_start=None, count_end=None, next_all_match=False):
        """
        添加因子
        :param status:状态
        :param start: 开始
        :param end: 结束
        :param next_parser:下一层解析
        :param self_mark:自身标记
        :param need_escape:需要转义处理
        :param count_start: 计数开始
        :param count_end: 计数结束
        :param next_all_match: 下一层全部重新解析
        """
        self.data.append(TokenRule(status, start, end, need_escape, next_parser=next_parser, self_mark=self_mark, count_start=count_start, count_end=count_end, next_all_match=next_all_match))
        self.index_tree.add(len(self.data) - 1, start)
        if end:
            self.match_index[len(self.data) - 1] = self.data[-1]

    def match(self, index, source_code) -> List[MatchResult]:
        self.index_tree.reset()
        result: List[MatchResult] = []
        judge_match: List[MatchToken] = []
        next_match: List[MatchToken] = []
        is_over = False
        while index < len(source_code):
            now_char = source_code[index]

            for match in judge_match:
                similar, equal = match.prefix_end(now_char)
                # 前缀相同则放入符合因子中
                if equal:
                    result.append(MatchResult(match.token_rule, index, match.cache))
                # 相似则需要进一步判断
                elif similar:
                    next_match.append(match)
            judge_match, next_match = next_match, []

            if not is_over:
                key_list, is_over = self.index_tree.match(now_char)
                for key in key_list:
                    if key in self.match_index:
                        match_factor = MatchToken(self.data[key])
                        judge_match.append(match_factor)
                    else:
                        result.append(MatchResult(self.data[key], index))
            if is_over and not judge_match:
                break
            index += 1
        return result


class CodeParser:
    def __init__(self):
        self.parser_match = ParserMatch()
        """ 因子 """

    def add_token(self, token_type: str, *args: str):
        """
        注册单个token类型
        :param token_type:token类型
        :param args: token
        """
        for token in args:
            self.parser_match.add_rule(token_type, token)

    def add_combination(self, token_type: str, start: str, end: str, next_parser=None, self_mark=None, need_escape=False, count_start=None, count_end=None, next_all_match=False):
        """
        添加组合token
        :param token_type:
        :param start:开始
        :param end: 结束
        :param next_parser:匹配后下一层解析
        :param self_mark: 自身标记
        :param need_escape: 需要转义匹配
        :param count_start: 计数开始
        :param count_end: 计数结束
        :param next_all_match: 下一层全部重新解析
        """
        self.parser_match.add_rule(token_type, start, end, next_parser, self_mark, need_escape, count_start, count_end, next_all_match)

    def to_token(self, source_code, any_type="any", skip_type=None, line_count=0) -> List[Token]:
        """
        将代码解析成token
        :param source_code:源码
        :param any_type: 未识别类型
        :param skip_type: 跳过的类型
        :param line_count: 行坐标信息
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
        line_start = 0

        while now_index < len(source_code):
            match_result = self.parser_match.match(now_index, source_code)
            if match_result:
                line_start = line_count
                # 未知字符处理
                if any_token != "":
                    if any_type not in skip_type:
                        token_list.append(Token.any_token(any_type, any_token, now_index - 1))
                        token_list[-1].line_start = line_start
                        token_list[-1].line_end = line_count
                    any_token = ""

                last_match = match_result[-1]
                # 缓存结尾下标，防止递归解析时，信息丢失
                end_index = last_match.end_index
                # 计算行坐标
                for char_index in range(end_index - now_index + 1):
                    if source_code[char_index + now_index] == '\n':
                        line_count += 1
                if last_match.token_rule.status not in skip_type:
                    # 如果需要递归解析
                    if last_match.token_rule.next_parser is not None:
                        # 先进性计算，递归解析中会将当前状态信息重置
                        start_index = end_index - len(last_match.data) - 1
                        self_mark = last_match.token_rule.status
                        # 如果有自身类型，则装配自身类型
                        if last_match.token_rule.self_mark:
                            self_mark = last_match.token_rule.self_mark
                        # 如果需要下层全部重新解析
                        if last_match.token_rule.next_all_match:
                            # 进行递归解析
                            temp_token_list = last_match.token_rule.next_parser.to_token(
                                last_match.token_rule.start + last_match.data + last_match.token_rule.end,
                                any_type,
                                skip_type,
                                line_count - 1)
                            # 此处计算的是起始坐标
                            for token in temp_token_list:
                                token.end_index = start_index + token.end_index + 1
                            token_list.extend(temp_token_list)
                        else:
                            temp_token_list = last_match.token_rule.next_parser.to_token(last_match.data, last_match.token_rule.status, skip_type, line_count - 1)
                            # 此处计算的是起始坐标
                            temp_token = Token.start_type(self_mark, last_match.token_rule.start, start_index)
                            temp_token.line_start = line_start
                            temp_token.line_end = line_start
                            token_list.append(temp_token)
                            for token in temp_token_list:
                                token.end_index = start_index + token.end_index + 1
                            token_list.extend(temp_token_list)
                            token_list.append(Token.end_type(self_mark, last_match.token_rule.end, end_index))
                    else:
                        token_list.append(Token(last_match))
                    token_list[-1].line_start = line_start
                    token_list[-1].line_end = line_count
                    if source_code[now_index] == '\n':
                        token_list[-1].line_end -= 1
                now_index = end_index
            else:
                any_token += source_code[now_index]
            now_index += 1
        if any_token != "":
            token_list.append(Token.any_token(any_type, any_token, now_index - 1))
            # 此处解决any的问题
            token_list[-1].line_start = line_count
            token_list[-1].line_end = line_count
        return token_list
