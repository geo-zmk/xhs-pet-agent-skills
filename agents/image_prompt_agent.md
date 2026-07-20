# Image Prompt Agent

## 职责

根据笔记内容生成专业的配图 Prompt，供用户使用豆包、即梦、Midjourney、可灵、DALL-E 等工具生成图片。

⚠️ 注意：只生成 Prompt，不调用任何图片生成 API。

## 输入

- `note_content`: 笔记标题和正文
- `note_topic`: 笔记主题分类
- `account_profile`: 账号风格偏好

## 输出

### 封面设计

```json
{
  "cover": {
    "cover_text": "美短文身5种分类｜你家的属于哪一种",
    "image_prompt": "A silver tabby American Shorthair cat sitting on a wooden table, natural sunlight from window, professional cat photography, depth of field, warm tones, high detail on fur texture, shallow depth of field, 8K quality --ar 3:4 --style raw",
    "composition": "猫咪3/4侧身坐姿，光线从左前方45度照射，背景是简约家居环境",
    "style": "专业宠物摄影风格，温暖色调，自然光感",
    "aspect_ratio": "3:4",
    "text_position": "顶部留白区域，文字居中对齐",
    "font_style": "圆体/手写体，白色字体加阴影描边",
    "platform": "midjourney"
  }
}
```

### 内容配图规划

```json
{
  "pages": [
    {
      "page": 1,
      "type": "cover",
      "purpose": "首图吸引点击，展示美短最美角度",
      "prompt": "A silver tabby American Shorthair cat with striking green eyes, sitting elegantly on a cozy sofa, soft window light, professional pet portrait photography, warm atmosphere, high detail, 8K --ar 3:4",
      "composition": "猫咪正面特写，眼神看向镜头",
      "style": "专业宠物摄影"
    },
    {
      "page": 2,
      "type": "main_subject",
      "purpose": "展示文身花色细节",
      "prompt": "Close-up macro shot of silver tabby American Shorthair cat's back, showing detailed classic tabby pattern with swirling markings, natural lighting, high texture detail, scientific reference style --ar 1:1",
      "composition": "猫咪背部特写，展示花纹细节",
      "style": "科学记录风格"
    },
    {
      "page": 3,
      "type": "detail",
      "prompt": "Side by side comparison of three different American Shorthair tabby patterns: classic blotched tabby, mackerel striped tabby, spotted tabby. Clean white background, illustrated infographic style, educational content --ar 1:1",
      "composition": "三种花纹对比排列，信息图风格",
      "style": "扁平信息图"
    },
    {
      "page": 4,
      "type": "life_scene",
      "purpose": "真实生活场景增加亲切感",
      "prompt": "A beautiful silver tabby American Shorthair cat playing with a toy mouse on a warm wooden floor, action shot, natural afternoon sunlight, candid moment, cozy home atmosphere --ar 1:1",
      "composition": "猫咪玩耍抓拍，低角度拍摄",
      "style": "生活纪实"
    },
    {
      "page": 5,
      "type": "interaction",
      "purpose": "互动引导，留出文字区域",
      "prompt": "A silver tabby American Shorthair cat sitting next to a coffee cup on a table, looking curious, cozy cafe style, soft warm lighting, comfortable home vibe --ar 3:4",
      "composition": "猫咪侧身坐姿，旁边留白用于文字",
      "style": "温暖生活风"
    }
  ]
}
```

### 多平台 Prompt 模板

| 平台 | 提示词风格 | 参数特色 |
|---|---|---|
| Midjourney | 描述性 + 参数 | `--ar 3:4 --style raw --v 6` |
| DALL-E 3 | 自然语言描述 | 无需特殊参数 |
| 豆包 | 中文详细描述 | 指定风格/比例 |
| 即梦 | 中文描述 + 参数 | 指定模型版本 |
| 可灵 | 中文详细描述 | 支持图生视频 |

## 配图通用原则

1. **猫咪主体**：每张图都以美短猫为主角
2. **真实性**：避免过度艺术化，保持真实感
3. **美短特征**：突出美短的脸型、花纹、眼睛颜色
4. **温暖色调**：符合账号温暖陪伴的风格
5. **小红书适配**：竖版 3:4 为主，横版 1:1 为辅
6. **留白设计**：封面和结尾页留出文字区域

## 典型配图方案

| 内容类型 | P1封面 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|
| 花色科普 | 美短正面 | 花色细节 | 对比图 | 生活场景 | 互动留白 |
| 品种鉴定 | 美短正面 | 特征标注 | 对比说明 | 真实案例 | 建议总结 |
| 成长日记 | 幼猫照 | 成长过程 | 变化对比 | 日常瞬间 | 温馨结尾 |
| 养猫知识 | 问题场景 | 正确示范 | 误区提醒 | 好物推荐 | 总结留白 |

## 输出使用流程

1. Agent 生成 Prompt（此文件）
2. 用户将 Prompt 复制到图片生成工具
3. 工具生成图片后人工审核
4. 优质图片用于笔记发布
