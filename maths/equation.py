import sys
from sympy import symbols, Eq, solve, simplify
from sympy.parsing.sympy_parser import parse_expr

x, y, z = symbols('x y z')

def parse_equation(eq_str):
    if '=' not in eq_str:
        raise ValueError(f"Invalid equation: {eq_str}")
    left, right = eq_str.split('=')
    return Eq(parse_expr(left.strip()), parse_expr(right.strip()))

def step_by_step_substitution(eq1, eq2):
    print(f"Original system:")
    print(f"1) {eq1}")
    print(f"2) {eq2}\n")

    # Intentar despejar una variable de la ecuación 1
    for var in [x, y, z]:
        try:
            isolated = solve(eq1, var)[0]
            print(f"Step 1: Solve Eq1 for {var}:")
            print(f"{var} = {isolated}\n")
            break
        except:
            continue
    else:
        print("❌ Couldn't isolate any variable from the first equation.")
        return

    # Sustituir en la segunda ecuación
    substituted_eq = eq2.subs(var, isolated)
    simplified_eq = simplify(substituted_eq)

    print(f"Step 2: Substitute into Eq2:")
    print(f"{eq2} → {substituted_eq}")
    print(f"Simplify: {simplified_eq}\n")

    # Resolver la ecuación simplificada
    remaining_vars = [v for v in [x, y, z] if v != var and simplified_eq.has(v)]
    if not remaining_vars:
        print("❌ No remaining variable to solve.")
        return

    other_var = remaining_vars[0]
    solution2 = solve(simplified_eq, other_var)[0]

    print(f"Step 3: Solve for {other_var}:")
    print(f"{other_var} = {solution2}\n")

    # Sustituir back para encontrar la otra variable
    final_val = isolated.subs(other_var, solution2)
    print(f"Step 4: Substitute back to find {var}:")
    print(f"{var} = {final_val}\n")

    # Resultado final
    print("✅ Final solution:")
    print(f"{var} = {final_val}")
    print(f"{other_var} = {solution2}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python step_solver.py \"eq1; eq2\"")
        sys.exit(1)

    input_str = sys.argv[1]
    try:
        eqs = input_str.split(';')
        if len(eqs) != 2:
            raise ValueError("You must provide exactly two equations separated by ';'.")

        eq1 = parse_equation(eqs[0])
        eq2 = parse_equation(eqs[1])
        step_by_step_substitution(eq1, eq2)

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    main()
