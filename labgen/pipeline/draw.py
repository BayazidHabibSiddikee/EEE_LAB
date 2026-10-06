import schemdraw
import schemdraw.elements as elm

def draw_diode_circuit(output_path):
    with schemdraw.Drawing(file=output_path, show=False) as d:
        d += elm.SourceV().up().label('Vs')
        d += elm.Resistor().right().label(r'1k$\Omega$')
        d += elm.Diode().down().label('1N4148')
        d += elm.Line().left()
        d += elm.Ground()
