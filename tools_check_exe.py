# -*- coding: utf-8 -*-
"""检查打包出的 exe 的 PE 头信息（架构、子系统、最低系统版本）。

用法：python tools_check_exe.py ["dist/Paji v1.5.exe"]
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, 'dist', 'Paji v1.5.exe')

MACHINES = {0x8664: 'x64', 0x14c: 'x86', 0xAA64: 'ARM64'}
SUBSYSTEMS = {2: 'WINDOWS_GUI', 3: 'WINDOWS_CUI'}


def pe_info(path):
    with open(path, 'rb') as f:
        data = f.read()

    if data[:2] != b'MZ':
        raise ValueError('不是 PE 文件')

    e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
    if data[e_lfanew:e_lfanew + 4] != b'PE\0\0':
        raise ValueError('PE 签名不对')

    machine = struct.unpack_from('<H', data, e_lfanew + 4)[0]
    sections = struct.unpack_from('<H', data, e_lfanew + 6)[0]
    opt = e_lfanew + 24
    magic = struct.unpack_from('<H', data, opt)[0]
    major_os, minor_os = struct.unpack_from('<HH', data, opt + 40)
    major_ss, minor_ss = struct.unpack_from('<HH', data, opt + 48)
    subsystem = struct.unpack_from('<H', data, opt + 68)[0]
    pe64 = magic == 0x20B

    return {
        'file': os.path.basename(path),
        'size_mb': round(os.path.getsize(path) / 1048576, 2),
        'machine': MACHINES.get(machine, hex(machine)),
        'pe32+': pe64,
        'sections': sections,
        'os_version': f'{major_os}.{minor_os}',
        'subsystem_version': f'{major_ss}.{minor_ss}',
        'subsystem': SUBSYSTEMS.get(subsystem, hex(subsystem)),
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if not os.path.exists(path):
        print('找不到 exe：', path)
        return 1
    info = pe_info(path)
    print('=' * 56)
    print('PE 兼容性检查')
    print('=' * 56)
    for k, v in info.items():
        print(f'  {k:20s} {v}')
    print()
    ok = True
    if info['machine'] != 'x64':
        print('  [!] 不是 x64，Win10/11 主流环境需要 x64')
        ok = False
    if info['subsystem'] != 'WINDOWS_GUI':
        print('  [!] 不是 GUI 子系统，运行会带控制台窗口')
        ok = False
    if info['os_version'] not in ('6.0', '6.1', '10.0'):
        print(f'  [!] 目标系统版本 {info["os_version"]} 需要确认')
        ok = False
    print('  结论：' + ('Windows 10 / 11 (x64) 可执行' if ok else '需进一步检查'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
