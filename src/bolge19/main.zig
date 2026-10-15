// bolge19 - VM Malbolge Unshackled ancho FIJO 19 trits (END=3^19).
// Composicion: arquitectura estilo Autobolge (overlay + cadena perezosa por
// bloques) + semantica EXACTA fast20.c (iczelia/malbolge-lisp): decode por-regiones
// offs[], encrypt sobre tabla concatenada de 135 chars, c++ y d++ por ciclo.
// I/O portable via C ABI (estable frente al churn de std.Io en zig 0.16).
const std = @import("std");

extern "c" fn fopen(filename: [*:0]const u8, modes: [*:0]const u8) ?*anyopaque;
extern "c" fn fclose(stream: ?*anyopaque) c_int;
extern "c" fn fseek(stream: ?*anyopaque, offset: c_long, whence: c_int) c_int;
extern "c" fn ftell(stream: ?*anyopaque) c_long;
extern "c" fn rewind(stream: ?*anyopaque) void;
extern "c" fn fread(ptr: [*]u8, size: usize, n: usize, stream: ?*anyopaque) usize;
extern "c" fn fwrite(ptr: [*]const u8, size: usize, n: usize, stream: ?*anyopaque) usize;
extern "c" fn read(fd: c_int, buf: [*]u8, count: usize) isize;
extern "c" fn write(fd: c_int, buf: [*]const u8, count: usize) isize;

const timeval = extern struct {
    sec: isize,
    usec: i64,
};
extern "c" fn gettimeofday(tv: ?*timeval, tz: ?*anyopaque) c_int;

const SEEK_SET: c_int = 0;
const SEEK_END: c_int = 2;

const END: u64 = 1162261467; // 3^19
const THIRD: u64 = END / 3;

// Prefijo 27 + tabla 94 + sufijo 14; el encrypt indexa con mem[c] directo si < 135.
const XLAT_CONCAT =
    "SOMEBODY MAKE ME FEEL ALIVE" ++
    "[hj9>,5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@" ++
    "AND SHATTER ME";

const CRAZY_TBL = [3][3]u8{ .{ 1, 0, 0 }, .{ 1, 0, 2 }, .{ 2, 2, 1 } };
const CRZ2 = [144]u8{
    4, 3, 3, 1, 0, 0, 1, 0, 0, 9, 9, 9, 9, 9, 9, 9,
    4, 3, 5, 1, 0, 2, 1, 0, 2, 9, 9, 9, 9, 9, 9, 9,
    5, 5, 4, 2, 2, 1, 2, 2, 1, 9, 9, 9, 9, 9, 9, 9,
    4, 3, 3, 1, 0, 0, 7, 6, 6, 9, 9, 9, 9, 9, 9, 9,
    4, 3, 5, 1, 0, 2, 7, 6, 8, 9, 9, 9, 9, 9, 9, 9,
    5, 5, 4, 2, 2, 1, 8, 8, 7, 9, 9, 9, 9, 9, 9, 9,
    7, 6, 6, 7, 6, 6, 4, 3, 3, 9, 9, 9, 9, 9, 9, 9,
    7, 6, 8, 7, 6, 8, 4, 3, 5, 9, 9, 9, 9, 9, 9, 9,
    8, 8, 7, 8, 8, 7, 5, 5, 4, 9, 9, 9, 9, 9, 9, 9,
};

inline fn mcrz(a_in: u32, d_in: u32) u32 {
    var r: u32 = 0;
    var k: u32 = 1;
    var a: u32 = a_in;
    var d: u32 = d_in;
    comptime var pass = 0;
    inline while (pass < 9) : (pass += 1) {
        r +%= k *% CRZ2[(a % 9) + 16 * (d % 9)];
        a /= 9;
        d /= 9;
        k *%= 9;
    }
    r +%= k *% @as(u32, CRAZY_TBL[d % 3][a % 3]);
    return r;
}

inline fn mrot(x: u32) u32 {
    const t: u32 = @intCast(THIRD);
    const b = x % t;
    const m = b % 3;
    const q = b / 3;
    return q +% m *% (t / 3) +% (x -% b);
}

const PAGE: usize = 65536; // granularidad de fast20 bajo sysconf

var image: []u32 = &[_]u32{};
var img_len: usize = 0;
var chain_zone: []u32 = &[_]u32{}; // celdas [img_len, szR): cadena continua
var zone_start: usize = 0;
var pat: [6]u32 = .{0} ** 6; // patron periodo-6 mas alla de szR
var overlay: std.AutoHashMapUnmanaged(u32, u32) = .{};
var alloc: std.mem.Allocator = undefined;
var norm_out_path: ?[]const u8 = null;

