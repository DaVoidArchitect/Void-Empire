#include <stdio.h>
#include <stdlib.h>
#include <string.h>

double safe_div(double a, double b) {
    if (b == 0.0) return 0.0;
    return a / b;
}

void print_escaped(FILE* f, const char* s) {
    for (int i = 0; s[i] != '\0'; i++) {
        if (s[i] == '\\') fprintf(f, "\\\\");
        else if (s[i] == '"') fprintf(f, "\\\"");
        else if (s[i] == '\n') fprintf(f, "\\n");
        else fputc(s[i], f);
    }
}
const char* C_PART1 = "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\ndouble safe_div(double a, double b) {\n    if (b == 0.0) return 0.0;\n    return a / b;\n}\n\nvoid print_escaped(FILE* f, const char* s) {\n    for (int i = 0; s[i] != '\\0'; i++) {\n        if (s[i] == '\\\\') fprintf(f, \"\\\\\\\\\");\n        else if (s[i] == '\"') fprintf(f, \"\\\\\\\"\");\n        else if (s[i] == '\\n') fprintf(f, \"\\\\n\");\n        else fputc(s[i], f);\n    }\n}\n";
const char* C_PART2 = "struct MeshContext {\n    double mass;\n    double energy;\n    double entropy;\n    double cycle;\n};\n\nstruct MeshContext mesh = {1e12, 1e12, 1e12, 1e12};\n\n// Runtime context guard variables\ndouble enabled = 1.0;\ndouble is_authorized = 0.0;\ndouble is_inter_subnet = 0.0;\ndouble is_valid_sig = 0.0;\ndouble limit = 10000.0;\ndouble priority = 0.0;\ndouble replayed = 0.0;\ndouble request_size = 0.0;\n\nstruct TransitionResult {\n    const char* status;\n    const char* from;\n    const char* to;\n    const char* detail;\n};\n\nconst char* logoscompiler_state = \"Initialize\";\n\nstruct TransitionResult process_event(const char* intent, const char* event) {\n    struct TransitionResult res;\n    res.status = \"no_match\";\n    res.from = \"\";\n    res.to = \"\";\n    res.detail = \"\";\n\n    struct MeshContext backup = mesh; // Transaction register backup\n\n    if (strcmp(intent, \"LogosCompiler\") == 0) {\n        res.from = logoscompiler_state;\n        res.to = logoscompiler_state;\n\n        if (strcmp(logoscompiler_state, \"Initialize\") == 0) {\n            if (strcmp(event, \"scan_tokens\") == 0) {\n                if (1) {\n                    if (mesh.energy < 19112.4) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient energy (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.energy -= 19112.4;\n                    if (mesh.cycle < 106.18) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient cycle (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.cycle -= 106.18;\n                    logoscompiler_state = \"Lexing\";\n                    res.to = \"Lexing\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n        }\n        if (strcmp(logoscompiler_state, \"Lexing\") == 0) {\n            if (strcmp(event, \"tokens_ready\") == 0) {\n                if (1) {\n                    if (mesh.energy < 38224.8) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient energy (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.energy -= 38224.8;\n                    if (mesh.cycle < 212.36) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient cycle (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.cycle -= 212.36;\n                    logoscompiler_state = \"Parsing\";\n                    res.to = \"Parsing\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n            if (strcmp(event, \"syntax_error\") == 0) {\n                if (1) {\n                    logoscompiler_state = \"Error\";\n                    res.to = \"Error\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n        }\n        if (strcmp(logoscompiler_state, \"Parsing\") == 0) {\n            if (strcmp(event, \"ast_built\") == 0) {\n                if (1) {\n                    if (mesh.energy < 95562.0) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient energy (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.energy -= 95562.0;\n                    if (mesh.cycle < 530.9000000000001) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient cycle (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.cycle -= 530.9000000000001;\n                    logoscompiler_state = \"SemanticVerification\";\n                    res.to = \"SemanticVerification\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n            if (strcmp(event, \"syntax_error\") == 0) {\n                if (1) {\n                    logoscompiler_state = \"Error\";\n                    res.to = \"Error\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n        }\n        if (strcmp(logoscompiler_state, \"SemanticVerification\") == 0) {\n            if (strcmp(event, \"thermo_verified\") == 0) {\n                if (1) {\n                    if (mesh.energy < 114674.40000000001) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient energy (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.energy -= 114674.40000000001;\n                    if (mesh.cycle < 318.54) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient cycle (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.cycle -= 318.54;\n                    logoscompiler_state = \"BytecodeLowering\";\n                    res.to = \"BytecodeLowering\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n            if (strcmp(event, \"constraint_violation\") == 0) {\n                if (1) {\n                    logoscompiler_state = \"Error\";\n                    res.to = \"Error\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n        }\n        if (strcmp(logoscompiler_state, \"BytecodeLowering\") == 0) {\n            if (strcmp(event, \"bytecode_ready\") == 0) {\n                if (1) {\n                    if (mesh.energy < 57337.200000000004) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient energy (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.energy -= 57337.200000000004;\n                    if (mesh.cycle < 212.36) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient cycle (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.cycle -= 212.36;\n                    logoscompiler_state = \"EmitBinary\";\n                    res.to = \"EmitBinary\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n        }\n        if (strcmp(logoscompiler_state, \"EmitBinary\") == 0) {\n            if (strcmp(event, \"write_success\") == 0) {\n                if (1) {\n                    if (mesh.energy < 7644.960000000001) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient energy (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.energy -= 7644.960000000001;\n                    if (mesh.cycle < 53.09) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient cycle (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.cycle -= 53.09;\n                    logoscompiler_state = \"Finished\";\n                    res.to = \"Finished\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n            if (strcmp(event, \"write_failure\") == 0) {\n                if (1) {\n                    logoscompiler_state = \"Error\";\n                    res.to = \"Error\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n        }\n        if (strcmp(logoscompiler_state, \"Finished\") == 0) {\n            if (strcmp(event, \"reset\") == 0) {\n                if (1) {\n                    logoscompiler_state = \"Initialize\";\n                    res.to = \"Initialize\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n        }\n        if (strcmp(logoscompiler_state, \"Error\") == 0) {\n            if (strcmp(event, \"fault_clear\") == 0) {\n                if (1) {\n                    if (mesh.energy < 191124.0) {\n                        res.status = \"blocked\";\n                        res.detail = \"Insufficient energy (with 6.18% fee). Transition FROZEN.\";\n                        mesh = backup; // Rollback registers\n                        return res;\n                    }\n                    mesh.energy -= 191124.0;\n                    logoscompiler_state = \"Initialize\";\n                    res.to = \"Initialize\";\n                    res.status = \"transitioned\";\n                    res.detail = \"OK\";\n                    return res;\n                }\n            }\n        }\n    }\n    return res;\n}\n\nvoid parse_mesh(const char* filepath) {\n    FILE* f = fopen(filepath, \"r\");\n    if (!f) return;\n    char buf[4096];\n    size_t len = fread(buf, 1, sizeof(buf) - 1, f);\n    buf[len] = '\\0';\n    fclose(f);\n\n    char* p;\n    if ((p = strstr(buf, \"\\\"mass\\\"\"))) {\n        sscanf(p + 6, \"%*[: \\t]%lf\", &mesh.mass);\n    }\n    if ((p = strstr(buf, \"\\\"energy\\\"\"))) {\n        sscanf(p + 8, \"%*[: \\t]%lf\", &mesh.energy);\n    }\n    if ((p = strstr(buf, \"\\\"entropy\\\"\"))) {\n        sscanf(p + 9, \"%*[: \\t]%lf\", &mesh.entropy);\n    }\n    if ((p = strstr(buf, \"\\\"cycle\\\"\"))) {\n        sscanf(p + 7, \"%*[: \\t]%lf\", &mesh.cycle);\n    }\n}\n\nvoid parse_context(const char* filepath) {\n    FILE* f = fopen(filepath, \"r\");\n    if (!f) return;\n    char buf[4096];\n    size_t len = fread(buf, 1, sizeof(buf) - 1, f);\n    buf[len] = '\\0';\n    fclose(f);\n\n    char* p;\n    if ((p = strstr(buf, \"\\\"enabled\\\"\"))) {\n        sscanf(p + 9, \"%*[: \\t]%lf\", &enabled);\n    }\n    if ((p = strstr(buf, \"\\\"is_authorized\\\"\"))) {\n        sscanf(p + 15, \"%*[: \\t]%lf\", &is_authorized);\n    }\n    if ((p = strstr(buf, \"\\\"is_inter_subnet\\\"\"))) {\n        sscanf(p + 17, \"%*[: \\t]%lf\", &is_inter_subnet);\n    }\n    if ((p = strstr(buf, \"\\\"is_valid_sig\\\"\"))) {\n        sscanf(p + 14, \"%*[: \\t]%lf\", &is_valid_sig);\n    }\n    if ((p = strstr(buf, \"\\\"limit\\\"\"))) {\n        sscanf(p + 7, \"%*[: \\t]%lf\", &limit);\n    }\n    if ((p = strstr(buf, \"\\\"priority\\\"\"))) {\n        sscanf(p + 10, \"%*[: \\t]%lf\", &priority);\n    }\n    if ((p = strstr(buf, \"\\\"replayed\\\"\"))) {\n        sscanf(p + 10, \"%*[: \\t]%lf\", &replayed);\n    }\n    if ((p = strstr(buf, \"\\\"request_size\\\"\"))) {\n        sscanf(p + 14, \"%*[: \\t]%lf\", &request_size);\n    }\n    if ((p = strstr(buf, \"\\\"logoscompiler_state\\\"\"))) {\n        static char state_buf_logoscompiler[128];\n        if (sscanf(p + 21, \"%*[: \\t\\\"]%127[^\\\"]\", state_buf_logoscompiler) == 1) {\n            logoscompiler_state = state_buf_logoscompiler;\n        }\n    }\n}\n\nvoid run_events(const char* filepath) {\n    FILE* f = fopen(filepath, \"r\");\n    if (!f) return;\n    char buf[65536];\n    size_t len = fread(buf, 1, sizeof(buf) - 1, f);\n    buf[len] = '\\0';\n    fclose(f);\n\n    int event_index = 0;\n    char* obj_start = strchr(buf, '{');\n    while (obj_start) {\n        char* obj_end = strchr(obj_start, '}');\n        if (!obj_end) break;\n        *obj_end = '\\0';\n\n        char intent[128] = {0};\n        char event[128] = {0};\n\n        char* p;\n        if ((p = strstr(obj_start, \"\\\"intent\\\"\"))) {\n            sscanf(p + 8, \"%*[: \\t\\\"]%127[^\\\"]\", intent);\n        }\n        if ((p = strstr(obj_start, \"\\\"event\\\"\"))) {\n            sscanf(p + 7, \"%*[: \\t\\\"]%127[^\\\"]\", event);\n        }\n        if ((p = strstr(obj_start, \"\\\"enabled\\\"\"))) {\n            sscanf(p + 9, \"%*[: \\t]%lf\", &enabled);\n        }\n        if ((p = strstr(obj_start, \"\\\"is_authorized\\\"\"))) {\n            sscanf(p + 15, \"%*[: \\t]%lf\", &is_authorized);\n        }\n        if ((p = strstr(obj_start, \"\\\"is_inter_subnet\\\"\"))) {\n            sscanf(p + 17, \"%*[: \\t]%lf\", &is_inter_subnet);\n        }\n        if ((p = strstr(obj_start, \"\\\"is_valid_sig\\\"\"))) {\n            sscanf(p + 14, \"%*[: \\t]%lf\", &is_valid_sig);\n        }\n        if ((p = strstr(obj_start, \"\\\"limit\\\"\"))) {\n            sscanf(p + 7, \"%*[: \\t]%lf\", &limit);\n        }\n        if ((p = strstr(obj_start, \"\\\"priority\\\"\"))) {\n            sscanf(p + 10, \"%*[: \\t]%lf\", &priority);\n        }\n        if ((p = strstr(obj_start, \"\\\"replayed\\\"\"))) {\n            sscanf(p + 10, \"%*[: \\t]%lf\", &replayed);\n        }\n        if ((p = strstr(obj_start, \"\\\"request_size\\\"\"))) {\n            sscanf(p + 14, \"%*[: \\t]%lf\", &request_size);\n        }\n\n        struct TransitionResult res = process_event(intent, event);\n        char icon = '?';\n        if (strcmp(res.status, \"transitioned\") == 0) icon = '+';\n        else if (strcmp(res.status, \"blocked\") == 0) icon = '-';\n\n        printf(\"[EVENT %d] %c %s --(%s)--> %s [%s]\\n\", event_index, icon, res.from, event, res.to, res.status);\n        if (strcmp(res.status, \"transitioned\") != 0) {\n            printf(\"          Detail: %s\\n\", res.detail);\n        }\n\n        event_index++;\n        obj_start = strchr(obj_end + 1, '{');\n    }\n\n    printf(\"\\n[LOGOS VM] Execution complete.\\n\");\n    printf(\"[LOGOS VM] Final mesh:\\n\");\n    printf(\"  mass: %.4f\\n\", mesh.mass);\n    printf(\"  energy: %.4f\\n\", mesh.energy);\n    printf(\"  entropy: %.4f\\n\", mesh.entropy);\n    printf(\"  cycle: %.4f\\n\", mesh.cycle);\n}\n\nint main(int argc, char** argv) {\n    if (argc < 2) {\n        printf(\"Usage: logos_app <events.json> [-m mesh.json] [-c context.json] [-o output_file]\\n\");\n        return 0;\n    }\n\n    const char* events_path = argv[1];\n    const char* output_path = NULL;\n    for (int i = 2; i < argc; i++) {\n        if (strcmp(argv[i], \"-m\") == 0 && i + 1 < argc) {\n            parse_mesh(argv[i+1]);\n            i++;\n        } else if (strcmp(argv[i], \"-c\") == 0 && i + 1 < argc) {\n            parse_context(argv[i+1]);\n            i++;\n        } else if (strcmp(argv[i], \"-o\") == 0 && i + 1 < argc) {\n            output_path = argv[i+1];\n            i++;\n        }\n    }\n\n    run_events(events_path);\n\n    if (output_path != NULL) {\n        FILE* out_f = fopen(output_path, \"w\");\n        if (out_f) {\n            fprintf(out_f, \"%s\", C_PART1);\n            fprintf(out_f, \"const char* C_PART1 = \\\"\");\n            print_escaped(out_f, C_PART1);\n            fprintf(out_f, \"\\\";\\nconst char* C_PART2 = \\\"\");\n            print_escaped(out_f, C_PART2);\n            fprintf(out_f, \"\\\";\\n\");\n            fprintf(out_f, \"%s\", C_PART2);\n            fclose(out_f);\n        }\n    }\n    return 0;\n}";
struct MeshContext {
    double mass;
    double energy;
    double entropy;
    double cycle;
};

