import time
from typing import List, Dict

from src.code.ChiyaScript import LoggerUtil
from src.code.CodeParser import Token
from src.code.Flow import Flow


def token_debug(tokens: Token | List[Token], indent=0):
    if isinstance(tokens, Token):
        tokens = [tokens]
    for token in tokens:
        token_info = LoggerUtil.padding([
            f'{indent * "  "}{token.type}',
            f'开始行:{token.line_start}',
            f'结束行:{token.line_end}',
            token.end_index,
            f'{token.start}'.encode(),
            f'{token.data}'.encode(),
            f'{token.end}'.encode()
        ], [35, 15, 15, 20, 15, 25, 5])
        print(token_info)
        if token.token_tree:
            token_debug(token.token_tree, indent + 1)


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

    def __init__(self, status, need_match=False, need_paired=False, extend_type=None, father_index=None, merge=False):
        """
        初始化
        :param status: 语法结构
        :param need_match: 需要匹配
        :param need_paired: 需要成对
        :param extend_type: 继承那个位置上的类型
        :param father_index: 充当父级token的下标
        :param merge: 根据上一个token类型判断是否需要合并
        """
        self.syntax: List[LexicalFactor] = []
        """ 语法结构 """
        self.status = status
        """ 自身类型 """
        self.need_match = need_match
        """ 需要匹配 """
        self.need_paired = need_paired
        """ 需要左右成对 """
        self.token_type: Dict[int, str | Dict[str, str]] = {}
        """ 匹配后替换的token类型 """
        self.extend_type = extend_type
        """ 继承类型为特定位置上的类型 """
        self.father_index = father_index
        """ 充当父级token的下标 """
        self.merge = merge
        """ 是否合并 """

    def add_lexical(self, *lexical_list: LexicalFactor):
        """
        添加语法
        :param lexical_list:
        :return:
        """
        for lexical in lexical_list:
            self.syntax.append(lexical)

    def add_type(self, type_info: Dict[int, str | Dict[str, str]]):
        """
        添加替换类型,会根据匹配位置进行类型替换,key为替换的下标,value为替换的类型
        :param type_info:类型列表
        """
        self.token_type.update(type_info)


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
        self.first_flag = True

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
                start_flag = self.token_same(start_token, next_token)
                end_flag = self.token_same(end_token, next_token)
                if start_flag:
                    self.paired_start_count += 1
                    self.paired_flag = True
                if end_flag:
                    self.paired_end_count += 1
                # 如果在同一个token中同时互相满足极为自身，要忽略第一次
                if start_flag and end_flag and self.first_flag:
                    self.first_flag = False
                    return True, False
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

    def change_type(self, token_list: List[Token]):
        """
        匹配后更改对应位置的token类型，以配置的类型为基准
        :param token_list:token列表
        """
        for index, token_type in self.syntax_factor.token_type.items():
            if isinstance(token_type, str):
                # 字符串的情况
                token_list[index].type = token_type
            elif isinstance(token_type, dict) and token_list[index].type in token_type:
                # 字典的情况
                token_list[index].type = token_type[token_list[index].type]


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


class SyntaxParserConfig:

    def __init__(self, need_recursion=False, prefix_outside=False, suffix_outside=False, prefix_match=False, suffix_match=False, next_paser=None):
        """
        语法解析配置
        :param need_recursion:需要递归
        :param prefix_outside:前缀匹配的token放到外层
        :param suffix_outside: 后缀匹配的token放到外层
        :param prefix_match:前缀继续匹配
        :param suffix_match:后缀继续匹配
        :param next_paser:下一层解析器
        """
        self.need_recursion = need_recursion
        """ 需要递归 """
        self.prefix_outside = prefix_outside
        """ 前缀匹配的token放到外层 """
        self.suffix_outside = suffix_outside
        """ 后缀匹配的token放到外层 """
        self.prefix_match = prefix_match
        """ 前缀继续匹配 """
        self.suffix_match = suffix_match
        """ 后缀继续匹配 """
        self.next_paser = next_paser


