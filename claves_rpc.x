/*
 * claves_rpc.x
 * Interfaz RPC para registrar operaciones <usuario, operación, fecha>
 */

struct log_entry {
    string usuario<256>;
    string operacion<256>;
    string param1<>;
    string fecha<256>;
};

program CLAVESRPC_PROG {
    version CLAVESRPC_VERS {
        int log_operation(log_entry) = 1;
    } = 1;
} = 0x31234567;
