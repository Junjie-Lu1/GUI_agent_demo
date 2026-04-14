import re
import json
from datetime import datetime
from typing import TypedDict
from pathlib import Path

from langgraph.graph import StateGraph, END
from operators.execute import Operation
from utils.model import LVMChat
from utils.prompt import COMPUTER_USE_UITARS_CN


# 定义State
class AgentState(TypedDict):
	instruction: str  # 用户指令
	screenshot_path: str  # 当前截图路径
	step: int  # 当前步骤
	thought: str  # 模型思考
	action: str  # 模型输出的动作
	finished: bool  # 是否完成


class GUIAgent:
	"""GUI自动化Agent"""
	
	def __init__(self, instruction: str, model_name: str = "glm-5v-turbo"):
		self.instruction = instruction
		self.operation = Operation()
		self.lvm_chat = LVMChat(model=model_name)
		self.lvm_chat.clear_history()
		self.s_dir = Path("s") 
		self.s_dir.mkdir(exist_ok=True) # 创建目录，已存在则不报错
		
		# 获取屏幕尺寸用于坐标映射
		import pyautogui
		self.screen_width, self.screen_height = pyautogui.size()
		print(f"🖥️  屏幕尺寸: {self.screen_width}x{self.screen_height}")
	
	def normalize_coords(self, x: int, y: int) -> tuple[int, int]:
		"""将归一化坐标(0-1000)转换为实际像素坐标"""
		actual_x = int(x / 1000.0 * self.screen_width)
		actual_y = int(y / 1000.0 * self.screen_height)
		print(f"   归一化坐标 ({x}, {y}) -> 实际坐标 ({actual_x}, {actual_y})")
		return actual_x, actual_y
		
	def take_screenshot(self, state: AgentState) -> AgentState:
		"""步骤1: 截图并保存"""
		step = state.get("step", 0) + 1
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		screenshot_path = str(self.s_dir / f"step_{step}_{timestamp}.png")
		
		self.operation.screenshot(screenshot_path)
		
		return {
			**state,
			"instruction": self.instruction,
			"screenshot_path": screenshot_path,
			"step": step,
			"finished": False
		}
        # 这些写法是正确的，新的键值对会自动覆盖state解包出来的键值对，比如step是用我们定义的这个新的，覆盖了原来解包出来的那个step
	
	def model_decide(self, state: AgentState) -> AgentState:
		"""步骤2: 模型决策（自动使用会话历史）"""
		prompt = COMPUTER_USE_UITARS_CN.format(instruction=state["instruction"])
		
		# 调用多模态模型
		response = self.lvm_chat.get_multimodal_response(
			text=prompt,
			image_path=state["screenshot_path"],
            res_format="json",
			use_history=True
		)
		
		print(f"\n📸 Step {state['step']} - 模型响应:\n{response}\n")
		
		# 解析JSON响应
		try:
			result = json.loads(response)
			thought = result.get("Thought", "")
			action = result.get("Action", "")
		except json.JSONDecodeError:
			thought_match = re.search(r'"Thought":\s*"([^"]*)"', response)
			action_match = re.search(r'"Action":\s*"([^"]*)"', response)
			thought = thought_match.group(1) if thought_match else ""
			action = action_match.group(1) if action_match else ""
		
		return {
			**state,
			"thought": thought,
			"action": action
		}
	
	def execute_action(self, state: AgentState) -> AgentState:
		"""步骤3: 解析并执行动作"""
		action = state["action"]
		
		if not action:
			print("⚠️ 没有可执行的动作")
			return {**state, "finished": True}
		
		# 检查是否完成
		if action.startswith("finished("):
            # 用正则表达式从 action 里提取内容：专门匹配格式：finished(content='xxx')，把单引号里的 xxx 抠出来
			content_match = re.search(r"finished\(content='([^']*)'\)", action)
            # 能匹配到内容，就用抠出来的 xxx，匹配不到，给默认值 "任务完成"
			content = content_match.group(1) if content_match else "任务完成"
			print(f"✅ 任务完成: {content}")
			return {**state, "finished": True}

		# 解析并执行动作
		try:
			self._parse_and_execute(action)
		except Exception as e:
			print(f"❌ 执行动作失败: {e}")
			print(f"   动作: {action}")
		
		return state
	
	def _parse_and_execute(self, action: str):
		"""解析动作字符串并执行"""
		print(f"🔧 执行动作: {action}")
		
		# click单击
		if action.startswith("click("):
			point_match = re.search(r"<point>(\d+)[,\s]+(\d+)</point>", action)
			if not point_match:
				point_match = re.search(r"point=['\"](\d+)[,\s]+(\d+)['\"]", action)
			if not point_match:
				point_match = re.search(r"point=['\"]<point>(\d+)[,\s]+(\d+)</point>['\"]", action)
			
			if point_match:
				x, y = int(point_match.group(1)), int(point_match.group(2))
				actual_x, actual_y = self.normalize_coords(x, y)
				self.operation.click(actual_x, actual_y)
			else:
				print(f"⚠️ 无法解析点击坐标: {action}")
		
		# left_double双击
		elif action.startswith("left_double("):
			point_match = re.search(r"<point>(\d+)[,\s]+(\d+)</point>", action)
			if not point_match:
				point_match = re.search(r"point=['\"](\d+)[,\s]+(\d+)['\"]", action)
			if not point_match:
				point_match = re.search(r"point=['\"]<point>(\d+)[,\s]+(\d+)</point>['\"]", action)
			
			if point_match:
				x, y = int(point_match.group(1)), int(point_match.group(2))
				actual_x, actual_y = self.normalize_coords(x, y)
				self.operation.double_click(actual_x, actual_y)
			else:
				print(f"⚠️ 无法解析双击坐标: {action}")
		
		# type输入文本
		elif action.startswith("type("):
			content_match = re.search(r"content=['\"]([^'\"]*)['\"]", action)
			if content_match:
				text = content_match.group(1)
				text = text.replace(r"\'", "'").replace(r'\"', '"').replace(r"\n", "\n")
				self.operation.input(text)
		
		# hotkey联合快捷键
		elif action.startswith("hotkey("):
			key_match = re.search(r"key=['\"]([^'\"]*)['\"]", action)
			if key_match:
				keys = key_match.group(1).split()
				self.operation.hotkey(*keys)
		
		# scroll滚动
		elif action.startswith("scroll("):
			point_match = re.search(r"<point>(\d+)[,\s]+(\d+)</point>", action)
			if not point_match:
				point_match = re.search(r"point=['\"](\d+)[,\s]+(\d+)['\"]", action)
			if not point_match:
				point_match = re.search(r"point=['\"]<point>(\d+)[,\s]+(\d+)</point>['\"]", action)
			
			direction_match = re.search(r"direction=['\"]([^'\"]*)['\"]", action)
			if point_match and direction_match:
				x, y = int(point_match.group(1)), int(point_match.group(2))
				actual_x, actual_y = self.normalize_coords(x, y)
				direction = direction_match.group(1)
				import pyautogui
				pyautogui.moveTo(actual_x, actual_y)
				scroll_amount = 3 if direction in ["up", "left"] else -3 # 向上/左滚动3像素，向下/右滚动-3像素
				pyautogui.scroll(scroll_amount)
		
		# wait等待
		elif action.startswith("wait("):
			self.operation.wait(seconds=5)
		
		# drag拖拽
		elif action.startswith("drag("):
			start_match = re.search(r"start_point=['\"]<point>(\d+)[,\s]+(\d+)</point>['\"]", action)
			end_match = re.search(r"end_point=['\"]<point>(\d+)[,\s]+(\d+)</point>['\"]", action)
			
			if not start_match:
				start_match = re.search(r"start_point=['\"](\d+)[,\s]+(\d+)['\"]", action)
				end_match = re.search(r"end_point=['\"](\d+)[,\s]+(\d+)['\"]", action)
			
			if start_match and end_match:
				x1, y1 = int(start_match.group(1)), int(start_match.group(2))
				x2, y2 = int(end_match.group(1)), int(end_match.group(2))
				actual_x1, actual_y1 = self.normalize_coords(x1, y1)
				actual_x2, actual_y2 = self.normalize_coords(x2, y2)
				import pyautogui
				pyautogui.moveTo(actual_x1, actual_y1)
				pyautogui.drag(actual_x2 - actual_x1, actual_y2 - actual_y1, duration=0.5) # 拖拽0.5秒
		
		# 等待界面响应
		self.operation.wait(seconds=1)
	
	def should_continue(self, state: AgentState) -> str:
		"""判断是否继续循环"""
		return "end" if state.get("finished", False) else "continue"
	
	def run(self):
		"""运行Agent"""
        # 画一个自动化流程，流程里所有数据都用 AgentState 这个结构存储
		workflow = StateGraph(AgentState)
		
		# 添加节点
        # 用法：第一个是节点步骤的名字，第二个是执行的函数，这个函数必须是 def 函数名(self, state: AgentState) -> AgentState:
		workflow.add_node("screenshot", self.take_screenshot)
		workflow.add_node("decide", self.model_decide)
		workflow.add_node("execute", self.execute_action)
		
		# 构建流程
        # 用法：这是说从哪个节点开始，填节点步骤名进去
		workflow.set_entry_point("screenshot")
        # 用法：这是说从哪个节点到哪个节点，前面填起点后面填终点
		workflow.add_edge("screenshot", "decide")
		workflow.add_edge("decide", "execute")
		workflow.add_conditional_edges( # 这个是条件边
			"execute",                  # 从哪个节点来
			self.should_continue,       # 判断的条件函数
			{                           # 根据你的判断函数返回的值，对应下一个动作是哪个节点步骤，END就是结束
				"continue": "screenshot",
				"end": END
			}
		)
		
		app = workflow.compile() # 把流程图编译为可执行程序
		print(f"🚀 开始执行任务: {self.instruction}\n")
		
		config = {"recursion_limit": 100}
		final_state = app.invoke( #给一个初始值，启动流程
			{"instruction": self.instruction, "step": 0},
			config=config
		)
		
		print(f"\n🎉 任务完成! 共执行 {final_state['step']} 步")
		return final_state

if __name__ == "__main__":

    agent = GUIAgent(instruction="""打开记事本新建一个文件，输入"hello world"，保存文件""")
    agent.run()