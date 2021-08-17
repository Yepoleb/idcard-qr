#!/usr/bin/python3

import base64
import sys
import hashlib

import ecdsa

if len(sys.argv) != 2:
    print("Verify and dump Austrian identity card QR data")
    print("Usage: python3 verifydata.py <qr_data.txt>")
    print("Certificates are loaded from certs_named/ and an image file is written to image.jp2")

qrpath = sys.argv[1]

qrdata = open(qrpath).read()

sections_data = [s.strip() for s in qrdata.split(";")]
sections_decoded = [base64.b64decode(sec) for sec in sections_data]

signature = sections_decoded[0].decode("ascii")
iv = sections_decoded[1].decode("ascii")
signature_id = sections_data[2]
mrz = sections_decoded[3] # Undecoded because I don't know the encoding
name = sections_decoded[4]
image = sections_decoded[5]


signature_bytes = bytes.fromhex(signature)
iv_bytes = bytes.fromhex(iv)
sign_data = iv_bytes + signature_id.encode("ascii") + b"\n" + mrz + name + image

with open("certs_named/{}.pem".format(signature_id), "rb") as key_file:
    key = ecdsa.VerifyingKey.from_pem(key_file.read())

key.verify(signature_bytes, sign_data, hashfunc=hashlib.sha256)
print("Data verified!")

print("Signature:", signature)
print("IV:", iv)
print("Signature ID:", signature_id)
print("MRZ:", mrz)
print("Name:", name)
print("Image:", "Stored at image.jp2")

open("image.jp2", "wb").write(image)
