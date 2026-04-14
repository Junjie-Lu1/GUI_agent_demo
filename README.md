# 🎯 GUI Agent - 智能GUI自动化助手

这是一个GUI Agent的demo，能实现让AI帮你操作电脑。

你可以输入简单的任务，一步一步观察AI在这个过程中是如何思考的，每个步骤是如何调用的，AI是如何操作电脑的，状态在各个节点之间是如何传递的……

一个很简单的例子：打开记事本写下hello world，并保存。效果如下（由于是使用Xbox录制的，只能录制当前界面，实际上在电脑前是能看到操作过程的）：
<video width="640" controls muted loop>
  <source src="demo.mp4" type="video/mp4">
  你的浏览器不支持视频播放
</video>

<details>
<summary>🎬 点击查看演示视频</summary>

![视频演示](./demo.mp4)

</details>


相信这个简单的demo能让你深刻理解背后的原理，这一点也不难，开始动手学习吧！

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-States-blueviolet)
![OpenAI](https://img.shields.io/badge/OpenAI-Compatible-green)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install langgraph langchain-openai pyautogui pyperclip mss
```

### 2. 配置API密钥

编辑 `utils/model.py`，找到这两行，填入你的API密钥：

```python
API_KEY = "your_api_key" # 这里写你的智谱API密钥
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"  # 智谱AI的URL地址
```

> 💡 推荐使用 [智谱AI](https://open.bigmodel.cn/) 的GLM系列模型，性价比高且效果不错。

### 3. 运行示例

```python
from main import GUIAgent

# 创建Agent，传入你想执行的任务
agent = GUIAgent(
    instruction="打开记事本，输入'你好，世界！'并保存",
    model_name="glm-5v-turbo"  # demo不会消耗多少token，可以用最强的模型，效果更好
)

# 启动工作流
agent.run()
```

## 📁 项目结构

```
GUI_agent_demo/
├── main.py                 # 🚀 入口程序 - Agent核心逻辑
├── operators/
│   └── execute.py          # 🎮 鼠标键盘操作工具箱
├── utils/
│   ├── model.py            # 🧠 多模态大模型调用接口，附带上下文记忆管理
│   └── prompt.py           # 📝 给AI的指令模板
├── s/                      # 📸 截图保存目录
└── image/                  # 🖼️ 测试图片目录
```

### 核心文件详解

#### 🎯 main.py - Agent大脑
这是整个项目的心脏，包含了：
- **GUIAgent类** - 主控类，管理整个自动化流程
- **状态图定义** - 使用LangGraph构建的三步工作流：截图 → 思考 → 执行
- **坐标转换** - 将AI返回的归一化坐标(0-1000)转换为实际屏幕像素
- **动作解析器** - 理解AI的输出，调用底层操作

工作流程：
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1.截图     │ → │  2.模型思考 │ → │  3.执行动作 │
│  takeShot   │    │ modelDecide │    │ executeAct  │
└─────────────┘    └─────────────┘    └─────────────┘
        ↑                                    │
        └────────── 循环，直到完成 ←─────────┘
```

#### 🎮 operators/execute.py - 你的手
底层操作封装，让AI能真正"动手"：
| 方法 | 功能 | 示例 |
|------|------|------|
| `click(x, y)` | 鼠标点击 | 点击按钮 |
| `input(text)` | 文字输入 | 填写表单 |
| `hotkey(*keys)` | 快捷键 | Ctrl+V粘贴 |
| `screenshot()` | 截图 | 获取当前界面 |
| `scroll()` | 滚动 | 翻页 |
| `wait()` | 等待 | 等待加载 |

> 💡 使用`pyperclip`粘贴方式输入，解决中文输入问题

#### 🧠 utils/model.py - AI眼睛和大脑
与多模态大模型通信的桥梁：
- **图片编码** - 将截图转为Base64发给AI
- **对话历史** - 记住之前的操作上下文
- **JSON响应** - 强制AI返回结构化输出，便于解析

#### 📝 utils/prompt.py - 指令模板
告诉AI如何工作的"说明书"，包含：
- 可用操作列表（click、type、scroll...）
- 输出格式要求
- 中文思考引导

## 🎨 支持的操作

| 操作 | 格式 | 说明 |
|------|------|------|
| 点击 | `click(point='<point>500 300</point>')` | 左键单击 |
| 双击 | `left_double(point='<point>500 300</point>')` | 左键双击 |
| 输入 | `type(content='你好\n世界')` | 支持中文和换行 |
| 快捷键 | `hotkey(key='ctrl c')` | 组合键用空格分隔 |
| 滚动 | `scroll(point='<point>500 300</point>', direction='down')` | 上下左右 |
| 拖拽 | `drag(start_point='<point>100 100</point>', end_point='<point>200 200</point>')` | 拖动操作 |
| 等待 | `wait()` | 等待5秒 |
| 完成 | `finished(content='任务完成！')` | 标记任务结束 |

## ⚠️ 注意事项

1. **坐标范围** - AI返回的坐标是归一化的(0-1000)，会自动转换为你的屏幕分辨率
2. **安全机制** - pyautogui的FAILSAFE已关闭，避免误触退出
3. **API费用** - 每次截图+推理都会消耗API额度，请注意使用
4. **模型选择** - 由于GUI agent需要依赖记忆，所以必须选择能够输入多图的模型

## 🔧 扩展开发

想要添加新操作？只需要：

1. 在 `operators/execute.py` 添加新方法
2. 在 `utils/prompt.py` 添加操作说明
3. 在 `main.py` 的 `_parse_and_execute` 添加解析逻辑

## 📝 License

MIT License - 欢迎自由使用和改进！

---

⭐ 如果这个项目对你有帮助，欢迎点个Star！
