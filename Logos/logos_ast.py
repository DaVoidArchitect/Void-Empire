from typing import Any, List, Dict, Optional, Union

class ASTNode:
    pass

class ExprNode(ASTNode):
    pass

class StmtNode(ASTNode):
    pass

class LiteralNode(ExprNode):
    def __init__(self, value: Any, type_: str, line: int):
        self.value = value
        self.type = type_
        self.line = line
    def __repr__(self) -> str: return f"LiteralNode({self.type}: {self.value})"

class BinaryOpNode(ExprNode):
    def __init__(self, left: ExprNode, op: str, right: ExprNode, line: int):
        self.left = left
        self.op = op
        self.right = right
        self.line = line
    def __repr__(self) -> str: return f"BinaryOpNode({self.op})"

class UnaryOpNode(ExprNode):
    def __init__(self, op: str, expr: ExprNode, line: int):
        self.op = op
        self.expr = expr
        self.line = line
    def __repr__(self) -> str: return f"UnaryOpNode({self.op})"

class CallNode(ExprNode):
    def __init__(self, callee: ExprNode, args: List[ExprNode], line: int):
        self.callee = callee
        self.args = args
        self.line = line
    def __repr__(self) -> str: return f"CallNode()"

class MemberAccessNode(ExprNode):
    def __init__(self, obj: ExprNode, member: str, line: int):
        self.obj = obj
        self.member = member
        self.line = line
    def __repr__(self) -> str: return f"MemberAccessNode({self.member})"

class IndexAccessNode(ExprNode):
    def __init__(self, obj: ExprNode, index: ExprNode, line: int):
        self.obj = obj
        self.index = index
        self.line = line
    def __repr__(self) -> str: return f"IndexAccessNode()"

class BlockNode(StmtNode):
    def __init__(self, statements: List[StmtNode], line: int):
        self.statements = statements
        self.line = line
    def __repr__(self) -> str: return f"BlockNode()"

class ExprStmtNode(StmtNode):
    def __init__(self, expr: ExprNode, line: int):
        self.expr = expr
        self.line = line
    def __repr__(self) -> str: return f"ExprStmtNode()"

class LetStmtNode(StmtNode):
    def __init__(self, name: str, is_mut: bool, type_ann: Optional[str], value: ExprNode, line: int):
        self.name = name
        self.is_mut = is_mut
        self.type_ann = type_ann
        self.value = value
        self.line = line
    def __repr__(self) -> str: return f"LetStmtNode({self.name})"

class IfStmtNode(StmtNode):
    def __init__(self, condition: ExprNode, then_block: BlockNode, else_block: Optional[Union[BlockNode, 'IfStmtNode']], line: int):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block
        self.line = line
    def __repr__(self) -> str: return f"IfStmtNode()"

class MatchArmNode(ASTNode):
    def __init__(self, pattern: str, block: BlockNode, line: int):
        self.pattern = pattern
        self.block = block
        self.line = line
    def __repr__(self) -> str: return f"MatchArmNode({self.pattern})"

class MatchStmtNode(StmtNode):
    def __init__(self, expr: ExprNode, arms: List[MatchArmNode], line: int):
        self.expr = expr
        self.arms = arms
        self.line = line
    def __repr__(self) -> str: return f"MatchStmtNode()"

class LoopStmtNode(StmtNode):
    def __init__(self, condition: Optional[ExprNode], body: BlockNode, line: int):
        self.condition = condition
        self.body = body
        self.line = line
    def __repr__(self) -> str: return f"LoopStmtNode()"

class ReturnStmtNode(StmtNode):
    def __init__(self, value: Optional[ExprNode], line: int):
        self.value = value
        self.line = line
    def __repr__(self) -> str: return f"ReturnStmtNode()"

class BreakStmtNode(StmtNode):
    def __init__(self, line: int):
        self.line = line
    def __repr__(self) -> str: return f"BreakStmtNode()"

class ContinueStmtNode(StmtNode):
    def __init__(self, line: int):
        self.line = line
    def __repr__(self) -> str: return f"ContinueStmtNode()"

class ImportNode(ASTNode):
    def __init__(self, path: str, line: int):
        self.path = path
        self.line = line
    def __repr__(self) -> str: return f'ImportNode("{self.path}")'

class FieldDefNode(ASTNode):
    def __init__(self, name: str, type_ann: str, line: int):
        self.name = name
        self.type_ann = type_ann
        self.line = line
    def __repr__(self) -> str: return f"FieldDefNode({self.name}: {self.type_ann})"

class StructDefNode(ASTNode):
    def __init__(self, name: str, fields: List[FieldDefNode], is_fractal: bool, line: int):
        self.name = name
        self.fields = fields
        self.is_fractal = is_fractal
        self.line = line
    def __repr__(self) -> str: return f"StructDefNode({self.name}, fractal={self.is_fractal})"

