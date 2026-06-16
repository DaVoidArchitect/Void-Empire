use std::collections::HashMap;
use std::convert::TryInto;
use std::env;
use std::fs::File;
use std::io::{self, Read, Write};
use std::process;

// ============================================================================
// 1. JSON AST & PARSER IMPLEMENTATION (Zero-dependency)
// ============================================================================

#[derive(Debug, Clone)]
enum JsonValue {
    Null,
    Bool(bool),
    Number(f64),
    String(String),
    Array(Vec<JsonValue>),
    Object(HashMap<String, JsonValue>),
}

impl JsonValue {
    fn as_object(&self) -> Option<&HashMap<String, JsonValue>> {
        match self {
            JsonValue::Object(map) => Some(map),
            _ => None,
        }
    }

    fn as_array(&self) -> Option<&Vec<JsonValue>> {
        match self {
            JsonValue::Array(arr) => Some(arr),
            _ => None,
        }
    }

    fn get(&self, key: &str) -> Option<&JsonValue> {
        self.as_object()?.get(key)
    }

    fn as_string(&self) -> Option<&str> {
        match self {
            JsonValue::String(s) => Some(s),
            _ => None,
        }
    }

    fn as_f64(&self) -> Option<f64> {
        match self {
            JsonValue::Number(n) => Some(*n),
            _ => None,
        }
    }

    fn as_bool(&self) -> Option<bool> {
        match self {
            JsonValue::Bool(b) => Some(*b),
            _ => None,
        }
    }

    // Required methods that return Result for compiler-friendly ? checks
    fn req_object(&self) -> Result<&HashMap<String, JsonValue>, String> {
        self.as_object().ok_or_else(|| "Value is not an object".to_string())
    }

    fn req_array(&self) -> Result<&Vec<JsonValue>, String> {
        self.as_array().ok_or_else(|| "Value is not an array".to_string())
    }

    fn req_get(&self, key: &str) -> Result<&JsonValue, String> {
        self.get(key).ok_or_else(|| format!("Key '{}' not found in object", key))
    }

    fn req_string(&self) -> Result<&str, String> {
        self.as_string().ok_or_else(|| "Value is not a string".to_string())
    }

    fn req_f64(&self) -> Result<f64, String> {
        self.as_f64().ok_or_else(|| "Value is not a number".to_string())
    }

    fn req_bool(&self) -> Result<bool, String> {
        self.as_bool().ok_or_else(|| "Value is not a boolean".to_string())
    }
}

struct JsonParser<'a> {
    input: &'a str,
    chars: std::iter::Peekable<std::str::Chars<'a>>,
}

impl<'a> JsonParser<'a> {
    fn new(input: &'a str) -> Self {
        Self {
            input,
            chars: input.chars().peekable(),
        }
    }

    fn skip_whitespace(&mut self) {
        while let Some(&c) = self.chars.peek() {
            if c.is_whitespace() {
                self.chars.next();
            } else {
                break;
            }
        }
    }

    fn parse_value(&mut self) -> Result<JsonValue, String> {
        self.skip_whitespace();
        let c = *self.chars.peek().ok_or("Unexpected EOF")?;
        if c == '{' {
            self.parse_object()
        } else if c == '[' {
            self.parse_array()
        } else if c == '"' {
            self.parse_string()
        } else if c.is_ascii_digit() || c == '-' {
            self.parse_number()
        } else if c == 't' || c == 'f' {
            self.parse_bool()
        } else if c == 'n' {
            self.parse_null()
        } else {
            Err(format!("Unexpected character: {}", c))
        }
    }

    fn parse_object(&mut self) -> Result<JsonValue, String> {
        self.chars.next(); // Consume '{'
        let mut map = HashMap::new();
        self.skip_whitespace();
        if self.chars.peek() == Some(&'}') {
            self.chars.next();
            return Ok(JsonValue::Object(map));
        }

        loop {
            self.skip_whitespace();
            if self.chars.peek() != Some(&'"') {
                return Err("Expected string key in object".to_string());
            }
            let key = match self.parse_string()? {
                JsonValue::String(s) => s,
                _ => return Err("Expected key".to_string()),
            };

            self.skip_whitespace();
            if self.chars.next() != Some(':') {
                return Err("Expected ':' after object key".to_string());
            }

            let value = self.parse_value()?;
            map.insert(key, value);

            self.skip_whitespace();
            match self.chars.next() {
                Some('}') => break,
                Some(',') => {}
                Some(c) => return Err(format!("Expected ',' or '}}', got '{}'", c)),
                None => return Err("Unclosed object".to_string()),
            }
        }

        Ok(JsonValue::Object(map))
    }

    fn parse_array(&mut self) -> Result<JsonValue, String> {
        self.chars.next(); // Consume '['
        let mut arr = Vec::new();
        self.skip_whitespace();
        if self.chars.peek() == Some(&']') {
            self.chars.next();
            return Ok(JsonValue::Array(arr));
        }

        loop {
            arr.push(self.parse_value()?);
            self.skip_whitespace();
            match self.chars.next() {
                Some(']') => break,
                Some(',') => {}
                Some(c) => return Err(format!("Expected ',' or ']', got '{}'", c)),
                None => return Err("Unclosed array".to_string()),
            }
        }
        Ok(JsonValue::Array(arr))
    }

