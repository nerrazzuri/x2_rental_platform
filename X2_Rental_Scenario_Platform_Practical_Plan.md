# X2 租赁场景编排平台实践方案

## 1. 项目定位

本方案的目标不是为单一客户活动做一次性二开，而是开发一套可复用的 **X2 租赁场景编排平台**，提供给机器人租赁公司长期使用。

租赁公司后续在接到不同客户活动时，可以通过后台快速配置客户资料、活动流程、话术、屏幕素材、动作、表情、TTS、移动路线等内容，让 X2 快速适配不同活动场景。

核心定位：

```text
让租赁公司每次接到活动后，不需要重新开发，只需要配置场景，即可让 X2 完成迎宾、主持、产品介绍、拍照互动、抽奖、FAQ、导览等任务。
```

---

## 2. 商业模式建议

### 2.1 推荐模式：按天 / 按周开放授权

由于第一个客户是长期合作伙伴，不建议一开始采用高额买断或复杂功能收费模式。推荐采用 **Founder Partner Launch Pricing**。

### 2.2 报价建议

#### Weekly Access

```text
RM 2,500 / week
```

包含：

```text
- 7 天系统开放权限
- 绑定 1 台 X2 / X2 Ultra
- 当前平台已有场景模板全部可用
- 后台管理端
- 平板控制台
- 话术、素材、产品、流程配置
- 基础远程支持
```

适合：

```text
- 展会
- 发布会
- 商场 roadshow
- 多日活动
- 彩排 + 正式活动
```

#### Daily Access

```text
RM 500 / day
```

包含：

```text
- 1 天系统开放权限
- 绑定 1 台 X2 / X2 Ultra
- 当前已有场景模板可用
- 后台配置 + 平板控制台
```

适合：

```text
- 单日活动
- 临时 demo
- 内部彩排
- 简单客户展示
```

#### Extra Robot

```text
+ RM 300 / day / robot
或
+ RM 1,500 / week / robot
```

### 2.3 Founder Partner 限制

为了避免未来价格被锁死，建议写明：

```text
该价格为首个合作伙伴 Founder Partner 价格，有效期为前 6 个月或前 10 场活动，以先到者为准。
```

后续正式市场价可调整为：

```text
Daily Access: RM 800 – 1,000 / day
Weekly Access: RM 3,500 – 5,000 / week
```

### 2.4 必须写入报价单 / 合同的边界

```text
1. 价格只包含平台已有功能使用权。
2. 不包含源码。
3. 不包含机器人硬件租赁费用。
4. 不包含现场驻场服务。
5. 不包含第三方 API 成本，例如 LLM、TTS、云服务。
6. 不包含新功能开发。
7. 不包含复杂场地移动路线调试。
8. 不包含复杂视觉定位现场调试。
9. 系统授权绑定指定租赁公司和指定机器人，不可转售。
10. 活动现场网络、电源、机器人硬件安全由租赁公司负责。
11. Founder Partner 价格不代表永久标准价格。
```

---

## 3. 平台整体架构

### 3.1 三层架构

```text
第一层：X2 Capability Layer
封装 X2 AimDK 能力：TTS、音频、屏幕、表情、LED、动作、移动、传感器。

第二层：Scenario Orchestration Layer
把机器人能力编排成活动流程：迎宾、主持、产品介绍、拍照、抽奖、问答、导览、移动路线。

第三层：Rental Business Layer
客户、活动、模板、素材、话术、平板控制、日志、授权、复用、白标。
```

### 3.2 系统模块

```text
x2-rental-platform
├── Admin Portal
├── Tablet Control Console
├── Scenario Engine
├── Robot Adapter
├── Asset Manager
├── Speech Manager
├── Screen Manager
├── Motion Manager
├── Movement Controller
├── Visual Marker Docking
├── Knowledge / RAG Manager
├── Event Access License Manager
├── Event Logger
└── Safety Controller
```

---

## 4. 核心模块说明

## 4.1 Admin Portal 后台管理

给租赁公司后台人员使用。

功能：

```text
- 创建客户
- 创建活动
- 选择场景模板
- 上传 Logo、视频、图片、二维码
- 编辑话术
- 配置产品介绍
- 配置主持流程
- 配置抽奖内容
- 配置机器人动作、表情、屏幕显示
- 预览活动流程
- 发布到平板控制台
- 查看活动授权有效期
```

---

## 4.2 Tablet Control Console 平板控制台

