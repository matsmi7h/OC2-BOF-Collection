from typing import List, Tuple

from outflank_stage1.task.base_bof_task import BaseBOFTask
from outflank_stage1.implant.enums import ImplantArch, ImplantPrivilege
from outflank_stage1.task.enums import BOFArgumentEncoding

class GhostTaskBOF(BaseBOFTask):
    def __init__(self):
        super().__init__(
            "ghost_task",
            base_binary_name = "ghost_task",
            min_privilege=ImplantPrivilege.MEDIUM,
            supported_architectures=[ImplantArch.INTEL_X64, ImplantArch.INTEL_X86]
        )

        self.parser.add_argument(
            "computername",
            help="Target computer name (use 'localhost' for local system)")

        self.parser.add_argument(
            "operation",
            choices=['add', 'delete'],
            help="Operation to perform (add or delete)")

        self.parser.add_argument(
            "taskname",
            help="Name of the scheduled task")

        self.parser.add_argument(
            "program",
            nargs='?',
            default='',
            help="Program to execute (required for 'add' operation)")

        self.parser.add_argument(
            "argument",
            nargs='?',
            default='',
            help="Arguments for the program (required for 'add' operation)")

        self.parser.add_argument(
            "username",
            nargs='?',
            default='',
            help="User account to run task under (required for 'add' operation)")

        self.parser.add_argument(
            "scheduletype",
            nargs='?',
            choices=['second', 'daily', 'weekly', 'logon'],
            help="Schedule type: second, daily, weekly, or logon (required for 'add' operation)")

        self.parser.add_argument(
            "time",
            nargs='?',
            default='',
            help="Execution time - seconds for 'second' type, HH:MM for 'daily'/'weekly' (required for 'add' operation with time-based schedules)")

        self.parser.add_argument(
            "days",
            nargs='?',
            default='',
            help="Days for weekly execution (e.g., 'monday,friday') (required for 'weekly' schedule type)")

        self.parser.description = "Create or delete scheduled tasks by directly modifying registry (ghost technique)"
        self.parser.epilog = (
            "Synopsis: ghost_task [computername] [operation] [taskname] [program] [argument] [username] [scheduletype] [time] [days]\n\n"
            "Operations:\n"
            "    add     - Create a scheduled task via registry modification\n"
            "    delete  - Delete a scheduled task via registry modification\n\n"
            "Schedule Types:\n"
            "    second  - Execute task every N seconds (time = number of seconds)\n"
            "    daily   - Execute task daily at specified time (time = HH:MM)\n"
            "    weekly  - Execute task weekly on specified days (time = HH:MM, days = comma-separated list)\n"
            "    logon   - Execute task at user logon\n\n"
            "Requirements:\n"
            "    - SYSTEM privileges (for local operations)\n"
            "    - Task Scheduler service must be restarted for changes to take effect\n"
            "    - For remote operations, ensure network access and appropriate permissions\n\n"
            "Examples:\n"
            "    ghost_task localhost add MyTask C:\\\\Windows\\\\System32\\\\calc.exe \"\" SYSTEM daily 14:30\n"
            "    ghost_task localhost add BackupTask C:\\\\backup.bat \"\" Administrator weekly 02:00 monday,friday\n"
            "    ghost_task localhost add BeaconTask C:\\\\beacon.exe \"\" SYSTEM logon\n"
            "    ghost_task localhost add FrequentTask C:\\\\script.exe \"\" SYSTEM second 60\n"
            "    ghost_task localhost delete MyTask\n"
            "    ghost_task remote-host add RemoteTask C:\\\\task.exe \"\" SYSTEM daily 12:00\n\n"
            "Note: After adding or deleting a task, restart the Schedule service:\n"
            "      sc stop schedule && sc start schedule"
        )

    def _encode_arguments_bof(self, arguments: List[str]) -> List[Tuple[BOFArgumentEncoding, str]]:
        parser_arguments = self.parser.parse_args(arguments)

        # Validate operation-specific arguments
        if parser_arguments.operation == 'add':
            if not parser_arguments.program:
                raise ValueError("Program path is required for 'add' operation")
            if not parser_arguments.username:
                raise ValueError("Username is required for 'add' operation")
            if not parser_arguments.scheduletype:
                raise ValueError("Schedule type is required for 'add' operation")

            # Validate schedule type-specific arguments
            if parser_arguments.scheduletype in ['second', 'daily', 'weekly']:
                if not parser_arguments.time:
                    raise ValueError(f"Time is required for '{parser_arguments.scheduletype}' schedule type")

            if parser_arguments.scheduletype == 'weekly':
                if not parser_arguments.days:
                    raise ValueError("Days are required for 'weekly' schedule type")

        # Build argument count - matches BOF's expectation
        arg_list = [
            parser_arguments.computername,
            parser_arguments.operation,
        ]

        if parser_arguments.operation == 'add':
            arg_list.extend([
                parser_arguments.taskname,
                parser_arguments.program,
                parser_arguments.argument if parser_arguments.argument else '',
                parser_arguments.username,
                parser_arguments.scheduletype,
            ])

            # Add time and days for appropriate schedule types
            if parser_arguments.scheduletype in ['second', 'daily']:
                arg_list.append(parser_arguments.time)
            elif parser_arguments.scheduletype == 'weekly':
                arg_list.append(parser_arguments.time)
                arg_list.append(parser_arguments.days if parser_arguments.days else '')
        else:  # delete operation
            arg_list.append(parser_arguments.taskname)

        # Encode as BOF arguments
        # Note: arglen in the BOF includes positions, so we need to account for
        # the fact that the BOF checks arglen > 8 for time-based schedules
        # For compatibility with the original BOF code, add +1 to arglen
        bof_args = [(BOFArgumentEncoding.INT, str(len(arg_list) + 1))]
        for arg in arg_list:
            bof_args.append((BOFArgumentEncoding.STR, arg))

        return bof_args