    fn parse_string(&mut self) -> Result<JsonValue, String> {
        self.chars.next(); // Consume '"'
        let mut s = String::new();
        while let Some(c) = self.chars.next() {
            if c == '"' {
                return Ok(JsonValue::String(s));
            } else if c == '\\' {
                let esc = self.chars.next().ok_or("Unescaped backslash")?;
                match esc {
                    '"' => s.push('"'),
                    '\\' => s.push('\\'),
                    '/' => s.push('/'),
                    'b' => s.push('\x08'),
                    'f' => s.push('\x0c'),
                    'n' => s.push('\n'),
                    'r' => s.push('\r'),
                    't' => s.push('\t'),
                    _ => s.push(esc),
                }
            } else {
                s.push(c);
            }
        }
        Err("Unclosed string".to_string())
    }

    fn parse_number(&mut self) -> Result<JsonValue, String> {
        let mut num_str = String::new();
        while let Some(&c) = self.chars.peek() {
            if c.is_whitespace() || c == ',' || c == '}' || c == ']' || c == ':' {
                break;
            }
            num_str.push(c);
            self.chars.next();
        }
        let val = num_str.parse::<f64>().map_err(|e| e.to_string())?;
        Ok(JsonValue::Number(val))
    }

    fn parse_bool(&mut self) -> Result<JsonValue, String> {
        let mut s = String::new();
        for _ in 0..4 {
            if let Some(c) = self.chars.next() {
                s.push(c);
            }
        }
        if s == "true" {
            Ok(JsonValue::Bool(true))
        } else {
            if let Some(c) = self.chars.next() {
                s.push(c);
            }
            if s == "false" {
                Ok(JsonValue::Bool(false))
            } else {
                Err(format!("Invalid boolean token: {}", s))
            }
        }
    }

    fn parse_null(&mut self) -> Result<JsonValue, String> {
        let mut s = String::new();
        for _ in 0..4 {
            if let Some(c) = self.chars.next() {
                s.push(c);
            }
        }
        if s == "null" {
            Ok(JsonValue::Null)
        } else {
            Err(format!("Invalid null token: {}", s))
        }
    }
}

fn parse_json(input: &str) -> Result<JsonValue, String> {
    JsonParser::new(input).parse_value()
}

// ============================================================================
// 2. VSMB BINARY IN-MEMORY SPECIFICATIONS
// ============================================================================

#[derive(Debug, Clone)]
struct HeaderVal {
    vtype: u8, // 0=string, 1=numeric, 2=dict (value+unit)
    str_val: String,
    num_val: f64,
    unit_val: String,
}

#[derive(Debug, Clone)]
struct Resource {
    resource_type: u8, // 0=mass, 1=energy, 2=entropy, 3=cycle
    value: f64,
    unit: String,
}

#[derive(Debug, Clone)]
struct Constraint {
    resource_type: u8,
    operator_type: u8, // 0=<, 1=>, 2=<=, 3=>=, 4===, 5=!=, 6=max, 7=min
    value: f64,
    unit: String,
}

#[derive(Debug, Clone)]
struct Expr {
    node_type: u8, // 0=literal, 1=binary, 2=unary
    lit_type: u8,  // 0=NUMBER, 1=STRING, 2=PERCENT, 3=IDENTIFIER
    lit_str: String,
    lit_num: f64,
    op_code: u8, // 0..11 for binary, 0..1 for unary
    left: Option<Box<Expr>>,
    right: Option<Box<Expr>>,
    expr: Option<Box<Expr>>,
}

#[derive(Debug, Clone)]
struct Transition {
    event: String,
    target: String,
    line: i32,
    guard: Option<Expr>,
    requires: Vec<Resource>,
}

#[derive(Debug, Clone)]
struct State {
    name: String,
    transitions: Vec<Transition>,
}

#[derive(Debug, Clone)]
struct Intent {
    name: String,
    headers: HashMap<String, HeaderVal>,
    requirements: Vec<Resource>,
    constraints: Vec<Constraint>,
    states: Vec<State>,
}

#[derive(Debug, Clone)]
struct Smir {
    intents: Vec<Intent>,
}

