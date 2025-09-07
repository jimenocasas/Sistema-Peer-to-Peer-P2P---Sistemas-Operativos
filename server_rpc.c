#include <stdio.h>
#include <string.h>
#include "claves_rpc.h"

int *log_operation_1_svc(struct log_entry *entry, struct svc_req *req) {
    static int result;
    FILE *fp = fopen("logs.txt", "a");
    
    if (fp == NULL) {
        result = -1;
        return &result;
    }

    // Imprimir según la operación
    if (strcmp(entry->operacion, "PUBLISH") == 0 || strcmp(entry->operacion, "DELETE") == 0) {
        fprintf(fp, "[%s] %s -> %s %s\n", entry->fecha, entry->usuario, entry->operacion, entry->param1);
    } else {
        fprintf(fp, "[%s] %s -> %s\n", entry->fecha, entry->usuario, entry->operacion);
    }

    fflush(fp);
    fclose(fp);
    result = 0;
    return &result;
}
