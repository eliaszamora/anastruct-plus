# anaStruct Plus

Extensión ligera de [`anaStruct`](https://github.com/anastruct/anaStruct) para mejorar sus gráficos de postproceso sin cambiar el solver estructural.

## Qué añade

- tamaño de figura automático según la geometría;
- unidades visuales de longitud, fuerza, carga distribuida y momento;
- etiquetas automáticas en los dos extremos de cada elemento;
- etiquetas del máximo y mínimo global de cada elemento;
- evita duplicar etiquetas cuando un extremo coincide con un máximo o mínimo;
- conserva la API habitual de `anaStruct`, incluyendo `values_only=True`.

> `anaStruct Plus` no convierte unidades. `anaStruct` sigue trabajando con números sin unidades; tú debes mantener un sistema coherente. Las unidades indicadas aquí son etiquetas de presentación.

## Instalación en Google Colab

```python
!pip install -q git+https://github.com/eliaszamora/anastruct-plus.git
```

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

ss.solve()

ss.show_structure()
ss.show_bending_moment()
ss.show_shear_force()
ss.show_axial_force()
```

Con:

```python
ss = SystemElements(force_unit="tonf", length_unit="m")
```

las etiquetas visuales se interpretan como:

- fuerza: `tonf`;
- longitud: `m`;
- carga distribuida: `tonf/m`;
- momento: `tonf·m`.

## Precisión

Los diagramas usan dos decimales por defecto:

```python
ss.show_bending_moment()
```

Puedes cambiarlo:

```python
ss.show_bending_moment(decimals=3)
```

## Tamaño de figura

Por defecto se ajusta automáticamente a la geometría. También puedes imponer un tamaño:

```python
ss.show_bending_moment(figsize=(10, 4))
```

o pedir explícitamente el autoajuste:

```python
ss.show_bending_moment(figsize="auto")
```

## API

Se mantienen los nombres familiares de `anaStruct`:

```python
ss.show_structure()
ss.show_bending_moment()
ss.show_shear_force()
ss.show_axial_force()
```

También puedes importar el nombre explícito de la subclase:

```python
from anastruct_plus import SystemElementsPlus
```

## Estado

Versión inicial `0.1.0`. El objetivo es mantener la extensión pequeña: `anaStruct` realiza el análisis y `anaStruct Plus` mejora únicamente la presentación y el postproceso gráfico.
