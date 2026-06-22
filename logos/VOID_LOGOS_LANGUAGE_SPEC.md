# Logos Language Specification (v1.0)
## Project Void — Phase 1: Syntax, Grammar, & Thermodynamic Compiler

Logos is an intent-driven, resource-constrained programming language designed for Project Void. Instead of traditional procedural instructions, a Logos file describes a set of **Intents** that compile into immutable state machines. These state machines represent resource needs and state flows that are physically constrained by thermodynamic reality.

---

## 1. Core Principles

1. **Intent-Driven:** Programs are declarations of desired states and resource needs.
2. **Thermodynamic Law:** Physical reality is the absolute boundary of compilation. An intent cannot compile if the available resource budget in the local mesh network is insufficient.
3. **Dark Logic Aesthetic:** Structural, minimalist syntax. Telemetry diagnostics are designed as high-contrast machine readouts.

---

## 2. Grammar (EBNF)

```ebnf
Program         ::= IntentDef*
IntentDef       ::= 'intent' Identifier '{' IntentBody* '}'
IntentBody      ::= HeaderDef | RequireBlock | StateDef
HeaderDef       ::= Identifier ':' (StringLiteral | Number | Identifier)
RequireBlock    ::= 'require' '{' Constraint* '}'
Constraint      ::= ResourceType ':' Operator? Number Unit
ResourceType    ::= 'mass' | 'energy' | 'entropy' | 'cycle'
Operator        ::= '<' | '>' | '<=' | '>=' | '=='
Unit            ::= Identifier | '%'
StateDef        ::= 'state' Identifier '{' Transition* '}'
Transition      ::= 'on' Identifier '->' Identifier
Identifier      ::= [a-zA-Z_][a-zA-Z0-9_]*
StringLiteral   ::= '"' [^"\\]* '"'
Number          ::= [0-9]+ ('.' [0-9]+)?
```

---

## 3. Thermodynamic Primitives & Normalization

Logos compiles physical constraints at the base layer. Primitives are normalized into SI standard units internally to guarantee check precision:

### A. Primitives & Normalization Mapping

| Primitive | Description | Source Units | Normalized Unit (Internal) |
| :--- | :--- | :--- | :--- |
| **`mass`** | Physical matter weight | `kg` (kilograms), `g` (grams), `mg` (milligrams), `t` (metric tons) | **Kilograms (kg)** |
| **`energy`** | Thermal/electrical work | `J` (Joules), `kJ` (kilojoules), `Wh` (Watt-hours), `kWh` (kilowatt-hours), `MWh` (megawatt-hours) | **Joules (J)** or **Kilowatt-hours (kWh)** |
| **`entropy`** | Mechanical wear/decay limit | `%` or decimal fraction (e.g., `0.05` or `5%`) | **Decimal Fraction (0.0 to 1.0)** |
| **`cycle`** | Material recycling loop efficiency | `%` or decimal fraction (e.g., `0.95` or `95%`) | **Decimal Fraction (0.0 to 1.0)** |

### B. Standard Normalization Formulas
- 1 g = 10^-3 kg
- 1 mg = 10^-6 kg
- 1 t = 10^3 kg
- 1 Wh = 3600 J
- 1 kWh = 3.6 * 10^6 J
- 1 MWh = 3.6 * 10^9 J
- 1 kJ = 1000 J

---

## 4. Compilation Constraints

When the compiler parses the AST, it evaluates the `require` block of each intent against a `MeshContext` dictionary representing verified local resource capacities:

```python
mesh_context = {
    "mass": 50.0,          # kg
    "energy": 7200000.0,   # Joules (2.0 kWh)
    "entropy": 0.02,       # Current mesh decay factor
    "cycle": 0.98          # Current mesh recycling rate
}
```

Compilation **halts** with a `ThermodynamicConstraintError` if:
1. `required_mass > available_mass`
2. `required_energy > available_energy`
3. `required_entropy < current_mesh_entropy` (mesh wear is too high to guarantee state execution)
4. `required_cycle > current_mesh_recycling_rate` (mesh cannot guarantee target material loop efficiency)

---

## 5. Tactical Telemetry Diagnostics

Generic Python stack traces are suppressed for thermodynamic errors. Telemetry errors print high-contrast, machine-like console telemetry blocks:

```text
================================================================================
                    LOGOS COMPILER SYSTEM ERROR TELEMETRY
================================================================================
LINE EXCEPTION: Line 8
CONSTRAINT TARGET: energy
UNITS FAILURE: Requested energy exceeds verified available capacity.

[REQUIRED AMOUNT]:  15000000.00 J (4.17 kWh)
[VERIFIED MESH]:    7200000.00 J (2.00 kWh)
[DEFICIT]:          7800000.00 J (2.17 kWh)

================================================================================
[COMPILATION TERMINATED: PHYSICAL LIMIT EXCEEDED]
================================================================================
```
