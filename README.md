# Forensics de MalbolgeLISP

Forensics reproducibles para **MalbolgeLISP v1.2** — un programa inusualmente grande
escrito en el lenguaje esoterico familia Malbolge, apuntando a un **modelo de memoria 3^19**
(Malbolge "Unshackled", ancho de rotacion fijo 19) — mas un
suite de validacion cross-implementation para Malbolge clasico 3^10.

Este repositorio responde tres preguntas con evidencia ejecutable:

1. ¿Por que el interprete empaquetado upstream `fast20` se cuelga en algunas configuraciones de Windows,
   y cual es exactamente el defecto?
2. ¿Como se puede ejecutar nativamente en Windows la imagen completa de 371 MB de MalbolgeLISP,
   y como se ve una ejecucion correcta?
3. ¿Pueden implementaciones independientes concordar en la semantica de Malbolge clasico hasta
   conteos de pasos identicos?

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

Dos mundos se mantienen estrictamente separados durante todo:

| Mundo | Word size | Memoria | Especimenes aqui |
|---|---|---|---|
| MALBOLGE CLASICO | 10 trits (3^10 = 59,049 celdas) | diminuto | hello world, Quijote cap. I |
| MALBOLGELISP | 19 trits (3^19 = 1,162,261,467 celdas) | ~371 MB de imagen | `lisp.mb` (ver abajo) |

**Walbolge NO decompila el monstruo 3^19.** Decompila
programas 3^10 producidos por el Translator; ese limite esta demostrado y reforzado
por diseno.

## Resultados principales (todos reproducibles, ver docs/CLAIMS.md)

- El `fast20.c` upstream se cuelga porque `mmap(MAP_FIXED)` de Cygwin retorna
  `EINVAL` sobre su propia reserva `PROT_NONE` en esta plataforma, y fast20
  ignora el valor de retorno. Se incluye un reproductor de 25 lineas
  (`src/diagnostics/mmap_repro.c`).
- Un fix de una llamada (`mprotect` en vez de `mmap(MAP_FIXED)`) hace que fast20 cargue
  la imagen de 371 MB en ~2 s y ejecute a ~5.7e8 pasos/s en la maquina de prueba.
- `bolge19`, una VM nativa de Windows escrita en Zig desde cero (sin Cygwin, sin
  tricks de `mmap`), arranca la REPL completa de MalbolgeLISP v1.2, evalua
  `(+ 1 2)` -> `3`, imprime su versiculo de despedida en EOF, y termina limpiamente:
  **HALT en 2,408,246,381 pasos en 75 s** (un solo nucleo).
- Concordancia de Malbolge clasico en cuatro backends distintos:
  hello world = `"Hello World!"` en exactamente **40 pasos**;
  encabezado del capitulo I del Quijote en exactamente **2632 pasos**.
- Roundtrip Translator → Walbolge: las cuatro banderas de verificacion en True.

## Layout del repositorio

```
docs/          claims, arquitectura, reproduccion, ledger de honestidad
src/bolge19/   VM nativa Zig para el modelo 3^19
src/patches/   parche minimal a upstream fast20.c (+ justificacion)
src/diagnostics/mmap_repro.c            reproductor minimal de bug Cygwin
third_party/upstream/  snapshot de upstream fast20.c + licencia upstream usada como base del parche
specimens/     hello world + Quijote cap. I (producto del Translator + manifest)
evidence/      logs curados, anclas, manifests, hashes (solo rutas relativas)
scripts/       runner local de validacion one-shot
```

Los especimenes gigantes (`lisp.mb` 371,331,415 bytes; forma normalizada, mismo tamano)
**no se redistribuyen aqui**. Ver `docs/REPRODUCTION.md` para procedencia e
instrucciones de verificacion, y consultar el upstream para los terminos de licencia
que aplican a la distribucion completa de MalbolgeLISP.

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

Repositorios publicos companeros usados por la validacion del lado clasico incluyen:

- https://github.com/DannyBaanks/Autobolge
- https://github.com/DannyBaanks/Walbolge
- https://github.com/DannyBaanks/Malbolge-Translator
- https://github.com/DannyBaanks/Malbolge-Engine
- https://github.com/DannyBaanks/malbolge-oracle
- https://github.com/DannyBaanks/malbolge-differential

## Licencia

Nuestras adiciones: MIT (ver `LICENSE`). Snapshot empaquetado upstream `fast20.c`: ver el texto CC0 1.0 acompanante en
`third_party/upstream/LICENSE.upstream`. Otros artifacts upstream no estan
re-licenciados por este repositorio.
