import struct

# Magic bytes & version
MAGIC = b"VSMB"
VERSION = 2

# Resource mapping
RESOURCE_MAP = {"mass": 0, "energy": 1, "entropy": 2, "cycle": 3}
REV_RESOURCE_MAP = {0: "mass", 1: "energy", 2: "entropy", 3: "cycle"}

# Operator mapping
OP_MAP = {"<": 0, ">": 1, "<=": 2, ">=": 3, "==": 4, "!=": 5, "max": 6, "min": 7}
REV_OP_MAP = {0: "<", 1: ">", 2: "<=", 3: ">=", 4: "==", 5: "!=", 6: "max", 7: "min"}

# Expression node types
EXPR_LITERAL = 0
EXPR_BINARY = 1
EXPR_UNARY = 2

# Literal types
LIT_NUMBER = 0
LIT_STRING = 1
LIT_PERCENT = 2
LIT_IDENTIFIER = 3

REV_LIT_MAP = {0: "NUMBER", 1: "STRING", 2: "PERCENT", 3: "IDENTIFIER"}
LIT_MAP = {"NUMBER": 0, "STRING": 1, "PERCENT": 2, "IDENTIFIER": 3}

# Binary expression operators
BIN_OP_MAP = {"+": 0, "-": 1, "*": 2, "/": 3, "<": 4, ">": 5, "<=": 6, ">=": 7, "==": 8, "!=": 9, "and": 10, "or": 11}
REV_BIN_OP_MAP = {v: k for k, v in BIN_OP_MAP.items()}

# Unary expression operators
UN_OP_MAP = {"not": 0, "-": 1}
REV_UN_OP_MAP = {v: k for k, v in UN_OP_MAP.items()}


def encode_string(s: str) -> bytes:
    b = s.encode("utf-8")
    return struct.pack("B", len(b)) + b


def decode_string(data: bytes, offset: int) -> tuple[str, int]:
    length = data[offset]
    offset += 1
    s = data[offset : offset + length].decode("utf-8")
    return s, offset + length


def encode_expr(expr: dict) -> bytes:
    etype = expr["type"]
    if etype == "literal":
        vtype = expr["value_type"]
        val = expr["value"]
        vtype_code = LIT_MAP[vtype]
        res = struct.pack("BB", EXPR_LITERAL, vtype_code)
        if vtype_code in (LIT_NUMBER, LIT_PERCENT):
            res += struct.pack("d", float(val))
        else:
            res += encode_string(str(val))
        return res
    elif etype == "binary":
        op = expr["op"]
        op_code = BIN_OP_MAP[op]
        res = struct.pack("BB", EXPR_BINARY, op_code)
        res += encode_expr(expr["left"])
        res += encode_expr(expr["right"])
        return res
    elif etype == "unary":
        op = expr["op"]
        op_code = UN_OP_MAP[op]
        res = struct.pack("BB", EXPR_UNARY, op_code)
        res += encode_expr(expr["expr"])
        return res
    else:
        raise ValueError(f"Unknown expression type: {etype}")


def decode_expr(data: bytes, offset: int) -> tuple[dict, int]:
    etype = data[offset]
    offset += 1
    if etype == EXPR_LITERAL:
        vtype_code = data[offset]
        offset += 1
        vtype = REV_LIT_MAP[vtype_code]
        if vtype_code in (LIT_NUMBER, LIT_PERCENT):
            val = struct.unpack_from("d", data, offset)[0]
            offset += 8
            # If it was originally an int, keep it if it equals the float value
            if val.is_integer() and vtype_code == LIT_NUMBER:
                val = int(val)
        else:
            val, offset = decode_string(data, offset)
        return {"type": "literal", "value_type": vtype, "value": val}, offset
    elif etype == EXPR_BINARY:
        op_code = data[offset]
        offset += 1
        op = REV_BIN_OP_MAP[op_code]
        left, offset = decode_expr(data, offset)
        right, offset = decode_expr(data, offset)
        return {"type": "binary", "op": op, "left": left, "right": right}, offset
    elif etype == EXPR_UNARY:
        op_code = data[offset]
        offset += 1
        op = REV_UN_OP_MAP[op_code]
        expr, offset = decode_expr(data, offset)
        return {"type": "unary", "op": op, "expr": expr}, offset
    else:
        raise ValueError(f"Unknown serialized expression type code: {etype}")


