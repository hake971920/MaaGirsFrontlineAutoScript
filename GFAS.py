# first_launch_task_scheme2.py

import time
import json
from pathlib import Path
from typing import Any # 导入 Any 用于类型提示

# 导入 MaaFramework Python 接口的核心模块
# 具体的导入方式需要参照官方文档，以及你的源码结构
try:
    # 假设核心类都在顶层 MaaFw 包下
    import MaaFw
    from MaaFw import Context, Resource, Controller, NotificationHandler, Job
    from MaaFw import AdbController # 如果使用 ADB 控制器
    from MaaFw import Library # 用于加载原生库
    from MaaFw import Toolkit # 可能用于查找设备或初始化选项
    from MaaFw import define # 可能需要用到其中的常量或结构体，例如 define.MaaStatusEnum

except ImportError:
    print("Error: MaaFw library not installed or not in PYTHONPATH.")
    print("Please run 'pip install MaaFw' or add the binding directory to PYTHONPATH.")
    exit()

# 游戏的包名
GAME_PACKAGE_NAME = "tw.txwy.and.snqx" # 替换成实际包名

# 模拟器或设备的连接字符串
# 例如：ADB 连接字符串 (如 'emulator-5554' 或 '127.0.0.1:5555')
# 也可以通过 Toolkit.find_adb_devices() 查找
DEVICE_CONNECTION_STRING = "127.0.0.1：16384" # 替换成实际连接字符串

# 定义一个简单的回调处理器来接收日志和通知
# 必须继承 MaaFw.NotificationHandler
class MyNotificationHandler(NotificationHandler):
    # 根据通知类型实现不同的 on_ 方法
    # 所有 on_ 方法都必须接收 noti_type (NotificationType) 和 detail (dataclass 或 Any)
    def on_log(self, noti_type: define.NotificationType, detail: Any):
        # LogDetail 应该是一个 dataclass，包含 level 和 message
        # 根据 level 打印不同级别的日志
        if isinstance(detail, dict) and 'level' in detail and 'message' in detail:
            log_level = detail.get('level', 0) # 假设 detail 是字典，level 是键
            message = detail.get('message', 'N/A')
            # 可以根据 level (整型值) 映射到日志级别名称
            print(f"[MaaFW Log] Level {log_level}: {message}")
        else:
             print(f"[MaaFW Log] {detail}") # 如果 detail 结构不对，直接打印

    def on_tasker_task(self, noti_type: define.NotificationType, detail: Any):
        # 任务状态变化通知
        if isinstance(detail, dict) and 'task_id' in detail and 'entry' in detail and 'uuid' in detail:
             task_id = detail.get('task_id')
             entry = detail.get('entry')
             noti_type_name = define.NotificationType(noti_type).name # 将整型通知类型转换为名称
             print(f"[MaaFW Task] Task {task_id} ({entry}) Status: {noti_type_name}")
        else:
             print(f"[MaaFW Task] {detail}")

    def on_controller_action(self, noti_type: define.NotificationType, detail: Any):
        # 控制器动作（如点击、滑动、截图、应用启动）的状态变化通知
        # ControllerActionDetail 应该包含 ctrl_id, uuid, action
        if isinstance(detail, dict) and 'action' in detail and 'uuid' in detail:
            action_name = detail.get('action')
            action_uuid = detail.get('uuid')
            noti_type_name = define.NotificationType(noti_type).name
            print(f"[MaaFW Controller Action] {action_name} ({action_uuid}) Status: {noti_type_name}")
        else:
             print(f"[MaaFW Controller Action] {detail}")


    def on_unknown_notification(self, noti_type: define.NotificationType, detail: Any):
        # 处理其他未知的通知类型
        noti_type_name = define.NotificationType(noti_type).name
        print(f"[MaaFW Unknown Notification] Type {noti_type_name} ({noti_type}): {detail}")


