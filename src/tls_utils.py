from OpenSSL import SSL

from OpenSSL import crypto

def get_common_name(certfile):
    """
    从证书文件中提取 Common Name (CN)。
    :param certfile: 证书文件路径
    :return: CN 字符串
    """
    with open(certfile, "rb") as f:
        cert_data = f.read()
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
    return cert.get_subject().CN


def create_tls_context(certfile, keyfile, cafile=None, server_side=False):
    """
    创建TLS上下文，用于客户端与服务端的加密通信。
    :param certfile: 证书文件路径
    :param keyfile: 私钥文件路径
    :param cafile: CA证书文件路径，用于验证对方身份
    :param server_side: 是否为服务端模式
    :return: TLS上下文对象
    """
    context = SSL.Context(SSL.TLS_METHOD)
    context.use_certificate_file(certfile)
    context.use_privatekey_file(keyfile)
    if cafile:
        context.load_verify_locations(cafile)
        context.set_verify(SSL.VERIFY_PEER, lambda conn, x509, errnum, errdepth, ok: ok)
    # context.set_mode(SSL.MODE_AUTO_RETRY)
    if server_side:
        context.set_options(SSL.OP_SINGLE_DH_USE | SSL.OP_SINGLE_ECDH_USE)
    return context
