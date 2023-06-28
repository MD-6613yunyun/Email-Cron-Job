import xmlrpc.client
from datetime import date, timedelta

class LineTracker:

    def __init__(self, db, username, pwd):
        self.db = db
        self.username = username
        self.pwd = pwd
        self.uid = 0
        self.total_record_creations = 0

    def authenticate_server(self, server):
        common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(server))
        uid = common.authenticate(self.db, self.username, self.pwd, {})
        if uid:
            print(f"Authenticated with the unique ID - {uid}")
            self.uid = uid
        else:
            print("Invalid credentials or login..")
            print("Try again with valid credentials")
        return uid

    def initialize_objects_in_server(self, server: str):
        models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(server))
        return models

    def track_lines_depart(self, obj_models: object, model: str, lines_include: bool = False):
        domain = [('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date)]
        flds = ['id', 'unit_id', 'create_uid', 'line_ids'] if lines_include else ['id', 'unit_id', 'create_uid']
        results = obj_models.execute_kw(self.db, self.uid, self.pwd, model, 'search_read',
                                        [domain], {"fields": flds})
        unit_dct = {}
        for data in results:
            try:
                unit = data['unit_id'][1]
            except TypeError:
                unit = data['unit_id']
                if unit == False:
                    unit = "Unknown Unit / Unavowed Unit"
            lines = len(data['line_ids']) if lines_include else 1
            if unit not in unit_dct:
                unit_dct[unit] = {}
                # unit_dct[unit]['counts'] = 1
                unit_dct[unit]['id_counts'] = {}
                idd = data['create_uid'][0]
                if idd not in unit_dct[unit]['id_counts']:
                    unit_dct[unit]['id_counts'][idd] = lines
                else:
                    unit_dct[unit]['id_counts'][idd] += lines
            else:
                # unit_dct[unit]['counts'] += 1
                idd = data['create_uid'][0]
                if idd not in unit_dct[unit]['id_counts']:
                    unit_dct[unit]['id_counts'][idd] = lines
                else:
                    unit_dct[unit]['id_counts'][idd] += lines
        id_list = []

        for data in unit_dct.values():
            id_list.extend(list(data['id_counts'].keys()))
        results = obj_models.execute_kw(self.db, self.uid, self.pwd, 'res.users', 'read', [id_list],
                                        {"fields": ['department_id']})
        index = 0
        for data in unit_dct.values():
            dct = {}
            for idd, count in data['id_counts'].items():
                dpt_id = results[index]['department_id'][1] if type(results[index]['department_id']) == type([]) else results[index]['department_id']
                if dpt_id not in dct:
                    dct[dpt_id] = count
                else:
                    dct[dpt_id] += count
                index += 1
            data['id_counts'] = dct
        return unit_dct

    def track_lines_for_accountant(self, obj_models: object):
        domain = [
            [('cash_type', '=', 'pay'), ('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date)],
            [('cash_type', '=', 'receive'), ('create_date', '>=', self.start_date),
             ('create_date', '<=', self.end_date)],
            [('partner_type', '=', 'supplier'), ('payment_type', '=', 'inbound'),
             ('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date)],
            [('partner_type', '=', 'supplier'), ('payment_type', '=', 'outbound'),
             ('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date)],
            [('partner_type', '=', 'customer'), ('payment_type', '=', 'inbound'),
             ('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date)],
            [('partner_type', '=', 'customer'), ('payment_type', '=', 'outbound'),
             ('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date)]]
        acc_results = []
        for i in range(6):
            if 0 <= i < 2:
                model = 'account.cashbook'
                name = 'tree_unit'
                flds = ['id', name, 'create_uid', 'line_ids']
            else:
                model = 'account.payment'
                name = 'unit_id'
                flds = ['id', name, 'create_uid']
            results = obj_models.execute_kw(self.db, self.uid, self.pwd, model, 'search_read',
                                            [domain[i]], {"fields": flds})
            unit_dct = {}
            for data in results:
                unit = data[name][1] if name == 'unit_id' else data[name]
                lines = len(data['line_ids']) if 0 <= i < 2 else 1
                if unit == False:
                    unit = "Unknown Unit / Unavowed Unit"
                if unit not in unit_dct:
                    unit_dct[unit] = {}
                    unit_dct[unit]['id_counts'] = {}
                    idd = data['create_uid'][0]
                    if idd not in unit_dct[unit]['id_counts']:
                        unit_dct[unit]['id_counts'][idd] = lines
                    else:
                        unit_dct[unit]['id_counts'][idd] += lines
                else:
                    idd = data['create_uid'][0]
                    if idd not in unit_dct[unit]['id_counts']:
                        unit_dct[unit]['id_counts'][idd] = lines
                    else:
                        unit_dct[unit]['id_counts'][idd] += lines
            id_list = []

            for data in unit_dct.values():
                id_list.extend(list(data['id_counts'].keys()))
            results = obj_models.execute_kw(self.db, self.uid, self.pwd, 'res.users', 'read', [id_list],
                                            {"fields": ['department_id']})
            index = 0
            for data in unit_dct.values():
                dct = {}
                for idd, count in data['id_counts'].items():
                    try:
                        depart = results[index]['department_id'][1]
                    except:
                        depart = 'Unavowed/Unassigned Department'
                    if depart not in dct:
                        dct[depart] = count
                    else:
                        dct[depart] += count
                    index += 1
                data['id_counts'] = dct
            acc_results.append(unit_dct)
        return acc_results

    def set_date(self, month, day, year, auto=True):
        if auto:
            self.end_date = date.today().strftime('%Y-%m-%d') + " 17:29:59"
            self.start_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d') + " 17:30:13"
        else:
            self.start_date = f"{str(year)}-0{str(month)}-{str(day - 1)} 17:30:13"
            self.end_date = f"{str(year)}-0{str(month)}-{str(day)} 17:29:59"



def add_data_to_table(data,clr):
    global html
    global counter
    if data != {}:
        total_rows = sum(len(nested_dict) for inner_dict in data.values() for nested_dict in inner_dict.values())
        html += f"<tr><td>{modules[counter]}</td>" if total_rows == 0 or total_rows == 1 else f"<tr><td rowspan='{total_rows}'>{modules[counter]}</td>" 
        for unit, id_counts in data.items():
            span_rows = len(id_counts['id_counts'])
            html += f"<td>{unit}</td>" if span_rows == 0 or span_rows == 1  else f"<td rowspan='{span_rows}'>{unit}</td>"
            
            for test, count in id_counts['id_counts'].items():
                html += f"<td>{test}</td><td bgcolor={clr}>{count}</td></tr><tr>"
            
            if not id_counts['id_counts']:
                html += "<td></td><td></td></tr>"
        counter += 1
    else:
        html += f"""<tr>
                        <td>{modules[counter]}</td>
                        <td></td>
                        <td></td>
                        <td bgcolor={clr}>0</td>
                    </tr>
                """

def internal_calculations():
    global html
    # requirements for authentication
    server, db = "http://ec2-13-213-221-73.ap-southeast-1.compute.amazonaws.com", "mmm_uat"
    username, pwd = "MD-6613", "mamayaykalparown"
    #  models used to check in
    models_check_in = ["sale.order", 'purchase.order', 'duty.process.line','purchase.requisition',
                       'stock.inventory.adjustment', 'expense.prepaid', 'hr.expense']
    ## Data processing
    # create an instance of our line tracker object
    mmm = LineTracker(db, username, pwd)
    # authentication
    uid = mmm.authenticate_server(server)
    # objects intialization to process datas within models
    models_obj = mmm.initialize_objects_in_server(server)
    # setting up the date when records were created
    mmm.set_date(4, 20, 2023)
    # colors 
    colors = [
    "#F5F5DC",  # Beige
    "#ECE5C8",
    "#E8E6C4",
    "#DFD7BE",
    "#D6CDBC",
    "#CEC5B4",
    "#C5BEAE",
    "#BDB7A8",
    "#B4B0A2",
    "#ABA99C",
    "#A2A395",
    "#99988F",
    "#908C89",
    "#888481",
    "#7F7A7A"
    ]

    cnt = 0
    # looping through the declared model and process the retrieval
    for i in range(7):
        # write the result and model name to the file
        if i == 6:
            returned_result = mmm.track_lines_depart(models_obj, models_check_in[i],lines_include=True)
        else:
            returned_result = mmm.track_lines_depart(models_obj, models_check_in[i])
        add_data_to_table(returned_result,colors[cnt])
        
        cnt += 1
    # data retrival from account module
    account = mmm.track_lines_for_accountant(models_obj)  # account
    for acc in account:
        print(acc)
        add_data_to_table(acc,colors[cnt])
        cnt += 1


if __name__ == '__main__':


    modules = ['Sale Module','Purchase Module','Duty Process Module','Purchase Requisition Module',
    'Inventory Adjustment Module','Advance  Expensese Module','General Expenses Module',
    'Cashbook Payment Module','Cashbook Receipt Module','Vendor Receipt Module',
    'Vendor Payment Module','Customer Payment Module','Customer Receipt Module' ]

    

    global html
    global counter
    html = """<!DOCTYPE html>
    <html>
    <head>
    <style>
    table {
    font-family: arial, sans-serif;
    border-collapse: collapse;
    width: 100%;
    }

    td, th {
    border: 1px solid #dddddd;
    text-align: center;
    padding: 8px;
    }
    h2{
    text-align:center;
    }

    </style>
    </head>
    <body>
    """

    counter = 0
    html += f"<h2>{date.today().strftime('%Y/%m/%d')} Record Creations Table</h2><table><tr><th>Module</th><th>Unit</th><th>Depart</th><th>Counts</th></tr>"
    internal_calculations()

    html += "</table></body></html>"
    file_path = "/path/to/the/file.html"
    with open(file_path,"w") as file:
        file.write(html)
