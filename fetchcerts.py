#!/usr/bin/python3

import urllib.request
import json
import os

CERTIFICATES_URL = "https://api.check-at.at/api/v1/certificates"
HEADERS = {"x-api-key": "1Rrt0JmIUyHM6ARj"}

OPENSSL_CMD_TEMPL = (
    "openssl ec -pubin -in certs/{name}.pem -param_enc named_curve "
    "-pubout -out certs_named/{name}.pem")

req = urllib.request.Request(CERTIFICATES_URL, headers=HEADERS)
resp = urllib.request.urlopen(req)
assert 200 <= resp.status < 400
resp_bytes = resp.read()
resp_json = json.loads(resp_bytes.decode("utf-8"))

try:
    os.mkdir("certs")
    os.mkdir("certs_named")
except FileExistsError:
    pass

os.makedirs("certs", exist_ok=True)
os.makedirs("certs_named", exist_ok=True)

for cert_entry in resp_json:
    cert_path = "certs/{}.pem".format(cert_entry["certificate_id"])
    print("Exporting", cert_path)
    with open(cert_path, "w") as cert_file:
        cert_file.write(cert_entry["public_key"])

print()
print("Now convert them using:")
for cert_entry in resp_json:
    print(OPENSSL_CMD_TEMPL.format(name=cert_entry["certificate_id"]))
