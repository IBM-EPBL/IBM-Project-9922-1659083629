from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_required
from .views import conn
import ibm_db
from .cust import QUERY_STATUS_OPEN

admin = Blueprint("admin", __name__)

# query to get all the confirmed agents 
get_confirmed_agents = '''
    SELECT first_name, agent_id FROM agent WHERE confirmed = ?
'''

@admin.route('/admin/tickets')
@login_required
def tickets():
    '''
        Loading all the OPEN tickets from the database
    '''
    from .views import admin

    if(hasattr(admin, 'email')):
        # Query to get all the unassigned tickets raised by all the users
        get_unassigned_tickets = '''
            SELECT 
                ticket_id,
                raised_on,
                customer.first_name,
                tickets.issue
            FROM
                tickets
            JOIN
                customer ON tickets.raised_by = customer.cust_id
            AND 
                tickets.assigned_to IS NULL
            ORDER BY
                raised_on ASC
        '''

        try:
            # getting the confirmed agents first
            stm = ibm_db.prepare(conn, get_confirmed_agents)
            ibm_db.bind_param(stm, 1, True)
            ibm_db.execute(stm)

            agents = ibm_db.fetch_assoc(stm)
            agents_list = []

            while(agents != False):
                temp = []

                temp.append(agents['FIRST_NAME'])
                temp.append(agents['AGENT_ID'])

                agents_list.append(temp)
                print(temp)

                agents = ibm_db.fetch_assoc(stm)


            # Getting the unassigned tickets
            stmt = ibm_db.prepare(conn, get_unassigned_tickets)
            ibm_db.execute(stmt)

            tickets = ibm_db.fetch_assoc(stmt)
            tickets_list = []

            if tickets:
                # means there are still some unassigned tickets
                while tickets != False:
                    temp = []

                    temp.append(tickets['TICKET_ID'])
                    temp.append(str(tickets['RAISED_ON'])[0:10])
                    temp.append(tickets['FIRST_NAME'])
                    temp.append(tickets['ISSUE'])

                    tickets_list.append(temp)

                    tickets = ibm_db.fetch_assoc(stmt)

                return render_template(
                    'admin tickets.html',
                    id = 0,
                    tickets_to_show = True,
                    tickets = tickets_list,
                    msg = "These are the unassigned tickets",
                    agents = agents_list
                )

            else:
                # all the tickets may be assigned
                # may be, there are no tickets raised in the system at all
                return render_template(
                    'admin tickets.html',
                    id = 0,
                    tickets_to_show = False,
                    msg = "There is nothing left to assign"
                )

        except:
            # something fishy happened while getting the tickets
            # so alerting the admin
            return render_template(
                'admin tickets.html',
                id = 0,
                to_show = True,
                message = "Something wrong! Please TrY Again"
            )

    else:
        return redirect('/')

@admin.route('/admin/agents')
@login_required
def agents():
    '''
        Returning all the confirmed agents from the database
    '''

    get_confirmed = '''
        SELECT * FROM agent WHERE confirmed = ?
    '''

    stmt = ibm_db.prepare(conn, get_confirmed)
    ibm_db.bind_param(stmt, 1, True)
    ibm_db.execute(stmt)

    agents = ibm_db.fetch_assoc(stmt)
    agents_list = []

    if agents:
        # there are some confirmed agents
        while agents != False:
            temp = []

            temp.append(agents['AGENT_ID'])
            temp.append(str(agents['DATE_JOINED'])[0:10])
            temp.append(agents['FIRST_NAME'])
            temp.append(agents['LAST_NAME'])
            temp.append(agents['EMAIL'])

            agents_list.append(temp)

            agents = ibm_db.fetch_assoc(stmt)
                
        return render_template(
            'admin agents.html',
            id = 1,
            msg = "List of confirmed agents",
            agents_to_show = True,
            agents = agents_list
        )

    else:
        # no confirmed agents present
        return render_template(
            'admin agents.html',
            id = 1,
            msg = "No agents present",
            agents_to_show = False
        )

@admin.route('/admin/accept')
@login_required
def accept():
    '''
        Loading the agents info from the database who are not yet confirmed
    '''
    
    # query to get all the agents from the database who are all not confirmed yet
    get_agents_query = '''
        SELECT * FROM agent WHERE confirmed = ?
    '''

    agents_to_show = False
    msg = ""

    try:
        stmt = ibm_db.prepare(conn, get_agents_query)
        ibm_db.bind_param(stmt, 1, False)
        ibm_db.execute(stmt)

        agents = ibm_db.fetch_assoc(stmt)

        agents_list = []

        while agents != False:
            temp = []

            temp.append(agents['AGENT_ID'])
            temp.append(agents['EMAIL'])
            temp.append(agents['FIRST_NAME'])
            temp.append(agents['DATE_JOINED'])

            agents_list.append(temp)

            agents = ibm_db.fetch_assoc(stmt)

        if len(agents_list) >= 1:
            # there are some agents who are not yet confirmed
            msg = "These are the pending requests"
            agents_to_show = True

        else:
            agents_to_show = False
            msg = "There are no pending requests"

        return render_template(
            'admin acc agent.html',
            id = 2,
            agents = agents_list,
            agents_to_show = agents_to_show,
            msg = msg
        )

    except:
        return render_template('admin acc agent.html', to_show = True, message = "Something went wrong!", id = 2)

@admin.route('/admin/about')
@login_required
def about():
    return render_template('admin about.html', id = 3)

@admin.route('/admin/support')
@login_required
def support():
    return render_template('admin support.html', id = 4)

@admin.route('/admin/<email>/<action>')
@login_required
def alter(email, action):
    '''
        Either accepting or denying the agent, as per the admin's decision
    '''
    if action == "True":
        # admin chose to the accept the agent
        accept_query = '''
            UPDATE agent SET confirmed = ? WHERE email = ?
        '''

        stmt = ibm_db.prepare(conn, accept_query)
        ibm_db.bind_param(stmt, 1, True)
        ibm_db.bind_param(stmt, 2, email)

        ibm_db.execute(stmt)

    else:
        # admin must have chosen to delete the agent
        delete_query = '''
            DELETE FROM agent WHERE email = ?
        '''

        stmt = ibm_db.prepare(conn, delete_query)
        ibm_db.bind_param(stmt, 1, email)

        ibm_db.execute(stmt)

    return "None"

@admin.route('/admin/update/<agent_id>/<ticket_id>')
@login_required
def assign(agent_id, ticket_id):
    '''
        Assigning an agent to the ticket
    '''

    # query to update the ASSIGNED_TO of a ticket
    assign_agent_query = '''
        UPDATE tickets SET assigned_to = ? WHERE ticket_id = ?
    '''

    stmt = ibm_db.prepare(conn, assign_agent_query)
    ibm_db.bind_param(stmt, 1, agent_id)
    ibm_db.bind_param(stmt, 2, ticket_id)
   
    ibm_db.execute(stmt)

    return "None"
