# -*- coding: utf-8 -*-
"""Database services — port of ``astronex/database.py`` (issue #11).

Two SQLite stores back Astro-Nex:
    * a read-only **localities** database (world cities / US cities / regions /
      timezones), bundled as ``astronex/data/local.db``.
    * a user **charts** database (``charts.db``), created in the user's home
      config dir on first use.

Port notes
----------
* ``cursor.next()`` (Py2) → ``next(cursor)`` (Py3) throughout.
* ``extensions.path`` → ``pathlib.Path``.
* Connection paths: localities DB is resolved from the packaged data dir;
  charts DB lives under the user config dir (``~/.astronex`` by default, or
  ``app.home_dir`` when the app object is provided).
* The world/USA locality tables are keyed by 2-letter country codes
  (e.g. ``sp`` for Spain, ``USCA`` for California); ``worldnames`` maps code→name,
  ``worldadmin``/``usaadmin`` hold regions, ``zonetab`` holds timezone rules.
* The locale-aware collation ``westcoll`` (via :func:`locale.strcoll`) is
  registered on every connection for correct name ordering.
"""
import locale
import sqlite3
from copy import copy
from pathlib import Path

from .utils import dectodeg, degtodec

# Ensure a sane locale for the locale-aware collation; original used
# locale.setlocale(locale.LC_ALL, ''). Keep best-effort: ignore if unsupported.
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    pass

local_conn = None
chart_conn = None
customloc_conn = None

world_schema = '''
CREATE TABLE custom.%s ( CC Text(2), AC Text(2), Ciudad Text(50), Latitud Text(10), Longitud Text(11))
'''

usa_schema = '''
CREATE TABLE custom.%s ( CC Text(2), AC Text(2), Ciudad Text(50), Latitud Real, Longitud Real )
'''

# Default user config dir; override via connect(app) / easy_connect(homedir).
_DEFAULT_HOME = Path.home() / ".astronex"
# Bundled localities database.
_LOCAL_DB = str(Path(__file__).parent.parent / "data" / "local.db")


def connect(app=None, homedir=None):
    """Open the localities + charts connections.

    With ``app`` (original signature): uses ``app.appath`` for the bundled DB
    and ``app.home_dir`` for the user charts DB. With ``homedir`` (test path):
    resolves the bundled DB from the package and the charts DB from ``homedir``
    (defaulting to ``~/.astronex``).
    """
    global local_conn, chart_conn, customloc_conn
    # Localities DB: bundled resource (app.appath/data takes precedence if set).
    if app is not None:
        local_dbfile = Path(app.appath) / "astronex" / "db" / "local.db"
        home = Path(app.home_dir)
    else:
        local_dbfile = Path(_LOCAL_DB)
        home = Path(homedir) if homedir else _DEFAULT_HOME

    local_conn = sqlite3.connect(str(local_dbfile))
    local_conn.create_collation('westcoll', westerncollate)

    home.mkdir(parents=True, exist_ok=True)
    chart_dbfile = home / "charts.db"
    chart_conn = sqlite3.connect(str(chart_dbfile))
    chart_conn.create_collation('westcoll', westerncollate)

    customloc_dbfile = home / "customloc.db"
    sql = "attach database '%s' as custom" % customloc_dbfile
    local_conn.execute(sql)


def easy_connect(homedir=None):
    """Convenience connect for standalone/test use (no app object)."""
    connect(homedir=homedir)


def westerncollate(s1, s2):
    return locale.strcoll(s1, s2)


def save_attached_loc(args):
    country, regcode, city, lat, long, usa = args
    if not usa:
        table = "cust_" + country.lower()
        schema = world_schema
        insert = "insert into %s  values(:count,:code,:city,:lat,:long)"
    else:
        table = "cust_US" + country
        schema = usa_schema
        insert = "insert into %s values(:count,:code,:city,:lat,:long)"

    sql = "select name from custom.sqlite_master where type='table'"
    att_tables = [str(row[0]) for row in local_conn.execute(sql)]
    if table not in att_tables:
        local_conn.execute(schema % table)

    bindings = (country, regcode, city, lat, long)
    local_conn.execute(insert % table, bindings)
    local_conn.commit()


