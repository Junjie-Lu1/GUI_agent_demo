import pyautogui
import pyperclip
import mss
import time

# 允许鼠标移动到屏幕角落（默认会触发fail-safe）
pyautogui.FAILSAFE = False

class Operation:
	"""GUI操作工具类"""
	
	def click(self, x: int, y: int):
		"""点击指定坐标"""
		print(f"🖱️  点击坐标 ({x}, {y})")
		pyautogui.click(x=x, y=y)
	
	def input(self, text: str):
		"""输入文本（使用粘贴方式，支持中文）"""
		print(f"⌨️  输入: {text}")
		pyperclip.copy(text)  # 复制到剪贴板
		pyautogui.hotkey('ctrl', 'v')  # Mac用command，Windows用ctrl
	
	def screenshot(self, save_path: str):
		"""截图并保存"""
		with mss.mss() as sct:
			sct.shot(output=save_path)
		print(f"📸 截图已保存: {save_path}")
	
	def hotkey(self, *keys):
		"""按下组合键（如ctrl+c）"""
		print(f"⌨️  按下组合键: {' + '.join(keys)}") # 把列表/字典的多个元素用 + 串起来
		pyautogui.hotkey(*keys)
	
	def wait(self, seconds: float = 1.0):
		"""等待指定时间"""
		print(f"⏱️  等待 {seconds} 秒...")
		time.sleep(seconds)