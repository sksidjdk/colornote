#!/usr/bin/env python3
"""
render-spec.py
使用 Jinja2 模板引擎自动替换 spec-template.md 中的占位符，基于 project.config.json 的值

使用方法：
    python3 scripts/render-spec.py
    或
    ./scripts/render-spec.py

输出：
    - spec-template-rendered.md：替换占位符后的文件（保留原模板不变）
"""

import json
import sys
import subprocess
from pathlib import Path

# 检查并安装依赖
def check_and_install_dependencies():
    try:
        import jinja2
        return True
    except ImportError:
        print("警告：未安装 Jinja2")
        print("正在尝试安装依赖...")
        
        # 检查是否有 requirements.txt
        script_dir = Path(__file__).parent
        requirements_file = script_dir / "requirements.txt"
        
        if requirements_file.exists():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
            except subprocess.CalledProcessError:
                print("错误：无法从 requirements.txt 安装依赖")
                print("请手动运行：pip install -r scripts/requirements.txt")
                sys.exit(1)
        else:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "jinja2"])
            except subprocess.CalledProcessError:
                print("错误：无法安装 Jinja2")
                print("请手动运行：pip install jinja2")
                sys.exit(1)
        
        # 使用纯 ASCII 字符避免在 Windows 控制台上出现编码问题
        print("[OK] 依赖安装完成")
        
        # 再次尝试导入
        try:
            import jinja2
            return True
        except ImportError:
            print("错误：安装后仍无法导入 Jinja2")
            sys.exit(1)

# 检查并安装依赖
check_and_install_dependencies()

from jinja2 import Template


def main():
    # 获取脚本所在目录和项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # 切换到项目根目录
    import os
    os.chdir(project_root)

    print("开始渲染 spec-template.md...")

    # 检查必要文件是否存在
    config_file = project_root / "project.config.json"
    template_file = project_root / "spec-template.md"

    if not config_file.exists():
        print(f"错误：找不到 {config_file}")
        sys.exit(1)

    if not template_file.exists():
        print(f"错误：找不到 {template_file}")
        sys.exit(1)

    # 读取 project.config.json
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误：无法解析 {config_file}: {e}")
        sys.exit(1)

    # 验证必需的配置项
    required_keys = ['github_owner', 'repo_name', 'default_branch']
    optional_keys = ['vercel_project_name']
    
    # 检查必需字段
    missing_keys = [key for key in required_keys if key not in config or not config[key]]
    
    # 检查可选字段，如果不存在则使用空字符串
    for key in optional_keys:
        if key not in config or not config[key]:
            config[key] = ""

    if missing_keys:
        print(f"错误：缺少必需的配置项: {', '.join(missing_keys)}")
        sys.exit(1)

    print("配置值：")
    for key in required_keys + optional_keys:
        value = config.get(key, "")
        print(f"  {key}: {value if value else '(未设置)'}")

    # 读取模板文件
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        print(f"错误：无法读取 {template_file}: {e}")
        sys.exit(1)

    # 使用 Jinja2 渲染模板
    try:
        template = Template(template_content)
        rendered_content = template.render(**config)
    except Exception as e:
        print(f"错误：模板渲染失败: {e}")
        sys.exit(1)

    # 写入渲染后的文件
    output_file = project_root / "spec-template-rendered.md"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
    except Exception as e:
        print(f"错误：无法写入 {output_file}: {e}")
        sys.exit(1)

    # 验证是否还有未替换的占位符
    import re
    remaining_placeholders = re.findall(r'\{\{[^}]+\}\}', rendered_content)

    if remaining_placeholders:
        print("\n警告：发现未替换的占位符：")
        for placeholder in set(remaining_placeholders):
            print(f"  {placeholder}")
    else:
        # 避免控制台编码问题，使用 ASCII 提示
        print("\n[OK] 所有占位符已成功替换")

    # 统计替换次数
    print("\n替换统计：")
    for key in required_keys + optional_keys:
        value = config.get(key, "")
        if value:
            count = rendered_content.count(value)
            print(f"  {key}: {count} 处")
        else:
            print(f"  {key}: (未设置，跳过统计)")

    # 使用 ASCII 字符，兼容 Windows 控制台编码
    print(f"\n[OK] 渲染完成！")
    print(f"输出文件：{output_file}")
    print("提示：原模板文件 spec-template.md 保持不变")


if __name__ == '__main__':
    main()