// Helper methods to convert parsed JSON to VSMB structures if JSON SMIR is provided
fn json_to_expr(val: &JsonValue) -> Result<Expr, String> {
    let etype = val.req_get("type")?.req_string()?;
    if etype == "literal" {
        let vtype = val.req_get("value_type")?.req_string()?;
        let value = val.req_get("value")?;
        let lit_type = match vtype {
            "NUMBER" => 0,
            "STRING" => 1,
            "PERCENT" => 2,
            "IDENTIFIER" => 3,
            _ => return Err(format!("Invalid literal value_type: {}", vtype)),
        };
        let mut lit_str = String::new();
        let mut lit_num = 0.0;
        if lit_type == 0 || lit_type == 2 {
            lit_num = value.req_f64()?;
        } else {
            lit_str = value.req_string()?.to_string();
        }
        Ok(Expr {
            node_type: 0,
            lit_type,
            lit_str,
            lit_num,
            op_code: 0,
            left: None,
            right: None,
            expr: None,
        })
    } else if etype == "binary" {
        let op = val.req_get("op")?.req_string()?;
        let op_code = match op {
            "+" => 0, "-" => 1, "*" => 2, "/" => 3,
            "<" => 4, ">" => 5, "<=" => 6, ">=" => 7,
            "==" => 8, "!=" => 9, "and" => 10, "or" => 11,
            _ => return Err(format!("Invalid binary op: {}", op)),
        };
        let left = Box::new(json_to_expr(val.req_get("left")?)?);
        let right = Box::new(json_to_expr(val.req_get("right")?)?);
        Ok(Expr {
            node_type: 1,
            lit_type: 0,
            lit_str: String::new(),
            lit_num: 0.0,
            op_code,
            left: Some(left),
            right: Some(right),
            expr: None,
        })
    } else if etype == "unary" {
        let op = val.req_get("op")?.req_string()?;
        let op_code = match op {
            "not" => 0,
            "-" => 1,
            _ => return Err(format!("Invalid unary op: {}", op)),
        };
        let expr = Box::new(json_to_expr(val.req_get("expr")?)?);
        Ok(Expr {
            node_type: 2,
            lit_type: 0,
            lit_str: String::new(),
            lit_num: 0.0,
            op_code,
            left: None,
            right: None,
            expr: Some(expr),
        })
    } else {
        Err(format!("Invalid expr type: {}", etype))
    }
}

// ============================================================================
// 3. BINARY DECODER FOR VSMB (Zero pointer allocation)
// ============================================================================

fn read_string(data: &[u8], offset: &mut usize) -> Result<String, String> {
    if *offset >= data.len() {
        return Err("Unexpected EOF reading string length".to_string());
    }
    let length = data[*offset] as usize;
    *offset += 1;
    if *offset + length > data.len() {
        return Err("Unexpected EOF reading string content".to_string());
    }
    let s = std::str::from_utf8(&data[*offset..*offset + length])
        .map_err(|e| e.to_string())?
        .to_string();
    *offset += length;
    Ok(s)
}

fn read_f64(data: &[u8], offset: &mut usize) -> Result<f64, String> {
    if *offset + 8 > data.len() {
        return Err("Unexpected EOF reading float64".to_string());
    }
    let bytes: [u8; 8] = data[*offset..*offset + 8].try_into().unwrap();
    *offset += 8;
    Ok(f64::from_le_bytes(bytes))
}

fn read_i32(data: &[u8], offset: &mut usize) -> Result<i32, String> {
    if *offset + 4 > data.len() {
        return Err("Unexpected EOF reading int32".to_string());
    }
    let bytes: [u8; 4] = data[*offset..*offset + 4].try_into().unwrap();
    *offset += 4;
    Ok(i32::from_le_bytes(bytes))
}

fn decode_expr_binary(data: &[u8], offset: &mut usize) -> Result<Expr, String> {
    if *offset >= data.len() {
        return Err("Unexpected EOF reading expression node type".to_string());
    }
    let node_type = data[*offset];
    *offset += 1;

    if node_type == 0 {
        // literal
        if *offset >= data.len() {
            return Err("Unexpected EOF reading literal value type".to_string());
        }
        let lit_type = data[*offset];
        *offset += 1;

        let mut lit_str = String::new();
        let mut lit_num = 0.0;

        if lit_type == 0 || lit_type == 2 {
            lit_num = read_f64(data, offset)?;
        } else {
            lit_str = read_string(data, offset)?;
        }

        Ok(Expr {
            node_type,
            lit_type,
            lit_str,
            lit_num,
            op_code: 0,
            left: None,
            right: None,
            expr: None,
        })
    } else if node_type == 1 {
        // binary
        if *offset >= data.len() {
            return Err("Unexpected EOF reading binary operator code".to_string());
        }
        let op_code = data[*offset];
        *offset += 1;

        let left = Box::new(decode_expr_binary(data, offset)?);
        let right = Box::new(decode_expr_binary(data, offset)?);

        Ok(Expr {
            node_type,
            lit_type: 0,
            lit_str: String::new(),
            lit_num: 0.0,
            op_code,
            left: Some(left),
            right: Some(right),
            expr: None,
        })
    } else if node_type == 2 {
        // unary
        if *offset >= data.len() {
            return Err("Unexpected EOF reading unary operator code".to_string());
        }
        let op_code = data[*offset];
        *offset += 1;

        let expr = Box::new(decode_expr_binary(data, offset)?);

        Ok(Expr {
            node_type,
            lit_type: 0,
            lit_str: String::new(),
            lit_num: 0.0,
            op_code,
            left: None,
            right: None,
            expr: Some(expr),
        })
    } else {
        Err(format!("Invalid expression type code: {}", node_type))
    }
}

