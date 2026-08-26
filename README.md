# anaStruct Plus

Extensión ligera de [`anaStruct`](https://github.com/anastruct/anaStruct) para mejorar sus gráficos de postproceso sin cambiar el solver estructural.

## Qué añade

- tamaño de figura automático según la geometría;
- encuadre compacto con margen visual para evitar recortes;
- unidades visuales de longitud, fuerza, carga distribuida, momento y desplazamiento;
- una sola etiqueta centrada para cargas distribuidas uniformes;
- IDs explícitos: nodos `N1`, `N2`, ... en azul y elementos `E1`, `E2`, ... en verde;
- valores automáticos en extremos y máximos/mínimos relevantes de momento, corte y axial;
- unidades escritas directamente junto a los resultados (`20.00 tonf·m`, `15.00 tonf`, etc.);
- reacciones identificadas por nodo (`R1x`, `R1y`, `M1`, etc.);
- anotación `u_max = ...` próxima a la deformada y conectada mediante flecha;
- ejes físicos calibrados para vigas rectas horizontales;
- conserva la API habitual de `anaStruct`, incluido `values_only=True`.

> `anaStruct Plus` no convierte unidades. `anaStruct` sigue trabajando con números sin unidades; debes mantener un sistema coherente. `force_unit` y `length_unit` definen las unidades de presentación.

## Instalación en Google Colab

```python
!pip install -q --upgrade --no-cache-dir git+https://github.com/eliaszamora/anastruct-plus.git
```

No es necesario instalar `anastruct` aparte: es una dependencia de `anastruct-plus`.

```python
from anastruct_plus import SystemElements
```

## Ejemplo mínimo

```python
from anastruct_plus import SystemElements

ss = SystemElements(force_unit="tonf", length_unit="m")

ss.add_element(location=[[0, 0], [4, 0]])
ss.add_support_fixed(node_id=1)
ss.add_support_hinged(node_id=2)
ss.q_load(element_id=1, q=-10)

ss.show_structure()

ss.solve()

ss.show_reaction_force()
ss.show_shear_force()
ss.show_bending_moment()
ss.show_displacement()
```

Con `force_unit="tonf"` y `length_unit="m"`:

- fuerza → `tonf`;
- longitud → `m`;
- carga distribuida → `tonf/m`;
- momento → `tonf·m`;
- desplazamiento → `m`.

## Estructura

`show_structure()` conserva las coordenadas geométricas reales y muestra:

- eje `x [m]`;
- eje `y [m]`;
- nodos como `N1`, `N2`, ...;
- elementos como `E1`, `E2`, ...;
- IDs separados mediante offsets de pantalla para evitar solapamientos con miembros, apoyos y cargas.

En vigas horizontales, los IDs de elementos se ubican preferentemente bajo la barra para no competir con cargas distribuidas situadas arriba.

## Cortante, momento y axial

Los diagramas muestran automáticamente:

- valor en el extremo inicial;
- valor en el extremo final;
- máximo global del elemento;
- mínimo global del elemento;
- unidad física junto a cada valor;
- sin duplicar etiquetas cuando un extremo coincide con un máximo o mínimo.

Para una **viga recta horizontal**, v0.2.6 reconstruye además la escala transversal física a partir de los resultados y del factor gráfico utilizado por anaStruct:

```text
Cortante  → V [tonf]
Momento   → M [tonf·m]
Axial     → N [tonf]
```

Por ejemplo, una etiqueta `M = 20.00 tonf·m` queda alineada con la ordenada `20.00` del eje `M [tonf·m]`. La cuadrícula horizontal utiliza esa misma escala física.

Esto corrige el problema de las versiones anteriores, donde anaStruct podía dibujar un resultado físico de `20 tonf·m` a una coordenada gráfica aproximada de `0.6`.

## Alcance de los ejes físicos

La calibración transversal se activa únicamente cuando existe una interpretación inequívoca: una estructura recta horizontal.

- **Viga horizontal:** `x` representa la posición real y el eje transversal del resultado se calibra físicamente.
- **Modelo vertical:** se conserva el eje longitudinal `y [unidad]`; no se inventa una escala transversal.
- **Marco 2D general:** se ocultan las escalas transversales gráficas de anaStruct porque no existe un único eje global que pueda representar simultáneamente los diagramas locales de todos los miembros.
- **Reacciones:** se conserva la posición longitudinal, pero no se crea un eje Y de fuerza a partir de la longitud gráfica de las flechas, ya que esas flechas están escaladas para presentación.

## Reacciones

Las etiquetas genéricas de anaStruct se reemplazan por componentes identificadas:

```text
R1x = ... tonf
R1y = ... tonf
M1  = ... tonf·m
```

La convención visual de `R1y` respeta el sentido mostrado en el gráfico cuando `invert_y_loads=True`. El solver y sus resultados internos no se modifican.

## Desplazamientos

Para una viga horizontal, la forma deformada conserva la amplificación gráfica de anaStruct, pero el eje se calibra con la magnitud física del desplazamiento:

```text
u_y [m]
```

La etiqueta de máximo permanece asociada a la curva mediante una flecha:

```text
u_max = 0.003 m  ──→  punto correspondiente
```

No se realiza conversión automática de `m` a `mm`.

## Precisión

Momento, corte, axial y reacciones usan dos decimales por defecto:

```python
ss.show_bending_moment()
ss.show_reaction_force()
```

Puedes cambiar la precisión de las etiquetas donde corresponde:

```python
ss.show_bending_moment(decimals=3)
ss.show_reaction_force(decimals=3)
```

Los ticks de esfuerzos usan dos decimales para mantener consistencia con las etiquetas. Los desplazamientos conservan precisión suficiente para magnitudes pequeñas.

## Tamaño de figura

Normalmente no necesitas especificar `figsize`:

```python
ss.show_structure()
ss.show_reaction_force()
ss.show_shear_force()
ss.show_bending_moment()
ss.show_displacement()
```

Aun puedes imponer un tamaño manual:

```python
ss.show_bending_moment(figsize=(10, 4))
```

## API

Se mantienen los nombres familiares de anaStruct:

```python
ss.show_structure()
ss.show_reaction_force()
ss.show_bending_moment()
ss.show_shear_force()
ss.show_axial_force()
ss.show_displacement()
```

También puedes importar explícitamente la subclase:

```python
from anastruct_plus import SystemElementsPlus
```

## Estado

Versión `0.2.6`. anaStruct realiza el análisis estructural; anaStruct Plus modifica únicamente la presentación y el postproceso gráfico.
