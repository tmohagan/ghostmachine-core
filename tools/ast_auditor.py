import ast
import logging

logger = logging.getLogger(__name__)

class SecurityAuditVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations = []
        self.dangerous_names = {"system", "run", "Popen", "eval", "exec", "__import__"}

    def visit_ExceptHandler(self, node):
        # Reject bare 'except:' blocks as per policy
        if node.type is None:
            self.violations.append(f"Line {node.lineno}: Bare except block detected. Explicit exception typing required.")
        self.generic_visit(node)

    def visit_Call(self, node):
        # Block dangerous primitives
        func_name = None
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            
        if func_name in self.dangerous_names:
            self.violations.append(f"Line {node.lineno}: Dangerous call to '{func_name}' detected.")
            
        self.generic_visit(node)

def validate_patch_syntax(source_code: str) -> list[str]:
    """Parses physical text into an AST to verify security guardrails."""
    logger.info("Allocating RAM to parse Abstract Syntax Tree...")
    try:
        tree = ast.parse(source_code)
        visitor = SecurityAuditVisitor()
        visitor.visit(tree)
        return visitor.violations
    except SyntaxError as e:
        return [f"Fatal Syntax Error at line {e.lineno}: {e.msg}"]
