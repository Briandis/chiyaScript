from typing import List, Dict, TypeVar, Generic

FlowConfig = TypeVar("FlowConfig")


class FlowInfo(Generic[FlowConfig]):
    def __init__(self, index, flow_type, config: FlowConfig, flow_data, context):
        self.index = index
        """ 流顺序 """
        self.type = flow_type
        """ 流类型 """
        self.config: FlowConfig = config
        """ 流配置 """
        self.flow_data = flow_data
        """ 流数据 """
        self.context = context
        """ 上下文 """


class FlowContext:
    def __init__(self):
        self.context = {}
        """ 上下文容器 """


class Flow(Generic[FlowConfig]):

    def __init__(self):
        self.flow: Dict[float, List[FlowInfo[FlowConfig]]] = {}
        """ 流容器 """
        self.context = FlowContext()
        """ 上下文 """

    def add_flow(self, index, flow_type, flow_data, config: FlowConfig):
        """
        添加流
        :param index: 流下标
        :param flow_type: 流类型
        :param flow_data: 流的数据
        :param config:流迭代时的配置
        """
        flow: FlowInfo[FlowConfig] = FlowInfo(index, flow_type, config, flow_data, self.context)
        if index in self.flow:
            self.flow[index].append(flow)
        else:
            self.flow[index] = [flow]

    def __iter__(self):
        now_index = list(self.flow.keys())
        now_index.sort()
        for index in now_index:
            for flow in self.flow[index]:
                yield flow