def fetch_all_from_custom():
    cursor = local_conn.cursor()
    sql = "select name from custom.sqlite_master where type='table'"
    att_tables = []
    for row in local_conn.execute(sql):
        table = str(row[0])
        _, code = table.split('_')
        if code.startswith('US'):
            name = get_name_from_usacode(code[2:])
        else:
            name = get_name_from_code(code)
        att_tables.append((table, name))
    locs = []
    for t, n in att_tables:
        sql = "select Ciudad, AC, Longitud, Latitud from '%s'" % t
        for city, ac, lg, lt in cursor.execute(sql):
            locs.append((city, ac, coalesce_geo(lg, lt), t, n))
    locs.sort()
    return locs


def delete_custom_loc(tbl, city, code):
    cursor = local_conn.cursor()
    sql = "delete from '%s' where Ciudad='%s' and AC='%s'" % (tbl, city, code)
    cursor.execute(sql)
    local_conn.commit()


##############################################
# locality services
##############################################
def get_states(usa=False):
    """list state names"""
    cursor = local_conn.cursor()
    sql = "select code, name from worldnames"
    if usa:
        sql = "select alfa, name from usastates"
    state_names = {}
    for alfa, name in cursor.execute(sql):
        if not usa:
            name = t(name)
        state_names[name] = alfa
    return state_names


def get_states_tuple(usa=False):
    cursor = local_conn.cursor()
    sql = "select code, name from worldnames"
    if usa:
        sql = "select alfa, name from usastates"
    state_names = []
    for alfa, name in cursor.execute(sql):
        if not usa:
            name = t(name)
        state_names.append((name, alfa))
    return state_names


def list_regions(count, usa=False):
    """list region names"""
    cursor = local_conn.cursor()
    tab = 'worldadmin'
    if usa:
        tab = 'usaadmin'
    sql = "select name, code from %s where alfa='%s' order by name asc" % (tab, count)
    out = []
    for name, code in cursor.execute(sql):
        out.append((name, code))
    return out


def get_name_from_code(code):
    """Gets country name from its code."""
    cursor = local_conn.cursor()
    sql = "select name from worldnames where code='%s'" % code.upper()
    cursor.execute(sql)
    return next(cursor)[0]


def get_regionname_from_code(alfa, code):
    """Gets region name from country code and code."""
    cursor = local_conn.cursor()
    sql = "select name from worldadmin where alfa='%s' and code='%s'" % (alfa, code)
    cursor.execute(sql)
    return next(cursor)[0]


def get_usadistrict_from_code(alfa, code):
    """Gets region name from country code and code."""
    cursor = local_conn.cursor()
    sql = "select name from usaadmin where alfa='%s' and code='%s'" % (alfa, code)
    cursor.execute(sql)
    return next(cursor)[0]


def get_name_from_usacode(code):
    """Gets state name from its code."""
    cursor = local_conn.cursor()
    sql = "select name from usastates where alfa='%s'" % code.upper()
    cursor.execute(sql)
    return next(cursor)[0]


def get_code_from_name(name):
    """Gets country code from its name."""
    cursor = local_conn.cursor()
    sql = "select code from worldnames where name='%s'" % name
    cursor.execute(sql)
    return next(cursor)[0]


def get_usacode_from_name(name):
    """Gets state alfa code from its name."""
    cursor = local_conn.cursor()
    sql = "select alfa from usastates where name='%s'" % name
    cursor.execute(sql)
    return next(cursor)[0]


def fetch_all_from_country(country, usa=False):
    """get cities from country"""
    cursor = local_conn.cursor()
    if not usa:
        main_tab = country
        custom_tab = "cust_" + country.lower()
    else:
        main_tab = 'US' + country
        custom_tab = "cust_US" + country

    sql = "select name from custom.sqlite_master where type='table'"
    att_tables = [str(row[0]) for row in local_conn.execute(sql)]

    sql = "select Ciudad, AC, Longitud, Latitud from '%s' " % main_tab
    if custom_tab in att_tables:
        union = " union select Ciudad, AC, Longitud, Latitud from '%s'" % custom_tab
    else:
        union = ""
    order = " order by Ciudad asc"
    sql += union + order
    out = []
    for city, ac, lg, lt in cursor.execute(sql):
        out.append((city, ac, coalesce_geo(lg, lt)))
    return out


