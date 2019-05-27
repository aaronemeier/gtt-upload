import os
import shutil
import re
import subprocess
import csv
import datetime
import time

import onedrivesdk
from onedrivesdk.error import OneDriveError
from operator import itemgetter
import xlsxwriter

def authenticate(client_secret, client_id, config_root):
    api_base_url='https://api.onedrive.com/v1.0/'
    scopes=['wl.signin', 'wl.offline_access', 'onedrive.readwrite']
    http_provider = onedrivesdk.HttpProvider()
    auth_provider = onedrivesdk.AuthProvider(http_provider=http_provider, 
                                            client_id=client_id,
                                            scopes=scopes)
    client = onedrivesdk.OneDriveClient(api_base_url, auth_provider, http_provider)
    authenticated = False
    try:
        auth_provider.load_session()
        auth_provider.refresh_token()
        client = onedrivesdk.OneDriveClient(api_base_url, auth_provider, http_provider)
        authenticated = True
    except:
        pass

    if not authenticated:
        redirect_uri = 'http://localhost:8080/'
        auth_url = client.auth_provider.get_auth_url(redirect_uri)

        print('Paste this URL into your browser, approve the app\'s access.')
        print('Copy everything in the address bar after "code=", and paste it below.')
        print(auth_url)
        code = input('Paste code here: ')
        client.auth_provider.authenticate(code, redirect_uri, client_secret)
        auth_provider.save_session()

        session_src = "session.pickle"
        session_dst = config_root + "session.pickle"
        if not os.path.exists(session_dst):
            shutil.copy(session_src, session_dst)

    return client