给现场工作人员使用。

必须包含：

```text
- 当前客户 / 当前活动
- 当前场景模板
- 开始
- 下一步
- 上一步
- 重播
- 停止
- 静音
- 音量调节
- 切换产品
- 切换语言
- 触发动作
- 紧急停止当前互动
- 查看机器人状态
```

设计原则：

```text
现场不能完全自动化，必须让工作人员可以控节奏。
```

---

## 4.3 Scenario Engine 场景编排引擎

所有场景都抽象成：

```text
Trigger + Flow + Assets + Robot Actions + External Integrations
```

### Trigger 触发器

```text
- 平板按钮
- 定时触发
- 二维码扫描
- 触摸传感器
- 摄像头识别
- 外部 API
- 签到系统 webhook
- 人工遥控器
```

### Flow 流程

```text
- 单步播放
- 多步骤主持流程
- 条件分支
- 循环播放
- 排队播放
- 优先级打断
- 超时处理
- 失败兜底
```

### Assets 素材

```text
- 文案
- 音频
- 视频
- 表情
- LED 灯效
- 二维码
- 产品图片
- 客户 Logo
```

### Robot Actions 机器人动作

```text
- TTS
- PlayAudioFile
- PlayVideo
- PlayEmoji
- LED
- Preset Motion
- LinkCraft Action
- Locomotion
- Hand / Gripper
```

---

## 4.4 Robot Adapter

封装 X2 AimDK，不让上层业务直接调用底层 ROS2 / AimDK。

建议接口：

```python
play_tts(text, priority=6)
play_audio(file_path, priority=6)
play_video(file_path, priority=5)
play_emoji(emoji_id, priority=5)
play_led(config)
play_motion(motion_id)
play_linkcraft(action_id)
set_volume(value)
stop_current()
get_robot_status()
send_velocity(forward, lateral, yaw_rate)
```

---

## 4.5 Asset Manager 素材管理

负责管理客户素材。

内容：

```text
- Logo
- 产品视频
- 产品图片
- 活动背景图
- 二维码
- TTS 文案
- 预生成音频
- 屏幕显示素材
```

建议素材结构：

```text
/client_id/event_id/assets/
├── logo/
├── videos/
├── images/
├── audio/
├── qr/
└── scripts/
```

---

## 4.6 Speech Manager

负责语音相关能力。

优先策略：

```text
1. 默认使用 X2 原生 TTS，保持机器人原本音色。
2. 如客户要求固定音频，则提前生成 WAV 后由 X2 播放。
3. 如客户要求品牌专属声音，后续再接 voice cloning TTS。
```

不建议第一版强推 voice cloning，因为会涉及授权、样本、训练质量和合规风险。

---

## 4.7 Knowledge / RAG Manager

用于产品文档导入、FAQ 问答和产品简介生成。

推荐流程：

```text
产品 PDF / Word / PPT
↓
Dify / RAG 知识库
↓
生成 30 秒 / 60 秒 / 90 秒简介
↓
人工审核
↓
保存到活动话术
↓
平板点击产品
↓
X2 使用原生 TTS 播放
```

第一版建议：

```text
RAG 只负责生成文字，不负责直接现场实时发挥。
```

---

## 4.8 Event Access License Manager

负责按天 / 按周授权。

字段建议：

```json
{
  "client_id": "rental_company_001",
  "event_id": "abc_product_launch",
  "robot_id": "X2U-001",
  "license_type": "weekly",
  "start_date": "2026-07-01",
  "end_date": "2026-07-07",
  "status": "active"
}
```

到期行为：

```text
- 平板控制台停止执行机器人动作
- 后台只允许查看历史项目
- 项目可复制为新活动
- 素材和日志保留 30 天
```

---

## 5. 内置场景模板

第一版建议内置 8 个模板。

---

## 5.1 Welcome Reception 迎宾机器人

场景：

```text
展会入口、发布会入口、酒店入口、商场活动入口。
```

能力：

```text
- 欢迎嘉宾
- 介绍品牌
- 邀请扫码
- 邀请合影
- 播放 Logo / 视频
- 挥手、比心、鼓掌
```

配置项：

```text
- 客户名称
- 品牌口号
- 欢迎语
- 活动名称
- 展位号
- 二维码
- Logo 视频
- 动作组合
- 语言
```

---

## 5.2 Product Presenter 产品介绍机器人

场景：