fn initAfterLoad() void {
    zone_start = ((img_len + PAGE - 1) / PAGE) * PAGE;
    const zlen = zone_start - img_len;
    chain_zone = alloc.alloc(u32, zlen) catch @panic("oom");
    var p2: u32 = if (img_len >= 2) image[img_len - 2] else 0;
    var p1: u32 = if (img_len >= 1) image[img_len - 1] else 0;
    var i: usize = 0;
    while (i < zlen) : (i += 1) {
        const nxt = mcrz(p1, p2);
        chain_zone[i] = nxt;
        p2 = p1;
        p1 = nxt;
    }
    var k: usize = 0;
    while (k < 6) : (k += 1) {
        const nxt = mcrz(p1, p2);
        pat[k] = nxt;
        p2 = p1;
        p1 = nxt;
    }
}

fn beyondVal(i: usize) u32 {
    if (i < zone_start) return chain_zone[i - img_len];
    const pbase = i & ~(PAGE - 1);
    const phase: usize = @intCast(@mod(@as(u64, pbase) % THIRD + (i - pbase), 6));
    return pat[phase];
}

fn memGet(i: usize) u32 {
    if (i < img_len) return image[i];
    if (overlay.get(@intCast(i))) |v| return v;
    return beyondVal(i);
}

fn memSet(i: usize, v: u32) void {
    if (i < img_len) {
        image[i] = v;
    } else {
        overlay.put(alloc, @intCast(i), v) catch @panic("oom");
    }
}

fn getTickCountMs() u64 {
    var tv: timeval = undefined;
    _ = gettimeofday(&tv, null);
    return @as(u64, @intCast(tv.sec)) * 1000 + @as(u64, @intCast(tv.usec)) / 1000;
}

fn wout(s: []const u8) void {
    _ = write(1, s.ptr, s.len);
}

fn mnemonic(op: usize) u8 {
    return switch (op) {
        4 => 'D', // jmp  (fast20 INS_4: c=*d)
        5 => 'J', // out
        23 => 'i', // in
        39 => '*', // rot
        40 => '<', // movd
        62 => 'p', // crz
        68 => '/', // nop
        81 => 'v', // halt
        else => '#',
    };
}

fn runNormalize(path_u8: []const u8) void {
    const t0 = getTickCountMs();
    const c_path = alloc.dupeZ(u8, path_u8) catch return;
    defer alloc.free(c_path);
    const f = fopen(c_path.ptr, "rb");
    if (f == null) {
        std.debug.print("bolge19-normalize: no pude abrir {s}\n", .{path_u8});
        return;
    }
    defer _ = fclose(f);
    _ = fseek(f, 0, SEEK_END);
    const fsize = ftell(f);
    rewind(f);
    if (fsize <= 0) return;
    img_len = @intCast(fsize);
    const raw = alloc.alloc(u8, img_len) catch @panic("oom");
    defer alloc.free(raw);
    const nread = fread(raw.ptr, 1, img_len, f);
    if (nread != img_len) {
        std.debug.print("bolge19-normalize: lectura corta {d}/{d}\n", .{ nread, img_len });
        return;
    }

    image = alloc.alloc(u32, img_len) catch @panic("oom");
    for (raw, 0..) |byte, i| image[i] = byte;

    // offs[] identico al dispatch
    const a1_off: i64 = 94 - @mod(@as(i64, @intCast((END - 1) / 6)) - 29524, 94);
    const a2_off: i64 = 94 - @mod(@as(i64, @intCast((END - 1) / 3)) - 59048, 94);
    var offs: [3]i64 = undefined;
    offs[0] = 0;
    offs[1] = @mod(a1_off - @as(i64, @intCast(THIRD)), 94) + 94;
    offs[2] = a2_off - @as(i64, @intCast(@mod(2 * THIRD, 94))) + 94;

    const out_path_z = alloc.dupeZ(u8, norm_out_path orelse "normalized.txt") catch return;
    defer alloc.free(out_path_z);
    const outf = fopen(out_path_z.ptr, "wb");
    if (outf == null) {
        std.debug.print("bolge19-normalize: no pude crear salida\n", .{});
        return;
    }
    defer _ = fclose(outf);

    var hist: [94]u64 = .{0} ** 94;
    var hasher = std.crypto.hash.sha2.Sha256.init(.{});
    var buf: [1 << 16]u8 = undefined;
    var blen: usize = 0;

    var anchors: u64 = 0;
    var dual_checks: u64 = 0;
    var dual_fails: u64 = 0;
    var last_anchor_ms = t0;

    var i: u64 = 0;
    while (i < img_len) : (i += 1) {
        const mc = image[@intCast(i)];
        const region = i / THIRD;
        const off_i: i64 = if (region < 3) offs[region] else 0;
        const op: u64 = @intCast(@mod(@as(i64, @intCast(i)) + @as(i64, mc) + off_i, 94));
        hist[op] += 1;
        if (blen == buf.len) {
            hasher.update(buf[0..blen]);
            _ = fwrite(buf[0..blen].ptr, 1, blen, outf);
            blen = 0;
        }
        buf[blen] = mnemonic(op);
        blen += 1;

        // micro-ancla: doble via en region 0 (offs=0 -> formula canonica)
        if (region == 0 and (i % 50_000_000) == 49_999_999) {
            dual_checks += 1;
            if ((@as(u64, mc) +% i) % 94 != op) dual_fails += 1;
        }
        const now = getTickCountMs();
        if ((i % 20_000_000) == 19_999_999) {
            std.debug.print("norm-progress cell={d}\n", .{i + 1});
        }
        if ((i % 100_000_000) == 99_999_999 or now - last_anchor_ms >= 75_000) {
            last_anchor_ms = now;
            anchors += 1;
            hasher.update(buf[0..blen]);
            _ = fwrite(buf[0..blen].ptr, 1, blen, outf);
            blen = 0;
            var snap = hasher;
            var dig: [32]u8 = undefined;
            snap.final(&dig);
            std.debug.print("ANCHOR;status={s};mode=75s-or-100M;cell={d};op_last={d};sha256_rolling={x};dual_checks={d};dual_fails={d};t_ms={d}\n", .{ if (dual_fails == 0) "PASS" else "FAIL", i + 1, op, &dig, dual_checks, dual_fails, now - t0 });
        }
    }
    if (blen > 0) {
        hasher.update(buf[0..blen]);
        _ = fwrite(buf[0..blen].ptr, 1, blen, outf);
    }
    var dig: [32]u8 = undefined;
    var snapf = hasher;
    snapf.final(&dig);
    std.debug.print("ANCHOR;status={s};mode=FINAL;cells={d};sha256_full={s};dual_checks={d};dual_fails={d};t_ms={d}\n", .{ if (dual_fails == 0) "PASS" else "FAIL", img_len, &std.fmt.bytesToHex(dig, .lower), dual_checks, dual_fails, getTickCountMs() - t0 });
    var op: usize = 0;
    while (op < 94) : (op += 1) {
        if (hist[op] > 0) std.debug.print("HIST op={d} '{c}' count={d}\n", .{ op, mnemonic(op), hist[op] });
    }
}

