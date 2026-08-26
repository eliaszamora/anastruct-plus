# anaStruct Plus

Extensión ligera de [`anaStruct`](https://github.com/anastruct/anaStruct) para mejorar sus gráficos de postproceso sin cambiar el solver estructural.

## Qué añade

- tamaño de figura automático según la geometría;
- encuadre compacto con margen visual adicional para evitar apoyos, etiquetas o extremos pegados a los bordes;
- unidades visuales de longitud, fuerza, carga distribuida, momento y desplazamiento;
- una sola etiqueta centrada para cargas distribuidas uniformes, separada de los identificadores del modelo;
- identificadores de nodos en azul e identificadores de elementos en verde, con fondo blanco y offsets geométricos para evitar solapamientos con miembros, apoyos y cargas;
- etiquetas automáticas en los extremos y máximos/mínimos relevantes de momento, corte y axial;
- reacciones con componentes identificadas por nodo (`R1x`, `R1y`, `M1`, etc.) y apilado de etiquetas para evitar solapamientos;
- forma deformada rotulada explícitamente como escala amplificada y magnitud real `u_max = ...` mediante una anotación cercana con flecha al punto correspondiente de la curva;
- semántica de ejes segura: no se muestran escalas numéricas que anaStruct usa solo como amplificación gráfica;
- conserva la API habitual de `anaStruct`, incluyendo `values_only=True`.

> `anaStruct Plus` no convierte unidades. `anaStruct` sigue trabajando con números sin unidades; debes mantener un sistema coherente. Las unidades indicadas aquí son etiquetas de presentación.

## Instalación en Google Colab

```python
!pip install -q git+https://github.com/eliaszamora/anastruct-plus.git
```

No es necesario instalar `anastruct` aparte: está declarado como dependencia de `anastruct-plus`.

Luego importa el `SystemElements` extendido:

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

Con:

```python
ss = SystemElements(force_unit="tonf", length_unit="m")
```

las etiquetas visuales se interpretan como:

- fuerza: `tonf`;
- longitud: `m`;
- carga distribuida: `tonf/m`;
- momento: `tonf·m`;
- desplazamiento: `m`.

## Identificadores del modelo

`show_structure()` conserva la numeración nativa de anaStruct, pero la hace más legible:

- nodos: azul;
- elementos: verde;
- ambos: texto en negrita con un pequeño fondo blanco;
- las etiquetas se separan de la geometría mediante offsets en puntos de pantalla, por lo que la separación no depende del tamaño físico del modelo.

En vigas horizontales, los IDs de elementos se colocan preferentemente bajo el miembro para no competir con las flechas de una carga distribuida situada arriba. En marcos, la colocación se deriva de la geometría y del centro del modelo.

## Diagramas de esfuerzos

Los diagramas de momento, corte y axial muestran automáticamente:

- valor en el extremo inicial;
- valor en el extremo final;
- máximo global del elemento;
- mínimo global del elemento;
- sin duplicar una etiqueta si el extremo coincide con un máximo o mínimo.

```python
ss.show_bending_moment()
ss.show_shear_force()
ss.show_axial_force()
```

Además, los límites finales reciben un pequeño margen visual adicional para que apoyos y rótulos no queden pegados a los bordes de la figura.

## Semántica de los ejes

`anaStruct` escala transversalmente los diagramas de momento, corte, axial, reacciones y deformada para hacerlos visibles. Esa amplitud dibujada **no es la magnitud física** del resultado. `anaStruct Plus` evita mostrar ticks numéricos que puedan sugerir lo contrario:

- en una viga horizontal se conserva únicamente `x [unidad]`, porque `x` sí representa la posición longitudinal real;
- en un elemento/modelo vertical se conserva únicamente `y [unidad]`;
- en marcos con elementos en distintas direcciones se ocultan ambos ejes numéricos en los diagramas de resultados, porque no existe un único eje longitudinal;
- las magnitudes físicas se leen en las etiquetas del propio diagrama y en sus unidades (`tonf`, `tonf·m`, etc.);
- `show_structure()` conserva ambos ejes geométricos `x` e `y`, ya que allí sí representan coordenadas reales del modelo.

Esto evita casos visualmente incorrectos como un máximo `M = 20 tonf·m` dibujado a una ordenada gráfica `0.6` que podría confundirse con una escala física.

## Reacciones

Las etiquetas genéricas `R=` y `T=` de anaStruct se reemplazan por componentes identificadas por nodo:

```text
R1x = ... tonf
R1y = ... tonf
M1  = ... tonf·m
```

Para la componente vertical, la etiqueta se presenta con el sentido visual del eje global mostrado en el gráfico. Esto evita que una reacción dibujada hacia arriba aparezca rotulada con signo negativo cuando `invert_y_loads=True`. El solver y sus resultados internos no se modifican.

## Desplazamientos

El gráfico conserva la deformada calculada por anaStruct, pero la identifica como una **forma deformada con escala amplificada**. La magnitud numérica real se muestra junto a la zona correspondiente mediante una flecha guía:

```text
u_max = 0.003 m  ──→  punto de la deformada
```

La flecha se ancla al punto de la curva deformada más cercano a la posición donde anaStruct ubicó originalmente el valor numérico. Así se mantiene la relación visual entre el valor y el punto que representa sin escribir el texto encima de la curva.

No se realiza conversión automática de `m` a `mm`.

## Precisión

Momento, corte, axial y reacciones usan dos decimales por defecto:

```python
ss.show_bending_moment()
ss.show_reaction_force()
```

Puedes cambiarlo donde corresponde:

```python
ss.show_bending_moment(decimals=3)
ss.show_reaction_force(decimals=3)
```

## Tamaño de figura

Por defecto se ajusta automáticamente a la geometría, por lo que normalmente no necesitas escribir `figsize`:

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

O pedir explícitamente el autoajuste:

```python
ss.show_bending_moment(figsize="auto")
```

## API

Se mantienen los nombres familiares de `anaStruct`:

```python
ss.show_structure()
ss.show_reaction_force()
ss.show_bending_moment()
ss.show_shear_force()
ss.show_axial_force()
ss.show_displacement()
```

También puedes importar el nombre explícito de la subclase:

```python
from anastruct_plus import SystemElementsPlus
```

## Estado

Versión `0.2.4`. El objetivo es mantener la extensión pequeña: `anaStruct` realiza el análisis y `anaStruct Plus` mejora únicamente la presentación y el postproceso gráfico.

### Nota sobre la forma deformada

La curva deformada se representa con una escala gráfica amplificada para hacer visible la deformación. Por eso la dirección transversal no presenta una escala numérica de desplazamiento. La magnitud real se muestra mediante la etiqueta `u_max = ...` con la unidad de longitud configurada y una flecha guía al punto de la curva.
