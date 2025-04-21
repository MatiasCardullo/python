import sys
import math
from datetime import datetime

HISTORIAL_PATH = "historial.txt"

# --------------------- Conversión de argumentos ---------------------

def convertir_argumentos(args, tipos):
    convertidos = []
    for arg, tipo in zip(args, tipos):
        try:
            if tipo == int:
                convertidos.append(int(arg))
            else:
                convertidos.append(float(arg))
        except ValueError:
            raise ValueError(f"El valor '{arg}' no se puede convertir a {tipo.__name__}")
    return convertidos

# --------------------- Funciones de cálculo ---------------------

def area(figura, args):
    if figura == "circulo":
        r, = convertir_argumentos(args, [float])
        resultado = math.pi * r ** 2
        pasos = f"Área del círculo: π × {r}² = {resultado:.5f}"

    elif figura == "rectangulo":
        b, h = convertir_argumentos(args, [float, float])
        resultado = b * h
        pasos = f"Área del rectángulo: {b} × {h} = {resultado:.5f}"

    elif figura == "triangulo":
        a, h = convertir_argumentos(args, [float, float])
        resultado = (a * h) / 2
        pasos = f"Área del triángulo: ({a} × {h}) / 2 = {resultado:.5f}"

    elif figura == "poligono_regular":
        n, l = convertir_argumentos(args, [int, float])
        perimetro = n * l
        apotema = l / (2 * math.tan(math.pi / n))
        resultado = (perimetro * apotema) / 2
        pasos = (f"Área del polígono regular:\n"
                 f"  perímetro = {n} × {l} = {perimetro:.5f}\n"
                 f"  apotema = {l} / (2 × tan(π / {n})) = {apotema:.5f}\n"
                 f"  área = ({perimetro:.5f} × {apotema:.5f}) / 2 = {resultado:.5f}")
    else:
        raise ValueError(f"Figura desconocida: '{figura}'")

    registrar_en_historial("area", figura, pasos)
    print(pasos)
    return resultado


def per(figura, args):
    if figura == "circulo":
        r, = convertir_argumentos(args, [float])
        resultado = 2 * math.pi * r
        pasos = f"Perímetro del círculo: 2π × {r} = {resultado:.5f}"

    elif figura == "rectangulo":
        b, h = convertir_argumentos(args, [float, float])
        resultado = 2 * (b + h)
        pasos = f"Perímetro del rectángulo: 2 × ({b} + {h}) = {resultado:.5f}"

    elif figura == "triangulo":
        a, b, c = convertir_argumentos(args, [float, float, float])
        resultado = a + b + c
        pasos = f"Perímetro del triángulo: {a} + {b} + {c} = {resultado:.5f}"

    elif figura == "poligono_regular":
        n, l = convertir_argumentos(args, [int, float])
        resultado = n * l
        pasos = f"Perímetro del polígono regular: {n} × {l} = {resultado:.5f}"
    else:
        raise ValueError(f"Figura desconocida: '{figura}'")

    registrar_en_historial("per", figura, pasos)
    print(pasos)
    return resultado


def vol(figura, args):
    if figura == "cubo":
        l, = convertir_argumentos(args, [float])
        resultado = l ** 3
        pasos = f"Volumen del cubo: {l}³ = {resultado:.5f}"

    elif figura == "cilindro":
        r, h = convertir_argumentos(args, [float, float])
        resultado = math.pi * r ** 2 * h
        pasos = f"Volumen del cilindro: π × {r}² × {h} = {resultado:.5f}"

    elif figura == "esfera":
        r, = convertir_argumentos(args, [float])
        resultado = (4/3) * math.pi * r ** 3
        pasos = f"Volumen de la esfera: (4/3)π × {r}³ = {resultado:.5f}"

    elif figura == "dodecaedro":
        l, = convertir_argumentos(args, [float])
        resultado = ((15 + 7 * math.sqrt(5)) / 4) * (l ** 3)
        pasos = f"Volumen del dodecaedro: ((15 + 7√5)/4) × {l}³ = {resultado:.5f}"

    elif figura == "icosaedro":
        l, = convertir_argumentos(args, [float])
        resultado = (5 * (3 + math.sqrt(5)) / 12) * (l ** 3)
        pasos = f"Volumen del icosaedro: (5(3 + √5)/12) × {l}³ = {resultado:.5f}"
    else:
        raise ValueError(f"Figura desconocida: '{figura}'")

    registrar_en_historial("vol", figura, pasos)
    print(pasos)
    return resultado

# --------------------- Registro e historial ---------------------

def registrar_en_historial(tipo, figura, texto):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORIAL_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {tipo}({figura})\n{textwrap(texto)}\n\n")

def textwrap(text):
    return "\n".join([line.strip() for line in text.strip().splitlines()])

# --------------------- Ayuda e interpretación ---------------------

def mostrar_ayuda():
    print("""
Uso: python calculadora_geometria.py <operacion> <figura> <valores...>

Operaciones disponibles:
  area    - Cálculo de áreas
  per     - Cálculo de perímetros
  vol     - Cálculo de volúmenes

Figuras válidas:
  Área: "circulo", "rectangulo", "triangulo", "poligono_regular"
  Perímetro: igual a área
  Volumen: "cubo", "cilindro", "esfera", "dodecaedro", "icosaedro"

Ejemplos:
  python calculadora_geometria.py area circulo 5
  python calculadora_geometria.py per triangulo 3 4 5
  python calculadora_geometria.py vol cilindro 3 10
""")

def main():
    if len(sys.argv) < 2:
        mostrar_ayuda()
        return

    operacion = sys.argv[1].lower()

    if operacion == "help":
        mostrar_ayuda()
        return

    if len(sys.argv) < 4:
        print("Error: Faltan argumentos.")
        mostrar_ayuda()
        return

    figura = sys.argv[2].lower()
    valores = sys.argv[3:]

    operaciones = {
        "area": area,
        "per": per,
        "vol": vol
    }

    if operacion not in operaciones:
        print(f"Operación desconocida: '{operacion}'")
        mostrar_ayuda()
        return

    try:
        resultado = operaciones[operacion](figura, valores)
        print(f"\nResultado final: {resultado:.5f}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