def coalesce_geo(plg, plt):
    if isinstance(plg, float):
        lg = dectodeg(plg)
        lt = dectodeg(plt)
    else:
        lg = plg.strip()
        lt = plt.strip()

    lg = lg[:-2]
    lt = lt[:-2]

    if lg.startswith('-'):
        lg = lg[1:]
        lg = lg[:-2].rjust(1, '0') + "W" + lg[-2:].rjust(2, '0')
    else:
        lg = lg[:-2].rjust(1, '0') + "E" + lg[-2:]

    if lt.startswith('-'):
        lt = lt[1:]
        lt = lt[:-2].rjust(1, '0') + "S" + lt[-2:].rjust(2, '0')
    else:
        lt = lt[:-2].rjust(1, '0') + "N" + lt[-2:]

    return lg + " " + lt


def fetch_all_from_country_and_region(country, reg, usa=False):
    """get cities from country and region"""
    cursor = local_conn.cursor()
    tab = ''
    if usa:
        tab = 'US'
    sql = "select Ciudad, AC from '%s' where AC='%s' order by Ciudad asc" % (tab + country, reg)
    out = []
    for city, ac in cursor.execute(sql):
        out.append((city, ac))
    return out


def fetch_blindly(country, city, loc):
    """get city data"""
    cursor = local_conn.cursor()
    if ("'") in city:
        city = city.replace("'", "''")
    sql = "select CC, AC, Ciudad, Latitud, Longitud from '%s' where Ciudad=='%s'" % (country, city)
    cursor.execute(sql)
    try:
        loc.country_code, loc.region_code, loc.city, loc.latitud, loc.longitud = next(cursor)
    except StopIteration:
        return "localidad no encontrada: %s" % city

    loc.latdec = degtodec(loc.latitud)
    loc.longdec = degtodec(loc.longitud)

    fetch_region(cursor, loc)
    fetch_country(cursor, loc)
    fetch_zone(cursor, loc)
    return loc


def fetch_blindly_usacity(country, city, loc):
    """get usa city data"""
    cursor = local_conn.cursor()
    sql = "select CC, AC, Ciudad, Latitud, Longitud from US%s where Ciudad == '%s'" % (country, city)
    cursor.execute(sql)
    try:
        loc.country, loc.region_code, loc.city, loc.latdec, loc.longdec = next(cursor)
    except StopIteration:
        return "localidad no encontrada: %s" % city
    loc.latitud = dectodeg(float(loc.latdec))
    loc.longitud = dectodeg(float(loc.longdec))
    sql = "select state, name from usaadmin where alfa == '%s' and code == '%s'" % (loc.country, loc.region_code)
    cursor.execute(sql)
    loc.country_code, loc.region = next(cursor)

    sql = "select name from usastates where alfa == '%s'" % loc.country
    cursor.execute(sql)
    loc.country = next(cursor)[0]
    loc.region += " (" + loc.country + ")"
    loc.country = "USA"

    sql = "select zones, name from zonetab where alfa == 'US'"
    for z, n in cursor.execute(sql):
        zz = z.split(";")
        for code in zz:
            if code.startswith(loc.country_code):
                if len(code) == len(loc.country_code):
                    loc.zone = n
                    break
                code = code[2:]
                if code.startswith('-'):
                    code = code[1:].split(',')
                    if loc.region_code not in code:
                        loc.zone = n
                        break
                else:   # +
                    code = code[1:].split(',')
                    if loc.region_code in code:
                        loc.zone = n
                        break
        if loc.zone:
            break
    return loc


