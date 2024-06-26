import json
import re
import textwrap

import bot
import responses
from command import (
    approve,
    calendar,
    clipboard,
    command_help,
    dict,
    game_1A2B,
    hash,
    issues,
    jump,
    math_calc,
    math_count,
    news,
    primes,
    random_number,
    random_vocab_review,
    random_vocab_test,
    remote_file,
    remote_terminal,
    search_github,
    search_online_judge,
    shortcut,
    todo,
    translate,
    tree,
    weather,
)
from constants import HELP_FLAG, TAB_SIZE


def load_terminal_mode_directory_structure() -> dict:
    with open("../data/json/terminal_mode_directory_structure.json") as file:
        return json.load(file)["structure"]


def load_Moonafly_structure() -> dict:
    with open("../data/json/Moonafly_structure.json") as file:
        return json.load(file)["structure"]


def load_user_cloak() -> dict:
    try:
        with open("../data/json/user_cloak.json") as file:
            user_cloak = json.load(file)
    except FileNotFoundError:
        user_cloak = {"terminal_mode": {}, "develop_mode": {}}
        with open("../data/json/user_cloak.json", "w") as file:
            json.dump(user_cloak, file, indent=4)
    return user_cloak


def write_user_cloak(user_cloak: dict):
    with open("../data/json/user_cloak.json", "w") as file:
        json.dump(user_cloak, file, indent=4)


def command_not_found(msg: str) -> str:
    space = "\n" + " " * TAB_SIZE * 2
    msg = space.join(msg.split("\n"))

    return textwrap.dedent(
        f"""
        ```
        {msg}: command not found
        {current_path()}
        ```
        """
    )


def function_developing() -> str:
    return textwrap.dedent(
        f"""
        ```
        sorry, this function is still developing
        {current_path()}
        ```
        """
    )


def handle_command_success(command: str) -> str:
    return textwrap.dedent(
        f"""
        ```
        {command} successfully
        {current_path()}
        ```
        """
    )


def handle_command_error(command: str, error_type: str, msg: str = None) -> str:
    error = ""
    if error_type == "format":
        error = "format error"
    elif error_type == "path":
        space = "\n" + " " * TAB_SIZE * 2
        path = space.join(msg.split("\n"))
        error = f"{path}: No such file or directory"
    elif error_type == "permission":
        error = "permission denied: requires highest authority"
    elif error_type == "index":
        error = "index out of range"
    elif error_type == "duplicated":
        error = "data duplicated"

    return textwrap.dedent(
        f"""
        ```
        {command}: {error}
        {current_path()}
        ```
        """
    )


def check_path_exists(command: str, path: str) -> tuple[bool, list]:
    # Skip all the '\' and split the path into a folder list
    path = path.replace("\\", "").split("/")

    # Create a copy of the current path stack
    temporary_path_stack = path_stack.copy()

    for folder in path:
        if folder == "" or folder == ".":
            continue

        # move up one directory
        elif folder == "..":
            if len(temporary_path_stack) > 1:
                temporary_path_stack.pop()

            elif temporary_path_stack[0] == "~":
                return False, handle_command_error(
                    command, "path", "/".join(path)
                )

        else:
            temporary_path_stack.append(folder)

    current_directory = load_terminal_mode_directory_structure()

    for folder in temporary_path_stack:
        if folder[-1] == ">":
            for item in list(current_directory):
                if (
                    item == "author"
                    and responses.terminal_mode_current_using_user
                    != responses.author
                ):
                    continue
                if item.startswith(folder[:-1]):
                    current_directory = current_directory[item]
                    temporary_path_stack[temporary_path_stack.index(folder)] = (
                        item
                    )
                    break

            else:
                return False, handle_command_error(
                    command, "path", "/".join(path)
                )

        elif folder in list(current_directory):
            if folder == "author":
                if (
                    responses.terminal_mode_current_using_user
                    == responses.author
                ):
                    current_directory = current_directory[folder]
                else:
                    return False, handle_command_error(command, "permission")
            else:
                current_directory = current_directory[folder]

        else:
            return False, handle_command_error(command, "path", "/".join(path))

    return True, temporary_path_stack


