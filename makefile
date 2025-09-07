# Makefile para el sistema P2P con soporte RPC (Parte 3)

# Compilador
CC = gcc
CFLAGS = -Wall -Wextra -pthread
INCLUDES = -I/usr/include/tirpc
RPCFLAGS = -Wno-unused-parameter -Wno-unused-variable -Wno-cast-function-type

# Ejecutables
SERVER_EXEC = server
RPC_SERVER_EXEC = servidor_rpc

# Archivos fuente
SERVER_SRC = server.c proxy_rpc.c
RPC_SERVER_SRC = server_rpc.c

# Archivos generados por rpcgen
RPCGEN_SRCS = claves_rpc.h claves_rpc_clnt.c claves_rpc_svc.c claves_rpc_xdr.c

# Regla principal
all: $(SERVER_EXEC) $(RPC_SERVER_EXEC)

# Generación automática de archivos RPC
$(RPCGEN_SRCS): claves_rpc.x
	rpcgen -C claves_rpc.x

# Compilación del servidor principal (cliente RPC)
$(SERVER_EXEC): $(SERVER_SRC) claves_rpc_clnt.c claves_rpc_xdr.c
	$(CC) $(CFLAGS) $(RPCFLAGS) $(INCLUDES) -o $(SERVER_EXEC) $(SERVER_SRC) claves_rpc_clnt.c claves_rpc_xdr.c -ltirpc

# Compilación del servidor RPC (registro de logs)
$(RPC_SERVER_EXEC): $(RPC_SERVER_SRC) claves_rpc_svc.c claves_rpc_xdr.c
	$(CC) $(CFLAGS) $(RPCFLAGS) $(INCLUDES) -o $(RPC_SERVER_EXEC) $(RPC_SERVER_SRC) claves_rpc_svc.c claves_rpc_xdr.c -ltirpc

# Limpiar todos los binarios y archivos generados
clean:
	rm -f $(SERVER_EXEC) $(RPC_SERVER_EXEC) $(RPCGEN_SRCS)

.PHONY: all clean