```text
客户在台上讲到某个产品，工作人员在平板点击产品，X2 开始介绍。
```

能力：

```text
- 按产品 ID 播放介绍
- 屏幕显示产品图片 / 视频
- 做抬手介绍动作
- 支持 30 秒 / 60 秒 / 90 秒版本
- 支持中英双语
- 可接 RAG 自动生成产品简介
```

配置项：

```text
- 产品名称
- 产品资料
- 产品卖点
- 介绍时长
- 屏幕视频
- TTS 文案
- 动作
- 表情
```

推荐实践：

```text
Dify 生成简介 → 人工审核 → X2 原生 TTS 播放。
```

---

## 5.3 Event MC 活动主持机器人

场景：

```text
发布会、开幕式、晚宴、周年庆、颁奖典礼。
```

能力：

```text
- 开场白
- 嘉宾介绍
- 倒计时
- 宣布启动仪式
- 抽奖播报
- 颁奖词
- 结束感谢
```

平板按钮示例：

```text
[开场]
[介绍嘉宾]
[倒计时]
[启动仪式]
[抽奖]
[结束语]
```

---

## 5.4 Lucky Draw 抽奖机器人

场景：

```text
企业晚宴、商场活动、发布会、年会。
```

能力：

```text
- 宣布抽奖规则
- 屏幕倒计时
- 播报中奖者
- 做鼓掌动作
- 播放 LED 灯效
```

配置项：

```text
- 奖项名称
- 抽奖名单
- 抽奖规则
- 倒计时文案
- 中奖播报文案
- 背景视频
```

---

## 5.5 Photo Booth 拍照打卡机器人

场景：

```text
商场、车展、品牌快闪、婚礼、企业活动。
```

能力：

```text
- 邀请观众合影
- 摆动作
- 说拍照口号
- 屏幕显示品牌 Logo
- 显示二维码取图
- 播放可爱表情
```

可集成：

```text
- 相机系统
- iPad 拍照
- 云相册
- 二维码取图
- 品牌水印
```

---

## 5.6 AI FAQ 接待机器人

场景：

```text
展会、地产展厅、大学开放日、企业 showroom。
```

能力：

```text
- 回答客户常见问题
- 介绍公司
- 介绍产品
- 提供地址、营业时间、联系方式
- 显示二维码
```

建议输入方式：

```text
- 平板选择问题
- 平板输入问题
- 二维码手机提问
- 外接 ASR
```

注意：

```text
第一版不要依赖机器人内建 ASR 作为主链路。
```

---

## 5.7 Guided Exhibit 展厅讲解机器人

场景：

```text
企业展厅、博物馆、学校、政府馆、科技馆。
```

能力：

```text
- A 展区讲解
- B 展区讲解
- 展品故事介绍
- 播放对应视频
- 回答常见问题
```

最稳触发方式：

```text
- 工作人员平板点击
- 二维码识别
- NFC 标签
- 展区按钮
```

---

## 5.8 Ceremony Launch 启动仪式机器人

场景：

```text
开幕仪式、发布会启动、品牌揭幕。
```

能力：

```text
- 倒计时
- 开幕台词
- 屏幕播放启动视频
- LED 灯效
- 挥手 / 鼓掌 / 敬礼动作
```

---

## 6. 移动能力实践方案

## 6.1 能不能支持移动？

可以。X2 二开可以通过 locomotion velocity 控制：

```text
- forward velocity
- lateral velocity
- yaw rate
```

但二开接口不是直接提供：

```text
walk_forward(3m)
turn_right(90deg)
```

这些高级函数需要平台自己封装。

---

## 6.2 相对移动控制

用户需求示例：

```text
启动前把当前站姿位置设为 0，然后往前走 3 米。
```

实践逻辑：

```text
1. 启动时读取当前 pose。
2. 把当前 pose 记录为 origin。
3. 发 forward velocity。
4. 持续读取当前 pose。
5. 计算当前位置相对 origin 的前向偏移。
6. 偏移达到 3 米后停止。
```

不是单纯靠：

```text
速度 × 时间
```

而是靠：

```text
当前 pose - origin pose
```

判断是否到达。

---

## 6.3 坐标计算

如果机器人启动时朝向不是世界坐标 x 方向，需要用 origin yaw 转换：

```text
relative_forward_distance =
cos(origin_yaw) * (current_x - origin_x)
+ sin(origin_yaw) * (current_y - origin_y)
```

