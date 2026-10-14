# MalbolgeLISP Forensics — Linux Benchmark & Malbolge Evolution Report

**Fecha de verificación:** 2026-10-13  
**Plataforma de prueba:** Linux x86_64 (Ubuntu 24.04 LTS, Kernel 6.8, GCC 13.3.0, Zig 0.16.0)  
**Host anterior (histórico):** Windows 11 / Cygwin (agosto 2026)  

---

## 1. Resumen Ejecutivo

Cuando `malbolge-lisp-forensics` se construyó en agosto de 2026, el entorno de referencia era Windows/Cygwin. Existían dos grandes barreras:
1. El intérprete `fast20.c` original de upstream se congelaba en Windows al 100% de CPU debido a un bug de Cygwin donde `mmap(MAP_FIXED)` sobre una reserva `PROT_NONE` retornaba `EINVAL`, ignorado por el manejador de señales.
2. `bolge19` (VM en Zig) dependía exclusivamente de la API de Win32 (`kernel32`, `shell32`, `CreateFileW`, `GetTickCount64`), haciendo imposible su compilación en Linux.
3. El repositorio se encontraba desconectado de la evolución posterior de la investigación de Malbolge en ISyCo (`MalbolgeFree`, `MALBOLGE-MB-DATABASE`, `GENEALOGIA_MALBOLGE`).

En esta sesión se resolvió la portabilidad completa a Linux y se ejecutaron los benchmarks canónicos:
- **`fast20_fixed.c` en Linux:** Descubrimiento y corrección de un desbordamiento de búfer en `NXT` (`xlat[mem[c]]` cuando `mem[c] >= 135`), permitiendo ejecutar los **2,401,426,208 pasos** de `lisp.mb` en **7.4 segundos** (~325,000,000 pasos/s).
- **`bolge19` en Linux:** Portado a C ABI portable (`fopen`, `fread`, `read(0)`, `write(1)`, `gettimeofday`, `std.process.Init.Minimal`). Compila nativamente en Zig 0.16.0 y reproduce bit a bit y paso a paso el comportamiento.
- **Acuerdo de Pasos Exactos:** En `init_module.mb`, ambos motores alcanzaron un acuerdo idéntico en exactamente **19,337 pasos** (`c=19435`, `d=19`, `a=710270897`) en **0.00s**.
- **Suite Clásica 3^10:** `scripts/run_validation.py` adaptado a Linux (`sys.executable` y auto-detección de herramientas vecinas), verificando 40 pasos en Hello World, 2632 pasos en Quijote y 4/4 banderas True en Walbolge roundtrip.
- **Danny Opera Solver:** 4 algoritmos de búsqueda (`Exhaustive`, `Simulated Annealing`, `Meta`, `Ablative`) ejecutados en Linux en **0.11s**.

---

## 2. Diagnóstico Técnico: El Bug de Linux en `fast20`

### El Defecto Oculto
En `third_party/upstream/fast20.c` y en el parche inicial de Windows:
```c
#define NXT mem[c] = \
  "SOMEBODY MAKE ME FEEL ALIVE" \
  "[hj9>,5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@" \
  "AND SHATTER ME"[mem[c]];c++;d++;BRA
```
La tabla concatenada tiene **135 bytes** (prefijo 27 + tabla 94 + sufijo 14).
En Malbolge, los opcodes solo se cifran si su valor está en el rango imprimible (33..126). Si un valor de memoria `mem[c]` excede 134 (por ejemplo tras operaciones `crz` o `rot`, donde `mem[c] = 581,130,726`), la indexación directa intenta leer 581 MB más allá de la cadena literal en el segmento de solo lectura (`.rodata`).

- **Bajo Windows/Cygwin:** La distribución de memoria permitía leer direcciones contiguas sin fallo inmediato en ciertos escenarios.
- **Bajo Linux ELF:** El intento de lectura más allá del segmento generó un `SIGSEGV` con `si_addr = 0x5e1b23a30afe` (fuera del espacio mapeado de `mem`).
- El manejador de señal `sigsegvh` asumía erróneamente que cualquier fallo era un fallo de página dentro de `mem`, e invocaba `mprotect` sobre una dirección no mapeada, retornando `errno=12 (ENOMEM)`.

### La Solución Canónica
`bolge19` en Zig ya contaba con esta protección en su bucle:
```zig
if (cv < XLAT_CONCAT.len) memSet(cur, XLAT_CONCAT[cv]);
```
Se aplicó la misma guarda a `fast20_fixed.c`:
```c
static const char *xlat = "SOMEBODY MAKE ME FEEL ALIVE"
  "[hj9>,5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
  "AND SHATTER ME";
#define NXT do{if(mem[c]<135)mem[c]=xlat[mem[c]];c++;d++;dbg_steps++;dbg_steps_global++; ... BRA;}while(0)
```
Con este ajuste, `fast20` nunca genera fallos fuera de `mem` y corre con estabilidad total en Linux.

---

## 3. Benchmarks Comparativos en Linux