def main():
    # --- 步骤 1: 初始化 MaaFramework 库和配置 ---
    # Library.open() 通常在 import MaaFw 时已经执行
    # 可以选择通过 Toolkit 初始化配置选项，例如设置用户配置目录
    try:
        print("Initializing MaaFramework Library and options...")
        # 如果你需要使用自定义的 config 文件夹，可以在这里指定
        # user_config_path = "./maa_user_config"
        # Path(user_config_path).mkdir(parents=True, exist_ok=True) # 确保文件夹存在
        # MaaFw.Toolkit.init_option(user_config_path) # 假设 API
        # 如果没有特殊配置，可以跳过 init_option 或使用默认路径

        # 打印 MaaFramework 版本 (可选)
        # version = MaaFw.Library.version() # 假设 Library.version() 返回版本字符串
        # print(f"MaaFramework Version: {version}")

        print("MaaFramework Library and options initialized.")
    except Exception as e:
        print(f"Error initializing MaaFramework Library/options: {e}")
        return

    # --- 2. 创建通知处理器实例 ---
    my_noti_handler = MyNotificationHandler()
    print("Notification handler created.")

    # --- 3. 创建 MaaFramework 上下文 ---
    # Context 是核心对象，需要通过 Library.framework().MaaCreateContext() 获取 handle
    # 再用 handle 创建 Context 对象，同时将通知处理器传递给 Context
    context_handle = None
    context = None
    try:
        print("Creating MaaFramework Context...")
        # MaaCreateContext 接收通知处理器的 C 回调函数和用户参数
        # NotificationHandler._gen_c_param(my_noti_handler) 是一个静态方法，用于生成 C 回调所需的参数
        context_handle = MaaFw.Library.framework().MaaCreateContext(
             *MaaFw.NotificationHandler._gen_c_param(my_noti_handler)
        ) # 假设 API
        if context_handle:
             context = Context(handle=context_handle) # 使用获取到的 handle 创建 Context 对象
             print("MaaFramework Context created.")
        else:
             print("Failed to create MaaFramework Context.")
             return
    except Exception as e:
        print(f"Error creating MaaFramework Context: {e}")
        # 异常时尝试清理 handle
        if context_handle:
             # MaaDestroyContext 是释放 Context handle 的底层 C API
             MaaFw.Library.framework().MaaDestroyContext(context_handle)
        return


    # --- 4. 创建 Resource 对象 ---
    # Resource 负责管理资源和注册自定义组件
    # Resource 的构造函数可能接收通知处理器
    resource = None
    try:
        print("Creating MaaFramework Resource...")
        # MaaResourceCreate 是释放 Resource handle 的底层 C API
        resource_handle = MaaFw.Library.framework().MaaResourceCreate(
            *MaaFw.NotificationHandler._gen_c_param(my_noti_handler)
        ) # 假设 API
        if resource_handle:
             resource = Resource(handle=resource_handle, notification_handler=my_noti_handler) # 使用 handle 创建 Resource 对象
             print("MaaFramework Resource created.")

        # TODO: 如果你有 interface.json 或 bundle，在这里加载资源
        # resource.post_bundle("./path/to/your/project_bundle").wait() # 假设加载方法并等待完成
        # resource.post_pi("./path/to/your/interface.json").wait() # 假设加载方法并等待完成

        # TODO: 如果你有自定义识别/动作，在这里注册
        # my_custom_reco = MyCustomRecognition() # 你的自定义识别类实例
        # resource.register_custom_recognition("MyRecoName", my_custom_reco) # 假设注册方法

    except Exception as e:
        print(f"Error creating MaaFramework Resource: {e}")
        # 异常时尝试清理 handle
        if resource and hasattr(resource, '_handle') and resource._handle:
             MaaFw.Library.framework().MaaResourceDestroy(resource._handle)
        if context and hasattr(context, '_handle') and context._handle:
             MaaFw.Library.framework().MaaDestroyContext(context._handle)
        return


    # --- 5. 创建 Controller 对象并连接设备 ---
    # 选择合适的 Controller 子类，例如 AdbController
    controller = None
    connect_job = None
    try:
        print(f"Creating AdbController for device: {DEVICE_CONNECTION_STRING}...")
        # AdbController 的构造函数可能接收连接字符串、通知处理器等
        # AdbController 内部会调用 Library.framework().MaaControllerCreate
        controller = AdbController(
             DEVICE_CONNECTION_STRING,
             # notification_handler=my_noti_handler # Controller 也可能接收通知处理器
        )
        print("AdbController created.")

        # post_connection() 方法返回一个 Job 对象，表示连接是异步操作
        connect_job = controller.post_connection()
        print("Connection job posted. Waiting for connection...")

        # 等待连接 Job 完成
        connect_job.wait()
        # 检查 Job 状态
        if connect_job.succeeded:
             print("Successfully connected to device.")
        else:
             print(f"Failed to connect to device. Status: {connect_job.status} ({define.MaaStatusEnum(connect_job.status.value).name})") # 使用 define.MaaStatusEnum 转换为名称
             # 进一步错误信息可能在回调中
             # 失败时清理 controller
             if controller and hasattr(controller, '_handle') and controller._handle:
                  MaaFw.Library.framework().MaaControllerDestroy(controller._handle)
             # 失败时清理 resource
             if resource and hasattr(resource, '_handle') and resource._handle:
                  MaaFw.Library.framework().MaaResourceDestroy(resource._handle)
             # 失败时清理 context
             if context and hasattr(context, '_handle') and context._handle:
                  MaaFw.Library.framework().MaaDestroyContext(context._handle)
             return


    except Exception as e:
        print(f"Error creating/connecting controller: {e}")
        # 异常时尝试清理已创建的对象
        if controller and hasattr(controller, '_handle') and controller._handle:
             MaaFw.Library.framework().MaaControllerDestroy(controller._handle)
        if resource and hasattr(resource, '_handle') and resource._handle:
             MaaFw.Library.framework().MaaResourceDestroy(resource._handle)
        if context and hasattr(context, '_handle') and context._handle:
             MaaFw.Library.framework().MaaDestroyContext(context._handle)
        return


    # --- 6. 绑定 Resource 和 Controller 到 Tasker ---
    # Tasker 实例在 Context 内部，通过 context.tasker 访问
    # Tasker 对象需要知道在哪里找到资源（流水线）以及在哪个设备上执行操作
    # Tasker.bind() 方法将 resource 和 controller 绑定到 Tasker 上
    bind_success = False
    if context and resource and controller: # 确保 Context, Resource, Controller 都已成功创建/连接
         try:
              print("Binding Resource and Controller to Tasker...")
              # Context.tasker 属性返回 Tasker 对象，Tasker.bind 接收 resource 和 controller
              bind_success = context.tasker.bind(resource, controller) # 假设 API
              if bind_success:
                   print("Resource and Controller bound successfully.")
              else:
                   print("Failed to bind Resource and Controller.")
                   # 失败时清理已创建的对象
                   if controller and hasattr(controller, '_handle') and controller._handle:
                        MaaFw.Library.framework().MaaControllerDestroy(controller._handle)
                   if resource and hasattr(resource, '_handle') and resource._handle:
                        MaaFw.Library.framework().MaaResourceDestroy(resource._handle)
                   if context and hasattr(context, '_handle') and context._handle:
                        MaaFw.Library.framework().MaaDestroyContext(context._handle)
                   return
         except Exception as e:
              print(f"Error binding Resource/Controller: {e}")
              # 异常时清理已创建的对象
              if controller and hasattr(controller, '_handle') and controller._handle:
                   MaaFw.Library.framework().MaaControllerDestroy(controller._handle)
              if resource and hasattr(resource, '_handle') and resource._handle:
                   MaaFw.Library.framework().MaaResourceDestroy(resource._handle)
              if context and hasattr(context, '_handle') and context._handle:
                   MaaFw.Library.framework().MaaDestroyContext(context._handle)
              return


    # --- 7. 启动游戏 App ---
    # 现在 Controller 已经连接且绑定到 Tasker 上
    # 查找 controller.py 或 AdbController 中类似 post_app_start, launch_app, post_app 等方法
    # 假设方法名为 post_app 并接收包名，返回一个 Job
    app_start_job = None
    if controller and bind_success: # 确保控制器已连接且绑定成功
        try:
            print(f"Starting app: {GAME_PACKAGE_NAME}...")
            # 查找 Controller 或 AdbController 中启动 App 的方法
            # 假设方法是 post_app 并接收包名，返回一个 Job
            # 你需要根据实际 API 来修改这里
            if hasattr(controller, 'post_app'): # **检查方法是否存在 (方法名待确认)**
                 app_start_job = controller.post_app(GAME_PACKAGE_NAME) # **假设 API**
                 print("App start job posted. Waiting for app to launch...")

                 # 等待启动 Job 完成
                 app_start_job.wait()
                 # 检查 Job 状态
                 if app_start_job.succeeded:
                      print(f"App {GAME_PACKAGE_NAME} started successfully.")
                      print("Waiting for game to load...")
                      time.sleep(15) # 示例等待时间，需要根据实际游戏加载速度调整
                      print("Initial wait complete.")
                 else:
                      print(f"Failed to start app: {GAME_PACKAGE_NAME}. Status: {app_start_job.status} ({define.MaaStatusEnum(app_start_job.status.value).name})") # 使用 define.MaaStatusEnum 转换为名称
                      # 进一步错误信息可能在回调中
            else:
                 print(f"Controller object does not have a 'post_app' method (or equivalent).")
                 print("Please consult MaaFw Python binding documentation for app launch API.")


        except Exception as e:
            print(f"Error starting app: {e}")

    # --- 8. (可选) 执行其他操作或任务 ---
    # 如果 App 成功启动，你可以在这里加载 JSON 任务流水线并发布任务
    # context.tasker 对象现在是可用的
    # if context and context.tasker and app_start_job and app_start_job.succeeded:
    #      print("App launched, proceeding with task pipeline...")
    #      # 假设你的 JSON 流水线文件在资源中被正确加载，并且入口节点名为 "StartGameTask"
    #      pipeline_entry = "StartGameTask"
    #      # run_task 是 Tasker 的方法，用于运行流水线任务，返回 JobWithResult
    #      task_run_job = context.tasker.run_task(pipeline_entry) # 假设 API
    #      if task_run_job:
    #           print(f"Task pipeline '{pipeline_entry}' posted. Waiting for completion...")
    #           task_run_job.wait() # 等待任务流水线执行完成
    #           if task_run_job.succeeded:
    #                print(f"Task pipeline '{pipeline_entry}' completed successfully.")
    #           else:
    #                print(f"Task pipeline '{pipeline_entry}' failed. Status: {task_run_job.status} ({define.MaaStatusEnum(task_run_job.status.value).name})")
    #           # 可以通过 task_run_job.get() 获取任务执行的详细结果 (TaskDetail)
    #           # task_detail = task_run_job.get()
    #      else:
    #           print(f"Failed to post task pipeline '{pipeline_entry}'.")


    # --- 9. 清理资源 ---
    # 在脚本结束时，释放连接和 MaaFramework 资源
    print("Cleaning up MaaFramework resources...")
    # 释放 Controller handle
    if controller and hasattr(controller, '_handle') and controller._handle:
         print("Destroying Controller...")
         MaaFw.Library.framework().MaaControllerDestroy(controller._handle) # 假设清理 API
         controller._handle = None # 将 Python 对象的 handle 设为 None，避免 __del__ 再次释放

    # 释放 Resource handle
    if resource and hasattr(resource, '_handle') and resource._handle:
         print("Destroying Resource...")
         MaaFw.Library.framework().MaaResourceDestroy(resource._handle) # 假设清理 API
         resource._handle = None # 避免重复释放

    # 释放 Context handle
    if context and hasattr(context, '_handle') and context._handle:
         print("Destroying Context...")
         MaaFw.Library.framework().MaaDestroyContext(context._handle) # 假设清理 API
         context._handle = None # 避免重复释放

    # TODO: 可能还需要调用 Library 的清理方法，如 Library.close() 或类似的
    # print("Closing MaaFramework Library...")
    # MaaFw.Library.close() # 假设存在这样的 API


    print("MaaFramework cleanup complete.")


if __name__ == "__main__":
    main()