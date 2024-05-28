import psycopg

from psycopg.rows import class_row

from flask import Blueprint, request, make_response, abort, render_template, flash, redirect, url_for

from flask_login import login_required, current_user

from gvm.connections import UnixSocketConnection
from gvm.errors import GvmError
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeCheckCommandTransform
from gvm.protocols.gmpv224 import ReportFormatType

from lxml import etree

from markupsafe import escape

from base64 import b64decode

from datetime import datetime

from .models import Target, Scan

api = Blueprint('api', __name__, url_prefix='/api')

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

@api.route("/version")
@login_required
def get_version():
    with Gmp(connection=connection, transform=transform) as gmp:
        response = gmp.get_version()
        vers = response.xpath('version/text()')[0]
    return {'version': vers}

@api.route("/scanners")
@login_required
def get_scanners():
    try:
        with Gmp(connection=connection, transform=transform) as gmp:
            gmp.authenticate(username, password)
            response = gmp.get_scanners()
            scanners = response.xpath('scanner/@id')
            names = response.xpath('scanner/name/text()')
        return {'scanners': scanners, 'names': names}
    except GvmError as e:
        abort(500)

@api.route("/configs")
@login_required
def get_configs():
    try:
        with Gmp(connection=connection, transform=transform) as gmp:
            gmp.authenticate(username, password)
            response = gmp.get_scan_configs()
            ids = response.xpath('config/@id')
            names = response.xpath('config/name/text()')
        return {'configs': ids, 'names': names}
    except GvmError as e:
        abort(500)

@api.route("/port_lists")
@login_required
def get_port_lists():
    try:
        with Gmp(connection=connection, transform=transform) as gmp:
            gmp.authenticate(username, password)
            response = gmp.get_port_lists()
            ids = response.xpath('port_list/@id')
            names = response.xpath('port_list/name/text()')
        return {'port_lists': ids, 'names': names}
    except GvmError as e:
        abort(500)

@api.route("/targets", methods = ['GET', 'POST'])
@login_required
def targets():
    if request.method == 'POST':
        name = request.form.get('name')
        hosts = request.form.get('host')
        if hosts is not None and name is not None:
            with psycopg.connect("host=db user=postgres password=admin") as conn:
                with conn.cursor(row_factory=class_row(Target)) as cur:
                    target = cur.execute("SELECT * FROM targets WHERE name = %s AND owner = %s LIMIT 1", (name,current_user.id)).fetchone()
                    if target is not None:
                        flash('A target with that name already exists!')
                        targets = cur.execute("SELECT * FROM targets WHERE owner = %s", (current_user.id,)).fetchall()
                        return render_template('targets_response.html', targets=targets)
                with conn.cursor() as cur:
                    try:
                        with Gmp(connection=connection, transform=transform) as gmp:
                            gmp.authenticate(username, password)
                            target_id = gmp.create_target(name=name + ' ' + current_user.id, hosts=[hosts], port_range='T:1-65535').xpath('@id')
                            cur.execute("INSERT INTO targets (uuid, name, hosts, owner) VALUES (%s, %s, %s, %s)", (target_id, name, hosts, current_user.id))
                    except GvmError as e:
                        abort(500)
                with conn.cursor(row_factory=class_row(Target)) as cur:
                    targets = cur.execute("SELECT * FROM targets WHERE owner = %s", (current_user.id,)).fetchall()
                    return render_template('targets_response.html', targets=targets)
        else:
            abort(400)
    elif request.method == 'GET':
        try:
            with Gmp(connection=connection, transform=transform) as gmp:
                gmp.authenticate(username, password)
                targets_xml = gmp.get_targets()
            return {'uuids': targets_xml.xpath('target/@id'), 'names': targets_xml.xpath('target/name/text()')}
        except GvmError as e:
            abort(500)

