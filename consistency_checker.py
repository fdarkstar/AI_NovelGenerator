# consistency_checker.py
# -*- coding: utf-8 -*-
from llm_adapters import create_llm_adapter

# ============== 增加对"剧情要点/未解决冲突"进行检查的可选引导 ==============
CONSISTENCY_PROMPT = """\
请检查下面的小说设定与最新章节是否存在明显冲突或不一致之处，如有请列出：
- 小说设定：
{novel_setting}

- 角色状态（可能包含重要信息）：
{character_state}

- 前文摘要：
{global_summary}

- 已记录的未解决冲突或剧情要点：
{plot_arcs}  # 若为空可能不输出

- 最新章节内容：
{chapter_text}

如果存在冲突或不一致，请说明；如果在未解决冲突中有被忽略或需要推进的地方，也请提及；否则请返回"无明显冲突"。
"""

# ============== 新增：检查章节是否超出目录描写、是否提前写了下一章的内容 ==============
BLUEPRINT_CONSISTENCY_PROMPT = """\
请检查当前章节的内容是否符合章节目录的规划，并检查是否提前写了下一章的内容。

- 当前章节目录信息：
  章号：第{current_chapter_number}章
  标题：{current_chapter_title}
  本章定位：{current_chapter_role}
  核心作用：{current_chapter_purpose}
  本章简述：{current_chapter_summary}

- 下一章节目录信息：
  章号：第{next_chapter_number}章
  标题：{next_chapter_title}
  本章定位：{next_chapter_role}
  核心作用：{next_chapter_purpose}
  本章简述：{next_chapter_summary}

- 当前章节内容：
{chapter_text}

请检查以下方面并返回结果：
1. 当前章节是否符合本章在目录中的定位和核心作用？
2. 当前章节是否提前涉及了下一章的情节、冲突或关键事件？
3. 如果检测到内容提前到了下一章，请具体指出哪些内容应该属于下一章，并建议如何调整。

请按以下格式返回：
【一致性检查】
[检查结果]

【内容提前检测】
[如果检测到内容提前，列出具体内容和建议；否则返回"无内容提前"]
"""

def check_consistency(
    novel_setting: str,
    character_state: str,
    global_summary: str,
    chapter_text: str,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float = 0.3,
    plot_arcs: str = "",
    interface_format: str = "OpenAI",
    max_tokens: int = 2048,
    timeout: int = 600
) -> str:
    """
    调用模型做简单的一致性检查。可扩展更多提示或校验规则。
    新增: 会额外检查对"未解决冲突或剧情要点"（plot_arcs）的衔接情况。
    """
    prompt = CONSISTENCY_PROMPT.format(
        novel_setting=novel_setting,
        character_state=character_state,
        global_summary=global_summary,
        plot_arcs=plot_arcs,
        chapter_text=chapter_text
    )

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )

    # 调试日志
    print("\n[ConsistencyChecker] Prompt >>>", prompt)

    response = llm_adapter.invoke(prompt)
    if not response:
        return "审校Agent无回复"
    
    # 调试日志
    print("[ConsistencyChecker] Response <<<", response)

    return response


def check_blueprint_consistency(
    current_chapter_info: dict,
    next_chapter_info: dict,
    chapter_text: str,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float = 0.3,
    interface_format: str = "OpenAI",
    max_tokens: int = 2048,
    timeout: int = 600
) -> str:
    """
    检查当前章节是否超出了目录的描写，是否提前写了下一章的内容。
    
    参数:
        current_chapter_info: 当前章节的目录信息，包含 chapter_number, chapter_title, 
                             chapter_role, chapter_purpose, chapter_summary
        next_chapter_info: 下一章的目录信息（同上结构），如果不存在则传入空dict
        chapter_text: 当前章节的文本内容
        其他参数: LLM 调用相关参数
    
    返回:
        检查结果字符串
    """
    # 提取当前章节信息
    current_chapter_number = current_chapter_info.get("chapter_number", 0)
    current_chapter_title = current_chapter_info.get("chapter_title", "")
    current_chapter_role = current_chapter_info.get("chapter_role", "")
    current_chapter_purpose = current_chapter_info.get("chapter_purpose", "")
    current_chapter_summary = current_chapter_info.get("chapter_summary", "")
    
    # 提取下一章信息
    next_chapter_number = next_chapter_info.get("chapter_number", 0)
    next_chapter_title = next_chapter_info.get("chapter_title", "")
    next_chapter_role = next_chapter_info.get("chapter_role", "")
    next_chapter_purpose = next_chapter_info.get("chapter_purpose", "")
    next_chapter_summary = next_chapter_info.get("chapter_summary", "")
    
    # 如果没有下一章信息，设置默认值
    if not next_chapter_title:
        next_chapter_number = current_chapter_number + 1
        next_chapter_title = "（暂无目录信息）"
        next_chapter_role = "（暂无目录信息）"
        next_chapter_purpose = "（暂无目录信息）"
        next_chapter_summary = "（暂无目录信息）"
    
    prompt = BLUEPRINT_CONSISTENCY_PROMPT.format(
        current_chapter_number=current_chapter_number,
        current_chapter_title=current_chapter_title,
        current_chapter_role=current_chapter_role,
        current_chapter_purpose=current_chapter_purpose,
        current_chapter_summary=current_chapter_summary,
        next_chapter_number=next_chapter_number,
        next_chapter_title=next_chapter_title,
        next_chapter_role=next_chapter_role,
        next_chapter_purpose=next_chapter_purpose,
        next_chapter_summary=next_chapter_summary,
        chapter_text=chapter_text
    )

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )

    # 调试日志
    print("\n[BlueprintConsistencyChecker] Prompt >>>", prompt)

    response = llm_adapter.invoke(prompt)
    if not response:
        return "目录一致性检查Agent无回复"
    
    # 调试日志
    print("[BlueprintConsistencyChecker] Response <<<", response)

    return response