这样才是真正的“以启动站姿方向为前方”。

---

## 6.4 移动控制等级

### Level 1：Open-loop 时间估算

```text
distance / speed = duration
```

优点：

```text
- 开发快
- 不依赖定位
- 适合舞台小动作
```

缺点：

```text
- 误差大
- 地面变化会影响结果
```

### Level 2：IMU Yaw 闭环

```text
- 前进距离可以先用时间估算
- 转 90 度用 IMU yaw 闭环
```

适合：

```text
- 舞台转身
- 展台内固定转向
```

### Level 3：Odom / SLAM Pose 全闭环

```text
- 记录 origin pose
- 计算目标相对坐标
- 实时读取当前 pose
- 根据误差发速度命令
- 到达阈值后停止
```

适合：

```text
- 舞台路线
- 固定展位路线
- 产品区移动讲解
```

---

## 6.5 移动安全限制

必须实现：

```text
- 最大速度限制
- 最大角速度限制
- 移动前语音提醒
- 移动中禁止复杂上肢动作
- 平板紧急停止
- 网络断开自动停止
- 定位丢失自动停止
- 超时自动停止
- 低电量禁止移动
- 非稳定站立状态禁止移动
```

---

## 7. ArUco / AprilTag 视觉点位停靠方案

## 7.1 功能定位

该功能建议命名为：

```text
Visual Marker Docking
视觉点位停靠
```

不要叫：

```text
自主导航
```

因为它不是完整导航，而是：

```text
机器人识别指定视觉 marker，并移动到 marker 附近停止。
```

---

## 7.2 为什么不用普通颜色贴纸

普通颜色贴纸可以做 demo，但不适合长期交付。

问题：

```text
- 容易受灯光影响
- 容易和地毯 / 地面颜色混淆
- 不能区分不同点位 ID
- 难以稳定估算位姿
```

更推荐：

```text
- ArUco Marker
- AprilTag Marker
```

---

## 7.3 Marker 准备

建议规格：

```text
- 尺寸：15cm × 15cm 起步
- 推荐：20cm × 20cm
- 黑白高对比
- 保留白边
- 避免反光
- 不要贴在容易被人踩坏的位置
```

Marker ID 示例：

```text
ID 1 = 舞台中心点
ID 2 = 产品 A 点位
ID 3 = 拍照点
ID 4 = 待机点
```

---

## 7.4 X2 Ultra 摄像头可行性判断

根据 X2 Ultra 传感器配置截图，X2 Ultra 具备：

```text
- LiDAR
- RGB-D Depth Camera
- Stereo RGB Cameras
- Rear RGB Camera
- Interactive RGB Cameras
```

其中最适合做 marker 停靠的是：

```text
RGB-D Depth Camera
```

原因：

```text
- RGB 图像可识别 ArUco / AprilTag
- Depth 可估算距离
- 比单纯 RGB 更适合判断机器人距离 marker 多远
```

不用 LiDAR 也可以做，但安全避障能力会弱一些。

---

## 7.5 实践流程

### Step 1：读取相机 topic

在 X2 上查找：

```bash
ros2 topic list | grep -Ei "rgb|depth|camera|image|camera_info"
```

需要找到：

```text
- RGB image topic
- Depth image topic
- Camera info / intrinsics topic
```

---

### Step 2：识别 Marker

使用：

```text
- OpenCV ArUco
或
- AprilTag detector
```

检测结果：

```text
- marker_id
- 四个角点 pixel 坐标
- marker 中心点
- marker 在画面中的大小
```

---

### Step 3：估算相对位置

简化版：

```text
marker 在画面左边 → 左转
marker 在画面右边 → 右转
marker 在画面中间 → 往前走
marker 距离小于阈值 → 停止
```

稳定版：

```text
使用 camera_info + marker 实际尺寸 + PnP / depth
计算 marker 相对相机的 x / y / z
再转换成 robot base 坐标
```

---

### Step 4：控制机器人移动

控制方式：

```text
1. marker 偏左 / 偏右明显时：只转向，不前进。
2. marker 接近画面中心时：慢速前进。
3. 前进过程中持续修正 yaw。
4. 距离 marker 小于 stop_distance 时停止。
5. marker 丢失时立即停止。
```

建议速度：

```text
forward velocity: 0.05 – 0.15 m/s
yaw rate: 0.1 – 0.3 rad/s
```

---