fn decode_vsmb(data: &[u8]) -> Result<Smir, String> {
    if data.len() < 7 {
        return Err("Data too short".to_string());
    }
    if &data[0..4] != b"VSMB" {
        return Err("Magic bytes mismatch".to_string());
    }
    let version = data[4];
    if version != 2 {
        return Err(format!("Unsupported version: {}", version));
    }

    let mut offset = 5;
    let intents_count = u16::from_le_bytes(data[offset..offset + 2].try_into().unwrap()) as usize;
    offset += 2;

    let mut intents = Vec::with_capacity(intents_count);

    for _ in 0..intents_count {
        let intent_name = read_string(data, &mut offset)?;

        // Headers
        let headers_count = data[offset] as usize;
        offset += 1;
        let mut headers = HashMap::with_capacity(headers_count);
        for _ in 0..headers_count {
            let key = read_string(data, &mut offset)?;
            let vtype = data[offset];
            offset += 1;

            let mut str_val = String::new();
            let mut num_val = 0.0;
            let mut unit_val = String::new();

            if vtype == 0 {
                str_val = read_string(data, &mut offset)?;
            } else if vtype == 1 {
                num_val = read_f64(data, &mut offset)?;
            } else if vtype == 2 {
                num_val = read_f64(data, &mut offset)?;
                unit_val = read_string(data, &mut offset)?;
            } else {
                return Err(format!("Invalid header value type: {}", vtype));
            }

            headers.insert(
                key,
                HeaderVal {
                    vtype,
                    str_val,
                    num_val,
                    unit_val,
                },
            );
        }

        // Requirements
        let reqs_count = data[offset] as usize;
        offset += 1;
        let mut requirements = Vec::with_capacity(reqs_count);
        for _ in 0..reqs_count {
            let resource_type = data[offset];
            offset += 1;
            let value = read_f64(data, &mut offset)?;
            let unit = read_string(data, &mut offset)?;
            requirements.push(Resource {
                resource_type,
                value,
                unit,
            });
        }

        // Constraints
        let consts_count = data[offset] as usize;
        offset += 1;
        let mut constraints = Vec::with_capacity(consts_count);
        for _ in 0..consts_count {
            let resource_type = data[offset];
            offset += 1;
            let operator_type = data[offset];
            offset += 1;
            let value = read_f64(data, &mut offset)?;
            let unit = read_string(data, &mut offset)?;
            constraints.push(Constraint {
                resource_type,
                operator_type,
                value,
                unit,
            });
        }

        // States
        let states_count = data[offset] as usize;
        offset += 1;
        let mut states = Vec::with_capacity(states_count);
        for _ in 0..states_count {
            let state_name = read_string(data, &mut offset)?;

            // Transitions
            let transitions_count = data[offset] as usize;
            offset += 1;
            let mut transitions = Vec::with_capacity(transitions_count);
            for _ in 0..transitions_count {
                let event = read_string(data, &mut offset)?;
                let target = read_string(data, &mut offset)?;
                let line = read_i32(data, &mut offset)?;
                let has_guard = data[offset] != 0;
                offset += 1;

                let mut guard = None;
                if has_guard {
                    guard = Some(decode_expr_binary(data, &mut offset)?);
                }

                // Requirements
                let tr_reqs_count = data[offset] as usize;
                offset += 1;
                let mut tr_requires = Vec::with_capacity(tr_reqs_count);
                for _ in 0..tr_reqs_count {
                    let resource_type = data[offset];
                    offset += 1;
                    let value = read_f64(data, &mut offset)?;
                    let unit = read_string(data, &mut offset)?;
                    tr_requires.push(Resource {
                        resource_type,
                        value,
                        unit,
                    });
                }

                transitions.push(Transition {
                    event,
                    target,
                    line,
                    guard,
                    requires: tr_requires,
                });
            }

            states.push(State {
                name: state_name,
                transitions,
            });
        }

        intents.push(Intent {
            name: intent_name,
            headers,
            requirements,
            constraints,
            states,
        });
    }

    Ok(Smir { intents })
}