@api.route("/create_task", methods = ['POST'])
@login_required
def create_task():
    name = request.form.get('name')
    target = request.form.get('target')
    config = request.form.get('config')
    scanner = request.form.get('scanner')
    if name is not None and target is not None and config is not None and scanner is not None:
        with psycopg.connect("host=db user=postgres password=admin") as conn:
            with conn.cursor(row_factory=class_row(Scan)) as cur:
                task = cur.execute("SELECT * FROM tasks WHERE name = %s AND owner = %s LIMIT 1", (name,current_user.id)).fetchone()
            if task is not None:
                flash('A scan with that name already exists!')
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
                return render_template('scan_response.html', targets=targets, scans=scan_list, scanners=scanners, configs=configs)
            with conn.cursor() as cur:
                try:
                    with Gmp(connection=connection, transform=transform) as gmp:
                        gmp.authenticate(username, password)
                        task_id = gmp.create_task(name=name + ' ' + current_user.id, config_id=config, scanner_id=scanner, target_id=target[1:-1]).xpath('@id')
                        cur.execute("INSERT INTO tasks (name, target, uuid, owner) VALUES (%s, %s, %s, %s)", (name, target, task_id, current_user.id))
                except GvmError as e:
                    abort(500)
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
            return render_template('scan_response.html', targets=targets, scans=scan_list, scanners=scanners, configs=configs)
    else:
        abort(400)

@api.route("/start_task", methods = ['POST'])
@login_required
def start_task():
    task_id = request.form.get('task_id')
    scan_name = request.form.get('scan_name')
    scan_target = request.form.get('scan_target')
    if task_id is not None:
        try:
            with Gmp(connection=connection, transform=transform) as gmp:
                gmp.authenticate(username, password)
                response_xml = gmp.get_task(task_id[1:-1])
                in_use = response_xml.xpath('task/in_use/text()')[0]
                if in_use == '0':
                    response_xml = gmp.start_task(task_id[1:-1])
                    report_id = response_xml.xpath('report_id/text()')[0]
                    with psycopg.connect("host=db user=postgres password=admin") as conn:
                        with conn.cursor() as cur:
                            cur.execute("INSERT INTO reports (uuid, owner, task, time) VALUES (%s, %s, %s, %s)", (report_id, current_user.id, task_id, datetime.now()))
            return render_template('start_task_response.html', scan_name=scan_name, scan_target=scan_target, scan_uuid=task_id)
        except GvmError as e:
            abort(500)
    else:
        abort(400)

@api.route("/get_task_in_use", methods = ['GET'])
@login_required
def get_scan_in_use():
    task_id = request.args.get('task_id')
    if task_id is not None:
        try:
            with Gmp(connection=connection, transform=transform) as gmp:
                gmp.authenticate(username, password)
                response_xml = gmp.get_task(task_id[1:-1])
                in_use = response_xml.xpath('task/in_use/text()')[0]
                if in_use == '0':
                    return '<button class="button" type="submit">Submit</button>'
                else:
                    return '<progress class="progress is-small"></progress>'
        except GvmError as e:
            abort(500)
    else:
        abort(400)

@api.route("/task_progress/<uuid:task_id>", methods = ['GET'])
@login_required
def task_progress(task_id):
    try:
        with Gmp(connection=connection, transform=transform) as gmp:
            gmp.authenticate(username, password)
            task_xml = gmp.get_task(escape(task_id))
        return {'status': task_xml.xpath('task/status/text()')[0], 'progress': task_xml.xpath('task/progress/text()')[0]}
    except GvmError as e:
        abort(500)

@api.route("/report_progress/<uuid:report_id>", methods = ['GET'])
@login_required
def report_progress(report_id):
    try:
        with Gmp(connection=connection, transform=transform) as gmp:
            gmp.authenticate(username, password)
            report_xml = gmp.get_report(escape(report_id))
        return {'progress': report_xml.xpath('report/report/task/progress/text()')[0]}
    except GvmError as e:
        abort(500)

@api.route("/report/<uuid:report_id>.pdf", methods = ['GET'])
@login_required
def get_report(report_id):
    try:
        with Gmp(connection=connection, transform=transform) as gmp:
            gmp.authenticate(username, password)
            report = gmp.get_report(report_id=escape(report_id), report_format_id=ReportFormatType.PDF)
            content = report.xpath('report/text()')[0]
            pdf_bytes = b64decode(content.encode("ascii"))
            response = make_response(pdf_bytes)
            response.headers.set('Content-Type', 'application/pdf')
            return response
    except GvmError as e:
        abort(500)
