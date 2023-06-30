from typing import Dict, List

from src.code.CodeParser import Token


class IterationStack:

    def __init__(self):
        self.var_stack = []
        """ 变量栈 """
        self.item_stack = []
        """ 迭代对象栈 """
        self.iteration_stack = []
        """ 迭代信息栈 """
        self.judge_method = None
        """ 判断是否继续添加方法 """
        self.before_method = None
        """ 在递归前的处理方法 """
        self.after_method = None
        """ 在递归后的处理方法 """
        self.is_push = False
        """ 是否进行了入栈操作 """

    def set(self, key, value):
        """
        设置迭代变量
        :param key:名称
        :param value: 值
        """
        self.var_stack[-1][key] = value

    def get(self, key, default=None):
        """
        获取迭代变量
        :param key:名称
        :param default:默认值
        :return: 值
        """
        value = self.var_stack[-1].get(key)
        return default if value is None else value

    def push(self, list_data):
        """
        入栈操作
        :param list_data:添加的迭代列表
        """
        self.var_stack.append({})
        self.item_stack.append(list_data)
        self.iteration_stack.append([0, True, True, True])
        self.is_push = True

    def iteration(self):
        """ 开始迭代处理 """
        while self.iteration_stack:
            iteration_info = self.iteration_stack[-1]
            if iteration_info[0] < len(self.item_stack[-1]):
                now_data = self.item_stack[-1][iteration_info[0]]
                if iteration_info[1] and self.before_method:
                    self.before_method(self, now_data)
                    iteration_info[1] = False
                if iteration_info[2] and self.judge_method:
                    self.judge_method(self, now_data)
                    iteration_info[2] = False
                    if self.is_push:
                        self.is_push = False
                        continue
                if iteration_info[3] and self.after_method:
                    self.after_method(self, now_data)
                    iteration_info[3] = False
                iteration_info[0] += 1
                iteration_info[1] = True
                iteration_info[2] = True
                iteration_info[3] = True
            else:
                self.iteration_stack.pop()
                self.item_stack.pop()
                self.var_stack.pop()

    def add_judge(self, method):
        """
        添加判断子项方法
        :param method:方法
        """
        self.judge_method = method

    def add_before(self, method):
        """
        提那就迭代前处理方法
        :param method: 方法
        """
        self.before_method = method

    def add_after(self, method):
        """
        添加迭代后处理方法
        :param method: 方法
        """
        self.after_method = method


class FormatCode:
    class _Config:
        def __init__(self,
                     line_before_use=False,
                     line_after_use=False,
                     indent_before_use=0,
                     indent_after_use=0,
                     child_line=False):
            """
            配置
            :param line_before_use: 使用前换行
            :param line_after_use: 使用后换行
            :param indent_before_use: 使用前增量
            :param indent_after_use: 使用后增量
            :param child_line: 子项换行
            """
            self.line_before_use = line_before_use
            """ 使用前换行 """
            self.line_after_use = line_after_use
            """ 使用后换行 """
            self.indent_before_use = indent_before_use
            """ 使用前增量 """
            self.indent_after_use = indent_after_use
            """ 使用后增量 """
            self.child_line = child_line
            """ 子项换行 """

    def __init__(self):
        self.rule: Dict[str, FormatCode._Config] = {}

    def add_rule(self, token_type,
                 line_before_use=False,
                 line_after_use=False,
                 indent_before_use=0,
                 indent_after_use=0,
                 child_line=False):
        """
        添加规则
        :param token_type: token类型
        :param line_before_use: 使用前换行
        :param line_after_use: 使用后换行
        :param indent_before_use: 使用前增量
        :param indent_after_use: 使用后增量
        :param child_line: 子项换行
        """
        self.rule[token_type] = FormatCode._Config(
            line_before_use,
            line_after_use,
            indent_before_use,
            indent_after_use,
            child_line)

    def format(self, list_token: List[Token]):
        iteration_stack = IterationStack()
        var = {"indent": 0, "result": "", "need_indent": False}

        def judge_method(iteration: IterationStack, token: Token):
            if token.token_tree:
                iteration.push(token.token_tree)
                now_rule = self.rule.get(token.type)
                if now_rule:
                    if now_rule.child_line:
                        iteration.set("child_line", True)

        def before_method(iteration: IterationStack, token: Token):
            now_rule = self.rule.get(token.type)
            if now_rule:
                var["indent"] += now_rule.indent_before_use
                if now_rule.line_before_use != 0 and var["result"][-1] not in [" ", "\n"]:
                    var["result"] += "\n"
                    var["need_indent"] = True
            if not var["need_indent"] and iteration.get("child_line", False) and var["result"][-1] not in [" ", "\n"]:
                var["result"] += "\n"
                var["need_indent"] = True

            if var["need_indent"]:
                var["result"] += "    " * var["indent"]
                var["need_indent"] = False

            if token.start or token.data or token.end:
                if var["result"] != "" and var["result"][-1] not in [" ", "\n"]:
                    var["result"] += " "

            if token.start:
                var["result"] += token.start
            if token.data:
                var["result"] += token.data
            if token.end:
                var["result"] += token.end

        def after_method(iteration: IterationStack, token: Token):
            now_rule = self.rule.get(token.type)
            if now_rule:
                var["indent"] += now_rule.indent_after_use
                if now_rule.line_after_use != 0 and var["result"][-1] not in [" ", "\n"]:
                    var["result"] += "\n"
                    var["need_indent"] = True

        iteration_stack.push(list_token)
        iteration_stack.add_judge(judge_method)
        iteration_stack.add_before(before_method)
        iteration_stack.add_after(after_method)
        iteration_stack.iteration()
        return var["result"]