### A. Espécimen Mínimo: `init_module.mb` (19,392 bytes)

| Motor | Binario | Pasos a HALT | Tiempo CPU | Registros Finales |
|---|---|---|---|---|
| **fast20 (parcheado)** | GCC 13.3 -O3 | **19,337** | **0.00 s** | `c=19435, d=19, a=710270897` |
| **bolge19 (Zig)** | Zig 0.16.0 ReleaseFast | **19,337** | **0.00 s** | `c=19435, d=19, a=710270897` |

*Acuerdo:* **100% idéntico** en pasos, registros y tiempo.

### B. Espécimen Completo: `lisp.mb` (371,331,415 bytes)
Sesión de evaluación `(+ 1 2)` -> `3` seguida de EOF (verso de despedida y HALT):

```
MALBOLGELISP V1.2 (2020-2021, PALAIOLOGOS)
DOT COMMANDS:  .F(eatures)  .A(uthor)  .R(eset)  .M(emory)  .S(ymbols)  .E(xport)  .I(mport)
% ......|....
3
% 
There is a sky illuminating us
Someone is out there that we truly trust
There is a rainbow for you and me
A beautiful sunrise eternally
DBG HALT steps=2401426208 c=581143360 d=581861866 a=10
```

- **Pasos ejecutados:** 2,401,426,208 pasos
- **Tiempo total en Linux:** **7.4 segundos**
- **Throughput:** **~324,500,000 pasos/segundo**
- **Fallas de página atendidas:** 1,133 fallas

---

## 4. Conexión con la Genealogía e Investigación Actual de Malbolge

El repositorio `malbolge-lisp-forensics` nació con una visión binaria y polarizada:
- **Mundo 3^10:** Classic Malbolge (59,049 celdas, ancho 10 trits).
- **Mundo 3^19:** MalbolgeLISP (1,162,261,467 celdas, ancho fijo 19 trits).

Entre agosto y octubre de 2026, la investigación en ISyCo dio saltos cuánticos que dejan a este repositorio en una nueva perspectiva:

### 1. `MalbolgeFree` (Octubre 2026) — La Unificación Paramétrica
`MalbolgeFree` demostró que la separación entre 3^10 y 3^19 no es un abismo ontológico:
- Introduce el núcleo unificado `MalbolgeCore(width, mem_limit, growth_policy)` en Zig.
- El ancho $w$ es una variable entera finita (no "infinito").
- La política de frontera (**epochal policy**) amplía el ancho $w$ de $10 \to 11 \to \dots \to 19$ cuando los punteros $c$ o $d$ alcanzan el límite de direccionamiento $3^w$.
- MalbolgeLISP no es un lenguaje diferente: es una ejecución en el escalón $w = 19$ de la escalera de Malbolge Free.

### 2. `MALBOLGE-MB-DATABASE` — Substrato Nativo y MBIR
- Toda la infraestructura se trasladó a Linux nativo (sin emulación Wine), utilizando LMAO v0.6.0 y ejecutores C nativos.
- Se formalizó el contrato intermedio **MBIR** (18 opcodes universales).
- Se descubrió el **Teorema del Reset Universal 3-Crazy**:
  $$\text{crz}(C_0, \text{crz}(C_2, \text{crz}(C_1, X))) = 29524 \quad \forall X \in [0, 59048]$$
  permitiendo implementar pilas LIFO y bucles reentrantes en Malbolge puro.
- Se construyeron módulos de ALU clásica con `ADD` ($P0$), `SUB` ($P1$) y `CMP_EQ` ($P2$).

### 3. `danny-opera-solver` y Síntesis Automática
- Integrado en este repositorio, el solucionador implementa 4 estrategias de síntesis:
  1. **Búsqueda Exhaustiva orientada en $Z^4$** (Meta/Grok style): halla replicadores en 4 ejes en milisegundos.
  2. **Simulated Annealing (SA)** (GPT style): convergencia estocástica con enfriamiento adaptativo.
  3. **Meta Search:** exploración exhaustiva de firmas.
  4. **Ablación mínima:** minimización de conjuntos vivos sin pérdida semántica.
- Permite sintetizar secuencias de Malbolge y evaluar especímenes en fracciones de segundo con oráculos locales.

---

## 5. Resumen de Archivos Actualizados

1. `src/patches/fast20_fixed.c`: Guarda de límites `mem[c] < 135` en el macro `NXT`.
2. `src/bolge19/main.zig`: Implementación multiplataforma en Zig 0.16.0 utilizando C ABI / syscalls estándar.
3. `scripts/run_validation.py`: Auto-detección de backends en repositorios vecinos y uso de `sys.executable`.
4. `danny-opera-solver/pyproject.toml`: Corrección de sintaxis TOML para compatibilidad con analizadores modernos.
5. `danny-opera-solver/test_pipeline_final.py`: Eliminación de rutas fijas `C:\` en favor de `Path(__file__)`.
6. `danny-opera-solver/danny/evaluator.py`: Soporte dinámico para oráculos y binarios en Linux y Windows.
