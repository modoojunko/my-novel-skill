"""
GitHub Issue 管理模块
为 my-novel-skill 提供 GitHub Issue 提交和查阅功能
注意：所有操作仅针对 https://github.com/modoojunko/my-novel-skill 仓库
      可以在任何目录下执行，会自动提交到指定仓库

Supports both interactive and non-interactive modes:
- Interactive: `story github <subcommand>` (normal output)
- Non-interactive: `story github <subcommand> --non-interactive`
- JSON output: `story github <subcommand> --json`
"""

import argparse
import sys
import subprocess
import json
from pathlib import Path

from . import cli


def show_github_help():
    print("""
Usage: story github <subcommand> [options]

GitHub Issue 管理工具 - 仅用于 modoojunko/my-novel-skill 仓库
注意：可以在任何目录下执行，会自动提交到指定仓库

Subcommands:
  check     Check GitHub CLI installation and auth status
  list      List issues
  view      View issue
  create    Create issue
  bug       Create bug report
  feature   Create feature request

Options:
  --json               Output JSON format for AI consumption
  --non-interactive    Non-interactive mode
  --args JSON          JSON string with arguments (not used for github)

Use 'story github <subcommand> --help' for subcommand-specific help.
""")


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


TARGET_REPO = "modoojunko/my-novel-skill"


