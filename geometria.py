import sys
import math
from calculator import solve_expression
from datetime import datetime

HISTORY_PATH = "history.txt"

# --------------------- Calculation functions ---------------------

def area(shape, *args):
    result = None
    steps = ""

    if shape == "circle":
        r = float(args[0])
        result = math.pi * r ** 2
        steps = f"Circle area: π × r² = π × {r}² = {result:.5f}"

    elif shape == "rectangle":
        b, h = map(float, args)
        result = b * h
        steps = f"Rectangle area: base × height = {b} × {h} = {result:.5f}"

    elif shape == "triangle":
        a, h = map(float, args)
        result = (a * h) / 2
        steps = f"Triangle area: (base × height) / 2 = ({a} × {h}) / 2 = {result:.5f}"

    elif shape == "regular_polygon":
        n = int(args[0])
        l = float(args[1])
        perimeter = n * l
        apothem_expr = f"{l} / (2 * tan(pi / {n}))"
        apothem = solve_with_calculator(apothem_expr)
        try:
            apothem_val = float(apothem.split('=')[-1].strip())
        except:
            apothem_val = 0
        result = (perimeter * apothem_val) / 2
        steps = (f"Regular polygon area (n={n}, l={l}):\n"
                 f"Step 1: perimeter = n × l = {n} × {l} = {perimeter:.5f}\n"
                 f"Step 2: apothem = {apothem_expr} = {apothem}\n"
                 f"Step 3: area = (perimeter × apothem) / 2 = ({perimeter:.5f} × {apothem_val:.5f}) / 2 = {result:.5f}")

    if result is not None:
        log_history("area", shape, steps)
        print(steps)
        return result


def perimeter(shape, *args):
    result = None
    steps = ""

    if shape == "circle":
        r = float(args[0])
        result = 2 * math.pi * r
        steps = f"Circle perimeter: 2π × r = 2π × {r} = {result:.5f}"

    elif shape == "rectangle":
        b, h = map(float, args)
        result = 2 * (b + h)
        steps = f"Rectangle perimeter: 2 × (b + h) = 2 × ({b} + {h}) = {result:.5f}"

    elif shape == "triangle":
        a, b, c = map(float, args)
        result = a + b + c
        steps = f"Triangle perimeter: a + b + c = {a} + {b} + {c} = {result:.5f}"

    elif shape == "regular_polygon":
        n = int(args[0])
        l = float(args[1])
        result = n * l
        steps = f"Regular polygon perimeter: n × l = {n} × {l} = {result:.5f}"

    if result is not None:
        log_history("perimeter", shape, steps)
        print(steps)
        return result


def volume(shape, *args):
    result = None
    steps = ""

    if shape == "cube":
        l = float(args[0])
        result = l ** 3
        steps = f"Cube volume: l³ = {l}³ = {result:.5f}"

    elif shape == "cylinder":
        r, h = map(float, args)
        result = math.pi * r ** 2 * h
        steps = f"Cylinder volume: π × r² × h = π × {r}² × {h} = {result:.5f}"

    elif shape == "sphere":
        r = float(args[0])
        result = (4/3) * math.pi * r ** 3
        steps = f"Sphere volume: (4/3)π × r³ = (4/3)π × {r}³ = {result:.5f}"

    elif shape == "dodecahedron":
        l = float(args[0])
        expr = f"((15 + 7 * sqrt(5)) / 4) * ({l} ** 3)"
        steps = f"Dodecahedron volume expression: {expr}"
        result = solve_with_calculator(expr)
        steps += f"\nResult: {result}"

    elif shape == "icosahedron":
        l = float(args[0])
        expr = f"(5 * (3 + sqrt(5)) / 12) * ({l} ** 3)"
        steps = f"Icosahedron volume expression: {expr}"
        result = solve_with_calculator(expr)
        steps += f"\nResult: {result}"

    if result is not None:
        log_history("volume", shape, steps)
        print(steps)
        return result

# --------------------- History log ---------------------

def log_history(kind, shape, text):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {kind}({shape})\n{textwrap(text)}\n\n")

def textwrap(text):
    return "\n".join([line.strip() for line in text.strip().splitlines()])


# --------------------- Expression solver ---------------------

def solve_with_calculator(expression):
    try:
        result_value = solve_expression(expression, log=True)
        return f"{expression} = {result_value}"
    except Exception as e:
        print(f"[solve_with_calculator error] {e}")
        return "Error: could not resolve expression."

# --------------------- Console input handler ---------------------

def parse_args():
    if len(sys.argv) < 2:
        return

    command = sys.argv[1].lower()

    if command == "help":
        print("""
Usage: python geometry_calculator.py [operation] [shape] [values...]

Operations:
  area         Calculate area of a shape
  perimeter    Calculate perimeter of a shape
  volume       Calculate volume of a 3D shape

Examples:
  python geometry_calculator.py area circle 5
  python geometry_calculator.py perimeter triangle 3 4 5
  python geometry_calculator.py volume icosahedron 2
""")
        return

    if len(sys.argv) < 4:
        print("Insufficient arguments. Use 'help' for usage.")
        return

    shape = sys.argv[2].lower()
    values = sys.argv[3:]

    try:
        func = {"area": area, "perimeter": perimeter, "volume": volume}.get(command)
        if func:
            func(shape, *values)
        else:
            print(f"Unknown operation '{command}'. Use 'help' for usage.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    parse_args()
