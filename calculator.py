import math
import re
import sys
from datetime import datetime

functions = {
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log10,
    'ln': math.log,
    'abs': abs
}

constants = {
    'pi': math.pi,
    'e': math.e
}

def format_number(n):
    if isinstance(n, float):
        n = round(n, 5)
        if n.is_integer():
            return str(int(n))
        return str(n)
    return str(n)

def safe_eval(expr):
    expr = expr.replace('^', '**')
    try:
        return eval(expr, {"__builtins__": None}, functions | constants | {'abs': abs})
    except Exception:
        return None

def simplify_expression(expr):
    expr = expr.replace(' ', '')
    steps = [expr]

    def resolve_simple(expr):
        func_pattern = re.compile(r'([a-z]+)\(([^()]+)\)')
        while re.search(func_pattern, expr):
            expr = re.sub(func_pattern, lambda m: format_number(safe_eval(f"{m.group(1)}({m.group(2)})")), expr)
            steps.append(expr)

        paren_pattern = re.compile(r'\(([^()]+)\)')
        while re.search(paren_pattern, expr):
            expr = re.sub(paren_pattern, lambda m: format_number(safe_eval(m.group(1))), expr)
            steps.append(expr)

        power_pattern = re.compile(r'(-?\d+(\.\d+)?)(\^)(-?\d+(\.\d+)?)')
        while re.search(power_pattern, expr):
            expr = re.sub(power_pattern, lambda m: format_number(safe_eval(f"{m.group(1)} ** {m.group(4)}")), expr, count=1)
            steps.append(expr)

        md_pattern = re.compile(r'(-?\d+(\.\d+)?)([*/])(-?\d+(\.\d+)?)')
        while re.search(md_pattern, expr):
            expr = re.sub(md_pattern, lambda m: format_number(safe_eval(f"{m.group(1)} {m.group(3)} {m.group(4)}")), expr, count=1)
            steps.append(expr)

        addsub_pattern = re.compile(r'(-?\d+(\.\d+)?)([+-])(-?\d+(\.\d+)?)')
        while re.search(addsub_pattern, expr):
            expr = re.sub(addsub_pattern, lambda m: format_number(safe_eval(f"{m.group(1)} {m.group(3)} {m.group(4)}")), expr, count=1)
            steps.append(expr)

        return expr

    resolve_simple(expr)
    return steps

def display_and_log(steps):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = [f"\n🧮 Step-by-step solution ({timestamp}):"]
    for i, step in enumerate(steps):
        output.append(("↓ " if i != 0 else "") + step)
    result = '\n'.join(output)

    # Print to console
    print(result)

    # Save to history
    with open("history.txt", "a", encoding="utf-8") as f:
        f.write(result + "\n\n")

def main():
    if len(sys.argv) > 1:
        expression = ' '.join(sys.argv[1:])
        steps = simplify_expression(expression)
        display_and_log(steps)
    else:
        while True:
            expression = input("\nEnter an expression (or 'exit'): ")
            if expression.lower() == 'exit':
                break
            steps = simplify_expression(expression)
            display_and_log(steps)

if __name__ == "__main__":
    main()