## 7.6 不要追求精准踩到贴纸中心

摄像头存在脚下盲区，marker 太近时可能看不到完整图案。

推荐定义：

```text
机器人移动到 marker 附近并停止。
```

不要定义：

```text
机器人精准踩到 marker 中心。
```

推荐设计：

```text
Marker 是导航参考点，不是脚掌最终落点。
机器人最终站位 = marker 前方或后方固定 offset。
```

例如：

```text
检测到 ID 3，距离 marker 0.5m 时停止。
此时机器人就是拍照点站位。
```

---

## 7.7 速度观感优化

走太慢会显得不真实。推荐使用：

```text
预设路线快速接近 + 视觉 marker 最后校准
```

例如：

```text
平板点击“去产品 A”
↓
机器人用相对移动脚本走到产品 A 附近
↓
最后 0.8 – 1.0m 开启 AprilTag 对准
↓
停稳
↓
屏幕切换产品视频
↓
抬手
↓
开始介绍
```

分段速度建议：

```text
3.0m → 1.5m:
forward 0.25 – 0.35 m/s

1.5m → 0.8m:
forward 0.15 – 0.25 m/s

0.8m → 0.5m:
forward 0.05 – 0.12 m/s

≤ 0.5m:
停止
```

---

## 8. Product Presenter + RAG + TTS 实践方案

## 8.1 推荐流程

```text
客户产品文档
↓
Dify Knowledge Base
↓
生成产品简介
↓
人工审核
↓
保存为活动话术
↓
平板点击产品
↓
X2 原生 TTS 播放
↓
屏幕显示产品视频
↓
机器人做介绍动作
```

---

## 8.2 为什么优先使用 X2 原生 TTS

如果客户要求保持机器人原有音色，最合适方式是：

```text
RAG 只生成文字，最终由 X2 原生 PlayTts 播放。
```

不建议第一版用外部 TTS 克隆 X2 音色，因为：

```text
- 音色授权不清楚
- 相似度不一定稳定
- 可能涉及合规问题
- 现场流程更复杂
```

---

## 8.3 Dify 文档导入实践

第一版手动导入即可：

```text
Dify → Knowledge → Create Knowledge → Import from file
```

文档建议：

```text
- 一个产品一个文档包
- 包含 brochure、规格书、FAQ、卖点说明
- 不要把所有产品塞进一个大 PDF
```

Prompt 模板：

```text
你是专业产品发布会主持人，现在要为一台人形机器人 X2 生成产品介绍词。

请严格基于知识库内容，为指定产品生成一段适合机器人在台上朗读的产品简介。

要求：
1. 语言：{{language}}
2. 时长：{{duration}} 秒
3. 语气：专业、自然、有亲和力
4. 句子要适合 TTS 朗读，不要太长
5. 不要编造知识库里没有的信息
6. 不要输出 bullet point
7. 不要输出标题
8. 不要提到“根据文档”或“资料显示”
9. 如果资料不足，请输出：“当前产品资料不足，无法生成准确介绍。”

产品名称：
{{product_name}}

知识库检索内容：
{{context}}

请直接输出最终讲稿。
```

---

## 9. 标准场景配置 JSON 示例

```json
{
  "scene_id": "product_presenter_001",
  "scene_name": "Product Presenter",
  "client": "ABC Tech",
  "language": "zh-CN",
  "trigger": {
    "type": "tablet_button",
    "button_label": "介绍产品 A"
  },
  "steps": [
    {
      "step_id": "opening",
      "actions": [
        {
          "type": "screen_video",
          "file": "/var/tmp/assets/abc_logo.mp4",
          "priority": 5
        },
        {
          "type": "emoji",
          "emoji_id": 90,
          "priority": 5
        },
        {
          "type": "motion",
          "motion_id": "wave"
        },
        {
          "type": "tts",
          "text": "大家好，欢迎来到 ABC Tech 的产品发布会。",
          "priority": 6
        }
      ]
    },
    {
      "step_id": "product_a_intro",
      "actions": [
        {
          "type": "screen_video",
          "file": "/var/tmp/assets/product_a.mp4",
          "priority": 5
        },
        {
          "type": "motion",
          "motion_id": "right_hand_raise"
        },
        {
          "type": "tts",
          "text": "接下来为您介绍我们的核心产品。",
          "priority": 6
        }
      ]
    }
  ],
  "fallback": {
    "on_error": "抱歉，我这里遇到了一点小问题，请稍后再试。",
    "on_network_lost": "stop_all"
  }
}
```

