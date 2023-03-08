import OpenSSL.crypto
from Crypto.Util import asn1


def is_validate_ssl_pair(ssl_key_string, ssl_cert_string):
    crypt = OpenSSL.crypto
    try:
        cert = crypt.load_certificate(crypt.FILETYPE_PEM, ssl_cert_string)
    except OpenSSL.crypto.Error:
        print('Certificate is not correct')
        return False
    try:
        private_key = crypt.load_privatekey(crypt.FILETYPE_PEM, ssl_key_string)
    except OpenSSL.crypto.Error:
        print('Private key is not correct')
        return False

    public_key = cert.get_pubkey()

    if public_key.type() != crypt.TYPE_RSA or private_key.type() != crypt.TYPE_RSA:
        print('Can only handle RSA keys')
        return False

    public_asn1 = crypt.dump_privatekey(crypt.FILETYPE_ASN1, public_key)
    private_asn1 = crypt.dump_privatekey(crypt.FILETYPE_ASN1, private_key)

    pub_der = asn1.DerSequence()
    pub_der.decode(public_asn1)
    private_der = asn1.DerSequence()
    private_der.decode(private_asn1)

    pub_modulus = pub_der[1]
    private_modulus = private_der[1]

    if pub_modulus == private_modulus:
        return True
    else:
        return False