def fetch_blindly_zone_usa(state, cc, loc):
    cursor = local_conn.cursor()
    sql = "select code, name from usaadmin where alfa == '%s' and state == '%s'" % (state, cc)
    for code, reg in cursor.execute(sql):
        loc.region, loc.region_code = reg, code
        break
    sql = "select name from usastates where alfa == '%s'" % state
    cursor.execute(sql)
    loc.country = next(cursor)[0]
    loc.region += " (" + loc.country + ")"
    loc.country = "USA"
    loc.country_code = cc

    sql = "select zones, name from zonetab where alfa == '%s'" % 'US'
    for z, n in cursor.execute(sql):
        zz = z.split(";")
        for code in zz:
            if code.startswith(loc.country_code):
                if len(code) == len(loc.country_code):
                    loc.zone = n
                    break
                code = code[2:]
                if code.startswith('-'):
                    code = code[1:].split(',')
                    if loc.region_code not in code:
                        loc.zone = n
                        break
                else:   # +
                    code = code[1:].split(',')
                    if loc.region_code in code:
                        loc.zone = n
                        break
        if loc.zone:
            break


def get_usa_state_code(name):
    cursor = local_conn.cursor()
    sql = "select alfa, code from usastates where name='%s'" % name
    cursor.execute(sql)
    return next(cursor)


def fetch_worldcity(country, city, code, loc):
    cursor = local_conn.cursor()
    if ("'") in city:
        city = city.replace("'", "''")

    custom_tab = "cust_" + country.lower()

    sql = "select name from custom.sqlite_master where type='table'"
    att_tables = [str(row[0]) for row in local_conn.execute(sql)]

    sql = "select CC, AC, Ciudad, Latitud, Longitud from '%s' where Ciudad == '%s' and AC == '%s' " % (country, city, code)

    if custom_tab in att_tables:
        union = " union select CC, AC, Ciudad, Latitud, Longitud from '%s' where Ciudad == '%s' and AC == '%s' " % (custom_tab, city, code)
    else:
        union = ""
    sql += union

    cursor.execute(sql)
    loc.country_code, loc.region_code, loc.city, loc.latitud, loc.longitud = next(cursor)

    loc.latdec = degtodec(loc.latitud.strip())
    loc.longdec = degtodec(loc.longitud.strip())

    fetch_region(cursor, loc)
    fetch_country(cursor, loc)
    fetch_zone(cursor, loc)


def fetch_region(cursor, loc):
    sql = """select name from worldadmin where alfa == '%s' and code == '%s'
    """ % (loc.country_code, loc.region_code)
    cursor.execute(sql)
    loc.region = next(cursor)[0]


def fetch_country(cursor, loc):
    sql = "select name from worldnames where code == '%s'" % loc.country_code
    cursor.execute(sql)
    loc.country = next(cursor)[0]


def fetch_zone(cursor, loc):
    sql = "select zones, name from zonetab where alfa == '%s'" % loc.country_code
    for zone, name in cursor.execute(sql):
        if zone.startswith('*'):
            loc.zone = name
            break
        if zone.startswith('-'):
            nozone = zone[1:].split(',')
            if loc.region_code not in nozone:
                loc.zone = name
                break
        else:
            okzone = zone.split(',')
            if loc.region_code in okzone:
                loc.zone = name
                break


def fetch_blindly_zone(loc):
    cursor = local_conn.cursor()
    sql = """select name, code from worldadmin where alfa='%s'
    """ % loc.country_code
    for reg, code in cursor.execute(sql):
        loc.region, loc.region_code = reg, code
        break
    fetch_zone(cursor, loc)


def fetch_usacity(country, city, code, loc):
    cursor = local_conn.cursor()

    custom_tab = "cust_US" + country

    sql = "select name from custom.sqlite_master where type='table'"
    att_tables = [str(row[0]) for row in local_conn.execute(sql)]

    sql = "select CC, AC, Ciudad, Latitud, Longitud from US%s where Ciudad == '%s' and AC == '%s'" % (country, city, code)

    if custom_tab in att_tables:
        union = " union select CC, AC, Ciudad, Latitud, Longitud from cust_US%s where Ciudad == '%s' and AC == '%s' " % (country, city, code)
    else:
        union = ""

    sql += union
    cursor.execute(sql)
    loc.country, loc.region_code, loc.city, loc.latdec, loc.longdec = next(cursor)

    loc.latitud = dectodeg(float(loc.latdec))
    loc.longitud = dectodeg(float(loc.longdec))

    sql = "select state, name from usaadmin where alfa == '%s' and code == '%s'" % (loc.country, loc.region_code)
    cursor.execute(sql)
    loc.country_code, loc.region = next(cursor)

    sql = "select name from usastates where alfa == '%s'" % loc.country
    cursor.execute(sql)
    loc.country = next(cursor)[0]
    loc.region += " (" + loc.country + ")"
    loc.country = "USA"

    fetch_zone_usa(cursor, loc)


