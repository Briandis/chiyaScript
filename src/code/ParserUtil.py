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
        new_code = ""
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
            new_code += old_code[now_index:start_index]
            now_index = end_index + 1
            # 替换
            new_code += token_list[token_index]
            token_index += 1
            # 深层递归
            if token.token_tree:
                next_list = [*token.token_tree]
                next_list.reverse()
                recursion_stack.extend(next_list)
        new_code += old_code[now_index:len(old_code)]
        return new_code

    @staticmethod
    def replace(code_token: List[Token], replace_rule: Dict[str, Dict[str, str]], ignore_case=False):
        """
        替换token列表
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