def run_gh_command(args, check=True):
    """运行 GitHub CLI 命令（指定仓库）"""
    try:
        result = subprocess.run(
            ["gh", "-R", TARGET_REPO] + args,
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
        if any([title, body, labels, body_file]):
            cli.print_out(cli.c("警告: --interactive 模式下忽略其他参数", cli.Colors.YELLOW))
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
                     os=None, python_version=None, skill_version="v2",
                     error_message=""):
    """创建 Bug 报告"""
    if os is None:
        os = sys.platform
    if python_version is None:
        python_version = sys.version.split()[0]
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
    if len(sys.argv) < 2:
        show_github_help()
        return

    # Check for help
    if sys.argv[1] in ('help', '--help', '-h'):
        show_github_help()
        return

    # First, extract --json, --non-interactive, --args from anywhere in args
    # and set cli module's global state manually
    json_mode = '--json' in sys.argv
    non_interactive = '--non-interactive' in sys.argv

    # Find and parse --args if present
    args_dict = {}
    if '--args' in sys.argv:
        args_idx = sys.argv.index('--args')
        if args_idx + 1 < len(sys.argv):
            try:
                args_dict = json.loads(sys.argv[args_idx + 1])
            except json.JSONDecodeError:
                pass

    # Set cli module's global state manually
    cli._json_mode = json_mode
    cli._non_interactive = non_interactive
    cli._args = args_dict

    # Now filter out the global options and process subcommand
    filtered_args = []
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ('--json', '--non-interactive'):
            i += 1
        elif arg == '--args':
            i += 2
        else:
            filtered_args.append(arg)
            i += 1

    if not filtered_args:
        show_github_help()
        return

    subcommand = filtered_args[0].lower()
    subcommand_args = filtered_args[1:]

    # Now parse the github-specific subcommands
    parser = argparse.ArgumentParser(
        description="GitHub Issue 查阅和创建工具"
    )

    if subcommand == "check":
        # Check command doesn't need additional args
        github_args = parser.parse_args(subcommand_args)
    elif subcommand == "list":
        parser.add_argument("--state", default="open", choices=["open", "closed", "all"], help="Issue 状态")
        parser.add_argument("--label", help="标签过滤")
        parser.add_argument("--limit", type=int, default=20, help="显示数量")
        github_args = parser.parse_args(subcommand_args)
    elif subcommand == "view":
        parser.add_argument("number", type=int, help="Issue 编号")
        parser.add_argument("--comments", action="store_true", help="显示评论")
        parser.add_argument("--web", action="store_true", help="在浏览器中打开")
        github_args = parser.parse_args(subcommand_args)
    elif subcommand == "create":
        parser.add_argument("--title", help="Issue 标题")
        parser.add_argument("--body", help="Issue 正文")
        parser.add_argument("--body-file", help="从文件读取正文")
        parser.add_argument("--label", action="append", help="标签（可多次使用）")
        parser.add_argument("--interactive", action="store_true", help="交互式创建")
        github_args = parser.parse_args(subcommand_args)
    elif subcommand == "bug":
        parser.add_argument("--title", required=True, help="Bug 标题")
        parser.add_argument("--description", required=True, help="问题描述")
        parser.add_argument("--steps", default="", help="重现步骤")
        parser.add_argument("--expected", default="", help="预期行为")
        parser.add_argument("--actual", default="", help="实际行为")
        parser.add_argument("--os", help="操作系统（默认自动检测）")
        parser.add_argument("--python-version", help="Python 版本（默认自动检测）")
        parser.add_argument("--skill-version", default="v2", help="my-novel-skill 版本")
        parser.add_argument("--error-message", default="", help="错误信息")
        parser.add_argument("--bug-label", default="bug", help="Bug 标签名称")
        github_args = parser.parse_args(subcommand_args)
    elif subcommand == "feature":
        parser.add_argument("--title", required=True, help="功能需求标题")
        parser.add_argument("--description", required=True, help="需求描述")
        parser.add_argument("--use-case", default="", help="使用场景")
        parser.add_argument("--suggestion", default="", help="建议方案")
        parser.add_argument("--references", default="", help="相关参考")
        parser.add_argument("--enhancement-label", default="enhancement", help="功能需求标签名称")
        github_args = parser.parse_args(subcommand_args)
    else:
        show_github_help()
        return

    # 检查是否是 check 命令
    if subcommand == "check":
        if cli.is_interactive() or not cli.is_json_mode():
            cli.print_out(cli.c("检查 GitHub CLI 安装状态...", cli.Colors.CYAN))
        installed, version = check_gh_installed()
        if not installed:
            if cli.is_json_mode():
                cli.output_json({'success': False, 'error': 'GitHub CLI 未安装', 'check': 'installed'})
            else:
                cli.print_out(cli.c("GitHub CLI 未安装！", cli.Colors.RED))
                cli.print_out("请参考 README.md 中的安装指南")
            return 1

        if cli.is_interactive() or not cli.is_json_mode():
            cli.print_out(cli.c(f"✓ GitHub CLI 已安装: {version}", cli.Colors.GREEN))
            cli.print_out(cli.c("检查 GitHub CLI 认证状态...", cli.Colors.CYAN))

        authed, status = check_gh_auth()
        if not authed:
            if cli.is_json_mode():
                cli.output_json({'success': False, 'error': 'GitHub CLI 未认证', 'check': 'auth', 'installed': True, 'version': version})
            else:
                cli.print_out(cli.c("GitHub CLI 未认证！", cli.Colors.YELLOW))
                cli.print_out("请运行 'gh auth login' 完成认证")
            return 1

        if cli.is_json_mode():
            cli.output_json({'success': True, 'installed': True, 'authed': True, 'version': version, 'status': status})
        else:
            cli.print_out(cli.c("✓ GitHub CLI 已认证", cli.Colors.GREEN))
            cli.print_out(status)
        return 0

    # 其他命令需要先检查安装和认证
    installed, _ = check_gh_installed()
    if not installed:
        if cli.is_json_mode():
            cli.output_json({'success': False, 'error': 'GitHub CLI 未安装'})
        else:
            cli.print_out(cli.c("GitHub CLI 未安装！请先运行 'python story.py github check' 检查", cli.Colors.RED))
        return 1

    authed, _ = check_gh_auth()
    if not authed:
        if cli.is_json_mode():
            cli.output_json({'success': False, 'error': 'GitHub CLI 未认证'})
        else:
            cli.print_out(cli.c("GitHub CLI 未认证！请先运行 'gh auth login' 完成认证", cli.Colors.RED))
        return 1

    # 处理各个子命令
    if subcommand == "list":
        if cli.is_interactive() or not cli.is_json_mode():
            cli.print_out(cli.c(f"获取 Issue 列表（状态: {github_args.state}）...", cli.Colors.CYAN))
        success, stdout, stderr = list_issues(github_args.state, github_args.label, github_args.limit)
        if success:
            if cli.is_json_mode():
                cli.output_json({'success': True, 'output': stdout})
            else:
                print(stdout)
        else:
            if cli.is_json_mode():
                cli.output_json({'success': False, 'error': stderr})
            else:
                cli.print_out(cli.c(stderr, cli.Colors.RED))
            return 1

    elif subcommand == "view":
        if cli.is_interactive() or not cli.is_json_mode():
            cli.print_out(cli.c(f"查看 Issue #{github_args.number}...", cli.Colors.CYAN))
        success, stdout, stderr = view_issue(github_args.number, github_args.comments, github_args.web)
        if success:
            if cli.is_json_mode():
                cli.output_json({'success': True, 'output': stdout})
            else:
                print(stdout)
        else:
            if cli.is_json_mode():
                cli.output_json({'success': False, 'error': stderr})
            else:
                cli.print_out(cli.c(stderr, cli.Colors.RED))
            return 1

    elif subcommand == "create":
        if github_args.interactive:
            if cli.is_interactive() or not cli.is_json_mode():
                cli.print_out(cli.c("交互式创建 Issue...", cli.Colors.CYAN))
            success, stdout, stderr = create_issue(None, interactive=True)
        else:
            if not github_args.title:
                if cli.is_json_mode():
                    cli.output_json({'success': False, 'error': '必须提供 --title 参数或使用 --interactive'})
                else:
                    cli.print_out(cli.c("必须提供 --title 参数或使用 --interactive", cli.Colors.RED))
                return 1
            if cli.is_interactive() or not cli.is_json_mode():
                cli.print_out(cli.c(f"创建 Issue: {github_args.title}", cli.Colors.CYAN))
            success, stdout, stderr = create_issue(
                github_args.title, github_args.body, github_args.label, github_args.body_file
            )
        if success:
            if cli.is_json_mode():
                cli.output_json({'success': True, 'output': stdout})
            else:
                cli.print_out(cli.c("✓ Issue 创建成功！", cli.Colors.GREEN))
                print(stdout)
        else:
            if cli.is_json_mode():
                cli.output_json({'success': False, 'error': stderr})
            else:
                cli.print_out(cli.c(stderr, cli.Colors.RED))
            return 1

    elif subcommand == "bug":
        if cli.is_interactive() or not cli.is_json_mode():
            cli.print_out(cli.c(f"创建 Bug 报告: {github_args.title}", cli.Colors.CYAN))
        body = create_bug_report(
            github_args.description, github_args.steps, github_args.expected, github_args.actual,
            github_args.os, github_args.python_version, github_args.skill_version, github_args.error_message
        )
        success, stdout, stderr = create_issue(
            f"🐛 Bug：{github_args.title}", body, [github_args.bug_label]
        )
        if success:
            if cli.is_json_mode():
                cli.output_json({'success': True, 'output': stdout})
            else:
                cli.print_out(cli.c("✓ Bug 报告创建成功！", cli.Colors.GREEN))
                print(stdout)
        else:
            if cli.is_json_mode():
                cli.output_json({'success': False, 'error': stderr})
            else:
                cli.print_out(cli.c(stderr, cli.Colors.RED))
            return 1

    elif subcommand == "feature":
        if cli.is_interactive() or not cli.is_json_mode():
            cli.print_out(cli.c(f"创建功能需求: {github_args.title}", cli.Colors.CYAN))
        body = create_feature_request(
            github_args.description, github_args.use_case, github_args.suggestion, github_args.references
        )
        success, stdout, stderr = create_issue(
            f"🚀 功能需求：{github_args.title}", body, [github_args.enhancement_label]
        )
        if success:
            if cli.is_json_mode():
                cli.output_json({'success': True, 'output': stdout})
            else:
                cli.print_out(cli.c("✓ 功能需求创建成功！", cli.Colors.GREEN))
                print(stdout)
        else:
            if cli.is_json_mode():
                cli.output_json({'success': False, 'error': stderr})
            else:
                cli.print_out(cli.c(stderr, cli.Colors.RED))
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