def fetch_zone_usa(cursor, loc):
    loc.zone = ''
    sql = "select zones, name from zonetab where alfa == 'US'"
    for zones, name in cursor.execute(sql):
        zone = zones.split(";")
        for code in zone:
            if code.startswith(loc.country_code):
                if len(code) == len(loc.country_code):
                    loc.zone = name
                    break
                code = code[2:]
                if code.startswith('-'):
                    code = code[1:].split(',')
                    if loc.region_code not in code:
                        loc.zone = name
                        break
                else:   # +
                    code = code[1:].split(',')
                    if loc.region_code in code:
                        loc.zone = name
                        break
        if loc.zone:
            break


##############################################
# chart services
##############################################

def create_table(tblname):
    cursor = chart_conn.cursor()
    sql = '''drop table if exists "%s"''' % tblname
    cursor.execute(sql)
    sql = '''create table "%s" (first Text NOT NULL default '',
    last Text NOT NULL default '',
    category Text NOT NULL default '',
    date Text NOT NULL default '',
    city Text NOT NULL default '',
    region Text NOT NULL default '',
    country Text NOT NULL default '',
    longitud Real NOT NULL default '0.0000000',
    latitud Real NOT NULL default '0.0000000',
    zone Text NOT NULL default '',
    sun Real NOT NULL default '0.0000000',
    moo Real NOT NULL default '0.0000000',
    mer Real NOT NULL default '0.0000000',
    ven Real NOT NULL default '0.0000000',
    mar Real NOT NULL default '0.0000000',
    jup Real NOT NULL default '0.0000000',
    sat Real NOT NULL default '0.0000000',
    ura Real NOT NULL default '0.0000000',
    nep Real NOT NULL default '0.0000000',
    plu Real NOT NULL default '0.0000000',
    nod Real NOT NULL default '0.0000000',
    h1 Real NOT NULL default '0.0000000',
    h2 Real NOT NULL default '0.0000000',
    h3 Real NOT NULL default '0.0000000',
    h4 Real NOT NULL default '0.0000000',
    h5 Real NOT NULL default '0.0000000',
    h6 Real NOT NULL default '0.0000000',
    h7 Real NOT NULL default '0.0000000',
    h8 Real NOT NULL default '0.0000000',
    h9 Real NOT NULL default '0.0000000',
    h10 Real NOT NULL default '0.0000000',
    h11 Real NOT NULL default '0.0000000',
    h12 Real NOT NULL default '0.0000000',
    comment Text NOT NULL default '',
    UNIQUE (first, last))''' % tblname
    cursor.execute(sql)


def delete_table(tblname):
    cursor = chart_conn.cursor()
    sql = "drop table if exists %s" % tblname
    cursor.execute(sql)
    chart_conn.commit()


def rename_chart(old, new):
    cursor = chart_conn.cursor()
    sql = 'alter table %s rename to %s' % (old, new)
    cursor.execute(sql)
    chart_conn.commit()


def store_chart(tbl, c):
    cursor = chart_conn.cursor()
    sql = '''insert into %s values(:f,:l,:c,:d,:ct,:r,:cy,:lg,:lt,:z,
            :s,:m,:my,:v,:mr,:j,:st,:u,:n,:p,:nd,
            :h1,:h2,:h3,:h4,:h5,:h6,:h7,:h8,:h9,:h10,:h11,:h12,:cm)''' % tbl
    p = c.planets
    h = c.houses
    # Named placeholders require a dict (Py3 sqlite3 is strict; the original Py2
    # accepted a sequence, but modern sqlite3 rejects mixing named + positional).
    bindings = {
        'f': c.first, 'l': c.last, 'c': c.category, 'd': c.date,
        'ct': c.city, 'r': c.region, 'cy': c.country,
        'lg': c.longitud, 'lt': c.latitud, 'z': c.zone,
        's': p[0], 'm': p[1], 'my': p[2], 'v': p[3], 'mr': p[4], 'j': p[5],
        'st': p[6], 'u': p[7], 'n': p[8], 'p': p[9], 'nd': p[10],
        'h1': h[0], 'h2': h[1], 'h3': h[2], 'h4': h[3], 'h5': h[4],
        'h6': h[5], 'h7': h[6], 'h8': h[7], 'h9': h[8], 'h10': h[9],
        'h11': h[10], 'h12': h[11], 'cm': c.comment,
    }
    cursor.execute(sql, bindings)
    chart_conn.commit()
    return cursor.lastrowid