def report(config_root, csv_report, csv_users):
    csv_issues = csv_report.split(".csv")[0] + ".issues.csv"
    csv_records = csv_report.split(".csv")[0] + ".records.csv"
    excel_report = config_root + "report.xlsx"

    try:
        os.remove(excel_report)
    except OSError:
        pass

    for file in (csv_users, csv_issues, csv_records):
        assert os.path.exists(file), "File {} does not exist!".format(file)

    users = {}
    with open(csv_users, 'r') as file:
        dict_reader = csv.DictReader(file)
        for entry in dict_reader:
            user = entry['user']
            name = entry['name']
            users[user] = name

    issues = {}
    with open(csv_issues, 'r') as file:
        dict_reader = csv.DictReader(file)
        for entry in dict_reader:
            iid = entry['iid']
            title = entry['title']
            description = entry['description']
            labels = entry['labels']
            label_match = re.search("M[0-9]{1,3}\.[0-9]{1,3}", labels)
            label = label_match.group(0) if label_match else ""
            milestone = entry['milestone']
            issues[iid] = { 'title': title, 'label': label, 'milestone': milestone }

    records = []
    with open(csv_records, 'r') as file:
        dict_reader = csv.DictReader(file)
        for entry in dict_reader:
            name = users[entry['user']]
            date = entry['date']
            issue_id = int(entry['iid'])
            title = issues[entry['iid']]['title']
            label = issues[entry['iid']]['label']
            milestone = issues[entry['iid']]['milestone']
            week = datetime.datetime.strptime(date, '%d.%m.%Y').isocalendar()[1]
            time = float(entry['time'])
            records.append((name, date, issue_id, title, label, milestone, week, time))
    
    labels = {}
    for name, date, issue_id, title, label, milestone, week, time in records:
        if label in labels:
            labels[label] += time
        else:
            labels[label] = time

    records.sort(key=lambda rec: datetime.datetime.strptime(rec[1], '%d.%m.%Y').toordinal())

    workbook = xlsxwriter.Workbook(excel_report)
    date_format = workbook.add_format({'num_format': 'dd.mm.yyyy'})
    time_format = workbook.add_format({'num_format': '###.##'})
    headings_format = workbook.add_format({'bold': 1})

    worksheet_all = workbook.add_worksheet('All')
    worksheet_all.write(0, 0, "name", headings_format)
    worksheet_all.write(0, 1, "date", headings_format)
    worksheet_all.write(0, 2, "issue_id", headings_format)
    worksheet_all.write(0, 3, "title", headings_format)
    worksheet_all.write(0, 4, "label", headings_format)
    worksheet_all.write(0, 5, "milestone", headings_format)
    worksheet_all.write(0, 6, "week", headings_format)
    worksheet_all.write(0, 7, "time", headings_format)
    worksheet_all.write(0, 8, "total", headings_format)
    # Note: description will be discarded

    row = 1
    for name, date, issue_id, title, label, milestone, week, time in records:
        worksheet_all.write(row, 0, name)
        worksheet_all.write(row, 1, date, date_format)
        worksheet_all.write(row, 2, issue_id)
        worksheet_all.write(row, 3, title)
        worksheet_all.write(row, 4, label)
        worksheet_all.write(row, 5, milestone)
        worksheet_all.write(row, 6, week)
        worksheet_all.write(row, 7, time)
        worksheet_all.write(row, 8, '=SUM(H2:H' + str(row+1) + ')')
        row += 1

    for user in users:
        worksheet = workbook.add_worksheet(users[user])
        worksheet.write(0, 0, "name", headings_format)
        worksheet.write(0, 1, "date", headings_format)
        worksheet.write(0, 2, "issue_id", headings_format)
        worksheet.write(0, 3, "title", headings_format)
        worksheet.write(0, 4, "label", headings_format)
        worksheet.write(0, 5, "milestone", headings_format)
        worksheet.write(0, 6, "week", headings_format)
        worksheet.write(0, 7, "time", headings_format)
        worksheet.write(0, 8, "total", headings_format)
        row = 1
        for name, date, issue_id, title, label, milestone, week, time in records:
            if name == users[user]:
                worksheet.write(row, 0, name)
                worksheet.write(row, 1, date, date_format)
                worksheet.write(row, 2, issue_id)
                worksheet.write(row, 3, title)
                worksheet.write(row, 4, label)
                worksheet.write(row, 5, milestone)
                worksheet.write(row, 6, week)
                worksheet.write(row, 7, time, time_format) 
                worksheet.write(row, 8, '=SUM(H2:H' + str(row+1) + ')', time_format)
                row += 1
        
    worksheet_labels = workbook.add_worksheet('Labels')
    worksheet_labels.write(0, 0, "label", headings_format)
    worksheet_labels.write(0, 1, "time", headings_format)

    row = 1
    for label, time in sorted(labels.items()):
        if not label:
            label = "Unassigned"
        worksheet_labels.write(row, 0, label)
        worksheet_labels.write(row, 1, time, time_format)
        row += 1
    
    worksheet_weeks = workbook.add_worksheet("Graph")
    worksheet_weeks.write(0, 0, "Weeks", headings_format)
    graph = workbook.add_chart({'type': 'line'})

    week_min = min(map(lambda rec: rec[6], records))
    week_max = max(map(lambda rec: rec[6], records))
    col = 1
    for user in users:
        name = users[user]
        worksheet_weeks.write(0, col, name, headings_format)
        row = 1
        for week in range(week_min, week_max):
            worksheet_weeks.write(row, 0, week)
            temp = list(filter(lambda rec: rec[6] == week and rec[0] == name, records))
            if len(temp) > 0:
                hours = sum(map(lambda rec: rec[7], temp))
            else:
                hours = 0
            worksheet_weeks.write(row, col, hours)
            row += 1
        graph.add_series({
            'name': ['Graph', 0, col],
            'categories': ['Graph', 1, 0, row-1, 0],
            'values': ['Graph', 1, col, row-1, col],
        })
        col += 1
    graph.set_title({'name': "Hours per week"})
    graph.set_x_axis({'name': "Weeks"})
    graph.set_y_axis({'name': "Hours"})
    graph.set_style(10)
    worksheet_weeks.insert_chart('D2', graph, {'x_offset': 25, 'y_offset': 10})
    workbook.close()

def main():
    onedrive_file = os.environ['ONEDRIVE_FILE'] or exit("ONEDRIVE_FILE not set")
    config_root = os.environ['CONFIG_ROOT'] or exit("CONFIG_ROOT not set")
    
    generate_only = False
    if not generate_only:
        client_secret = os.environ['GTT_CLIENT_SECRET'] or exit("GTT_CLIENT_SECRET not set")
        client_id = os.environ['GTT_CLIENT_ID'] or exit("GTT_CLIENT_ID not set")

    report_file = os.environ['REPORT_FILE'] or exit("REPORT_FILE  not set")
    users_file = os.environ['USERS_FILE'] or exit("USERS_FILE not set")

    # Restore session
    session_src = config_root + "session.pickle"
    session_dst = "session.pickle"
    if os.path.exists(session_src):
        shutil.copy(session_src, session_dst)

    report(config_root, report_file, users_file)

    if not generate_only:
        client = authenticate(client_secret, client_id, config_root)
        tries = 50
        while(tries > 0): 
            try:
                item = client.item(drive='me', id='root').children[onedrive_file].upload(config_root + "report.xlsx")
                tries = 0
            except OneDriveError:
                print("Problem uploading to OneDrive, trying again..")
                tries -= 1
                time.sleep(5)
                pass
            
if __name__ == "__main__":
    main()
