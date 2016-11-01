#!/usr/bin/env python

# Jacky Liang 2016
                                                                          
# OS and Python Version
# Python 2.7.8                                                         
# OS X Yosemite 10.10.5 (14F27)
                                                                          
# Libraries:
# Uses the mechanize + lxml library
#     pip install mechanize
#     pip install lxml

# TODO:
# 1. Drop classes
# 2. Better/more error handling
# 3. Not hardcoding the term selection
# 4. Prettify course submission errors

import mechanize, os, json, sys
import lxml.html


def parse_info(info="./info.json"):
    # Parse info.json which contains our three input params
    if os.path.exists(info):
        with open(info) as data_file:
            info = json.load(data_file)
    else:
        raise Exception

    # Grab username, password, and classes from info.json
    username = info['username']
    password = info['password']
    classes = info['classes']
    term = info['term']

    return username, password, classes, term


def drexel_login(browser, username, password):
    """
    Logs the mechanize browser in to DrexelOne
    """
    # Drexel One login URL
    url = 'https://login.drexel.edu/cas/login?service=https%3A%2F%2Fone.drexel.edu%2Fc%2Fportal%2Flogin'

    # Open the Drexel One URL
    browser.open(url)

    # Select the first form element where the username and password is
    browser.select_form(nr=0)
    browser.form['username'] = username
    browser.form['password'] = password

    # Login by submitting the form
    browser.submit()


def add_classes(browser, term, classes):
    """
    Adds all the classes using the browser instance logged in to the add/drop classes page
    """
    # Navigate to the "Add/Drop Classes" page
    browser.open('https://bannersso.drexel.edu'
            '/ssomanager/c/SSB?pkg=bwszkfrag.P_DisplayFinResponsibility%3Fi_url%3Dbwskfreg.P_AltPin')

    # Select the academic year term
    browser.select_form(nr=1)
    form = browser.form
    form['term_in'] = [term, ]

    # Submit the form
    browser.submit()

    # Select the second form in the add/remove class page
    browser.select_form(nr=1)

    for id_tag, crn in classes.items():
        # Convert ID tags to integers
        id_tag_int = int(id_tag)
        # Only valid ID tags and non-spaces will be submitted
        # to the form
        if 1 <= id_tag_int <= 10:
            # Ignore if input is empty
            if crn:
                print 'Attempting to add CRN ' + crn + "..."
                # Assign the CRN as the value based on the form name and crn_id form ID tag
                add_control = browser.form.find_control(name='CRN_IN', id='crn_id' + id_tag)
                add_control.value = crn

    # Submit the form after all textboxes filled in
    browser.submit()

    # Convert all forms to a list to access its key-value pairs
    return list(browser.forms())


def main():
    #Read info.json
    print "Reading info.json"
    try:
        username, password, classes, term = parse_info()
    except KeyError:
        print "There was an error reading your info.json"
        sys.exit(1)
    except:
        print "ERROR: download info.json here: " \
              "https://github.com/jackyliang/Drexel-Shaft-Protection/blob/master/change_me_to_info.json"
        sys.exit(1)
    print '(OK)'

    # Create a new Mechanize browser
    br = mechanize.Browser()

    # Allow redirection as Drexel One has a ton of redirections
    br.set_handle_redirect(True)

    # Log in
    print 'Logging in for: ' + username
    drexel_login(br, username, password)

    # Select the second form in the page which is the select for the academic year
    try:
        br.select_form(nr=1)
    except Exception:
        print 'ERROR: Seems like your login credentials are wrong. Check info.json to make sure!'
        sys.exit(1)

    print '(OK)'

    f = add_classes(br, term, classes)

    # Read the HTML and convert it to XML for traversal
    html = br.response().read()
    root = lxml.html.fromstring(html)

    # Get total credits
    total_credits = root.xpath('/html/body/div[3]/form/table[2]/tr[1]/td[2]/text()')
    try:
            total_credits = total_credits[0].strip(' ')
    except:
            total_credits = '0'

    # Print out all added classes
    print '*****************************************************************'
    print '       All your added classes with total credits: ' + total_credits
    print '*****************************************************************'

    for k,v in f[1]._pairs():
        class_info = ''
        # Ignore dummy values
        if v == 'DUMMY':
            continue
        if k == 'CRN_IN':
            class_info += '[' + v + '] '
        if k == 'SUBJ':
            class_info += v
        if k == 'CRSE':
            class_info += '-' + v
        if k == 'SEC':
            class_info += ' ' + v
        if k == 'TITLE':
            class_info += ' ' + v
            print '    ' + class_info

    # Print out all errors
    print '*****************************************************************'
    print '          All errors will be shown here (if any)'
    print '*****************************************************************'

    for i in range(10):
        # Print all errors
        errors = root.xpath('/html/body/div[3]/form/table[4]/tr[' + str(i) + ']/td/text()')

        # Join the list and print it if not empty
        if errors:
            print '    [x] ' + ' '.join(errors)

if __name__ == "__main__":
    main()
