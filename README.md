# anaStruct Plus

Extensión ligera de [`anaStruct`](https://github.com/anastruct/anaStruct) para mejorar sus gráficos de postproceso sin cambiar el solver estructural.

## Qué añade

- tamaño de figura automático según la geometría;
- encuadre más compacto alrededor de la estructura y los diagramas;
- unidades visuales de longitud, fuerza, carga distribuida, momento y desplazamiento;
- una sola etiqueta centrada para cargas distribuidas uniformes;
- etiquetas automáticas en los extremos y máximos/mínimos relevantes de momento, corte y axial;
- reacciones con componentes identificadas por nodo (`R1x`, `R1y`, `M1`, etc.);
- desplazamientos con unidad e identificación `u = ...`;
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

## Reacciones

Las etiquetas genéricas `R=` y `T=` de anaStruct se reemplazan por componentes identificadas por nodo:

```text
R1x = ... tonf
R1y = ... tonf
M1  = ... tonf·m
```

Los signos numéricos se mantienen según la convención de anaStruct.

## Desplazamientos

El gráfico conserva la deformada calculada por anaStruct y añade unidad e identificación a sus valores relevantes:

```text
u = 0.003 m
```

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

Versión `0.2.0`. El objetivo es mantener la extensión pequeña: `anaStruct` realiza el análisis y `anaStruct Plus` mejora únicamente la presentación y el postproceso gráfico.