// Convert JSON SMIR to internal Smir structure
fn decode_json_smir(json: &JsonValue) -> Result<Smir, String> {
    let intents_val = json
        .req_get("intents")?
        .req_array()?;
    let mut intents = Vec::with_capacity(intents_val.len());

    for i_val in intents_val {
        let name = i_val
            .req_get("name")?
            .req_string()?
            .to_string();

        // Headers
        let mut headers = HashMap::new();
        if let Ok(headers_map) = i_val.req_get("headers").and_then(|h| h.req_object()) {
            for (k, v) in headers_map {
                let mut str_val = String::new();
                let mut num_val = 0.0;
                let mut unit_val = String::new();
                let vtype;

                if let Ok(s) = v.req_string() {
                    vtype = 0;
                    str_val = s.to_string();
                } else if let Ok(n) = v.req_f64() {
                    vtype = 1;
                    num_val = n;
                } else if let Ok(map) = v.req_object() {
                    vtype = 2;
                    num_val = map.get("value").ok_or_else(|| "No value key".to_string())?.req_f64()?;
                    unit_val = map
                        .get("unit")
                        .ok_or_else(|| "No unit key".to_string())?
                        .req_string()?
                        .to_string();
                } else {
                    return Err("Invalid header value type".to_string());
                }

                headers.insert(
                    k.clone(),
                    HeaderVal {
                        vtype,
                        str_val,
                        num_val,
                        unit_val,
                    },
                );
            }
        }

        // Requirements
        let reqs_val = i_val
            .get("requirements")
            .and_then(|r| r.as_array())
            .map(|a| a.as_slice())
            .unwrap_or(&[]);
        let mut requirements = Vec::with_capacity(reqs_val.len());
        for r_val in reqs_val {
            let res_str = r_val.req_get("resource")?.req_string()?;
            let resource_type = match res_str {
                "mass" => 0,
                "energy" => 1,
                "entropy" => 2,
                "cycle" => 3,
                _ => return Err(format!("Invalid resource: {}", res_str)),
            };
            let value = r_val.req_get("value")?.req_f64()?;
            let unit = r_val
                .get("unit")
                .and_then(|u| u.as_string())
                .unwrap_or("")
                .to_string();
            requirements.push(Resource {
                resource_type,
                value,
                unit,
            });
        }

        // Constraints
        let consts_val = i_val
            .get("constraints")
            .and_then(|c| c.as_array())
            .map(|a| a.as_slice())
            .unwrap_or(&[]);
        let mut constraints = Vec::with_capacity(consts_val.len());
        for c_val in consts_val {
            let res_str = c_val.req_get("resource")?.req_string()?;
            let resource_type = match res_str {
                "mass" => 0,
                "energy" => 1,
                "entropy" => 2,
                "cycle" => 3,
                _ => return Err(format!("Invalid resource: {}", res_str)),
            };
            let op_str = c_val.req_get("operator")?.req_string()?;
            let operator_type = match op_str {
                "<" => 0,
                ">" => 1,
                "<=" => 2,
                ">=" => 3,
                "==" => 4,
                "!=" => 5,
                "max" => 6,
                "min" => 7,
                _ => return Err(format!("Invalid operator: {}", op_str)),
            };
            let value = c_val.req_get("value")?.req_f64()?;
            let unit = c_val
                .get("unit")
                .and_then(|u| u.as_string())
                .unwrap_or("")
                .to_string();
            constraints.push(Constraint {
                resource_type,
                operator_type,
                value,
                unit,
            });
        }

        // States
        let states_val = i_val
            .req_get("states")?
            .req_array()?;
        let mut states = Vec::with_capacity(states_val.len());
        for s_val in states_val {
            let s_name = s_val.req_get("name")?.req_string()?.to_string();

            let trans_val = s_val
                .get("transitions")
                .and_then(|t| t.as_array())
                .map(|a| a.as_slice())
                .unwrap_or(&[]);
            let mut transitions = Vec::with_capacity(trans_val.len());
            for t_val in trans_val {
                let event = t_val.req_get("event")?.req_string()?.to_string();
                let target = t_val.req_get("target")?.req_string()?.to_string();
                let line = t_val
                    .get("line")
                    .and_then(|l| l.as_f64())
                    .unwrap_or(-1.0) as i32;

                let mut guard = None;
                if let Some(g_val) = t_val.get("guard") {
                    guard = Some(json_to_expr(g_val.req_get("expr")?)?);
                }

                // Requirements
                let t_reqs_val = t_val
                    .get("requires")
                    .and_then(|r| r.as_array())
                    .map(|a| a.as_slice())
                    .unwrap_or(&[]);
                let mut tr_requires = Vec::with_capacity(t_reqs_val.len());
                for tr_val in t_reqs_val {
                    let tr_res_str = tr_val.req_get("resource")?.req_string()?;
                    let tr_resource_type = match tr_res_str {
                        "mass" => 0,
                        "energy" => 1,
                        "entropy" => 2,
                        "cycle" => 3,
                        _ => return Err(format!("Invalid resource: {}", tr_res_str)),
                    };
                    let tr_value = tr_val.req_get("value")?.req_f64()?;
                    let tr_unit = tr_val
                        .get("unit")
                        .and_then(|u| u.as_string())
                        .unwrap_or("")
                        .to_string();
                    tr_requires.push(Resource {
                        resource_type: tr_resource_type,
                        value: tr_value,
                        unit: tr_unit,
                    });
                }

                transitions.push(Transition {
                    event,
                    target,
                    line,
                    guard,
                    requires: tr_requires,
                });
            }

            states.push(State {
                name: s_name,
                transitions,
            });
        }

        intents.push(Intent {
            name,
            headers,
            requirements,
            constraints,
            states,
        });
    }

    Ok(Smir { intents })
}

// ============================================================================
// 4. NATIVE VM IMPLEMENTATION (With Transaction register rollback)
// ============================================================================

struct LogosVM {
    smir: Smir,
    mesh: HashMap<String, f64>,
    runtime_ctx: HashMap<String, JsonValue>,
    intent_states: HashMap<String, String>,
}

impl LogosVM {
    fn new(smir: Smir, mesh_context: HashMap<String, f64>, runtime_context: HashMap<String, JsonValue>) -> Self {
        let mut intent_states = HashMap::new();
        for intent in &smir.intents {
            if let Some(first_state) = intent.states.first() {
                intent_states.insert(intent.name.clone(), first_state.name.clone());
            }
        }

        Self {
            smir,
            mesh: mesh_context,
            runtime_ctx: runtime_context,
            intent_states,
        }
    }