def delete_chart(tbl, id):
    cursor = chart_conn.cursor()
    sql = "delete from %s where rowid='%s'" % (tbl, id)
    cursor.execute(sql)
    chart_conn.commit()


def delete_chart_from_name(tbl, fi, la):
    cursor = chart_conn.cursor()
    sql = "delete from %s where first='%s' and last='%s'" % (tbl, fi, la)
    cursor.execute(sql)
    chart_conn.commit()


def load_chart(tbl, id, chart):
    cursor = chart_conn.cursor()
    sql = "select * from %s where rowid='%s'" % (tbl, id)
    ch = next(cursor.execute(sql))
    setchart(chart, ch)


def retrieve_chart(tbl, id, chart):
    cursor = chart_conn.cursor()
    sql = "select * from %s where rowid='%s'" % (tbl, id)
    ch = next(cursor.execute(sql))
    return ch


def retrieve_all_charts(tbl, chart):
    cursor = chart_conn.cursor()
    sql = "select rowid from %s" % tbl
    charts = []
    for row in cursor.execute(sql):
        ch = copy(chart)
        load_chart(tbl, row[0], ch)
        charts.append(ch)
    return charts


def load_chart_from_name(tbl, fi, la, chart):
    cursor = chart_conn.cursor()
    sql = "select * from %s where first='%s' and last='%s'" % (tbl, fi, la)
    ch = next(cursor.execute(sql))
    setchart(chart, ch)


def setchart(chart, ch):
    chart.first = ch[0]
    chart.last = ch[1]
    chart.category = ch[2]
    chart.date = ch[3]
    chart.city = ch[4]
    chart.region = ch[5]
    chart.country = ch[6]
    chart.longitud = ch[7]
    chart.latitud = ch[8]
    chart.zone = ch[9]
    chart.planets = list(ch[10:21])
    chart.houses = list(ch[21:33])
    chart.comment = ch[33]


def get_databases():
    cursor = chart_conn.cursor()
    sql = "select tbl_name from sqlite_master where type='table' order by tbl_name"
    tables = []
    for tbl in cursor.execute(sql):
        tables.append(tbl[0])
    return tables


def get_chartlist(tbl):
    cursor = chart_conn.cursor()
    sql = "select rowid, first, last from %s order by last, first collate westcoll" % tbl
    charts = []
    for row in cursor.execute(sql):
        charts.append(row)
    return charts


def get_favlist(tbl, lim, chart):
    cursor = chart_conn.cursor()
    sql = "select rowid, first, last from %s limit %s" % (tbl, lim)
    charts = []
    for row in cursor.execute(sql):
        ch = copy(chart)
        load_chart(tbl, row[0], ch)
        charts.append(ch)
    return charts


def vacuum():
    cursor = chart_conn.cursor()
    sql = "pragma vacuum"
    cursor.execute(sql)


def get_datum(tbl, datum):
    cursor = chart_conn.cursor()
    sql = "select %s from %s" % (datum, tbl)
    data = []
    for row in cursor.execute(sql):
        data.append(row[0])
    return data


def search_by_name_all_tables(name):
    cursor = chart_conn.cursor()
    sql = "select name from sqlite_master where type='table'"
    tables = [str(row[0]) for row in cursor.execute(sql)]
    nm = name + "%"
    results = []
    for tbl in tables:
        sql = """select rowid, first, last from %s where first like '%s' or
        last like '%s' order by last, first collate westcoll""" % (tbl, nm, nm)
        for row in cursor.execute(sql):
            results.append([tbl] + list(row))
    return results
