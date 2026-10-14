# Patches para `fast20` (MalbolgeLISP 3^19)

Este directorio contiene las implementaciones corregidas y el parche canónico para el intérprete `fast20.c` de MalbolgeLISP.

## Contenido del directorio

| Archivo | Propósito | Características |
|---|---|---|
| [`fast20_clean.c`](fast20_clean.c) | Intérprete minimal de producción | Parche limpio, sin instrumentación de depuración, máxima velocidad (>320M pasos/s). |
| [`fast20_fixed.c`](fast20_fixed.c) | Intérprete forense instrumentado | Incluye telemetría paso a paso (`DBG`), contador de fallas de página (`dbg_faults`) y ciclos globales. Utilizado por `danny-opera-solver` y la suite de evaluación. |
| [`fast20.patch`](fast20.patch) | Parche unificado (`diff -u`) | Diferencial directo aplicable sobre `third_party/upstream/fast20.c`. |

---

## Defectos reparados y causa raíz

### 1. Windows / Cygwin: `mmap(MAP_FIXED)` → `EINVAL`
* **Defecto upstream:** En Cygwin, llamar a `mmap(..., MAP_FIXED, ...)` sobre una reserva existente creada con `PROT_NONE` retorna `EINVAL`.
* **Impacto:** La página nunca se protegía para lectura/escritura y el manejador `sigsegvh` reintentaba la instrucción en un bucle infinito al 100% de CPU.
* **Solución:** Reemplazar `mmap(MAP_FIXED)` por `mprotect(b, l, PROT_READ|PROT_WRITE)`.

### 2. Linux x86_64: Lectura fuera de límites en tabla `.rodata`
* **Defecto upstream:** El macro `NXT` indexaba directamente `xlat[mem[c]]`. La tabla mide 135 bytes y reside en `.rodata`. Cuando `mem[c] >= 135` (e.g. 581,130,726 tras operaciones `crz` o `rot`), indexaba a más de 581 MB fuera del segmento.
* **El enmascaramiento upstream:** En upstream, el `sigsegvh` llamaba a `mmap(MAP_FIXED)` sobre esa dirección, lo que en Linux ELF creaba una página anónima nueva en caliente y leía basura. Al introducir `mprotect`, este devolvió `ENOMEM` (errno 12) porque esa región nunca fue reservada, exponiendo la violación de memoria.
* **Solución:** Guarda estricta de límites:
  ```c
  static const char *xlat = "SOMEBODY MAKE ME FEEL ALIVE..." "AND SHATTER ME";
  #define NXT do{if(mem[c]<135)mem[c]=xlat[mem[c]];c++;d++;BRA;}while(0)
  ```
  El compilador traduce esto a un `cmp $0x86` (`134`) sin penalización de predicción de saltos.

---

## Compilación y Uso

```bash
# Versión de producción limpia:
gcc -O3 src/patches/fast20_clean.c -o fast20

# Versión instrumentada con telemetría:
gcc -O3 src/patches/fast20_fixed.c -o fast20_fixed

# Aplicar el parche sobre un checkout de upstream:
patch -p1 < src/patches/fast20.patch
```

## Atribución y Licencia

El trabajo original de `fast20.c` pertenece a **Iczelia (`kspalaiologos`)** bajo licencia **CC0 1.0 Universal** (ver `third_party/upstream/LICENSE.upstream`). Nuestras correcciones y adaptaciones forenses son liberadas bajo licencia MIT.