    fn eval_expr(&self, expr: &Expr) -> JsonValue {
        match expr.node_type {
            0 => {
                // literal
                match expr.lit_type {
                    0 => JsonValue::Number(expr.lit_num),
                    1 => JsonValue::String(expr.lit_str.clone()),
                    2 => JsonValue::Number(expr.lit_num / 100.0),
                    3 => {
                        // Lookup in runtime context
                        if let Some(val) = self.runtime_ctx.get(&expr.lit_str) {
                            val.clone()
                        } else {
                            JsonValue::Number(0.0)
                        }
                    }
                    _ => JsonValue::Null,
                }
            }
            1 => {
                // binary
                let left_val = self.eval_expr(expr.left.as_ref().unwrap());
                let right_val = self.eval_expr(expr.right.as_ref().unwrap());
                let op = expr.op_code; // 0=+, 1=-, 2=*, 3=/, 4=<, 5=>, 6=<=, 7=>=, 8===, 9=!=, 10=and, 11=or
                match (left_val, right_val) {
                    (JsonValue::Number(l), JsonValue::Number(r)) => match op {
                        0 => JsonValue::Number(l + r),
                        1 => JsonValue::Number(l - r),
                        2 => JsonValue::Number(l * r),
                        3 => JsonValue::Number(if r != 0.0 { l / r } else { 0.0 }),
                        4 => JsonValue::Bool(l < r),
                        5 => JsonValue::Bool(l > r),
                        6 => JsonValue::Bool(l <= r),
                        7 => JsonValue::Bool(l >= r),
                        8 => JsonValue::Bool(l == r),
                        9 => JsonValue::Bool(l != r),
                        _ => JsonValue::Null,
                    },
                    (JsonValue::Bool(l), JsonValue::Bool(r)) => match op {
                        10 => JsonValue::Bool(l && r),
                        11 => JsonValue::Bool(l || r),
                        8 => JsonValue::Bool(l == r),
                        9 => JsonValue::Bool(l != r),
                        _ => JsonValue::Null,
                    },
                    (JsonValue::String(l), JsonValue::String(r)) => match op {
                        8 => JsonValue::Bool(l == r),
                        9 => JsonValue::Bool(l != r),
                        _ => JsonValue::Null,
                    },
                    _ => JsonValue::Null,
                }
            }
            2 => {
                // unary
                let inner_val = self.eval_expr(expr.expr.as_ref().unwrap());
                let op = expr.op_code; // 0=not, 1=-
                match inner_val {
                    JsonValue::Bool(b) => {
                        if op == 0 {
                            JsonValue::Bool(!b)
                        } else {
                            JsonValue::Null
                        }
                    }
                    JsonValue::Number(n) => {
                        if op == 1 {
                            JsonValue::Number(-n)
                        } else {
                            JsonValue::Null
                        }
                    }
                    _ => JsonValue::Null,
                }
            }
            _ => JsonValue::Null,
        }
    }

    fn check_constraints(&self, constraints: &[Constraint]) -> Option<String> {
        for c in constraints {
            let res_name = match c.resource_type {
                0 => "mass",
                1 => "energy",
                2 => "entropy",
                3 => "cycle",
                _ => continue,
            };
            let current = *self.mesh.get(res_name).unwrap_or(&0.0);
            let limit = c.value;
            let op = c.operator_type;

            let violated = match op {
                0 => !(current < limit),
                1 => !(current > limit),
                2 => !(current <= limit),
                3 => !(current >= limit),
                4 => current != limit,
                5 => current == limit,
                6 => current > limit,  // max constraint: current must be <= max limit
                7 => current < limit,  // min constraint: current must be >= min limit
                _ => false,
            };

            if violated {
                let op_str = match op {
                    0 => "<", 1 => ">", 2 => "<=", 3 => ">=", 4 => "==", 5 => "!=", 6 => "max", 7 => "min",
                    _ => "?",
                };
                return Some(format!(
                    "{} constraint '{} {} {}' violated. Current mesh value: {} {}.",
                    res_name, op_str, limit, c.unit, current, c.unit
                ));
            }
        }
        None
    }

