"""
GitHub Issue 管理模块
为 my-novel-skill 提供 GitHub Issue 提交和查阅功能
"""

import argparse
import sys
import subprocess
import json
from pathlib import Path

from . import cli


def check_gh_installed():
    """检查 GitHub CLI 是否已安装"""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, None


def check_gh_auth():
    """检查 GitHub CLI 是否已认证"""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError:
        return False, None


def run_gh_command(args, check=True):
    """运行 GitHub CLI 命令"""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            check=check
        )
        return True, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stdout.strip(), e.stderr.strip()


def list_issues(state="open", label=None, limit=20):
    """列出 Issue"""
    args = ["issue", "list", "--limit", str(limit), "--state", state]
    if label:
        args.extend(["--label", label])
    return run_gh_command(args)


def view_issue(number, comments=False, web=False):
    """查看单个 Issue"""
    args = ["issue", "view", str(number)]
    if comments:
        args.append("--comments")
    if web:
        args.append("--web")
    return run_gh_command(args)


def create_issue(title, body=None, labels=None, body_file=None, interactive=False):
    """创建 Issue"""
    args = ["issue", "create"]
    if interactive:
        return run_gh_command(args)
    
    args.extend(["--title", title])
    
    if body:
        args.extend(["--body", body])
    elif body_file:
        args.extend(["--body-file", str(body_file)])
    
    if labels:
        for label in labels:
            args.extend(["--label", label])
    
    return run_gh_command(args)


BUG_TEMPLATE = """## Bug 反馈

### 问题描述
{description}

### 重现步骤
{steps}

### 预期行为
{expected}

### 实际行为
{actual}

### 环境信息
- 操作系统: {os}
- Python 版本: {python_version}
- my-novel-skill 版本: {skill_version}

### 错误信息
{error_message}

---
**提交者:** 用户
**项目:** my-novel-skill
"""

FEATURE_TEMPLATE = """## 功能需求

### 需求描述
{description}

### 使用场景
{use_case}

### 建议方案
{suggestion}

### 相关参考
{references}

---
**提交者:** 用户
**项目:** my-novel-skill
"""


def create_bug_report(description, steps="", expected="", actual="", 
                     os="", python_version="", skill_version="v2", 
                     error_message=""):
    """创建 Bug 报告"""
    return BUG_TEMPLATE.format(
        description=description,
        steps=steps,
        expected=expected,
        actual=actual,
        os=os,
        python_version=python_version,
        skill_version=skill_version,
        error_message=error_message
    )


