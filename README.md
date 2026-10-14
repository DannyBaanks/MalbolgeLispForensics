# Forensics de MalbolgeLISP

Forensics reproducibles para **MalbolgeLISP v1.2** — un programa inusualmente grande
escrito en el lenguaje esoterico familia Malbolge, apuntando a un **modelo de memoria 3^19**
(Malbolge "Unshackled", ancho de rotacion fijo 19) — mas un
suite de validacion cross-implementation para Malbolge clasico 3^10, y el framework de busqueda y evaluacion **Danny Opera Solver**.

Este repositorio responde cuatro preguntas con evidencia ejecutable:

1. ¿Por que el interprete empaquetado upstream `fast20` se cuelga en Windows (Cygwin `EINVAL`) y en Linux (lectura fuera de limites en tabla cifrada), y como se reparo?
2. ¿Como se ejecuta de forma nativa y multiplataforma (Linux y Windows) la imagen completa de 371 MB de MalbolgeLISP, alcanzando >300M pasos/segundo?
3. ¿Como se conecta MalbolgeLISP 3^19 con los avances modernos de Malbolge (`MalbolgeFree` y la escalera parametrica $w=10 \to 19$, `MALBOLGE-MB-DATABASE` y MBIR)?
4. ¿Pueden implementaciones independientes concordar en la semantica de Malbolge clasico hasta conteos de pasos identicos?

## El pipeline que validamos

```
texto ordinario
    |  Traductor (harness de ancla)
    v
Programa Malbolge (.mal)
    |  multiples backends distintos: motor C / oraculo Python /
   |   toolkit Python / VM Zig
    v
output exacto (byte-identico, conteos de pasos identicos)
    |  Walbolge (traduccion inversa)
    v
representacion reconstruida == texto original (roundtrip verificado)
```

Dos mundos tradicionalmente separados, ahora unidos por la investigacion de `MalbolgeFree`:

| Mundo | Word size | Memoria | Estado en este repo |
|---|---|---|---|
| MALBOLGE CLASICO | 10 trits ($3^{10} = 59,049$ celdas) | diminuto | hello world, Quijote cap. I (validacion cruzada) |
| MALBOLGELISP | 19 trits ($3^{19} = 1,162,261,467$ celdas) | ~371 MB de imagen | `lisp.mb` ejecutado en C y Zig en Linux/Windows |
| MALBOLGE FREE | $w$ variable ($10 \to 19$) | escalonado | Puente formal documentado (ver `docs/LINUX_BENCHMARK_AND_EVOLUTION.md`) |

**Walbolge NO decompila el monstruo 3^19.** Decompila
programas 3^10 producidos por el Translator; ese limite esta demostrado y reforzado
por diseno.

## Resultados principales (todos reproducibles, ver docs/CLAIMS.md y docs/LINUX_BENCHMARK_AND_EVOLUTION.md)

- **Correccion de `fast20.c` en Windows y Linux:**
  - *Windows:* Upstream se colgaba porque `mmap(MAP_FIXED)` de Cygwin retornaba `EINVAL` sobre su propia reserva `PROT_NONE`. Se corrigio con `mprotect`.
  - *Linux:* `fast20` crasheaba con `SIGSEGV` en `NXT` debido a indexacion fuera de limites en la tabla de cifrado (`xlat[mem[c]]`) cuando `mem[c] >= 135` (e.g. 581M). Se anadio la guarda `if (mem[c] < 135)`.
