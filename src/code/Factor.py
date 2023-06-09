from typing import List

from src.code.CodeParser import Token


class WordRule:
    def __init__(self, start=None, data=None, end=None):
        """
        字符规则
        :param start:起始字符
        :param data: 中间字符
        :param end: 结尾字符
        """
        self.start = start
        """ 起始字符 """
        self.data = data
        """ 中间字符 """
        self.end = end
        """ 结尾字符 """

    def is_same(self, token: Token):
        """
        判断与token是否相同
        :param token: Token
        :return:  相同/不同
        """
        start_flag = self.start is None or self.start == token.start
        data_flag = self.data is None or self.data == token.data
        end_flag = self.end is None or self.end == token.end
        return start_flag and data_flag and end_flag


class LexicalFactor:
    def __init__(self, word_rule: WordRule | None = None, *token_type, allow_end=False):
        """
        词法
        :param token_type: token类型
        :param word_rule: 字符规则
        :param allow_end:允许结尾没有匹配
        """
        self.type = []
        """ token类型 """
        self.word_rule = word_rule
        """ token的值 """
        self.type.extend(token_type)
        self.allow_end = allow_end
        """ 允许结尾没有匹配 """


class SyntaxFactor:

    def __init__(self, status, need_match=False, need_paired=False):
        self.syntax: List[LexicalFactor] = []
        """ 语法结构 """
        self.status = status
        """ 自身类型 """
        self.need_match = need_match
        """ 需要匹配 """
        self.need_paired = need_paired
        """ 需要左右成对 """

    def add_lexical(self, *lexical_list):
        """
        添加语法
        :param lexical_list:
        :return:
        """
        for lexical in lexical_list:
            self.syntax.append(lexical)


class SyntaxMatch:

    def __init__(self, syntax_factor: SyntaxFactor):
        self.syntax_factor = syntax_factor
        """ 语法因子 """
        self.now_index = 0
        """ 当前下标 """
        self.paired_start_count = 0
        """ 成对左边计数 """
        self.paired_end_count = 0
        """ 成对右边技术 """
        self.paired_flag = False
        """ 成对标记 """
        self.end_flag = False
        """ 标记允许匹配到结尾中止 """

    @staticmethod
    def token_same(now_factor, now_token):
        """
        token与匹配值相同
        :param now_factor:
        :param now_token:
        :return:
        """
        in_type = None in now_factor.type or now_token.type in now_factor.type or len(now_factor.type) == 0
        in_data = now_factor.word_rule is None or now_factor.word_rule.is_same(now_token)
        return in_type and in_data

    def prefix(self, next_token: Token):
        """
        判断因子符不符合条件
        :param next_token: 下一个
        :return: True/False
        """
        # 匹配规则下
        if self.syntax_factor.need_match:
            self.now_index += 1
            start_token = self.syntax_factor.syntax[0]
            end_token = self.syntax_factor.syntax[-1]
            if self.syntax_factor.need_paired:
                if self.token_same(start_token, next_token):
                    self.paired_start_count += 1
                    self.paired_flag = True
                if self.token_same(end_token, next_token):
                    self.paired_end_count += 1
                return self.paired_flag, self.paired_start_count != 0 and self.paired_start_count == self.paired_end_count
            else:
                if not self.paired_flag and self.token_same(start_token, next_token):
                    self.paired_flag = True
                elif self.paired_flag and self.token_same(end_token, next_token):
                    return True, True
                return self.paired_flag, False
        else:
            now_factor = self.syntax_factor.syntax[self.now_index]
            if isinstance(now_factor, LexicalFactor):
                self.now_index += 1
                is_end = len(self.syntax_factor.syntax) == self.now_index
                is_similar = self.token_same(now_factor, next_token)
                return is_similar, is_similar and is_end


class SyntaxList:
    def __init__(self):
        self.data: List[SyntaxFactor] = []
        """ 语法 """

    def add_syntax(self, syntax: SyntaxFactor):
        """
        添加语法
        :param syntax: 语法
        """
        self.data.append(syntax)

    def to_match(self) -> List[SyntaxMatch]:
        """
        输出匹配列表对象
        :return: 匹配对象
        """
        out_list = []
        for factor in self.data:
            out_list.append(SyntaxMatch(factor))
        return out_list


