# Ghost Task BOF Makefile
# Compatible with Cobalt Strike and OST's C2 (OC2)
# Creates scheduled tasks via registry manipulation (ghost technique)

# Compiler settings
CC_x64 := x86_64-w64-mingw32-gcc
CC_x86 := i686-w64-mingw32-gcc
STRIP_x64 := x86_64-w64-mingw32-strip
STRIP_x86 := i686-w64-mingw32-strip

# Compiler flags
CFLAGS := -c -Os
CFLAGS += -masm=intel
CFLAGS += -Wall -Wno-format
CFLAGS += -DBOF

# Include paths
INCLUDES := -I.

# Source files
ENTRY_SRC := entry.c

# Output files
BOF_NAME := ghost_task
OUTPUT_x64 := $(BOF_NAME).x64.o
OUTPUT_x86 := $(BOF_NAME).x86.o

# Default target - build both architectures
all: x64 x86

# 64-bit target
x64: $(OUTPUT_x64)

$(OUTPUT_x64): $(ENTRY_SRC) ghost_task.c ghost_task.h beacon.h bofdefs.h base.c
	@echo "[*] Compiling Ghost Task BOF (x64)..."
	$(CC_x64) $(CFLAGS) $(INCLUDES) $(ENTRY_SRC) -o $(OUTPUT_x64)
	$(STRIP_x64) --strip-unneeded $(OUTPUT_x64)
	@echo "[+] Successfully compiled: $(OUTPUT_x64)"

# 32-bit target
x86: $(OUTPUT_x86)

$(OUTPUT_x86): $(ENTRY_SRC) ghost_task.c ghost_task.h beacon.h bofdefs.h base.c
	@echo "[*] Compiling Ghost Task BOF (x86)..."
	$(CC_x86) $(CFLAGS) $(INCLUDES) $(ENTRY_SRC) -o $(OUTPUT_x86)
	$(STRIP_x86) --strip-unneeded $(OUTPUT_x86)
	@echo "[+] Successfully compiled: $(OUTPUT_x86)"
	@echo ""
	@echo "[*] To use with Cobalt Strike:"
	@echo "    1. Load the BOF using inline-execute or beacon_inline_execute"
	@echo "    2. Example: inline-execute $(OUTPUT_x64) localhost add MyTask C:\\\\calc.exe \"\" SYSTEM daily 14:30"
	@echo ""
	@echo "[*] To use with OC2:"
	@echo "    1. Copy ghost_task_bof_s1.py and *.o files to stage1c2server/shared/bofs/"
	@echo "    2. Restart OC2 server: python3 manage.py restart"
	@echo "    3. Use command: ghost_task localhost add MyTask C:\\\\calc.exe \"\" SYSTEM daily 14:30"
	@echo ""
	@echo "[!] IMPORTANT: After adding/deleting tasks, restart Schedule service:"
	@echo "    sc stop schedule && sc start schedule"

# Clean target
clean:
	@echo "[*] Cleaning build artifacts..."
	rm -f $(OUTPUT_x64) $(OUTPUT_x86)
	@echo "[+] Clean complete"

# Help target
help:
	@echo "Ghost Task BOF - Build Instructions"
	@echo ""
	@echo "Targets:"
	@echo "  make          - Build both x86 and x64 BOFs (default)"
	@echo "  make x64      - Build x64 BOF only"
	@echo "  make x86      - Build x86 BOF only"
	@echo "  make clean    - Remove compiled files"
	@echo "  make help     - Show this help message"
	@echo ""
	@echo "Requirements:"
	@echo "  - mingw-w64 cross-compiler (x86_64-w64-mingw32-gcc and i686-w64-mingw32-gcc)"
	@echo ""
	@echo "Installation:"
	@echo "  Ubuntu/Debian: sudo apt install mingw-w64"
	@echo "  Kali Linux:    sudo apt install mingw-w64"
	@echo "  MacOS:         brew install mingw-w64"
	@echo ""
	@echo "About Ghost Task:"
	@echo "  Ghost Task creates scheduled tasks by directly manipulating Windows registry keys,"
	@echo "  bypassing standard Task Scheduler APIs. This technique requires SYSTEM privileges"
	@echo "  for local operations and the Schedule service must be restarted for changes to take effect."

.PHONY: all x64 x86 clean help
