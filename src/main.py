# coding: UTF-8
#
# 自动解析部分Google北京hosts
# author: mckelvin

import subprocess
import multiprocessing as mp
import shelve
from fnmatch import fnmatch
from optparse import OptionParser
from util import get_ssl_subject_CN

SHELVE_FILE = 'db.shelve'
GOOGLE_DOMAINS_FILE = 'google_domains.txt'
K_LATEST_MAPPING_RESULT = 'latest_mapping_result'
K_LATEST_PING_RESULT = 'latest_ping_result'


def one_ping(ip):
    ping_count = '1'
    ping_timeout = '1'
    res = subprocess.Popen(
        ['ping', '-c', ping_count, '-n', '-W', ping_timeout, ip],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()
    print 'ping %s : %s' % (ip, 'active' if res == 0 else 'inactive')
    return ip, res


def get_candidate_google_ips():
    ips = []
    for ip3 in range(32, 64):
        for ip4 in range(1, 255):
            ips.append('203.208.%s.%s' % (ip3, ip4))
    return ips


# STEP 1
def find_active_ips():
    '''使用ping批量检测指定网段存活主机
    Google Beijing:
       203.208.32.0 – 203.208.63.255
    网络通畅情况下20进程预计耗时: (32 * 255 / 20. /60.) ~ 7 mins
    '''
    ips = get_candidate_google_ips()
    pool = mp.Pool(20)
    res = pool.map(one_ping, ips)
    active_ips = [item[0] for item in res if len(item) == 2 and item[1] == 0]
    s = shelve.open(SHELVE_FILE)
    s[K_LATEST_PING_RESULT] = active_ips
    s.close()
    with open('active_google_ips.txt', 'w') as fh:
        fh.writelines('\n'.join(active_ips))


# STEP 2
def resolve_host_ip_mapping():
    '''通过检测443端口的SSL证书判断某个IP属于哪个域名，最后得到host-ip隐射{host1:[ip1, ip2, ip3],...}'''
    s = shelve.open(SHELVE_FILE)
    active_ips = s[K_LATEST_PING_RESULT]
    s.close()

    host_ips = {}
    for each_ip in active_ips:
        each_ip = each_ip.strip()
        c_CN = get_ssl_subject_CN(each_ip)
        print 'find mapping: %s in %s' % (each_ip, c_CN)
        host_ips.setdefault(c_CN, []).append(each_ip)
    host_ips.pop(None)

    s = shelve.open(SHELVE_FILE)
    s[K_LATEST_MAPPING_RESULT] = host_ips
    s.close()


# STEP 3
def generate_hosts():
    '''通过已知host-ip隐射生成hosts条目'''
    s = shelve.open(SHELVE_FILE)
    host_ips = s[K_LATEST_MAPPING_RESULT]
    s.close()
    hosts = []
    with open(GOOGLE_DOMAINS_FILE) as fh:
        for domain in fh:
            domain = domain.strip()
            if domain.startswith('#') or domain == '':
                continue
            ip = None
            for domain_pattern in host_ips.keys():
                if (domain_pattern is not None and
                        fnmatch(domain, domain_pattern)):
                    ip = host_ips[domain_pattern][0]
                    break
            hosts.append((domain, ip))
    return hosts


def main():
    parser = OptionParser()
    parser.add_option(
        '-f', '--force', help="force to find ips(step1) and "
                              "resolve host-ip mapping(step2)",
        dest="force", default=False, action='store_true')
    (opts, args) = parser.parse_args()

    s = shelve.open(SHELVE_FILE)
    latest_ping_result = s.get(K_LATEST_PING_RESULT)
    latest_mapping_result = s.get(K_LATEST_MAPPING_RESULT)
    s.close()
    if not latest_ping_result or opts.force:
        find_active_ips()  # step 1
    if not latest_mapping_result or opts.force:
        resolve_host_ip_mapping()  # step2
    hosts = generate_hosts()  # test3
    with open('hosts', 'w') as fh:
        fh.writelines(('%s   %s\n' % (i[1] or '#unknown', i[0])
                      for i in hosts))
    print 'done! checkout `hosts` in current directory'


if __name__ == '__main__':
    main()
