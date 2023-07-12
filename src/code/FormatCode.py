from typing import Dict, List

from src.code.CodeParser import Token


class IndexDict:
    class _DictNode:

        def __init__(self, default=None):
            self.data = {}
            self.default = default

        def set(self, key, value):
            if key is None:
                self.default = value
            self.data[key] = value

        def set_default(self, value):
            self.default = value

        def get(self, key):
            if key in self.data:
                return self.data[key]
            return self.default

        def __setitem__(self, key, value):
            self.set(key, value)

        def __getitem__(self, item):
            return self.get(item)

    def __init__(self):
        self.data: Dict[str, IndexDict._DictNode] = {}

    def set(self, key, value, auxiliary_key=None):
        if key not in self.data:
            self.data[key] = IndexDict._DictNode()
        self.data[key][auxiliary_key] = value

    def get(self, key, auxiliary_key=None):
        data = self.data.get(key)
        if data:
            return data[auxiliary_key]
        return None


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


class FormatData:

    def __init__(self):
        self.indent = 0
        """ 当前缩进数量 """
        self.data = ""
        """ 当前格式化的代码 """
        self.need_indent = False
        """ 需要缩进 """
        self.need_space = True
        """ 需要空格 """
        self.last_right_space = True
        """ 右侧需要空格 """
        self.last_priority_space = 0
        """ 上一个配置的优先级 """

    def is_not_space(self):
        """ 最后一个字符是否为空 """
        return self.data != "" and self.data[-1] not in [" ", "\n", "\t"]

    def code_indent(self, mandatory=0):
        """ 代码缩进 """
        if mandatory != 0:
            self.data += " " * 4 * (self.indent + mandatory)
            self.need_indent = False
        if self.need_indent:
            self.data += " " * self.indent * 4
            self.need_indent = False

    def code_line(self, mandatory=False):
        """
        代码换行
        :param mandatory:强制换行
        """
        if mandatory or self.is_not_space():
            self.data += "\n"
        self.need_indent = True

    def add_data(self, *list_data: str | None):
        """
        写入数据
        :param list_data:多个数据
        """
        flag = False
        temp = ""
        for data in list_data:
            if data is not None and data != "":
                flag = True
                temp += data
        if flag:
            if self.need_indent:
                self.code_indent()
                self.need_indent = False
            if self.need_space and self.is_not_space():
                self.data += " "
            self.data += temp


class FormatCode:
    class _Config:
        def __init__(self,
                     line_before_use=False,
                     line_after_use=False,
                     indent_before_use=0,
                     indent_after_use=0,
                     child_line=False,
                     left_space=True,
                     right_space=True,
                     priority_space=0,
                     child_interval=False,
                     next_line_indent=False,
                     ):
            """
            配置
            :param line_before_use: 使用前换行
            :param line_after_use: 使用后换行
            :param indent_before_use: 使用前增量
            :param indent_after_use: 使用后增量
            :param child_line: 子项换行
            :param left_space:左边需要空格
            :param right_space:右边需要空格
            :param priority_space:优先级
            :param child_interval:子项换行具有间隔
            :param next_line_indent:下一行强制缩进1行
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
            self.left_space = left_space
            """ 左边需要空格 """
            self.right_space = right_space
            """ 右边需要空格 """
            self.priority_space = priority_space
            """ 优先级 """
            self.child_interval = child_interval
            """ 子项换行具有间隔 """
            self.next_line_indent = next_line_indent
            """ 下一行强制缩进1行 """

    def __init__(self):
        self.rule = IndexDict()

    def add_rule(self, token_type,
                 line_before_use=False,
                 line_after_use=False,
                 indent_before_use=0,
                 indent_after_use=0,
                 child_line=False,
                 left_space=True,
                 right_space=True,
                 content=None,
                 priority_space=0,
                 child_interval=False,
                 next_line_indent=False,
                 ):
        """
        添加规则
        :param token_type: token类型
        :param line_before_use: 使用前换行
        :param line_after_use: 使用后换行
        :param indent_before_use: 使用前增量
        :param indent_after_use: 使用后增量
        :param child_line: 子项换行
        :param left_space:左边需要空格
        :param right_space:右边需要空格
        :param content:辅助索引内容
        :param priority_space:优先级
        :param child_interval:子项换行具有间隔
        :param next_line_indent:下一行强制缩进1行
        """
        data = FormatCode._Config(
            line_before_use,
            line_after_use,
            indent_before_use,
            indent_after_use,
            child_line,
            left_space,
            right_space,
            priority_space,
            child_interval,
            next_line_indent
        )
        self.rule.set(token_type, data, content)

    def format(self, list_token: List[Token]):
        iteration_stack = IterationStack()
        form_data = FormatData()

        def judge_method(iteration: IterationStack, token: Token):
            if token.token_tree:
                iteration.push(token.token_tree)
                now_rule: FormatCode._Config = self.rule.get(token.type, token.start)
                if now_rule:
                    iteration.set("child_line", now_rule.child_line)
                    iteration.set("child_interval", now_rule.child_interval)

        def before_method(iteration: IterationStack, token: Token):
            now_rule: FormatCode._Config = self.rule.get(token.type, token.start)
            if now_rule:
                form_data.indent += now_rule.indent_before_use
                if now_rule.line_before_use:
                    form_data.code_line()

            if iteration.get("child_line", False):
                form_data.code_line()
            if iteration.get("child_interval", False):
                form_data.code_line(True)

            if now_rule:
                if now_rule.priority_space > form_data.last_priority_space:
                    form_data.need_space = now_rule.left_space
                else:
                    form_data.need_space = now_rule.left_space and form_data.last_right_space
                form_data.last_right_space = now_rule.right_space
                form_data.last_priority_space = now_rule.priority_space
            else:
                form_data.need_space = form_data.last_right_space

            form_data.add_data(token.start, token.data, token.end)

        def after_method(iteration: IterationStack, token: Token):
            now_rule: FormatCode._Config = self.rule.get(token.type, token.start)
            if now_rule:
                form_data.indent += now_rule.indent_after_use
                if now_rule.line_after_use:
                    form_data.code_line()
                if now_rule.next_line_indent:
                    form_data.code_line()
                    form_data.code_indent(1)

        iteration_stack.push(list_token)
        iteration_stack.add_judge(judge_method)
        iteration_stack.add_before(before_method)
        iteration_stack.add_after(after_method)
        iteration_stack.iteration()
        return form_data.data