class SyntaxParser:

    def __init__(self):
        self.flow_list = []
        self.keyword_list = []

    def add_syntax(self, flow, syntax_factor: SyntaxFactor, need_recursion=False, prefix_outside=False, suffix_outside=False):
        """
        添加语法，
        :param flow: 优先级
        :param syntax_factor:语法
        :param need_recursion:需要递归解析
        :param prefix_outside:匹配的前缀放置外层
        :param suffix_outside:匹配的周会放置外层
        """
        for flow_info in self.flow_list:
            if flow_info[0] == flow:
                flow_info[1].add_syntax(syntax_factor)
                return
        self.flow_list.append([flow, SyntaxList(), need_recursion, prefix_outside, suffix_outside])
        self.flow_list[-1][1].add_syntax(syntax_factor)

    @staticmethod
    def mark_type(token_list: List[Token], old_type: List[str] | str, new_type: str, old_data: List[str] = None, not_case_data: List[str] | None = None):
        """
        标记类型
        :param token_list: token列表
        :param old_type: 旧类型
        :param new_type: 新类型
        :param old_data: 区分大小写的之
        :param not_case_data: 不区分大小写的值
        """
        # 全部小写化
        if not_case_data:
            new_case = set()
            for data in not_case_data:
                new_case.add(data.lower())
            not_case_data = new_case
        if isinstance(old_data, str):
            old_data = [old_data]
        for token_data in token_list:
            if token_data.type in old_type:
                if old_data or not_case_data:
                    if old_data and token_data.data in old_data:
                        token_data.type = new_type
                    elif not_case_data and token_data.data.lower() in not_case_data:
                        token_data.type = new_type
                else:
                    token_data.type = new_type
        return token_list

    def mark_keyword(self, token_list: List[Token]):
        """
        标记关键字
        :param token_list: token列表
        :return:
        """
        # 标记关键字
        for token_data in token_list:
            if token_data.type == "any" and token_data.data in self.keyword_list:
                token_data.type = "key:" + token_data.data
        return token_list

    def register_keyword(self, *keyword):
        """
        声明关键字
        :param keyword:关键字
        """
        for key in keyword:
            self.keyword_list.append(key)

    @staticmethod
    def switch_factor(factor: SyntaxList, index, token_list: List[Token]) -> List[SyntaxMatch]:
        """
        选取因子
        :param factor: 因子列表
        :param index: 当前下标
        :param token_list: token列表
        :return: 因子匹配式子
        """
        # 符合的因子
        satisfy_factor = []
        # 判断起始因子队列
        judge_start_list = factor.to_match()
        # 下一次待判断因子
        next_start_list = []
        while index < len(token_list):
            now_token = token_list[index]

            for factor_match in judge_start_list:
                similar, equal = factor_match.prefix(now_token)
                if equal:
                    satisfy_factor.append(factor_match)
                elif similar:
                    next_start_list.append(factor_match)

            # 队列交换操作
            judge_start_list, next_start_list = next_start_list, []
            if len(judge_start_list) == 0:
                break
            index += 1
        # 对循环结束，允许匹配到结尾的类型
        if judge_start_list:
            for factor_match in judge_start_list:
                if factor_match.syntax_factor.syntax[-1].allow_end:
                    factor_match.end_flag = True
                    satisfy_factor.append(factor_match)
        # 排序，起始标识进行升序
        satisfy_factor.sort(key=lambda x: x.now_index)
        return satisfy_factor

    def parser(self, token_list: List[Token]):
        """
        解析生成语法树
        :param token_list:Token列表
        :return:
        """
        self.flow_list.sort(key=lambda x: x[0])
        while_list = [*token_list]

        for flow in self.flow_list:
            now_index = 0
            while now_index < len(while_list):
                # 匹配找到的token
                syntax_factor = self.switch_factor(flow[1], now_index, while_list)

                # 重新生成token序列
                new_while = []
                for add_index in range(now_index):
                    new_while.append(while_list[add_index])
                jump_index = 0
                # 如果存在构成词法的，则进行添加
                if syntax_factor:
                    syntax = syntax_factor[0]

                    branch = Token()
                    branch.type = syntax.syntax_factor.status
                    # 匹配查找
                    if flow[2]:
                        temp_list = []
                        for index in range(syntax.now_index):
                            temp_list.append(while_list[now_index + index])
                        # 对于匹配想，将前后匹配项加入树中，根据条件选择放置外面还是里面
                        if flow[3]:
                            new_while.append(temp_list[0])
                            now_index += 1
                        else:
                            branch.add_tree(temp_list[0])
                        for token in self.parser(temp_list[1:-1]):
                            branch.add_tree(token)
                        # 中间部分
                        new_while.append(branch)
                        # 结尾是否放入外面还是里面，如果是空结尾则不进行添加
                        if flow[4] and not syntax.end_flag:
                            new_while.append(temp_list[-1])
                            syntax.now_index -= 1
                        else:
                            branch.add_tree(temp_list[-1])
                    else:
                        for index in range(syntax.now_index):
                            branch.add_tree(while_list[now_index + index])
                        new_while.append(branch)
                    jump_index = syntax.now_index
                for add_index in range(now_index + jump_index, len(while_list)):
                    new_while.append(while_list[add_index])
                while_list = new_while
                if not syntax_factor:
                    now_index += 1
        return while_list
