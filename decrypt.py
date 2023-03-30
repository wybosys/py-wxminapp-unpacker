#!/usr/bin/env python3

from argparse import ArgumentParser
import re
import os
from hashlib import pbkdf2_hmac
from Crypto.Cipher import AES

PAT_WXMINAPP = re.compile(r'wx[a-z0-9]+')


def IsCrypted(f: str) -> bool:
    with open(f, 'b+r') as fd:
        buf = fd.read(6)
        # print(buf)
        if buf == b'V1MMWX':
            return True
        buf += fd.read(8)
        # print(buf)
        if buf[0] != ord('\xBE') or buf[13] != ord('\xED'):
            raise Exception('不是微信小程序')
    return False


def GenAesKey(wxAppId: str) -> bytes:
    raw = pbkdf2_hmac('sha1', wxAppId.encode(), b'saltiest', 1000, 32)
    # print(raw, len(raw))
    return raw


def DecryptWxApkg(f: str, wxAppId: str) -> bool:
    print('准备解密', f)
    if not IsCrypted(f):
        print('不需要解密', f)
        return True

    out = bytes()

    with open(f, 'b+r') as fd:
        # 跳过magic
        fd.seek(6)

        # 解密文件头
        buf = fd.read(1024)
        key = GenAesKey(wxAppId)
        aes = AES.new(key, AES.MODE_CBC, 'the iv: 16 bytes'.encode())
        buf = aes.decrypt(buf)
        # print(buf)
        if buf[0] != ord('\xBE') or buf[13] != ord('\xED'):
            raise Exception('不是微信小程序')
        out += buf[:-1]  # 跳过结束符

        # 解密数据段
        buf = bytearray(fd.read())
        key = ord(wxAppId[len(wxAppId) - 2])
        for idx in range(len(buf)):
            buf[idx] ^= key
        # print(buf)
        out += buf

        # 输出
        of = f.replace('.wxapkg', '.raw.wxapkg')
        print("输出", of)
        with open(of, 'b+w') as outfd:
            outfd.write(out)


def decrypt(d: str, wxAppId: str):
    for each in os.listdir(d):
        f = d + '/' + each
        if os.path.isfile(f):
            if each.endswith('.wxapkg') and not each.endswith('.raw.wxapkg'):
                DecryptWxApkg(f, wxAppId)
        else:
            decrypt(f, wxAppId)


def GetWxAppID(d: str) -> str:
    base = os.path.basename(d)
    res = PAT_WXMINAPP.findall(base)
    if not res:
        return None
    return base


def Decrypt(d: str):
    appId = GetWxAppID(d)
    if not appId:
        raise Exception('不是正确的微信小程序目录')
    decrypt(d, appId)


if __name__ == '__main__':
    args = ArgumentParser()
    args.add_argument('app', help='小程序目录，类似 wxxxxxxxx0 的格式')
    args = args.parse_args()

    Decrypt(args.app)
