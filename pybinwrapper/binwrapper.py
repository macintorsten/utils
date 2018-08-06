#!/usr/bin/env python

# Inspired by 'In-Memory-Only ELF Execution (Without tmpfs)'
# https://magisterquis.github.io/2018/03/31/in-memory-only-elf-execution.html

import base64
import ctypes
import os
import sys
import zlib
from distutils.spawn import find_executable
MEMFD_CREATE = 319
MFD_CLOEXEC = 1

def run(elf, argv):

    # Get syscall function
    libc = ctypes.CDLL(None)
    syscall = libc.syscall

    # Create anon fd
    anon_fd = syscall(MEMFD_CREATE, "", MFD_CLOEXEC)
    anon_path = "/proc/self/fd/%d" % anon_fd

    # Write elf binary to anon_fd and execute
    os.write(anon_fd, elf)
    os.execv(anon_path, argv)

def run_compressed(elf_gz_b64, argv):

    # Decompress - zlib.MAX_WBITS|16 needed for data compressed with gzip command
    elf = zlib.decompress(base64.b64decode(elf_gz_b64))
    run(elf, argv)

def main(elf_gz_b64, argv):

    # Create python binary wrapper - regenerate main()
    if len(sys.argv) > 1:
        command = sys.argv[1]
        command_argv = sys.argv[1:]
        binary_path = find_executable(command) or command

        # Read binary and create b64 gzip
        bin_gz_b64 = ""
        with open(binary_path, 'r') as binary:
            bin_gz = zlib.compress(binary.read())
            bin_gz_b64 = base64.b64encode(bin_gz)

        # Read the source code of this program
        self_src = ""
        with open(__file__) as pybin:
            self_src = pybin.read()

        # Overwrite this program with modified elf_gz_b64 call to main()
        self_serc = self_src.strip()
        self_src = self_src.rsplit("\n",2)[0]
        self_src += "\nmain('%s', %s)" % (bin_gz_b64, command_argv)

        if sys.stdout.isatty():
            print("Updating %s with embedded command: %s" % (__file__, " ".join(command_argv)))
            with open(__file__, 'w') as pybin:
                pybin.write(self_src)
        else:
            sys.stderr.write("Writing python code with embedded command %s to stdout\n" % argv)
            print(self_src)

    # Run embedded binary with args
    else:
        run_compressed(elf_gz_b64, argv)

main('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', sys.argv)
