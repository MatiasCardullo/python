from sympy import symbols, Eq, solve, simplify, expand, factor, diff, lambdify
import matplotlib.pyplot as plt
import numpy as np
import sys

x = symbols('x')

def show_help():
    print("""
Usage: python polynomial_solver.py "<polynomial>" [option] [value]

Options:
  eval [value]     - Evaluate the polynomial at a specific value of x.
  roots            - Solve for the roots of the polynomial.
  derivative       - Show the derivative of the polynomial.
  factor           - Factor the polynomial (if possible).
  expand           - Expand the polynomial.
  plot             - Plot the polynomial curve.
  help             - Show this help message.

Examples:
  python polynomial_solver.py "x**2 - 5*x + 6" roots
  python polynomial_solver.py "x**2 - 5*x + 6" eval 2
  python polynomial_solver.py "x*(x - 2)" expand
  python polynomial_solver.py "x**3 - 3*x" plot
""")


def plot_polynomial(poly):
    f = lambdify(x, poly, "numpy")
    x_vals = np.linspace(-10, 10, 400)
    y_vals = f(x_vals)

    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.plot(x_vals, y_vals, label=f"P(x) = {poly}")
    plt.title("Polynomial Graph")
    plt.xlabel("x")
    plt.ylabel("P(x)")
    plt.legend()
    plt.grid(True)
    plt.show()


def main():
    if len(sys.argv) < 3:
        show_help()
        return

    poly_input = sys.argv[1]
    option = sys.argv[2]

    try:
        poly = simplify(poly_input)
    except Exception as e:
        print(f"Invalid polynomial: {e}")
        return

    if option == "eval":
        if len(sys.argv) != 4:
            print("Missing value for evaluation.")
            return
        try:
            val = float(sys.argv[3])
            f = lambdify(x, poly, "math")
            result = f(val)
            print(f"P({val}) = {result}")
        except Exception as e:
            print(f"Error evaluating: {e}")

    elif option == "roots":
        result = solve(Eq(poly, 0), x)
        print(f"Roots: {result}")

    elif option == "derivative":
        deriv = diff(poly, x)
        print(f"Derivative: {deriv}")

    elif option == "factor":
        factored = factor(poly)
        print(f"Factored form: {factored}")

    elif option == "expand":
        expanded = expand(poly)
        print(f"Expanded form: {expanded}")

    elif option == "plot":
        plot_polynomial(poly)

    elif option == "help":
        show_help()

    else:
        print(f"Unknown option: {option}")
        show_help()


if __name__ == "__main__":
    main()