---

## 10. MVP 开发范围

第一版目标：

```text
让租赁公司可以创建一个客户活动，选择场景模板，上传素材，编辑话术，然后用平板控制 X2 完成现场互动。
```

### 10.1 MVP 必须支持

```text
- 客户管理
- 活动管理
- 按天 / 按周授权
- 场景模板选择
- 话术编辑
- 素材上传
- 平板控制台
- TTS
- 表情
- 屏幕视频
- 预设动作
- 停止 / 重播 / 音量控制
- 日志记录
```

### 10.2 MVP 场景模板

```text
1. Welcome Reception
2. Product Presenter
3. Event MC
4. Photo Booth
5. Lucky Draw
```

### 10.3 第二阶段功能

```text
- RAG 产品介绍
- FAQ 接待
- 移动脚本
- Visual Marker Docking
- 多机器人管理
- 白标界面
```

---

## 11. 技术栈建议

### 后端

```text
Python FastAPI
PostgreSQL
Redis
ROS2 bridge / rclpy node
```

### 前端

```text
Admin Portal: Vue / React
Tablet Console: Web App / PWA
```

### 文件存储

```text
本地文件存储 / MinIO / S3-compatible storage
```

### RAG

```text
Dify Cloud / Self-hosted Dify
```

### X2 机器人侧

```text
ROS2 node
AimDK service/topic adapter
Asset sync script
Runtime status monitor
```

---

## 12. 风险与边界

不要第一版承诺：

```text
- 任意环境自主导航
- 自动上下楼梯
- 自动避开复杂人群
- 自动识别所有产品
- 语音自由问答 100% 准确
- 自动抓取任意物品
- 无需现场人员看管
```

可以承诺：

```text
- 平板可控互动
- 预设场景流程
- 产品介绍
- 迎宾 / 主持 / 抽奖 / 拍照
- 简单受控移动
- 视觉 marker 辅助停靠
- RAG 辅助生成话术
```

---

## 13. 推荐交付路线

### Phase 1：基础平台

```text
- Robot Adapter
- Admin Portal
- Tablet Console
- 场景模板
- 授权管理
- 话术 / 素材管理
```

### Phase 2：产品介绍增强

```text
- Dify 文档导入
- 产品简介生成
- 多语言话术
- 人工审核流程
```

### Phase 3：移动能力

```text
- 手动遥控
- 简单移动脚本
- 相对移动控制
- 安全停止
```

### Phase 4：视觉点位停靠

```text
- ArUco / AprilTag 识别
- RGB-D 距离估算
- 视觉闭环靠近
- 丢失目标停止
```

### Phase 5：商业化增强

```text
- 活动包管理
- 多机器人授权
- 白标界面
- 远程诊断
- 日志导出
```

---

## 14. 最终产品定义

```text
X2 Rental Scenario Platform

一套给机器人租赁公司的 X2 场景编排系统。
租赁公司可以按天或按周开通系统，在活动期间配置客户内容、控制机器人、复用场景模板，从而快速交付不同类型的机器人活动服务。
```

核心价值：

```text
1. 缩短活动准备时间。
2. 减少每次活动重新开发。
3. 提高 X2 租赁服务单价。
4. 让普通工作人员也能操作机器人。
5. 把迎宾、主持、产品介绍、抽奖、拍照、FAQ、移动站位等能力模板化。
```

---

## 15. 对租赁公司的销售话术

```text
你们不需要一次性买断整套系统，也不需要每次活动重新开发。

我们按天或按周开放 X2 场景平台。
你们有客户活动时，只需要开通对应时间，上传客户资料、配置话术和素材，就可以让 X2 执行迎宾、产品介绍、主持、抽奖、拍照等互动任务。

这样你们可以用更低成本开始使用系统，也可以根据活动数量灵活付费。
```

---

## 16. 当前最推荐执行策略

```text
1. 以 Founder Partner 价格签下第一个租赁公司。
2. 报价：RM 2,500 / week，RM 500 / day。
3. 先实现 5 个高频场景模板。
4. 不卖源码，只卖系统使用权。
5. 所有当前已有功能包含在授权内。
6. 新功能、复杂现场调试、外部系统对接另行讨论。
7. 前 6 个月收集真实活动反馈，打磨平台。
8. 6 个月后重新定义正式市场价。
```