def encode_vsmb(smir: dict) -> bytes:
    """Encode SMIR dictionary into binary VSMB format."""
    res = bytearray()
    res.extend(MAGIC)
    res.extend(struct.pack("B", VERSION))

    intents = smir.get("intents", [])
    res.extend(struct.pack("H", len(intents)))

    for intent in intents:
        # 1. Intent Name
        res.extend(encode_string(intent["name"]))

        # 2. Headers
        headers = intent.get("headers", {})
        res.extend(struct.pack("B", len(headers)))
        for k, v in headers.items():
            res.extend(encode_string(k))
            if isinstance(v, dict) and "value" in v:  # lifetime or similar structure
                res.extend(struct.pack("B", 2))  # dict value type
                res.extend(struct.pack("d", float(v["value"])))
                res.extend(encode_string(v.get("unit", "")))
            elif isinstance(v, (int, float)):
                res.extend(struct.pack("B", 1))  # numeric type
                res.extend(struct.pack("d", float(v)))
            else:
                res.extend(struct.pack("B", 0))  # string type
                res.extend(encode_string(str(v)))

        # 3. Requirements
        reqs = intent.get("requirements", [])
        res.extend(struct.pack("B", len(reqs)))
        for r in reqs:
            res.extend(struct.pack("B", RESOURCE_MAP[r["resource"]]))
            res.extend(struct.pack("d", float(r["value"])))
            res.extend(encode_string(r.get("unit", "")))

        # 4. Constraints
        consts = intent.get("constraints", [])
        res.extend(struct.pack("B", len(consts)))
        for c in consts:
            res.extend(struct.pack("B", RESOURCE_MAP[c["resource"]]))
            res.extend(struct.pack("B", OP_MAP[c["operator"]]))
            res.extend(struct.pack("d", float(c["value"])))
            res.extend(encode_string(c.get("unit", "")))

        # 5. States
        states = intent.get("states", [])
        res.extend(struct.pack("B", len(states)))
        for s in states:
            res.extend(encode_string(s["name"]))

            # Transitions
            transitions = s.get("transitions", [])
            res.extend(struct.pack("B", len(transitions)))
            for t in transitions:
                res.extend(encode_string(t["event"]))
                res.extend(encode_string(t["target"]))
                res.extend(struct.pack("i", t.get("line", -1)))

                # Guard presence
                has_guard = 1 if "guard" in t else 0
                res.extend(struct.pack("B", has_guard))
                if has_guard:
                    res.extend(encode_expr(t["guard"]["expr"]))

                # Transition-level requirements
                trans_reqs = t.get("requires", [])
                res.extend(struct.pack("B", len(trans_reqs)))
                for tr in trans_reqs:
                    res.extend(struct.pack("B", RESOURCE_MAP[tr["resource"]]))
                    res.extend(struct.pack("d", float(tr["value"])))
                    res.extend(encode_string(tr.get("unit", "")))

    return bytes(res)


def decode_vsmb(data: bytes) -> dict:
    """Decode binary VSMB bytes into SMIR dictionary."""
    if len(data) < 7:
        raise ValueError("Invalid VSMB data: too short")

    magic = data[0:4]
    if magic != MAGIC:
        raise ValueError(f"Invalid VSMB magic header: {magic}")

    version = data[4]
    if version != VERSION:
        raise ValueError(f"Unsupported VSMB version: {version}")

    offset = 5
    intents_count = struct.unpack_from("H", data, offset)[0]
    offset += 2

    intents = []
    for _ in range(intents_count):
        # 1. Intent Name
        name, offset = decode_string(data, offset)

        # 2. Headers
        headers_count = data[offset]
        offset += 1
        headers = {}
        for _ in range(headers_count):
            k, offset = decode_string(data, offset)
            vtype = data[offset]
            offset += 1
            if vtype == 0:  # string
                v, offset = decode_string(data, offset)
            elif vtype == 1:  # numeric
                v = struct.unpack_from("d", data, offset)[0]
                offset += 8
                if v.is_integer():
                    v = int(v)
            elif vtype == 2:  # dict
                val = struct.unpack_from("d", data, offset)[0]
                offset += 8
                if val.is_integer():
                    val = int(val)
                unit, offset = decode_string(data, offset)
                v = {"value": val, "unit": unit}
            else:
                raise ValueError(f"Unknown header value type: {vtype}")
            headers[k] = v

        # 3. Requirements
        reqs_count = data[offset]
        offset += 1
        requirements = []
        for _ in range(reqs_count):
            res_code = data[offset]
            offset += 1
            val = struct.unpack_from("d", data, offset)[0]
            offset += 8
            unit, offset = decode_string(data, offset)
            requirements.append({
                "resource": REV_RESOURCE_MAP[res_code],
                "value": val,
                "unit": unit
            })

        # 4. Constraints
        consts_count = data[offset]
        offset += 1
        constraints = []
        for _ in range(consts_count):
            res_code = data[offset]
            offset += 1
            op_code = data[offset]
            offset += 1
            val = struct.unpack_from("d", data, offset)[0]
            offset += 8
            unit, offset = decode_string(data, offset)
            constraints.append({
                "resource": REV_RESOURCE_MAP[res_code],
                "operator": REV_OP_MAP[op_code],
                "value": val,
                "unit": unit
            })

        # 5. States
        states_count = data[offset]
        offset += 1
        states = []
        for _ in range(states_count):
            s_name, offset = decode_string(data, offset)

            # Transitions
            transitions_count = data[offset]
            offset += 1
            transitions = []
            for _ in range(transitions_count):
                t_evt, offset = decode_string(data, offset)
                t_tgt, offset = decode_string(data, offset)
                line = struct.unpack_from("i", data, offset)[0]
                offset += 4

                has_guard = data[offset]
                offset += 1

                trans_dict = {
                    "event": t_evt,
                    "target": t_tgt,
                    "line": line
                }

                if has_guard:
                    guard_expr, offset = decode_expr(data, offset)
                    trans_dict["guard"] = {"expr": guard_expr}

                # Transition requirements
                trans_reqs_count = data[offset]
                offset += 1
                trans_reqs = []
                for _ in range(trans_reqs_count):
                    tr_res_code = data[offset]
                    offset += 1
                    tr_val = struct.unpack_from("d", data, offset)[0]
                    offset += 8
                    tr_unit, offset = decode_string(data, offset)
                    trans_reqs.append({
                        "resource": REV_RESOURCE_MAP[tr_res_code],
                        "value": tr_val,
                        "unit": tr_unit
                    })

                if trans_reqs:
                    trans_dict["requires"] = trans_reqs

                transitions.append(trans_dict)

            states.append({
                "name": s_name,
                "transitions": transitions
            })

        intents.append({
            "name": name,
            "headers": headers,
            "requirements": requirements,
            "constraints": constraints,
            "states": states
        })

    return {
        "logos_version": "2.0-declarative",
        "intents": intents
    }
