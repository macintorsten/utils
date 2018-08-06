#include <stdio.h>

int main(int argc, char* argv[]) {
    printf("Usage:\n");
    printf("$ %s                            # Run embedded command\n", argv[0]);
    printf("$ %s <command> [args]           # Embed new command in this file\n", argv[0]);
    printf("$ %s <command> [args] > new.py  # Create new file with embedded command\n", argv[0]);
    printf("$ python < %s                   # Run from stdin\n", argv[0]);
	return 0;
}