    fn send_event(&mut self, intent_name: &str, event: &str) -> Result<HashMap<String, JsonValue>, String> {
        let intent = self
            .smir
            .intents
            .iter()
            .find(|i| i.name == intent_name)
            .ok_or_else(|| format!("Unknown intent: '{}'", intent_name))?;

        let current_state_name = self
            .intent_states
            .get(intent_name)
            .ok_or_else(|| format!("Intent '{}' not initialized", intent_name))?
            .clone();

        let state = intent
            .states
            .iter()
            .find(|s| s.name == current_state_name)
            .ok_or_else(|| format!("Current state '{}' not found", current_state_name))?;

        let mut output = HashMap::new();
        output.insert("intent".to_string(), JsonValue::String(intent_name.to_string()));
        output.insert("event".to_string(), JsonValue::String(event.to_string()));
        output.insert("from".to_string(), JsonValue::String(current_state_name.clone()));

        for trans in &state.transitions {
            if trans.event != event {
                continue;
            }

            // Evaluate guard
            if let Some(ref guard) = trans.guard {
                let guard_res = self.eval_expr(guard);
                if !guard_res.as_bool().unwrap_or(false) {
                    continue; // Guard failed, try next
                }
            }

            // Transaction Register Rollback Setup: copy current registers
            let mesh_backup = self.mesh.clone();

            // Pre-deduction pass with hardcoded 6.18% Platform Fee/Tariff
            let mut failed = false;
            let mut detail = String::new();

            for req in &trans.requires {
                let res_name = match req.resource_type {
                    0 => "mass",
                    1 => "energy",
                    2 => "entropy",
                    3 => "cycle",
                    _ => continue,
                };

                // Platform fee: multiply energy & cycle by 1.0618 (6.18% tariff)
                let multiplier = if req.resource_type == 1 || req.resource_type == 3 {
                    1.0618
                } else {
                    1.0
                };
                let deduct_value = req.value * multiplier;

                let available = *self.mesh.get(res_name).unwrap_or(&0.0);
                if deduct_value > available {
                    failed = true;
                    detail = format!(
                        "Insufficient {}: need {} {} (includes 6.18% tax), have {} {}. Transition FROZEN.",
                        res_name, deduct_value, req.unit, available, req.unit
                    );
                    break;
                } else {
                    // Provisional deduction
                    self.mesh.insert(res_name.to_string(), available - deduct_value);
                }
            }

            if failed {
                // Register Rollback
                self.mesh = mesh_backup;
                output.insert("to".to_string(), JsonValue::String(current_state_name.clone()));
                output.insert("status".to_string(), JsonValue::String("blocked".to_string()));
                output.insert("detail".to_string(), JsonValue::String(detail));
                return Ok(output);
            }

            // Check post-deduction constraints
            if let Some(violation_detail) = self.check_constraints(&intent.constraints) {
                // Register Rollback
                self.mesh = mesh_backup;
                output.insert("to".to_string(), JsonValue::String(current_state_name.clone()));
                output.insert("status".to_string(), JsonValue::String("blocked".to_string()));
                output.insert(
                    "detail".to_string(),
                    JsonValue::String(format!("Constraint violation: {}", violation_detail)),
                );
                return Ok(output);
            }

            // Commit transaction
            self.intent_states.insert(intent_name.to_string(), trans.target.clone());
            output.insert("to".to_string(), JsonValue::String(trans.target.clone()));
            output.insert("status".to_string(), JsonValue::String("transitioned".to_string()));
            output.insert("detail".to_string(), JsonValue::String("OK".to_string()));
            return Ok(output);
        }

        // No matching transition
        output.insert("to".to_string(), JsonValue::String(current_state_name.clone()));
        output.insert("status".to_string(), JsonValue::String("no_match".to_string()));
        output.insert(
            "detail".to_string(),
            JsonValue::String(format!(
                "No transition for event '{}' in state '{}'.",
                event, current_state_name
            )),
        );
        Ok(output)
    }
}

// ============================================================================
// 5. CLI RUNNER / REPL INTERFACE
// ============================================================================

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: logos_vm <smir.vsmb/json> [-e events.json] [-m mesh.json] [-c context.json] [--interactive]");
        process::exit(1);
    }

    let smir_path = &args[1];

    // Load SMIR (bytes)
    let mut smir_file = File::open(smir_path).unwrap_or_else(|e| {
        eprintln!("[LOGOS VM ERROR] SMIR file not found: {}. {}", smir_path, e);
        process::exit(1);
    });
    let mut smir_data = Vec::new();
    smir_file.read_to_end(&mut smir_data).unwrap();

    let smir = if smir_data.starts_with(b"VSMB") {
        decode_vsmb(&smir_data).unwrap_or_else(|e| {
            eprintln!("[LOGOS VM ERROR] Failed to decode VSMB: {}", e);
            process::exit(1);
        })
    } else {
        // Parse JSON fallback
        let s = std::str::from_utf8(&smir_data).unwrap();
        let json = parse_json(s).unwrap_or_else(|e| {
            eprintln!("[LOGOS VM ERROR] Failed to parse JSON SMIR: {}", e);
            process::exit(1);
        });
        decode_json_smir(&json).unwrap_or_else(|e| {
            eprintln!("[LOGOS VM ERROR] Failed to map JSON SMIR: {}", e);
            process::exit(1);
        })
    };

    // CLI option parsing
    let mut events_path = None;
    let mut mesh_path = None;
    let mut context_path = None;
    let mut interactive = false;

    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "-e" | "--events" => {
                events_path = Some(&args[i + 1]);
                i += 2;
            }
            "-m" | "--mesh" => {
                mesh_path = Some(&args[i + 1]);
                i += 2;
            }
            "-c" | "--context" => {
                context_path = Some(&args[i + 1]);
                i += 2;
            }
            "--interactive" => {
                interactive = true;
                i += 1;
            }
            _ => {
                eprintln!("Unknown argument: {}", args[i]);
                process::exit(1);
            }
        }
    }

    // Load mesh context
    let mut mesh_context = HashMap::new();
    if let Some(m_path) = mesh_path {
        let mut f = File::open(m_path).unwrap();
        let mut s = String::new();
        f.read_to_string(&mut s).unwrap();
        let json = parse_json(&s).unwrap();
        if let Some(obj) = json.as_object() {
            for (k, v) in obj {
                if let Some(n) = v.as_f64() {
                    mesh_context.insert(k.clone(), n);
                }
            }
        }
    } else {
        mesh_context.insert("mass".to_string(), 1e12);
        mesh_context.insert("energy".to_string(), 1e12);
        mesh_context.insert("entropy".to_string(), 1e12);
        mesh_context.insert("cycle".to_string(), 1e12);
    }

    // Load runtime context
    let mut runtime_ctx = HashMap::new();
    if let Some(c_path) = context_path {
        let mut f = File::open(c_path).unwrap();
        let mut s = String::new();
        f.read_to_string(&mut s).unwrap();
        let json = parse_json(&s).unwrap();
        if let Some(obj) = json.as_object() {
            for (k, v) in obj {
                runtime_ctx.insert(k.clone(), v.clone());
            }
        }
    }

    let mut vm = LogosVM::new(smir, mesh_context, runtime_ctx);

    if interactive {
        run_interactive(&mut vm);
    } else if let Some(ev_path) = events_path {
        run_batch(&mut vm, ev_path);
    } else {
        println!("[LOGOS VM] No events file or --interactive flag. Nothing to execute.");
    }
}