- **Rendimiento record en Linux:** `fast20_fixed` ejecuta los **2,401,426,208 pasos** de la sesion completa de `lisp.mb` en solo **7.4 segundos** (~324.5M pasos/s), evaluando `(+ 1 2)` -> `3` y emitiendo el verso de despedida.
- **`bolge19` Multiplataforma (Zig 0.16.0):** VM nativa escrita en Zig desde cero, ahora completamente portada a C ABI / POSIX para compilar tanto en Linux como en Windows sin trucos de `mmap`. En el especimen `init_module.mb` concuerda al 100% con C en exactamente **19,337 pasos** (`c=19435`, `d=19`, `a=710270897`) en **0.00 s**.
- **Danny Opera Solver integrado:** Framework de sintesis y evaluacion en $Z^4$ con 4 estrategias (`Exhaustive`, `Simulated Annealing`, `Meta`, `Ablative`) ejecutadas en **0.11 s** en Linux.
- **Concordancia de Malbolge clasico en cuatro backends:**
  hello world = `"Hello World!"` en exactamente **40 pasos**;
  encabezado del capitulo I del Quijote en exactamente **2632 pasos**.
- **Roundtrip Translator → Walbolge:** Las cuatro banderas de verificacion en `True`.

## Layout del repositorio

```
docs/                  claims, arquitectura, reproduccion, ledger de honestidad
                       y reporte de benchmarks en Linux
src/bolge19/           VM nativa Zig multiplataforma para el modelo 3^19
src/patches/           parche minimal y corregido para fast20.c (+ justificacion)
src/diagnostics/       reproductor minimal de bug Cygwin
danny-opera-solver/    framework de busqueda, sintesis de programas y evaluador unificado
third_party/upstream/  snapshot de upstream fast20.c + licencia upstream usada como base del parche
specimens/             hello world + Quijote cap. I (producto del Translator + manifest)
evidence/              logs curados, anclas, manifests, hashes (solo rutas relativas)
scripts/               runners de validacion para entornos Linux y Windows
```

Los especimenes gigantes (`lisp.mb` 371,331,415 bytes; forma normalizada, mismo tamano)
**no se redistribuyen aqui**. Ver `docs/REPRODUCTION.md` para procedencia e
instrucciones de verificacion, y consultar el upstream para los terminos de licencia
que aplican a la distribucion completa de MalbolgeLISP.

## Conexion con la Investigacion ISyCo

Este trabajo se articula directamente con los siguientes proyectos del ecosistema Malbolge de ISyCo:
- **[MalbolgeFree](https://github.com/DannyBaanks/MalbolgeFree):** Nucleo `MalbolgeCore` con ancho parametrico $w$ y ensanchamiento de frontera ($10 \to 19$).
- **[MALBOLGE-MB-DATABASE](https://github.com/DannyBaanks/MALBOLGE-MB-DATABASE):** Especificacion MBIR, reset universal 3-crazy, y componentes de ALU/Loader en Malbolge puro.
- **[Walbolge](https://github.com/DannyBaanks/Walbolge):** Decompilador inverso y verificacion de roundtrip.
- **[Malbolge-Engine](https://github.com/DannyBaanks/Malbolge-Engine):** Interprete C de alta velocidad para Malbolge clasico.
- **[malbolge-oracle](https://github.com/DannyBaanks/malbolge-oracle):** Oraculo de referencia en Python con conteo exacto de ciclos.

## Procedencia y atribucion

MalbolgeLISP, `fast20.c`, el manual y `lisp.zip` son trabajo upstream de
iczelia / kspalaiologos. El snapshot de `fast20.c` aqui va acompanado de la
licencia CC0 upstream en `third_party/upstream/LICENSE.upstream`. Este repositorio
no intenta re-licenciar la distribucion completa de MalbolgeLISP; consultar
upstream para sus terminos de licencia completos. Todo en `src/patches` se deriva
del fuente publico `fast20.c` y nuestras modificaciones estan claramente marcadas.
Autobolge/Walbolge/Translator/engine/oracle/toolkit pertenecen al workspace de
investigacion ISyCo y se referencian, no se re-publican, mas alla de los pequenos
snapshots de specimens/manifest necesarios para reproduccion.

## Licencia

Nuestras adiciones: MIT (ver `LICENSE`). Snapshot empaquetado upstream `fast20.c`: ver el texto CC0 1.0 acompanante en
`third_party/upstream/LICENSE.upstream`. Otros artifacts upstream no estan
re-licenciados por este repositorio.
