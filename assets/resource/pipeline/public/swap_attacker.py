from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction

@AgentServer.custom_action("SelectForce")
class SelectForceAction(CustomAction):
    """
    自定义动作：根据 first_time 类变量，在第一次和之后执行时点击不同的坐标。
    这个类变量 first_time 会在 CustomAction 的不同实例之间共享（如果使用同一个类）。
    """
    # 使用类变量来记录状态
    first_time = True # 记录是否是第一次执行这个动作的标志
    def run(self, context, argv):
        if SelectForceAction.first_time:
            click_job = context.controller.post_click(270, 270)
            click_job.wait()
            SelectForceAction.first_time = False
        else:
            click_job = context.controller.post_click(100, 270)
            click_job.wait()
        return True

AgentServer.start_up(sock_id)