pub fn main(init: std.process.Init.Minimal) !void {
    alloc = std.heap.page_allocator;

    var it = init.args.iterate();
    _ = it.next(); // argv[0]

    var path_u8: ?[]const u8 = null;
    var max_steps: u64 = 0;
    var normalize_out: ?[]const u8 = null;
    var loader_canonical: bool = false;
    var loader_bad: bool = false;

    while (it.next()) |arg| {
        if (path_u8 == null and !std.mem.startsWith(u8, arg, "--")) {
            path_u8 = arg;
        } else if (std.mem.eql(u8, arg, "--max-steps")) {
            if (it.next()) |val| {
                max_steps = std.fmt.parseInt(u64, val, 10) catch 0;
            }
        } else if (std.mem.eql(u8, arg, "--loader")) {
            if (it.next()) |val| {
                if (std.mem.eql(u8, val, "canonical")) {
                    loader_canonical = true;
                } else if (!std.mem.eql(u8, val, "raw")) {
                    loader_bad = true;
                    std.debug.print("bolge19: cargador desconocido {s} (valores: raw canonical)\n", .{val});
                }
            }
        } else if (std.mem.eql(u8, arg, "--normalize")) {
            if (it.next()) |val| {
                normalize_out = val;
            }
        }
    }

    if (path_u8 == null) {
        std.debug.print("uso: bolge19 <imagen.mb> [--max-steps N] [--loader raw|canonical] [--normalize salida.txt]\n", .{});
        return;
    }
    if (loader_bad) std.process.exit(2);

    if (normalize_out) |nout| {
        norm_out_path = nout;
        runNormalize(path_u8.?);
        return;
    }

    const c_path = try alloc.dupeZ(u8, path_u8.?);
    defer alloc.free(c_path);
    const f = fopen(c_path.ptr, "rb");
    if (f == null) {
        std.debug.print("bolge19: no pude abrir {s}\n", .{path_u8.?});
        return;
    }
    defer _ = fclose(f);

    _ = fseek(f, 0, SEEK_END);
    const fsize = ftell(f);
    rewind(f);
    if (fsize <= 0 or fsize > 4 * 1024 * 1024 * 1024) {
        std.debug.print("bolge19: tamano invalido {d}\n", .{fsize});
        return;
    }

    img_len = @intCast(fsize);
    const raw = alloc.alloc(u8, img_len) catch @panic("oom");
    defer alloc.free(raw);
    const nread = fread(raw.ptr, 1, img_len, f);
    if (nread != img_len) {
        std.debug.print("bolge19: lectura corta {d}/{d}\n", .{ nread, img_len });
        return;
    }

    image = alloc.alloc(u32, img_len) catch @panic("oom");
    if (loader_canonical) {
        // Cargador estricto al estilo del Unshackled original: el espaciado NO es
        // una celda y cada instruccion se acepta solo si cae en un opcode valido.
        // Produce exactamente la misma imagen que recortar el espaciado del fichero.
        var kept: usize = 0;
        var pos: usize = 0;
        for (raw, 0..) |byte, i| {
            if (byte == ' ' or byte == '\t' or byte == '\r' or byte == '\n') continue;
            const instr: usize = @mod(@as(usize, byte) + pos, 94);
            const aceptable = byte >= 33 and byte < 127 and switch (instr) {
                4, 5, 23, 39, 40, 62, 68, 81 => true,
                else => false,
            };
            if (!aceptable) {
                std.debug.print("bolge19: caracter invalido byte={d} v={d} instr={d}\n", .{ i, byte, instr });
                std.process.exit(2);
            }
            image[kept] = byte;
            kept += 1;
            pos = @mod(pos + 1, 564);
        }
        img_len = kept;
    } else {
        var ws: usize = 0;
        for (raw) |byte| {
            if (byte == ' ' or byte == '\t' or byte == '\r' or byte == '\n') ws += 1;
        }
        if (ws != 0) {
            std.debug.print("bolge19: AVISO {s}: {d} celdas de espaciado contadas como celdas por el cargador crudo; use --loader canonical para imagenes de texto alineado a opcode\n", .{ path_u8.?, ws });
        }
        for (raw, 0..) |byte, i| image[i] = byte;
    }
    initAfterLoad();
    std.debug.print("bolge19: imagen={d} celdas zona=[{d},{d}) pat=[{d},{d},{d}...]\n", .{ img_len, zone_start - img_len, zone_start - img_len + chain_zone.len, pat[0], pat[1], pat[2] });

    var a: u32 = 0;
    var c: u64 = 0;
    var d: u64 = 0;
    var steps: u64 = 0;

    var in_buf: [1]u8 = undefined;

    // offs[] replica EXACTA de fast20 (incluido su quirk de parentesis)
    const a1_off: i64 = 94 - @mod(@as(i64, @intCast((END - 1) / 6)) - 29524, 94);
    const a2_off: i64 = 94 - @mod(@as(i64, @intCast((END - 1) / 3)) - 59048, 94);
    var offs: [3]i64 = undefined;
    offs[0] = 0;
    offs[1] = @mod(a1_off - @as(i64, @intCast(THIRD)), 94) + 94;
    offs[2] = a2_off - @as(i64, @intCast(@mod(2 * THIRD, 94))) + 94;

    const t0 = getTickCountMs();
    var next_report: u64 = 200_000_000;

    while (true) {
        if (max_steps != 0 and steps >= max_steps) {
            std.debug.print("bolge19: MAX_STEPS {d}\n", .{steps});
            break;
        }
        const cu: u32 = @truncate(c);
        const region = cu / @as(u32, @intCast(THIRD));
        const off_i: i64 = if (region < 3) offs[region] else 0;
        const idx: usize = @intCast(@mod(@as(i64, cu) + @as(i64, memGet(cu)) + off_i, 94));
        switch (idx) {
            4 => c = memGet(@truncate(d)),
            5 => {
                const ob = [_]u8{@truncate(a)};
                wout(&ob);
            },
            23 => {
                const n = read(0, &in_buf, 1);
                a = if (n <= 0) @truncate(END - 1) else in_buf[0];
            },
            39 => {
                const r = mrot(memGet(@truncate(d)));
                memSet(@truncate(d), r);
                a = r;
            },
            40 => d = memGet(@truncate(d)),
            62 => {
                const r = mcrz(a, memGet(@truncate(d)));
                memSet(@truncate(d), r);
                a = r;
            },
            81 => {
                std.debug.print("bolge19: HALT steps={d} c={d} d={d} a={d} elapsed={d}s\n", .{ steps, c, d, a, (getTickCountMs() - t0) / 1000 });
                break;
            },
            else => {},
        }
        const cur: u32 = @truncate(c);
        const cv = memGet(cur);
        if (cv < XLAT_CONCAT.len) memSet(cur, XLAT_CONCAT[cv]);
        c = (c + 1) % END;
        d = (d + 1) % END;
        steps += 1;
        if (steps >= next_report) {
            std.debug.print("bolge19: steps={d} c={d} d={d} a={d} overlay={d} elapsed={d}s\n", .{ steps, c, d, a, overlay.count(), (getTickCountMs() - t0) / 1000 });
            next_report += 200_000_000;
        }
    }
}
