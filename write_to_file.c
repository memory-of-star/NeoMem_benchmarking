#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <value> <file_path>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    const char *file_path = argv[2];
    const char *value = argv[1];

    FILE *fp = fopen(file_path, "w");
    if (fp == NULL) {
        perror("fopen");
        exit(EXIT_FAILURE);
    }

    fprintf(fp, "%s\n", value);
    
    fclose(fp);

    printf("Successfully wrote '%s' to %s\n", value, file_path);
    return 0;
}