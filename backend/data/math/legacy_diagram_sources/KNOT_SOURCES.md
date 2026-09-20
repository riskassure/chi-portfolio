# Knot diagram sources

The four historical knot examples used by the PlanetMath `knot theory`
entry are retained from the references selected during restoration:

- `knot10_89.gif`: Knot Atlas, Rolfsen knot 10_89
  <https://katlas.org/wiki/10_89>
- `trefoil.gif`: Knot Atlas, Rolfsen knot 3_1 (the trefoil)
  <https://katlas.org/wiki/3_1>
- `nasty_unknot.jpg`: The seven-crossing "nasty" unknot
  <https://horizonofreason.com/science/unknot-diagrams-trivial-knot-collection/>
- `unknot.png`: The eleven-crossing Goeritz unknot
  <https://horizonofreason.com/science/unknot-diagrams-trivial-knot-collection/>

These files are served directly so that the over/under information at every
crossing remains faithful to the reference diagrams. New knot diagrams can be
drawn as vectors with MiKTeX's installed TikZ `knots` library (provided by the
`spath3` package).

During the diagram build, `knot10_89.gif` and `trefoil.gif` are converted from
outlined bands to single centerlines. The conversion retains the source
projection and its crossing gaps and produces `knot10_89.png` and
`trefoil.png` for the website.