struct MeshContext mesh = {1e12, 1e12, 1e12, 1e12};

// Runtime context guard variables
double enabled = 1.0;
double is_authorized = 0.0;
double is_inter_subnet = 0.0;
double is_valid_sig = 0.0;
double limit = 10000.0;
double priority = 0.0;
double replayed = 0.0;
double request_size = 0.0;

struct TransitionResult {
    const char* status;
    const char* from;
    const char* to;
    const char* detail;
};

const char* logoscompiler_state = "Initialize";

struct TransitionResult process_event(const char* intent, const char* event) {
    struct TransitionResult res;
    res.status = "no_match";
    res.from = "";
    res.to = "";
    res.detail = "";

    struct MeshContext backup = mesh; // Transaction register backup

    if (strcmp(intent, "LogosCompiler") == 0) {
        res.from = logoscompiler_state;
        res.to = logoscompiler_state;

        if (strcmp(logoscompiler_state, "Initialize") == 0) {
            if (strcmp(event, "scan_tokens") == 0) {
                if (1) {
                    if (mesh.energy < 19112.4) {
                        res.status = "blocked";
                        res.detail = "Insufficient energy (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.energy -= 19112.4;
                    if (mesh.cycle < 106.18) {
                        res.status = "blocked";
                        res.detail = "Insufficient cycle (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.cycle -= 106.18;
                    logoscompiler_state = "Lexing";
                    res.to = "Lexing";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
        }
        if (strcmp(logoscompiler_state, "Lexing") == 0) {
            if (strcmp(event, "tokens_ready") == 0) {
                if (1) {
                    if (mesh.energy < 38224.8) {
                        res.status = "blocked";
                        res.detail = "Insufficient energy (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.energy -= 38224.8;
                    if (mesh.cycle < 212.36) {
                        res.status = "blocked";
                        res.detail = "Insufficient cycle (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.cycle -= 212.36;
                    logoscompiler_state = "Parsing";
                    res.to = "Parsing";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
            if (strcmp(event, "syntax_error") == 0) {
                if (1) {
                    logoscompiler_state = "Error";
                    res.to = "Error";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
        }
        if (strcmp(logoscompiler_state, "Parsing") == 0) {
            if (strcmp(event, "ast_built") == 0) {
                if (1) {
                    if (mesh.energy < 95562.0) {
                        res.status = "blocked";
                        res.detail = "Insufficient energy (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.energy -= 95562.0;
                    if (mesh.cycle < 530.9000000000001) {
                        res.status = "blocked";
                        res.detail = "Insufficient cycle (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.cycle -= 530.9000000000001;
                    logoscompiler_state = "SemanticVerification";
                    res.to = "SemanticVerification";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
            if (strcmp(event, "syntax_error") == 0) {
                if (1) {
                    logoscompiler_state = "Error";
                    res.to = "Error";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
        }
        if (strcmp(logoscompiler_state, "SemanticVerification") == 0) {
            if (strcmp(event, "thermo_verified") == 0) {
                if (1) {
                    if (mesh.energy < 114674.40000000001) {
                        res.status = "blocked";
                        res.detail = "Insufficient energy (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.energy -= 114674.40000000001;
                    if (mesh.cycle < 318.54) {
                        res.status = "blocked";
                        res.detail = "Insufficient cycle (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.cycle -= 318.54;
                    logoscompiler_state = "BytecodeLowering";
                    res.to = "BytecodeLowering";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
            if (strcmp(event, "constraint_violation") == 0) {
                if (1) {
                    logoscompiler_state = "Error";
                    res.to = "Error";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
        }
        if (strcmp(logoscompiler_state, "BytecodeLowering") == 0) {
            if (strcmp(event, "bytecode_ready") == 0) {
                if (1) {
                    if (mesh.energy < 57337.200000000004) {
                        res.status = "blocked";
                        res.detail = "Insufficient energy (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.energy -= 57337.200000000004;
                    if (mesh.cycle < 212.36) {
                        res.status = "blocked";
                        res.detail = "Insufficient cycle (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.cycle -= 212.36;
                    logoscompiler_state = "EmitBinary";
                    res.to = "EmitBinary";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
        }
        if (strcmp(logoscompiler_state, "EmitBinary") == 0) {
            if (strcmp(event, "write_success") == 0) {
                if (1) {
                    if (mesh.energy < 7644.960000000001) {
                        res.status = "blocked";
                        res.detail = "Insufficient energy (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.energy -= 7644.960000000001;
                    if (mesh.cycle < 53.09) {
                        res.status = "blocked";
                        res.detail = "Insufficient cycle (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.cycle -= 53.09;
                    logoscompiler_state = "Finished";
                    res.to = "Finished";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
            if (strcmp(event, "write_failure") == 0) {
                if (1) {
                    logoscompiler_state = "Error";
                    res.to = "Error";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
        }
        if (strcmp(logoscompiler_state, "Finished") == 0) {
            if (strcmp(event, "reset") == 0) {
                if (1) {
                    logoscompiler_state = "Initialize";
                    res.to = "Initialize";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
        }
        if (strcmp(logoscompiler_state, "Error") == 0) {
            if (strcmp(event, "fault_clear") == 0) {
                if (1) {
                    if (mesh.energy < 191124.0) {
                        res.status = "blocked";
                        res.detail = "Insufficient energy (with 6.18% fee). Transition FROZEN.";
                        mesh = backup; // Rollback registers
                        return res;
                    }
                    mesh.energy -= 191124.0;
                    logoscompiler_state = "Initialize";
                    res.to = "Initialize";
                    res.status = "transitioned";
                    res.detail = "OK";
                    return res;
                }
            }
        }
    }
    return res;
}

void parse_mesh(const char* filepath) {
    FILE* f = fopen(filepath, "r");
    if (!f) return;
    char buf[4096];
    size_t len = fread(buf, 1, sizeof(buf) - 1, f);
    buf[len] = '\0';
    fclose(f);

    char* p;
    if ((p = strstr(buf, "\"mass\""))) {
        sscanf(p + 6, "%*[: \t]%lf", &mesh.mass);
    }
    if ((p = strstr(buf, "\"energy\""))) {
        sscanf(p + 8, "%*[: \t]%lf", &mesh.energy);
    }
    if ((p = strstr(buf, "\"entropy\""))) {
        sscanf(p + 9, "%*[: \t]%lf", &mesh.entropy);
    }
    if ((p = strstr(buf, "\"cycle\""))) {
        sscanf(p + 7, "%*[: \t]%lf", &mesh.cycle);
    }
}

void parse_context(const char* filepath) {
    FILE* f = fopen(filepath, "r");
    if (!f) return;
    char buf[4096];
    size_t len = fread(buf, 1, sizeof(buf) - 1, f);
    buf[len] = '\0';
    fclose(f);

    char* p;
    if ((p = strstr(buf, "\"enabled\""))) {
        sscanf(p + 9, "%*[: \t]%lf", &enabled);
    }
    if ((p = strstr(buf, "\"is_authorized\""))) {
        sscanf(p + 15, "%*[: \t]%lf", &is_authorized);
    }
    if ((p = strstr(buf, "\"is_inter_subnet\""))) {
        sscanf(p + 17, "%*[: \t]%lf", &is_inter_subnet);
    }
    if ((p = strstr(buf, "\"is_valid_sig\""))) {
        sscanf(p + 14, "%*[: \t]%lf", &is_valid_sig);
    }
    if ((p = strstr(buf, "\"limit\""))) {
        sscanf(p + 7, "%*[: \t]%lf", &limit);
    }
    if ((p = strstr(buf, "\"priority\""))) {
        sscanf(p + 10, "%*[: \t]%lf", &priority);
    }
    if ((p = strstr(buf, "\"replayed\""))) {
        sscanf(p + 10, "%*[: \t]%lf", &replayed);
    }
    if ((p = strstr(buf, "\"request_size\""))) {
        sscanf(p + 14, "%*[: \t]%lf", &request_size);
    }
    if ((p = strstr(buf, "\"logoscompiler_state\""))) {
        static char state_buf_logoscompiler[128];
        if (sscanf(p + 21, "%*[: \t\"]%127[^\"]", state_buf_logoscompiler) == 1) {
            logoscompiler_state = state_buf_logoscompiler;
        }
    }
}

void run_events(const char* filepath) {
    FILE* f = fopen(filepath, "r");
    if (!f) return;
    char buf[65536];
    size_t len = fread(buf, 1, sizeof(buf) - 1, f);
    buf[len] = '\0';
    fclose(f);

    int event_index = 0;
    char* obj_start = strchr(buf, '{');
    while (obj_start) {
        char* obj_end = strchr(obj_start, '}');
        if (!obj_end) break;
        *obj_end = '\0';

        char intent[128] = {0};
        char event[128] = {0};

        char* p;
        if ((p = strstr(obj_start, "\"intent\""))) {
            sscanf(p + 8, "%*[: \t\"]%127[^\"]", intent);
        }
        if ((p = strstr(obj_start, "\"event\""))) {
            sscanf(p + 7, "%*[: \t\"]%127[^\"]", event);
        }
        if ((p = strstr(obj_start, "\"enabled\""))) {
            sscanf(p + 9, "%*[: \t]%lf", &enabled);
        }
        if ((p = strstr(obj_start, "\"is_authorized\""))) {
            sscanf(p + 15, "%*[: \t]%lf", &is_authorized);
        }
        if ((p = strstr(obj_start, "\"is_inter_subnet\""))) {
            sscanf(p + 17, "%*[: \t]%lf", &is_inter_subnet);
        }
        if ((p = strstr(obj_start, "\"is_valid_sig\""))) {
            sscanf(p + 14, "%*[: \t]%lf", &is_valid_sig);
        }
        if ((p = strstr(obj_start, "\"limit\""))) {
            sscanf(p + 7, "%*[: \t]%lf", &limit);
        }
        if ((p = strstr(obj_start, "\"priority\""))) {
            sscanf(p + 10, "%*[: \t]%lf", &priority);
        }
        if ((p = strstr(obj_start, "\"replayed\""))) {
            sscanf(p + 10, "%*[: \t]%lf", &replayed);
        }
        if ((p = strstr(obj_start, "\"request_size\""))) {
            sscanf(p + 14, "%*[: \t]%lf", &request_size);
        }

        struct TransitionResult res = process_event(intent, event);
        char icon = '?';
        if (strcmp(res.status, "transitioned") == 0) icon = '+';
        else if (strcmp(res.status, "blocked") == 0) icon = '-';

        printf("[EVENT %d] %c %s --(%s)--> %s [%s]\n", event_index, icon, res.from, event, res.to, res.status);
        if (strcmp(res.status, "transitioned") != 0) {
            printf("          Detail: %s\n", res.detail);
        }

        event_index++;
        obj_start = strchr(obj_end + 1, '{');
    }

    printf("\n[LOGOS VM] Execution complete.\n");
    printf("[LOGOS VM] Final mesh:\n");
    printf("  mass: %.4f\n", mesh.mass);
    printf("  energy: %.4f\n", mesh.energy);
    printf("  entropy: %.4f\n", mesh.entropy);
    printf("  cycle: %.4f\n", mesh.cycle);
}

int main(int argc, char** argv) {
    if (argc < 2) {
        printf("Usage: logos_app <events.json> [-m mesh.json] [-c context.json] [-o output_file]\n");
        return 0;
    }

    const char* events_path = argv[1];
    const char* output_path = NULL;
    for (int i = 2; i < argc; i++) {
        if (strcmp(argv[i], "-m") == 0 && i + 1 < argc) {
            parse_mesh(argv[i+1]);
            i++;
        } else if (strcmp(argv[i], "-c") == 0 && i + 1 < argc) {
            parse_context(argv[i+1]);
            i++;
        } else if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            output_path = argv[i+1];
            i++;
        }
    }

    run_events(events_path);

    if (output_path != NULL) {
        FILE* out_f = fopen(output_path, "w");
        if (out_f) {
            fprintf(out_f, "%s", C_PART1);
            fprintf(out_f, "const char* C_PART1 = \"");
            print_escaped(out_f, C_PART1);
            fprintf(out_f, "\";\nconst char* C_PART2 = \"");
            print_escaped(out_f, C_PART2);
            fprintf(out_f, "\";\n");
            fprintf(out_f, "%s", C_PART2);
            fclose(out_f);
        }
    }
    return 0;
}