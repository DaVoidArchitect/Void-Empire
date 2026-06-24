# Logos Language Specification (v3.0) — The Sovereign Universal Engine

Logos is a Turing-complete, thermodynamic, zero-dependency systems programming language. It is designed to drive the Void Omniverse and execute highly concurrent runtime tasks through wide vector pipelining and strict self-compilation bootstrapping.

## 1. Core Architectural Pillars

### 1.1 The Fractal Invariant
Logos implements native **Fractal Architecture**. Memory bounds and logic scaling are governed by self-similar properties. By using the `fractal` keyword, an `intent` or `struct` guarantees that its memory mapping and transition rules scale predictably from a single micro-chip (VLEN=32) up to a macro-civilizational platform without architectural fragmentation.

### 1.2 Thermodynamic Linear Memory Slices
Logos abandons traditional garbage collection (GC) and compile-time borrow checking. Instead:
- Memory is managed via **zero-copy, contiguous linear page slices**.
- Allocation (`alloc`) and deallocation (`free`) are deterministic and linear.
- **The Treasury Fee**: Every execution block automatically calculates and splits a fixed 6.18% platform utility fee, routed directly to the native `treasury.logos` reserve module.

### 1.3 Right-to-Left (RTL) Evaluation Pipeline
Logos enforces absolute **Right-to-Left (RTL) token evaluation** for expressions (similar to APL/BQN).
- Expressions parse from the end of the line backward.
- This structural design guarantees that high-level abstractions map directly to sequential hardware execution registers without relying on intermediary execution stacking.
- Example: `A * B + C` evaluates as `A * (B + C)`.

---

## 2. Grammar & Advanced Typing

Logos utilizes a Multi-Paradigm Typing System incorporating linear types and dependent typing. It features zero-cost compile-time static reflection through the `^^T` operator.

### 2.1 Core Glyph Operations
The grammar natively interprets specialized Unicode glyphs to handle complex domain operations seamlessly:
- **`◰` (Spatial Layout Matrix)**: Frames coordinate boundaries and structures multi-dimensional canvas views for volumetric rendering.
- **`⨀` (Tensor Composition)**: Executes multi-lane vector array multiplication mapping logic directly to 2048-bit wide hardware lanes (512 individual 32-bit streams).
- **`⊸` (Polymorphic Mutation)**: Binds independent execution matrices directly to incoming raw intent token streams.

### 2.2 Grammar Definition (EBNF)

```ebnf
Program         ::= Import* (StructDef | IntentDef | FuncDef)*

Import          ::= 'import' StringLiteral ';'

StructDef       ::= 'fractal'? 'struct' Identifier '{' FieldDef* '}'
FieldDef        ::= Identifier ':' Type ';'

Type            ::= Identifier | '^' Type | '[' Type ';' Number ']' | 'fn(' ParamList ')' '->' Type
Reflection      ::= '^^' Type

IntentDef       ::= 'fractal'? 'intent' Identifier '{' IntentBody* '}'
IntentBody      ::= RequireBlock | StateDef | FuncDef

RequireBlock    ::= 'require' '{' ResourceDecl* '}'
ResourceDecl    ::= ('mass' | 'energy' | 'entropy' | 'cycle') ':' Number Unit? ';'

StateDef        ::= 'state' Identifier '{' Transition* '}'
Transition      ::= 'on' Identifier '->' Identifier ';'

FuncDef         ::= 'fn' Identifier '(' ParamList? ')' ('->' Type)? Contract* Block
ParamList       ::= Param (',' Param)*
Param           ::= 'mut'? Identifier ':' Type
Contract        ::= ('pre' | 'post') '{' Expression* '}'

Block           ::= '{' Statement* '}'
Statement       ::= LetStmt | ExprStmt | IfStmt | MatchStmt | LoopStmt | ReturnStmt
LetStmt         ::= 'let' 'mut'? Identifier (':' Type)? '=' Expression ';'
MatchStmt       ::= 'match' Expression '{' MatchArm* '}'
MatchArm        ::= Identifier '->' Block

# Expressions parse strictly Right-To-Left. 
Expression      ::= Term ( ('⨀' | '⊸' | '◰' | '+' | '-' | '*' | '/' | '==' | '=') Term )*
Term            ::= Identifier | Number | StringLiteral | Call | Reflection | '(' Expression ')'
```

---

## 3. Strict Execution Validation

### 3.1 Pre and Post Thermodynamic Contracts
All function definitions must be flanked by mandatory compile-time `pre` and `post` validation contracts.
- **`pre`**: Asserts the initial memory and thermal constraints before execution.
- **`post`**: Verifies the resulting architectural state.
- **Halting Invariant**: The compiler natively refuses to compile the binary if the static analyzer cannot mathematically guarantee physical execution safety and thermal bounds before invocation.

---

## 4. The Bootstrapping Pipeline (L_n -> L_n+1)

Logos implements a rigorous 3-stage self-compilation matrix:
1. **Stage 1 (logosc_v3.exe / python)**: The initial interpreter capable of parsing the complex RTL grammar.
2. **Stage 2 (logosc.logos)**: The universal compiler logic written in Pure Logos. Stage 1 compiles Stage 2 down to the Structural Machine Intermediate Representation (SMIR).
3. **Stage 3 (Native Emission)**: The SMIR is transpiled directly to AOT binaries, producing an unassailable, natively deterministic standalone compiler capable of building itself recursively.