fn run_batch(vm: &mut LogosVM, events_path: &str) {
    let mut f = File::open(events_path).unwrap();
    let mut s = String::new();
    f.read_to_string(&mut s).unwrap();
    let json = parse_json(&s).unwrap();
    let events = json.as_array().unwrap();

    for (i, evt) in events.iter().enumerate() {
        let intent = evt.req_get("intent").unwrap().req_string().unwrap();
        let event = evt.req_get("event").unwrap().req_string().unwrap();

        if let Ok(ctx_val) = evt.req_get("context") {
            if let Ok(obj) = ctx_val.req_object() {
                for (k, v) in obj {
                    vm.runtime_ctx.insert(k.clone(), v.clone());
                }
            }
        }

        match vm.send_event(intent, event) {
            Ok(res) => {
                let status = res.get("status").unwrap().as_string().unwrap();
                let from = res.get("from").unwrap().as_string().unwrap();
                let to = res.get("to").unwrap().as_string().unwrap();
                let icon = if status == "transitioned" {
                    "+"
                } else if status == "blocked" {
                    "-"
                } else {
                    "?"
                };
                println!("[EVENT {}] {} {} --({})--> {} [{}]", i, icon, from, event, to, status);
                if status != "transitioned" {
                    println!("          Detail: {}", res.get("detail").unwrap().as_string().unwrap());
                }
            }
            Err(e) => {
                println!("[EVENT {}] ERROR: {}", i, e);
            }
        }
    }

    println!("\n[LOGOS VM] Execution complete.");
    println!("[LOGOS VM] Final mesh:");
    for (k, v) in &vm.mesh {
        println!("  {}: {:.4}", k, v);
    }
}

fn run_interactive(vm: &mut LogosVM) {
    println!("================================================================================");
    println!("                 LOGOS NATIVE RUST VM — INTERACTIVE EXECUTION");
    println!("================================================================================");
    println!("Commands: <intent> <event>   |   :state <intent>   |   :mesh   |   :quit");
    println!("================================================================================");

    let stdin = io::stdin();
    let mut stdout = io::stdout();

    loop {
        print!("\n[LOGOS VM] > ");
        stdout.flush().unwrap();
        let mut line = String::new();
        if stdin.read_line(&mut line).unwrap() == 0 {
            break;
        }
        let line = line.trim();
        if line.is_empty() {
            continue;
        }

        if line == ":quit" || line == ":exit" {
            println!("[LOGOS VM] Session terminated.");
            break;
        } else if line == ":mesh" {
            for (k, v) in &vm.mesh {
                println!("  {}: {:.4}", k, v);
            }
            continue;
        } else if line.startswith(":state ") {
            let intent = line[7..].trim();
            if let Some(state) = vm.intent_states.get(intent) {
                println!("[LOGOS VM] {} -> {}", intent, state);
            } else {
                println!("[LOGOS VM] Intent '{}' not found.", intent);
            }
            continue;
        }

        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() != 2 {
            println!("[LOGOS VM] Usage: <intent> <event>");
            continue;
        }

        let intent = parts[0];
        let event = parts[1];

        match vm.send_event(intent, event) {
            Ok(res) => {
                let status = res.get("status").unwrap().as_string().unwrap();
                let from = res.get("from").unwrap().as_string().unwrap();
                let to = res.get("to").unwrap().as_string().unwrap();
                let icon = if status == "transitioned" {
                    "+"
                } else if status == "blocked" {
                    "-"
                } else {
                    "?"
                };
                println!("  {} {} --({})--> {} [{}]", icon, from, event, to, status);
                if status != "transitioned" {
                    println!("     Detail: {}", res.get("detail").unwrap().as_string().unwrap());
                }
            }
            Err(e) => {
                println!("[LOGOS VM] ERROR: {}", e);
            }
        }
    }
}

trait StartsWithExt {
    fn startswith(&self, prefix: &str) -> bool;
}
impl StartsWithExt for str {
    fn startswith(&self, prefix: &str) -> bool {
        self.starts_with(prefix)
    }
}