class EnumDefNode(ASTNode):
    def __init__(self, name: str, variants: List[str], line: int):
        self.name = name
        self.variants = variants
        self.line = line
    def __repr__(self) -> str: return f"EnumDefNode({self.name})"

class ResourceDeclNode(ASTNode):
    def __init__(self, resource: str, value: float, unit: str, line: int):
        self.resource = resource
        self.value = value
        self.unit = unit
        self.line = line
    def __repr__(self) -> str: return f"ResourceDeclNode({self.resource})"

class RequireNode(ASTNode):
    def __init__(self, requirements: List[ResourceDeclNode]):
        self.requirements = requirements
    def __repr__(self) -> str: return f"RequireNode()"

class ConstraintNode(ASTNode):
    def __init__(self, resource: str, operator: str, value: float, unit: str, line: int):
        self.resource = resource
        self.operator = operator
        self.value = value
        self.unit = unit
        self.line = line
    def __repr__(self) -> str: return f"ConstraintNode()"

class ConstraintBlockNode(ASTNode):
    def __init__(self, constraints: List[ConstraintNode]):
        self.constraints = constraints
    def __repr__(self) -> str: return f"ConstraintBlockNode()"

class GuardNode(ASTNode):
    def __init__(self, expr: ExprNode):
        self.expr = expr
    def __repr__(self) -> str: return f"GuardNode()"

class TransitionNode(ASTNode):
    def __init__(self, event: str, target: str, guard: Optional[GuardNode] = None, transition_requires: Optional[List[ResourceDeclNode]] = None, line: int = -1):
        self.event = event
        self.target = target
        self.guard = guard
        self.transition_requires = transition_requires if transition_requires is not None else []
        self.line = line
    def __repr__(self) -> str: return f"TransitionNode({self.event}->{self.target})"

class StateNode(ASTNode):
    def __init__(self, name: str, transitions: List[TransitionNode]):
        self.name = name
        self.transitions = transitions
    def __repr__(self) -> str: return f"StateNode({self.name})"

class KeyValNode(ASTNode):
    def __init__(self, key: str, value: ExprNode, line: int):
        self.key = key
        self.value = value
        self.line = line
    def __repr__(self) -> str: return f"KeyValNode({self.key})"

class SpatialBlockNode(ASTNode):
    def __init__(self, name: str, properties: List[KeyValNode], line: int):
        self.name = name
        self.properties = properties
        self.line = line
    def __repr__(self) -> str: return f"SpatialBlockNode({self.name})"

class SocketBlockNode(ASTNode):
    def __init__(self, name: str, properties: List[KeyValNode], line: int):
        self.name = name
        self.properties = properties
        self.line = line
    def __repr__(self) -> str: return f"SocketBlockNode({self.name})"

class PreBlockNode(ASTNode):
    def __init__(self, exprs: List[ExprNode], line: int):
        self.exprs = exprs
        self.line = line
    def __repr__(self) -> str: return f"PreBlockNode()"

class PostBlockNode(ASTNode):
    def __init__(self, exprs: List[ExprNode], line: int):
        self.exprs = exprs
        self.line = line
    def __repr__(self) -> str: return f"PostBlockNode()"

class FuncDefNode(ASTNode):
    def __init__(self, name: str, params: List[Dict[str, Any]], return_type: Optional[str], pre_contracts: List[PreBlockNode], post_contracts: List[PostBlockNode], body: BlockNode, line: int):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.pre_contracts = pre_contracts
        self.post_contracts = post_contracts
        self.body = body
        self.line = line
    def __repr__(self) -> str: return f"FuncDefNode({self.name})"

class IntentNode(ASTNode):
    def __init__(self, name: str, is_fractal: bool, headers: Dict[str, Any], require_block: Optional[RequireNode], constraint_block: Optional[ConstraintBlockNode], states: List[StateNode], spatial_blocks: List[SpatialBlockNode], socket_blocks: List[SocketBlockNode], functions: List[FuncDefNode]):
        self.name = name
        self.is_fractal = is_fractal
        self.headers = headers
        self.require_block = require_block
        self.constraint_block = constraint_block
        self.states = states
        self.spatial_blocks = spatial_blocks
        self.socket_blocks = socket_blocks
        self.functions = functions
    def __repr__(self) -> str: return f"IntentNode({self.name}, fractal={self.is_fractal})"

class ProgramNode(ASTNode):
    def __init__(self, imports: List[ImportNode], items: List[ASTNode]):
        self.imports = imports
        self.items = items
    def __repr__(self) -> str: return f"ProgramNode(imports={len(self.imports)}, items={len(self.items)})"
