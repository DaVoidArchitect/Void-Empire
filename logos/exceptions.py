"""
Logos Exception Hierarchy — Tactical Error Telemetry

Every exception produces high-contrast diagnostic output designed for
the "Dark Logic" paradigm: deep black backdrops with amber/gold readouts.
All errors halt compilation or execution and report exact deficits.
"""


class LogosCompilerError(Exception):
    """Base exception class for Logos compiler errors."""
    pass


class LogosSyntaxError(LogosCompilerError):
    """Raised when there is a lexer or parser syntax error in the Logos code."""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, Column {column}: {message}")


class ThermodynamicConstraintError(LogosCompilerError):
    """Raised when available mesh resources are insufficient to compile an intent."""
    def __init__(
        self,
        constraint_type: str,
        required_value: float,
        required_unit: str,
        available_value: float,
        available_unit: str,
        line: int,
        details: str = ""
    ):
        self.constraint_type = constraint_type
        self.required_value = required_value
        self.required_unit = required_unit
        self.available_value = available_value
        self.available_unit = available_unit
        self.line = line
        self.details = details

        deficit = max(0.0, required_value - available_value)

        # Helper formatting for energy (J <-> kWh) and mass (kg <-> g)
        required_display = f"{required_value:.4f} {required_unit}"
        available_display = f"{available_value:.4f} {available_unit}"
        deficit_display = f"{deficit:.4f} {required_unit}"

        if required_unit == "J" and required_value >= 1000:
            kwh_val = required_value / 3600000.0
            required_display += f" ({kwh_val:.4f} kWh)"
        elif required_unit == "kWh":
            j_val = required_value * 3600000.0
            required_display += f" ({j_val:.2f} J)"

        if available_unit == "J" and available_value >= 1000:
            kwh_val = available_value / 3600000.0
            available_display += f" ({kwh_val:.4f} kWh)"
        elif available_unit == "kWh":
            j_val = available_value * 3600000.0
            available_display += f" ({j_val:.2f} J)"

        if required_unit == "J" and deficit >= 1000:
            kwh_val = deficit / 3600000.0
            deficit_display += f" ({kwh_val:.4f} kWh)"
        elif required_unit == "kWh":
            j_val = deficit * 3600000.0
            deficit_display += f" ({j_val:.2f} J)"

        # Build tactical report
        report = (
            "\n"
            "================================================================================\n"
            "                    LOGOS COMPILER SYSTEM ERROR TELEMETRY\n"
            "================================================================================\n"
            f"LINE EXCEPTION: Line {line}\n"
            f"CONSTRAINT TARGET: {constraint_type}\n"
            "UNITS FAILURE: Requested resource exceeds verified available capacity.\n"
        )
        if details:
            report += f"DIAGNOSTIC DETAIL: {details}\n"

        report += (
            "\n"
            f"[REQUIRED AMOUNT]:  {required_display}\n"
            f"[VERIFIED MESH]:    {available_display}\n"
            f"[DEFICIT]:          {deficit_display}\n"
            "================================================================================\n"
            "[COMPILATION TERMINATED: PHYSICAL LIMIT EXCEEDED]\n"
            "================================================================================"
        )
        super().__init__(report)


class CyclicImportError(LogosCompilerError):
    """Raised when a cyclic import dependency is detected in the import DAG."""
    def __init__(self, path: str, chain: list[str] | None = None):
        self.path = path
        self.chain = chain or []
        chain_str = " -> ".join(self.chain + [path]) if self.chain else path
        report = (
            "\n"
            "================================================================================\n"
            "                    LOGOS COMPILER SYSTEM ERROR TELEMETRY\n"
            "================================================================================\n"
            f"IMPORT CYCLE DETECTED\n"
            f"DEPENDENCY CHAIN: {chain_str}\n"
            "================================================================================\n"
            "[COMPILATION TERMINATED: CYCLIC IMPORT]\n"
            "================================================================================"
        )
        super().__init__(report)


class LogosRuntimeError(Exception):
    """Raised when there is an execution error in the Logos VM."""
    def __init__(self, message: str, line: int = -1):
        self.message = message
        self.line = line
        super().__init__(f"Runtime Error (Line {line}): {message}" if line >= 0 else f"Runtime Error: {message}")


class TransitionFrozenError(LogosRuntimeError):
    """Raised when an atomic transition cannot proceed due to resource deficit."""
    def __init__(self, event: str, state: str, resource: str, deficit: float, unit: str):
        self.event = event
        self.state = state
        self.resource = resource
        self.deficit = deficit
        self.unit = unit
        report = (
            "\n"
            "================================================================================\n"
            "                    LOGOS VM TRANSITION FROZEN TELEMETRY\n"
            "================================================================================\n"
            f"STATE: {state}\n"
            f"EVENT: {event}\n"
            f"RESOURCE: {resource}\n"
            f"DEFICIT: {deficit:.4f} {unit}\n"
            "RESOLUTION: Transition FROZEN. No resources deducted. State unchanged.\n"
            "================================================================================"
        )
        super().__init__(report)
