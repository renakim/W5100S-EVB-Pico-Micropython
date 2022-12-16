# Certificate

certificates are required to connect to the AWS IoT endpoint.

* Device Certificate
* Device Private key

```
# Certificate path
cert_file = 'cert/device_cert.crt.der'
key_file = 'cert/privateKey.key.der'
```

## Convert certificates

Convert the downloaded certificate files to `der` form.

```
openssl x509 -outform der -in device_cert.pem.cert -out device_cert.crt.der
openssl rsa -inform pem -in privateKey.pem.key -outform DER -out privateKey.key.der
```
