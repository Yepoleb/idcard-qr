# Austrian ID Card QR Code

This document aims to be a complete documentation of the format used in the QR area on the back of new Austrian ID cards (Personalausweis) issued after 2nd of August 2021. The launch was acompanied by the introduction of the CHECK-AT app to cryptographically verify the data contained in the code. Unfortunately there is no public documentation of its format and the app is proprietary and obfuscated. The official website claims an open source release is being evaluated, but considering the technology is developed by a private company, youniqx Identity AG, which wants to sell it to other countries as well, I don't believe it will ever happen. I want publicly funded technology to be open source though, so I decided to make my own documentation, hoping anyone who's good at app development will pick it up and make an app.

## Sections of the QR Code

The QR code consists of 6 semicolon (`;`) separated sections. Some of them are padded with spaces. They are listed here in the same order as they are in the encoding.

### Part 1: Signature

The signature is a base64 encoded hexstring where the first 64 hex characters represent the r value of an ECDSA signature and the last 64 characters represent the s number. Some crypto libraries want the r and s values individually, some as a concatenated bytestring and others as a DER encoded binary. You can create such a DER encoding using the `ecdsa.util.sigcode_der` function of the ecdsa Python module for example. Most crypto libraries have some way to convert signatures to and from DER encoding.

### Part 2: IV

Another base64 encoded hexstring. It is only relevant for generating the signature data.

### Part 3: Signature ID

Not really a signature ID, but that's what it's called in the code. It is actually a certificate identifier. Judging from the data we currently have, private keys will get rotated every couple of months and this identifier tells you which certificate to use. This is the only part that is not encoded in any way.

### Part 4: MRZ

MRZ is the machine readable zone on the back of the identification card which is printed in big monospace letters and has lots of angle brackets. The format is well documented and human readable, so I will not be covering it in this document. This part is base64 encoded.

### Part 5: Name

Full name in uppercase letters separated by newlines, also base64 encoded.

### Part 6: Image

Very low-res version of the photo on the card in the rather obscure [JPEG2000](https://en.wikipedia.org/wiki/JPEG_2000) format and again base64 encoded. JPEG2000 is not the same as the well supported original JPEG standard and might require specialized software to view. Writing the bytestream to a file with a `.jp2` extension seems to be all that's needed to view the content in those programs though.

## API

Intercepting the web traffic by the app there were a few API endpoints of which only one was actually useful. I'm documenting them all for completeness though. The app always sets the `x-api-key` header to `1Rrt0JmIUyHM6ARj`, although this does not seem to be required to access the data. The key is hardcoded and I am not aware of any others.

Example request:

```sh
curl -H "x-api-key: 1Rrt0JmIUyHM6ARj" https://api.check-at.at/api/v1/certificates
```

### /ready

I don't really know what the point of this is. It just returns a success value.

Full URL: https://api.check-at.at/api/v1/ready

Example response:

```json
{"success": true}
```

### /certificates

This endpoint returns the certificate data used to verify the signatures. The example response only lists one certificate, but there are multiple.

Full URL: https://api.check-at.at/api/v1/certificates

```json
[{
  "certificate_id": "A16ATS004008",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBMzCB7AYHKoZIzj0CATCB4AIBATAsBgcqhkjOPQEBAiEAqftX26Huqbw+ZgqQ\nnYONcm479iPVJiAoIBNIHR9uU3cwRAQgfVoJdfwsMFfu9nUwQXr/5/uAVcEm3Fxs\n6UpLRPMwtdkEICbcXGzpSktE8zC12bvXfL+VhBYpXPfhzmvM3Bj/jAe2BEEEi9Ku\nuct+V8ssS0gv/IG3r7neJ+HjvSPCOkRTvZrOMmJUfvg1w9rE/Zf4RhoUYR3JwndF\nEy3tjlRcHVTHLwRplwIhAKn7V9uh7qm8PmYKkJ2DjXGMOXqjtWGm95AeDoKXSFan\nAgEBA0IABIFUQPj5oSWqeV7HqNKmQaUwEmChzR02q6K9Gjcr6UPjUdZAxd/51L2b\nyb1n0kFQoLMwEZBcUaF7G2LSfgLw6k0=\n-----END PUBLIC KEY-----",
  "valid_until": "2031-08-15T11:10:40Z"
}]
```

### /documents

Returns some kind of document directory. At the time of writing only has one entry.

Full URL: https://api.check-at.at/api/v1/documents

```json
[{
  "document_id": 1,
  "name": "Personalausweis",
  "steps_updated_at": "2021-08-17T15:52:09.908791Z"
}]
```

### steps/1

Lists the steps to manually check the ID card by the person using the app. It's unclear why this is even loaded because the content is unlikely to change so rapidly that it would warrant building an API for it.

Full URL: https://api.check-at.at/api/v1/steps/1

No example provided because it would take up too much space.

## Cryptography

The signature algorithm is ECDSA with SHA256. The certificates use a brainpoolP256r1 curve.

### Key Format

The certificates API returns PEM encoded public keys. They are not proper certificate because they are not signed by any entity and do not contain any of the usual attributes like a common name or expiration date. A function made for loading public keys has to be used instead of one for certificates.

Another pitfall is that the curve of the keys is encoded explicitly. This means that in addition to the public or private bits they contain each of the parameters that make up an elliptic curve. Very few tools and libraries seem to be able to deal with this format and instead expected a "named" curve where the parameters are given by a standardized name like `nistp256` or `brainpoolP256r1`.

OpenSSL can be used to convert between the two key types. The `-param_enc` parameter of the `openssl ec` utility defines which format will be used. Details can be found in the [manpage](https://manpages.debian.org/stable/openssl/ec.1ssl.en.html). An example command is given below:

```sh
openssl ec -pubin -in key_explicit.pem -param_enc named_curve -pubout -out key_named.pem
```

### Signed Data

An important part of verifying signatures is getting a reproducible representation of the data to be signed. In this case it is comprised of the items listed below concatenated in order without any separation.

* The IV value with the hex values decoded to binary
* The signature ID encoded as ASCII
* A single line feed (`\n` or 0x0A)
* The MRZ data as decoded from base64
* The name data as decoded
* The image data as decoded

For an example check the provided Python code.

## Demo usage

At first the certificates have to be fetched from the API. They will be placed in the directory `certs`. Another directory `certs_named` will also be created to be used later.

```sh
python3 fetchcerts.py
```

The script will tell you to convert the explicit certificates to named ones using a command like this:

```sh
openssl ec -pubin -in certs/A16ATS004008.pem -param_enc named_curve -pubout -out certs_named/A16ATS004008.pem
```

Be aware that while fetching and converting the certificates is a separate step, it should be repeated regularly because new certificates will very likely be added with time. 

Now to get the data to be verified scan the QR code on the ID card and copy it to a text file. Whitespace is irrelevant and does not need to be preserved. I have named my file `qr_data.txt`. It can now be decoded and verified.

```sh
python3 verifydata.py qt_data.txt
```

## OpenSSL usage

OpenSSL can use the original certificates without conversion. To try it modify the example to write `sign_data` to a binary file. I'll call it `sign_data.bin` in this example. Then convert the signature to DER which can be done using the following code and write it also to a file.

```py3
import ecdsa.util
signature_r = int(signature[:64], 16)
signature_s = int(signature[64:], 16)
signature_der = ecdsa.util.sigencode_der(signature_r, signature_s, order=None)
```

Then openssl can be called to verify the signature:

```sh
openssl dgst -sha256 -verify certs/A16ATS004008.pem -signature signature_der.bin sign_data.bin
```

## License

* CC BY 4.0

