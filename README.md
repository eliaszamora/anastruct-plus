# anaStruct Plus

Extensión ligera de [`anaStruct`](https://github.com/anastruct/anaStruct) para mejorar sus gráficos y su entrada de cargas sin modificar el solver estructural.

## Qué añade

- tamaño de figura automático según la geometría;
- encuadre compacto con margen visual para evitar recortes;
- unidades visuales de longitud, fuerza, carga distribuida, momento y desplazamiento;
- una sola etiqueta centrada para cargas distribuidas uniformes;
- componentes distribuidas nombradas, por ejemplo `pp=-4, sc=-3`, combinadas de forma segura en una única resultante para el solver;
- IDs explícitos: nodos `N1`, `N2`, ... en azul y elementos `E1`, `E2`, ... en verde;
- valores automáticos en extremos y máximos/mínimos relevantes de momento, corte y axial;
- unidades escritas directamente junto a los resultados (`20.00 tonf·m`, `15.00 tonf`, etc.);
- reacciones identificadas por nodo (`R1x`, `R1y`, `M1`, etc.);
- anotación `u_max = ...` próxima a la deformada y conectada mediante flecha;
- ejes físicos calibrados para vigas rectas horizontales;
- alineación visual común entre reacciones, cortante, momento y deformada, incluso cuando reacciones no tiene eje Y físico;
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

## Componentes de carga distribuida

Desde la versión `0.2.8`, una carga distribuida puede introducirse mediante nombres elegidos directamente como argumentos de `q_load()`:

```python
ss.q_load(element_id=1, pp=-4, sc=-3)
```

También pueden añadirse en llamadas separadas:

```python
ss.q_load(element_id=1, pp=-4)
ss.q_load(element_id=1, sc=-3)
```

En ambos casos anaStruct Plus conserva las componentes por separado, calcula algebraicamente la resultante y entrega **solo esa resultante** al solver de anaStruct. Por ejemplo:

```text
pp = -4
sc = -3
Σq = -7
```

produce el mismo análisis estructural que:

```python
ss.q_load(element_id=1, q=-7)
```

`show_structure()` mantiene una única fila de flechas correspondiente a la carga resultante y muestra el desglose de componentes, por ejemplo:

```text
pp = 4.0 tonf/m
sc = 3.0 tonf/m
Σq = 7.0 tonf/m
```

Esto evita superponer varias filas de flechas sobre la misma viga y mantiene visible el origen de la carga total.

La sintaxis tradicional sigue disponible y conserva el comportamiento nativo de anaStruct:

```python
ss.q_load(element_id=1, q=-7)
```

Si se usa dos veces `q=` sobre el mismo elemento, la segunda llamada reemplaza a la primera, igual que en anaStruct original. No se permite mezclar `q=` y componentes nombradas en la misma llamada porque sería ambiguo.

En esta primera versión, las componentes nombradas requieren un único `element_id`, valores escalares y no admiten `q_perp`.

## Cortante, momento y axial

Los diagramas muestran automáticamente:

- valor en el extremo inicial;
- valor en el extremo final;
- máximo global del elemento;
- mínimo global del elemento;
- unidad física junto a cada valor;
- sin duplicar etiquetas cuando un extremo coincide con un máximo o mínimo.

Para una **viga recta horizontal**, anaStruct Plus reconstruye además la escala transversal física a partir de los resultados y del factor gráfico utilizado por anaStruct:

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

Desde la versión `0.2.7`, el gráfico de reacciones reserva el mismo espacio lateral y utiliza la misma caja de ejes que los diagramas de `V`, `M` y `u_y`. Esto mantiene las figuras alineadas en Colab/Jupyter aun cuando el gráfico de reacciones no muestra una escala Y numérica. El espacio adicional es únicamente de layout: **no representa una magnitud física ni añade un eje Y ficticio**.

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

Versión `0.2.8`. anaStruct realiza el análisis estructural; anaStruct Plus administra la descomposición de cargas y modifica la presentación/postproceso sin cambiar el solver.
