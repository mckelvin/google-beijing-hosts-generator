# coding: UTF-8

from M2Crypto import SSL


def get_ssl_subject_CN(ip_address, ssl_port=443):
    ctx = SSL.Context()
    ctx.set_allow_unknown_ca(True)
    ctx.set_verify(SSL.verify_none, 1)
    conn = SSL.Connection(ctx)
    conn.postConnectionCheck = None
    timeout = SSL.timeout(1)
    conn.set_socket_read_timeout(timeout)
    conn.set_socket_write_timeout(timeout)
    try:
        conn.connect((ip_address, ssl_port))
    except:
        return

    cert = conn.get_peer_cert()
    try:
        c_CN = cert.get_subject().CN
    except AttributeError:
        c_CN = ""
    conn.close()
    return c_CN

if __name__ == '__main__':
    assert get_ssl_subject_CN('203.208.36.1') == '*.google.com'
