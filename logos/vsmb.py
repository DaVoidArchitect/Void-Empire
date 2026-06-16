import json

def encode_vsmb(smir: dict) -> bytes:
    """Dummy encode_vsmb that serializes SMIR to JSON prefixed with b'VSMB'."""
    return b"VSMB" + json.dumps(smir).encode('utf-8')

def decode_vsmb(data: bytes) -> dict:
    """Dummy decode_vsmb that deserializes the JSON payload after stripping b'VSMB'."""
    if not data.startswith(b"VSMB"):
        raise ValueError("Invalid VSMB magic header")
    return json.loads(data[4:].decode('utf-8'))
