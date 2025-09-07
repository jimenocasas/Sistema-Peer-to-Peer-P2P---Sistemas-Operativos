#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "claves_rpc.h"

// Función para registrar una operación en el servidor RPC
int registrar_log_rpc(const char *usuario, const char *operacion, const char *param1, const char *fecha) {
    CLIENT *clnt;
    int *result;

    // Conexión al servidor RPC en localhost
    clnt = clnt_create("localhost", CLAVESRPC_PROG, CLAVESRPC_VERS, "tcp");
    if (clnt == NULL) {
        clnt_pcreateerror("Error al crear cliente RPC");
        return -1;
    }

    // Crear la entrada de log
    struct log_entry entrada;
    entrada.usuario = strdup(usuario);
    entrada.operacion = strdup(operacion);
    entrada.fecha = strdup(fecha);

    // Si param1 es NULL, se pasa como cadena vacía
    entrada.param1 = (param1 == NULL) ? strdup("\0") : strdup(param1);

    // Llamar a la función remota
    result = log_operation_1(&entrada, clnt);

    if (result == NULL) {
        clnt_perror(clnt, "Error al invocar log_operation");
        clnt_destroy(clnt);
        return -1;
    }

    free(entrada.usuario);
    free(entrada.operacion);
    free(entrada.fecha);
    clnt_destroy(clnt);
    return (result != NULL) ? *result : -1;
}
