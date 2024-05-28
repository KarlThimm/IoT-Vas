# main.py

import psycopg

from psycopg.rows import class_row
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from gvm.connections import UnixSocketConnection
from gvm.errors import GvmError
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeCheckCommandTransform
from gvm.protocols.gmpv224 import ReportFormatType

from lxml import etree

from .models import Target, Scan, Report

main = Blueprint('main', __name__)

path = '/run/gvmd/gvmd.sock'
connection = UnixSocketConnection(path=path)
transform = EtreeCheckCommandTransform()

# default username with greenbone containers
username = 'admin'

# default password with greenbone containers
# CHANGE ACCORDING TO:
# https://greenbone.github.io/docs/latest/22.4/container/index.html#setting-up-an-admin-user
# AFTER docker compose up -d
password = 'admin'

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.id)

@main.route('/scan')
@login_required
def scan():
    with psycopg.connect("host=db user=postgres password=admin") as conn:
        with conn.cursor(row_factory=class_row(Target)) as cur:
            targets = cur.execute("SELECT * FROM targets WHERE owner = %s", (current_user.id,)).fetchall()
        with conn.cursor(row_factory=class_row(Scan)) as cur:
            scans = cur.execute("SELECT * FROM tasks WHERE owner = %s", (current_user.id,)).fetchall()
    try:
        with Gmp(connection=connection, transform=transform) as gmp:
            gmp.authenticate(username, password)
            response = gmp.get_scanners()
            scanner_ids = response.xpath('scanner/@id')
            scanner_names = response.xpath('scanner/name/text()')
            scanners = []
            for id, name in zip(scanner_ids, scanner_names):
                scanners.append((id, name))
            response = gmp.get_scan_configs()
            config_ids = response.xpath('config/@id')
            config_names = response.xpath('config/name/text()')
            configs = []
            for id, name in zip(config_ids, config_names):
                configs.append((id, name))
            scan_list = []
            for scan in scans:
                response_xml = gmp.get_task(scan.uuid[1:-1])
                in_use = response_xml.xpath('task/in_use/text()')[0]
                scan_list.append((scan, in_use))
    except GvmError as e:
        abort(500)
    return render_template('scan.html', targets=targets, scans=scan_list, scanners=scanners, configs=configs)

@main.route('/targets')
@login_required
def targets():
    with psycopg.connect("host=db user=postgres password=admin") as conn:
        with conn.cursor(row_factory=class_row(Target)) as cur:
            targets = cur.execute("SELECT * FROM targets WHERE owner = %s", (current_user.id,)).fetchall()
    return render_template('targets.html', targets=targets)

@main.route('/reports')
@login_required
def reports():
    report_list = []
    with psycopg.connect("host=db user=postgres password=admin") as conn:
        with conn.cursor(row_factory=class_row(Report)) as cur:
            reports = cur.execute("SELECT * FROM reports WHERE owner = %s", (current_user.id,)).fetchall()
        with conn.cursor() as cur:
            for report in reports:
                scan_name = cur.execute("SELECT name FROM tasks WHERE uuid = %s", (report.task,)).fetchone()[0]
                report_list.append((report, scan_name))
    return render_template('reports.html', reports=report_list)


