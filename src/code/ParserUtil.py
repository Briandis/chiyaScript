from typing import List, Dict

from src.code.CodeParser import Token


class CodeHandle:
    @staticmethod
    def join(old_code: str, code_token: List[Token], token_list: List[str]) -> str:
        """
        替换代码
        :param old_code: 旧代码
        :param code_token: 旧代码的token
        :param token_list: 要替换的新token
        :return:
        """
        new_code = []
        now_index = 0
        token_index = 0
        recursion_stack = [*code_token]
        recursion_stack.reverse()

        while recursion_stack:
            token = recursion_stack.pop()
            # 计算切割位置
            end_index = token.end_index
            if token.end:
                end_index = token.end_index - len(token.end)
            start_index = end_index - len(token.data) + 1
            # 切割无关字符
            new_code.append(old_code[now_index:start_index])
            now_index = end_index + 1
            # 替换
            new_code.append(token_list[token_index])
            token_index += 1
            # 深层递归
            if token.token_tree:
                next_list = [*token.token_tree]
                next_list.reverse()
                recursion_stack.extend(next_list)
        new_code.append(old_code[now_index:len(old_code)])
        return "".join(new_code)

    @staticmethod
    def replace(code_token: List[Token], replace_rule: Dict[str, Dict[str, str]], ignore_case=False):
        """
        替换token列表,替换规则为{
            "类型1":{"old":"new"},
            "类型2":{"old":"new"}
        }
        :param code_token:token列表
        :param replace_rule: 替换规则
        :param ignore_case: 是否忽略大小写
        :return:
        """
        replace_data = []
        rule = replace_rule
        # 大小写统一处理
        if ignore_case:
            rule = {}
            for token_type, token_replace in replace_rule.items():
                rule[token_type.lower()] = {}
                for old_data, new_data in token_replace.items():
                    rule[token_type.lower()][old_data.lower()] = new_data
        recursion_stack = [*code_token]
        recursion_stack.reverse()
        while recursion_stack:
            token = recursion_stack.pop()
            # 类型
            compare = token.data
            if ignore_case:
                compare = compare.lower()
            if token.type in rule and compare in rule[token.type]:
                replace_data.append(rule[token.type][compare])
            else:
                replace_data.append(token.data)
            # 如果有深层，则对深层的进行递归
            if token.token_tree:
                next_list = [*token.token_tree]
                next_list.reverse()
                recursion_stack.extend(next_list)
        # 返回
        return replace_data

    @staticmethod
    def equal(a_token: Token, b_token: Token):
        type_flag = b_token.type is None or a_token.type == b_token.type
        data_flag = b_token.start is None or b_token.start == a_token.start
        data_flag = data_flag and (b_token.data is None or b_token.data == "" or b_token.data == a_token.data)
        data_flag = data_flag and (b_token.end is None or b_token.end == a_token.end)
        return type_flag and data_flag

    @staticmethod
    def match(list_token: List[Token], rule: List[Token]):
        flag = True
        for index in range(0, len(rule)):
            match_token = list_token[index]
            rule_token = rule[index]
            if CodeHandle.equal(match_token, rule_token):
                flag = flag and CodeHandle.match(match_token.token_tree, rule_token.token_tree)
            else:
                return False
        return flag

    @staticmethod
    def find(list_token: List[Token], rule: List[Token], result: []):
        index = 0
        for token in list_token:
            if CodeHandle.match(list_token[index:], rule):
                result.append(token)
            index += 1
            if token.token_tree:
                CodeHandle.find(token.token_tree, rule, result)

    @staticmethod
    def tree_replace(list_token: List[Token], rule: List[Token], get_token_method):
        index = 0
        for token in list_token:
            if CodeHandle.match(list_token[index:], rule):
                list_token[index] = get_token_method(list_token[index])
            index += 1
            if token.token_tree:
                CodeHandle.tree_replace(token.token_tree, rule, get_token_method)
