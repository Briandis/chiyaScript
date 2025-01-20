from abc import abstractmethod
from typing import Dict, List

from src.code.CodeParser import Token
from src.code.FormatCode import IterationStack


class AssignmentSyntaxTree:
    def __init__(self, set_value, next_token: Token):
        """ 赋值树 """
        self.next_token: Token | None = next_token
        """ 下一个token """
        self.set_value = set_value
        """ 语法树赋值方法 """


class AbstractSyntaxTree:
    """ 抽象语法树 """

    @abstractmethod
    def get_type(self) -> str:
        """
        获取语法树类型
        :return: 类型
        """

    @abstractmethod
    def build(self, token: Token):
        """
        构建语法树
        :param token:当前token
        :return:
        """


class SyntaxTreeParser:
    def __init__(self):
        self.rule_method: Dict[str, AssignmentSyntaxTree] = {}
        """ 规则解析 """
        self.context = {}
        """ 上下文 """
        self.need_judge: List[AssignmentSyntaxTree] = []
        """ 待判断队列 """

    def recursion(self):
        iteration_stack = IterationStack()

        def judge_method(iteration: IterationStack, token: Token):
            if self.need_judge:
                iteration.push(self.need_judge)
                self.need_judge.clear()

        def before_method(iteration: IterationStack, token: Token):
            pass

        def after_method(iteration: IterationStack, token: Token):
            pass

        iteration_stack.is_list_copy = True
        # 初始化迭代数据
        iteration_stack.push(self.need_judge)
        self.need_judge.clear()
        # 封装方法
        iteration_stack.add_judge(judge_method)
        iteration_stack.add_before(before_method)
        iteration_stack.add_after(after_method)
        iteration_stack.iteration()
        # 清除上下文
        self.context.clear()

    def next_parser(self):
        pass

    def parser(self, list_token: List[Token]):
        list_tree = []
        for token in list_token:
            pass


class BuildAbstractTree:
    def build_tree(self, syntax_tree_parser: SyntaxTreeParser, token: Token):
        pass