class SyntaxParser:

    def __init__(self):
        self.flow: Flow[SyntaxParserConfig] = Flow()
        self.keyword_list = []

    def add_syntax(self, index, syntax_factor: SyntaxFactor, need_recursion=False, prefix_outside=False, suffix_outside=False, prefix_match=False, suffix_match=False, next_paser=None):
        """
        添加语法，
        :param index: 优先级
        :param syntax_factor:语法
        :param need_recursion:需要递归解析
        :param prefix_outside:匹配的前缀放置外层
        :param suffix_outside:匹配的周会放置外层
        :param prefix_match:前缀继续匹配
        :param suffix_match:后缀继续匹配
        :param next_paser:下一层解析器
        """

        if index in self.flow.flow:
            self.flow.flow[index][0].flow_data.add_syntax(syntax_factor)
        else:
            syntax = SyntaxList()
            syntax.add_syntax(syntax_factor)
            self.flow.add_flow(index, "syntax", syntax, SyntaxParserConfig(need_recursion, prefix_outside, suffix_outside, prefix_match, suffix_match, next_paser))

    def add_flow(self, index, method):
        """
        添加流
        :param index:流索引
        :param method: 处理方法
        """
        self.flow.add_flow(index, "flow", method, None)

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

    def mark_keyword(self, token_list: List[Token], ignore_case=False, replace_type="any"):
        """
        标记关键字
        :param token_list: token列表
        :param ignore_case:忽略大小写
        :param replace_type:替换的类型
        """
        # 标记关键字
        keyword = set()
        if ignore_case:
            for item in self.keyword_list:
                keyword.add(item.lower())
        else:
            keyword.update(self.keyword_list)

        for token_data in token_list:
            now_data = token_data.data
            if ignore_case:
                now_data = now_data.lower()
            if token_data.type == replace_type and now_data in keyword:
                token_data.type = "key:" + now_data
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
        return satisfy_factor[::-1]

    @staticmethod
    def father_token(syntax: SyntaxMatch, branch: Token, while_list: List[Token], now_index):
        """
        父级继承类型token处理
        :param syntax:语法匹配器
        :param branch: 当前构建支
        :param while_list: 下一次匹配判别队列
        :param now_index: 当前下标
        :return:
        """
        if syntax.syntax_factor.father_index is not None:
            temp_branch = branch.token_tree[syntax.syntax_factor.father_index]
            if syntax.syntax_factor.merge and temp_branch.type == syntax.syntax_factor.status or syntax.syntax_factor.merge is False:
                # 如果需要合并，且和自身类型相同或者是不需要合并
                for temp_token in branch.token_tree:
                    if temp_branch != temp_token:
                        temp_branch.token_tree.append(temp_token)
                while_list[now_index] = temp_branch
                while_list[now_index].line_start = while_list[now_index].token_tree[0].line_start
                while_list[now_index].line_end = while_list[now_index].token_tree[-1].line_end
            else:
                # 不满足则新建
                while_list[now_index] = branch
        else:
            while_list[now_index] = branch

    def to_token(self, flow, while_list, is_debug=False):
        now_index = 0
        next_list = []
        while now_index < len(while_list):
            # 匹配找到的token
            syntax_factor = self.switch_factor(flow.flow_data, now_index, while_list)
            # 如果存在构成词法的，则进行添加
            if syntax_factor:
                syntax = syntax_factor[0]
                branch = Token()
                branch.type = syntax.syntax_factor.status
                if is_debug:
                    print("当前判别类型", syntax.syntax_factor.status, "找到的结尾", syntax.now_index)
                    token_debug(while_list)
                    print()
                # 需要递归
                if flow.config.need_recursion:
                    temp_list = while_list[now_index:now_index + syntax.now_index]
                    syntax.change_type(temp_list)

                    start_index = 1
                    end_index = -1
                    if flow.config.prefix_match:
                        start_index = 0
                    else:
                        # 该token是否放置外层
                        if flow.config.prefix_outside:
                            next_list.append(temp_list[0])
                        else:
                            branch.add_tree(temp_list[0])
                    if flow.config.suffix_match:
                        end_index = None
                    if is_debug:
                        print("递归解析", start_index, end_index, len(temp_list))
                        token_debug(temp_list[start_index:end_index])
                        print()

                    for token in self.parser(temp_list[start_index:end_index], is_debug):
                        branch.add_tree(token)
                    if is_debug:
                        print("回退", syntax.now_index)
                    now_index = now_index + syntax.now_index - 1
                    if flow.config.suffix_outside and not flow.config.suffix_match and not syntax.end_flag:
                        # 如果有放置在外层，且不要后续匹配，且不需要结尾匹配
                        next_list.append(branch)
                    else:
                        if not flow.config.suffix_match:
                            branch.add_tree(temp_list[-1])
                        # 改变token树
                        self.father_token(syntax, branch, while_list, now_index)
                    if is_debug:
                        print("以递归方式判别到的", syntax.syntax_factor.status)
                        token_debug(branch)
                        print()
                else:
                    for token in while_list[now_index:now_index + syntax.now_index]:
                        branch.add_tree(token)
                    if is_debug:
                        print("以常规方式判别到的", syntax.syntax_factor.status)
                        token_debug(branch)
                        print()
                    now_index = now_index + syntax.now_index - 1
                    # 改变token树
                    self.father_token(syntax, branch, while_list, now_index)
                    syntax.change_type(branch.token_tree)
                if syntax.syntax_factor.extend_type is not None:
                    branch.type = branch.token_tree[syntax.syntax_factor.extend_type].type
                # 更新当前分支的所在行信息
                branch.line_start = branch.token_tree[0].line_start
                branch.line_end = branch.token_tree[-1].line_end
            else:
                next_list.append(while_list[now_index])
                now_index += 1
        return next_list

    def parser(self, token_list: List[Token], is_debug=False):
        """
        解析生成语法树
        :param token_list:Token列表
        :param is_debug: debug选项
        :return:
        """
        while_list = [*token_list]
        for flow in self.flow:
            match flow.type:
                case "syntax":
                    while_list = self.to_token(flow, while_list, is_debug)
                case "flow":
                    while_list = flow.flow_data(while_list)
        if is_debug:
            print("解析结束返回")
            token_debug(while_list)
            print()
        return while_list
