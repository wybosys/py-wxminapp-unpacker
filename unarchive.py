#!/usr/bin/env python3

from argparse import ArgumentParser

import decrypt
import os
import shutil


class ArchivedFile:
    name: str
    offset: int
    length: int


def GetFileList(srcFile: str) -> list[ArchivedFile]:
    ret = []
    with open(srcFile, 'b+r') as fd:
        fd.seek(0xe)
        count = int.from_bytes(fd.read(4), 'big')
        for _ in range(count):
            t = ArchivedFile()
            lname = int.from_bytes(fd.read(4), 'big')
            t.name = fd.read(lname)
            t.offset = int.from_bytes(fd.read(4), 'big')
            t.length = int.from_bytes(fd.read(4), 'big')

            # print(lname, len(t.name), t.name, hex(t.offset), t.length)
            t.name = t.name.decode()
            ret.append(t)
    return ret


def UnArchiveFiles(files: list[ArchivedFile], srcFile: str, destDir: str):
    with open(srcFile, 'b+r') as srcfd:
        for file in files:
            tgt = destDir + '/' + file.name
            dirs = os.path.dirname(tgt)
            if not os.path.isdir(dirs):
                os.makedirs(dirs)
            print('输出到:', tgt)
            with open(tgt, 'b+w') as destfd:
                srcfd.seek(file.offset)
                buf = srcfd.read(file.length)
                destfd.write(buf)

                if tgt.endswith('.json'):
                    print(buf)


def UnArchiveWxApkg(srcFile: str, destDir: str):
    print('准备解压', srcFile)
    files = GetFileList(srcFile)
    # print(files)
    UnArchiveFiles(files, srcFile, destDir)


def unarchive(src: str, dest: str, wxAppId: str):
    for each in os.listdir(src):
        f = src + '/' + each
        if os.path.isfile(f):
            if each.endswith('.wxapkg') and not decrypt.IsCrypted(f):
                UnArchiveWxApkg(f, dest)
        else:
            unarchive(f, dest, wxAppId)


def UnArchive(src: str, dest: str):
    appId = decrypt.GetWxAppID(src)
    if not appId:
        raise Exception('不是正确的微信小程序目录')
    if not os.path.isdir(dest):
        os.makedirs(dest)
    unarchive(src, dest, appId)


if __name__ == '__main__':
    args = ArgumentParser()
    args.add_argument('wxapp', help='小程序目录')
    args.add_argument('output', help='输出目录')
    args = args.parse_args()

    UnArchive(args.wxapp, args.output)