def create_feature_request(description, use_case="", suggestion="", references=""):
    """创建功能需求"""
    return FEATURE_TEMPLATE.format(
        description=description,
        use_case=use_case,
        suggestion=suggestion,
        references=references
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="GitHub Issue 查阅和创建工具"
    )
    subparsers = parser.add_subparsers(title="子命令", dest="subcommand")
    
    # 检查命令
    check_parser = subparsers.add_parser("check", help="检查 GitHub CLI 安装和认证状态")
    
    # 列出命令
    list_parser = subparsers.add_parser("list", help="列出 Issues")
    list_parser.add_argument("--state", default="open", choices=["open", "closed", "all"], help="Issue 状态")
    list_parser.add_argument("--label", help="标签过滤")
    list_parser.add_argument("--limit", type=int, default=20, help="显示数量")
    
    # 查看命令
    view_parser = subparsers.add_parser("view", help="查看 Issue")
    view_parser.add_argument("number", type=int, help="Issue 编号")
    view_parser.add_argument("--comments", action="store_true", help="显示评论")
    view_parser.add_argument("--web", action="store_true", help="在浏览器中打开")
    
    # 创建命令
    create_parser = subparsers.add_parser("create", help="创建 Issue")
    create_parser.add_argument("--title", help="Issue 标题")
    create_parser.add_argument("--body", help="Issue 正文")
    create_parser.add_argument("--body-file", help="从文件读取正文")
    create_parser.add_argument("--label", action="append", help="标签（可多次使用）")
    create_parser.add_argument("--interactive", action="store_true", help="交互式创建")
    
    # Bug 报告子命令
    bug_parser = subparsers.add_parser("bug", help="创建 Bug 报告")
    bug_parser.add_argument("--title", required=True, help="Bug 标题")
    bug_parser.add_argument("--description", required=True, help="问题描述")
    bug_parser.add_argument("--steps", default="", help="重现步骤")
    bug_parser.add_argument("--expected", default="", help="预期行为")
    bug_parser.add_argument("--actual", default="", help="实际行为")
    bug_parser.add_argument("--os", default="", help="操作系统")
    bug_parser.add_argument("--python-version", default="", help="Python 版本")
    bug_parser.add_argument("--skill-version", default="v2", help="my-novel-skill 版本")
    bug_parser.add_argument("--error-message", default="", help="错误信息")
    
    # 功能需求子命令
    feature_parser = subparsers.add_parser("feature", help="创建功能需求")
    feature_parser.add_argument("--title", required=True, help="功能需求标题")
    feature_parser.add_argument("--description", required=True, help="需求描述")
    feature_parser.add_argument("--use-case", default="", help="使用场景")
    feature_parser.add_argument("--suggestion", default="", help="建议方案")
    feature_parser.add_argument("--references", default="", help="相关参考")
    
    args = parser.parse_args()
    
    if args.subcommand is None:
        parser.print_help()
        return
    
    # 检查是否是 check 命令
    if args.subcommand == "check":
        cli.print_out(cli.c("检查 GitHub CLI 安装状态...", cli.Colors.CYAN))
        installed, version = check_gh_installed()
        if not installed:
            cli.print_out(cli.c("GitHub CLI 未安装！", cli.Colors.RED))
            cli.print_out("请参考 README.md 中的安装指南")
            return 1
        
        cli.print_out(cli.c(f"✓ GitHub CLI 已安装: {version}", cli.Colors.GREEN))
        
        cli.print_out(cli.c("检查 GitHub CLI 认证状态...", cli.Colors.CYAN))
        authed, status = check_gh_auth()
        if not authed:
            cli.print_out(cli.c("GitHub CLI 未认证！", cli.Colors.YELLOW))
            cli.print_out("请运行 'gh auth login' 完成认证")
            return 1
        
        cli.print_out(cli.c("✓ GitHub CLI 已认证", cli.Colors.GREEN))
        cli.print_out(status)
        return 0
    
    # 其他命令需要先检查安装和认证
    installed, _ = check_gh_installed()
    if not installed:
        cli.print_out(cli.c("GitHub CLI 未安装！请先运行 'python story.py github check' 检查", cli.Colors.RED))
        return 1
    
    authed, _ = check_gh_auth()
    if not authed:
        cli.print_out(cli.c("GitHub CLI 未认证！请先运行 'gh auth login' 完成认证", cli.Colors.RED))
        return 1
    
    # 处理各个子命令
    if args.subcommand == "list":
        cli.print_out(cli.c(f"获取 Issue 列表（状态: {args.state}）...", cli.Colors.CYAN))
        success, stdout, stderr = list_issues(args.state, args.label, args.limit)
        if success:
            print(stdout)
        else:
            cli.print_out(cli.c(stderr, cli.Colors.RED))
            return 1
    
    elif args.subcommand == "view":
        cli.print_out(cli.c(f"查看 Issue #{args.number}...", cli.Colors.CYAN))
        success, stdout, stderr = view_issue(args.number, args.comments, args.web)
        if success:
            print(stdout)
        else:
            cli.print_out(cli.c(stderr, cli.Colors.RED))
            return 1
    
    elif args.subcommand == "create":
        if args.interactive:
            cli.print_out(cli.c("交互式创建 Issue...", cli.Colors.CYAN))
            success, stdout, stderr = create_issue(None, interactive=True)
        else:
            if not args.title:
                cli.print_out(cli.c("必须提供 --title 参数或使用 --interactive", cli.Colors.RED))
                return 1
            cli.print_out(cli.c(f"创建 Issue: {args.title}", cli.Colors.CYAN))
            success, stdout, stderr = create_issue(
                args.title, args.body, args.label, args.body_file
            )
        if success:
            cli.print_out(cli.c("✓ Issue 创建成功！", cli.Colors.GREEN))
            print(stdout)
        else:
            cli.print_out(cli.c(stderr, cli.Colors.RED))
            return 1
    
    elif args.subcommand == "bug":
        cli.print_out(cli.c(f"创建 Bug 报告: {args.title}", cli.Colors.CYAN))
        body = create_bug_report(
            args.description, args.steps, args.expected, args.actual,
            args.os, args.python_version, args.skill_version, args.error_message
        )
        success, stdout, stderr = create_issue(
            f"🐛 Bug：{args.title}", body, ["bug"]
        )
        if success:
            cli.print_out(cli.c("✓ Bug 报告创建成功！", cli.Colors.GREEN))
            print(stdout)
        else:
            cli.print_out(cli.c(stderr, cli.Colors.RED))
            return 1
    
    elif args.subcommand == "feature":
        cli.print_out(cli.c(f"创建功能需求: {args.title}", cli.Colors.CYAN))
        body = create_feature_request(
            args.description, args.use_case, args.suggestion, args.references
        )
        success, stdout, stderr = create_issue(
            f"🚀 功能需求：{args.title}", body, ["enhancement"]
        )
        if success:
            cli.print_out(cli.c("✓ 功能需求创建成功！", cli.Colors.GREEN))
            print(stdout)
        else:
            cli.print_out(cli.c(stderr, cli.Colors.RED))
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
