# !/usr/bin/env python
#  -*- coding: utf-8 -*-
import MySQLdb
from data import cpanel, conf
from model import Cflow, Flow, Packet


def read_pcap(group_id):
    db = MySQLdb.connect(conf.DB.HOST, conf.DB.USER, conf.DB.PASS, conf.DB.NAME)
    cursor = db.cursor()
    sql = "select * from Packets where GROUP_ID={} order by id".format(group_id)

    raw_packets = cursor.fetchmany(cursor.execute(sql))
    print '[database] Selected Packets: {}'.format(len(raw_packets))

    cpanel.START_TIME = raw_packets[0][2]
    print '[common] START_TIME: %s' % str(cpanel.START_TIME)
    for p in raw_packets:
        cpanel.PACKETS.append(Packet(p))

    print '[common] Packets loading finished.'


def split_flow():
    flows = {}
    for p in cpanel.PACKETS:
        vector = ':'.join([p.ip_src, p.ip_dst, p.port_src, p.port_dst])
        if vector in flows:
            flows[vector].append(p)
        else:
            flows[vector] = [p]
    print '[common] Total flows: {}'.format(len(flows))

    count = 1
    filtered_flows = []
    for _vector, _packets in flows.iteritems():
        if len(_packets) < 2:  # 删除只有一个包的flow，根据测试效果决定是否选用
            pass
        else:
            filtered_flows.append(Flow(count, _vector, _packets))
            count += 1

    cpanel.FLOWS = filtered_flows
    print '[common] Instant flows: {}'.format(len(cpanel.FLOWS))

    # 计算三个关键值
    for f in cpanel.FLOWS:
        f.calc()


def split_cflow():
    cflow = {}
    for f in cpanel.FLOWS:
        vector = f.ip_src
        if vector in cflow:
            cflow[vector].append(f)
        else:
            cflow[vector] = [f]
    print '[common] Total C_flows: {}'.format(len(cflow))

    count = 1
    filtered_cflows = []
    for _vector, _flows in cflow.iteritems():
        # TODO add filter here
        filtered_cflows.append(Cflow(count, 24, _vector, _flows))  # TODO epoch调整为全局变量？动态获取？
        count += 1

    cpanel.C_FLOWS = filtered_cflows
    print '[common] Instant C_flows: {}'.format(len(cpanel.C_FLOWS))


def save(output_path):
    with open(output_path, 'w') as f:  # TODO more checks here
        for cf in cpanel.C_FLOWS:
            line = ','.join([str(cf.id), str(cf.fph), str(cf.bps), str(cf.bpp), str(cf.ppf), str(cf.ip_src)]).replace(
                '[', '').replace(']', '').replace(' ', '')
            f.write(line + '\n')