def get_ls_command_output(files: list, tab_count: int) -> str:
    if len(files) == 0:
        return ""
    output = ""
    max_file_length = max(len(file) for file in files)
    terminal_width = 79
    min_column_width = max_file_length + 2

    columns = min(len(files), terminal_width // min_column_width)
    column_groups = [files[i : len(files) : columns] for i in range(columns)]
    column_widths = [
        max(len(file) for file in group) + 2 for group in column_groups
    ]

    for index, file in enumerate(files):
        group_index = index % columns
        output += file.ljust(column_widths[group_index])
        if group_index == columns - 1 and index != len(files) - 1:
            output += "\n" + " " * TAB_SIZE * tab_count

    return output


path_stack = []


def path_stack_match(index: int, cur_dir_name: str) -> bool:
    global path_stack
    return len(path_stack) > index and path_stack[index] == cur_dir_name


# generating the current working directory
def current_path() -> str:
    global path_stack
    # show the current using user
    path = f"{responses.terminal_mode_current_using_user}@Moonafly:"
    for folder in path_stack:
        if folder != "~":
            path += "/"
        path += folder
    return path + "$"


def in_interaction() -> bool:
    directory_statuses = [
        game_1A2B.playing_game_1A2B,
        clipboard.checking_clipboard_keyword_override,
        random_vocab_test.random_vocab_testing,
    ]
    return any(directory_statuses) is True


async def get_response_in_terminal_mode(message) -> str:
    username = str(message.author)
    msg = str(message.content).strip()
    user_shortcuts = shortcut.load_user_shortcuts()
    msg = user_shortcuts.get(username, {}).get(msg, msg)

    # for directory
    global path_stack

    if not in_interaction():
        if msg.startswith("help"):
            msg = msg[5:].strip()
            if msg.startswith(HELP_FLAG):
                return command_help.load_help_cmd_info("help")

            return textwrap.dedent(
                f"""
                ```
                ███╗   ███╗ ██████╗  ██████╗ ███╗   ██╗ █████╗ ███████╗██╗  ██╗   ██╗
                ████╗ ████║██╔═══██╗██╔═══██╗████╗  ██║██╔══██╗██╔════╝██║  ╚██╗ ██╔╝
                ██╔████╔██║██║   ██║██║   ██║██╔██╗ ██║███████║█████╗  ██║   ╚████╔╝
                ██║╚██╔╝██║██║   ██║██║   ██║██║╚██╗██║██╔══██║██╔══╝  ██║    ╚██╔╝
                ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝██║ ╚████║██║  ██║██║     ███████╗██║
                ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝

                {responses.Moonafly_version}

                - normal mode
                - terminal mode (current)
                - develop mode

                a star(*) in front of the command means that it requires the highest authority

                 cd [dir]
                 clear
                 cloak {{+-}}h [dir]
                 exit [--save]
                 help
                 jump [folder]
                 ls [-a]
                 pwd
                 tree [-aM]
                {current_path()}
                ```
                """
            )

        elif msg.startswith("cd"):
            msg = msg[3:].strip()
            if msg.startswith(HELP_FLAG):
                return command_help.load_help_cmd_info("cd")

            path = msg

            # blank or ~ should go directly to ~
            if path == "" or path == "~":
                path_stack = ["~"]
                return f"```{current_path()}```"

            # go to the root directory
            if path[0] == "/" and username != responses.author:
                return handle_command_error("cd", "permission")

            exists, temporary_path_stack = check_path_exists("cd", path)

            if not exists:
                return temporary_path_stack

            path_stack = temporary_path_stack
            return f"```{current_path()}```"

        elif msg.startswith("clear"):
            msg = msg[6:].strip()
            if msg.startswith(HELP_FLAG):
                return command_help.load_help_cmd_info("clear")

            await bot.clear_msgs(message, responses.start_using_timestamp)
            return f"```{current_path()}```"

        elif msg.startswith("cloak"):
            msg = msg[6:].strip()
            if msg.startswith(HELP_FLAG):
                return command_help.load_help_cmd_info("cloak")

            pattern = r"^([+-])[h]\s*(.*)$"
            match = re.match(pattern, msg)
            if match:
                operation = match.group(1)
                path = match.group(2)

                exists, temporary_path_stack = check_path_exists("cloak", path)

                if not exists:
                    return temporary_path_stack

                folder_name = temporary_path_stack[-1]
                user_cloak = load_user_cloak()
                user_terminal_mode_cloak = user_cloak[
                    "terminal_mode"
                ].setdefault(username, [])
                if operation == "+":
                    if folder_name not in user_terminal_mode_cloak:
                        user_terminal_mode_cloak.append(folder_name)
                else:
                    if folder_name in user_terminal_mode_cloak:
                        user_terminal_mode_cloak.remove(folder_name)
                write_user_cloak(user_cloak)

                return textwrap.dedent(
                    f"""
                    ```
                    folder '{folder_name}' has been successfully {'un' if operation == '-' else ''}hidden
                    {current_path()}
                    ```
                    """
                )
            else:
                return handle_command_error("cloak", "format")

        elif msg.startswith("jump"):
            msg = msg[5:].strip()
            return jump.jump_to_folder(msg)

        elif msg.startswith("ls"):
            msg = msg[3:].strip()
            if msg.startswith(HELP_FLAG):
                return command_help.load_help_cmd_info("ls")

            current_directory = load_terminal_mode_directory_structure()
            # and move it to the current directory
            for folder in path_stack:
                current_directory = current_directory[folder]

            # sort the folders alphabetically
            files_in_current_directory = sorted(current_directory)
            if (
                username != responses.author
                and "author" in files_in_current_directory
            ):
                files_in_current_directory.remove("author")

            if not msg.startswith("-a") and not msg.startswith("--all"):
                user_cloak = load_user_cloak()
                for folder in user_cloak["terminal_mode"].get(username, []):
                    if folder in files_in_current_directory:
                        files_in_current_directory.remove(folder)

            return textwrap.dedent(
                f"""
                ```
                {get_ls_command_output(files_in_current_directory, 4)}
                {current_path()}
                ```
                """
            )

        # return the full pathname of the current working directory
        elif msg.startswith("pwd"):
            msg = msg[4:].strip()
            if msg.startswith(HELP_FLAG):
                return command_help.load_help_cmd_info("pwd")

            # delete the prefix 'Moonafly:' and the suffix '$'
            path = current_path()[(10 + len(username)) : -1]
            # delete the prefix no matter it is '~' or '/' path_stack still has the data
            path = path[1:]

            if path_stack[0] == "~":
                path = "home/Moonafly" + path

            return textwrap.dedent(
                f"""
                ```
                /{path}
                {current_path()}
                ```
                """
            )

        # show the terminal_mode_directory_structure
        elif msg.startswith("tree"):
            msg = msg[5:].strip()
            if msg.startswith(HELP_FLAG):
                return command_help.load_help_cmd_info("tree")

            if (
                msg.startswith("-M") or msg.startswith("--Moonafly")
            ) and username == responses.author:
                return tree.visualize_structure(load_Moonafly_structure())

            current_structure = load_terminal_mode_directory_structure()
            # and move it to the current directory
            for folder in path_stack:
                current_structure = current_structure[folder]

            if msg.startswith("-a") or msg.startswith("--all"):
                return tree.visualize_structure(current_structure, False)

            return tree.visualize_structure(current_structure)

    # only author can access this part
    if path_stack_match(1, "author"):
        if path_stack_match(2, "approve"):
            return approve.approve_requests(msg)

        elif path_stack_match(2, "remote"):
            if path_stack_match(3, "file"):
                return remote_file.load_remote_file(msg, "author")
            elif path_stack_match(3, "terminal"):
                return remote_terminal.get_remote_terminal_response(msg)

    # commands in certain directory
    if path_stack_match(1, "calendar"):
        return calendar.get_calendar_response(msg)

    elif path_stack_match(1, "clipboard"):
        return clipboard.get_clipboard_response(msg)

    elif path_stack_match(1, "dict"):
        if path_stack_match(2, "en"):
            return dict.get_dict_response(msg, "en")

        elif path_stack_match(2, "en-zh_TW"):
            return dict.get_dict_response(msg, "en-zh_TW")

    elif path_stack_match(1, "game"):
        if path_stack_match(2, "1A2B"):
            return game_1A2B.play_game_1A2B(message)

    elif path_stack_match(1, "hash"):
        return hash.get_hash(msg)

    elif path_stack_match(1, "math"):
        if path_stack_match(2, "calc"):
            return math_calc.get_math_calc_response(msg)

        elif path_stack_match(2, "count"):
            return math_count.get_math_count_response(msg)

        elif path_stack_match(2, "primes"):
            return primes.get_primes_response(msg)

    elif path_stack_match(1, "news"):
        return news.get_news(msg)

    elif path_stack_match(1, "random"):
        if path_stack_match(2, "number"):
            return random_number.get_random_number_response(msg)

        elif path_stack_match(2, "vocab"):
            if path_stack_match(3, "review"):
                return random_vocab_review.get_random_vocab_review(msg)

            elif path_stack_match(3, "test"):
                return random_vocab_test.get_random_vocab_test(msg)

    elif path_stack_match(1, "search"):
        if path_stack_match(2, "github"):
            if path_stack_match(3, "issues"):
                return issues.get_issues(msg)

            return search_github.get_search_github_response(msg)

        elif path_stack_match(2, "online-judge"):
            return search_online_judge.get_online_judge_info(msg)

    elif path_stack_match(1, "shortcut"):
        return shortcut.get_shortcut_response(msg)

    elif path_stack_match(1, "todo"):
        return todo.get_todo_response(msg)

    elif path_stack_match(1, "translate"):
        return translate.get_translated_text(msg)

    elif path_stack_match(1, "weather"):
        return weather.get_weather_response(msg)

    else:
        return command_not_found(msg)
