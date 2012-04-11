#!/usr/bin/python
"""
A moderately labyrinthine script to help LTLMoP developers
set their computer up for working with LTLMoP on GitHub.

Written by Cameron Finucane <cpf37@cornell.edu>
"""

import textwrap, getpass
import sys, math, os, time
import urllib2, json
import subprocess, socket
import base64

def patrickSays(msg):
    # Wrap to an appropriate width between 10 and 60 characters
    # This is super inefficient... but we are using modern computers!
    for wrap_width in xrange(10,60):
        wrapped_msg = textwrap.wrap(msg, wrap_width)
        if len(wrapped_msg) <= 2:
            break
    
    # Fill to at least 2 lines
    while (len(wrapped_msg) < 2):
        wrapped_msg.append("")

    plain_cat = r"""
          /\___/\**
    /   /  .   . \*
    \   \    ^   /*
    \  /        \**
    \ /______  \***
*******************""".replace("*"," ").split("\n")
    
    plain_bubble = r"""
    __{0}_
   /  %-{1}s \
  <   %-{1}s  |
   |  %-{1}s  |
    \_{0}_/
    """.format("_"*wrap_width, wrap_width).split("\n")
    
    # Make the bubble the right size
    extra_height = len(wrapped_msg) - 2
    plain_bubble = plain_bubble[0:4] + [plain_bubble[4]]*max(0,extra_height) + plain_bubble[5:]
    if extra_height <= 0:
        plain_bubble[4] = plain_bubble[4].replace(r" \_", r"\__") # Tweaking

    cat_index, bubble_index, msg_index = (0,0,0)
    while bubble_index < len(plain_bubble):
        if "%" in plain_bubble[bubble_index]:
            print plain_cat[cat_index] + plain_bubble[bubble_index] % (wrapped_msg[msg_index])
            msg_index += 1
        else:
            print plain_cat[cat_index] + plain_bubble[bubble_index]

        cat_index = min(cat_index+1, len(plain_cat)-1)
        bubble_index += 1

def openInBrowser(url):
    if sys.platform in ['win32', 'cygwin']:
        cmd = "start"
        shell = True
    elif sys.platform.startswith('linux'):
        cmd = "xdg-open"
        shell = False
    elif sys.platform == 'darwin':
        cmd = "open"
        shell = True
    else:
        print "Sorry, I don't know how to open the default browser on your computer."
        print "You'll need to visit %s on your own :(" % url
        return

    subprocess.Popen([cmd, url], shell=shell)

def githubAPICall(path, data=None, method=None):
    """
    Relies on GitHub API v3
    """

    headers = {}

    if data is not None:
        data = json.dumps(data)
        headers.update({'Content-Type': 'application/json'})

        # Most likely you want to be POSTing
        if method is None:
            method = "POST"
    else:
        data = ""

        # Most likely you want to be GETing
        if method is None:
            method = "GET"

    if method == "POST":
        req = urllib2.Request("https://api.github.com"+path, data, headers)

        # Work around GitHub bug where the fork request doesn't send back a 401
        # From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/267197
        global github_username, github_password
        base64string = base64.encodestring('%s:%s' % (github_username, github_password))[:-1]
        authheader =  "Basic %s" % base64string
        req.add_header("Authorization", authheader)
    elif method == "PATCH":
        req = urllib2.Request("https://api.github.com"+path, data, headers)
        req.get_method = lambda: "PATCH"
    elif method == "GET":
        req = urllib2.Request("https://api.github.com"+path)
    else:
        print "ERROR: Unknown HTTP method %s!" % method
        return None

    f = urllib2.urlopen(req)
    response = json.load(f) 
    f.close()

    return response

if __name__ == "__main__":
    patrickSays("Hi! I'm a harmless cat who's going to help you out with Git.")

    print
    print "Hey there, let's get you set up to work with LTLMoP on GitHub."
    print "(Tip: If you mess up and want to restart this process, press Ctrl-C at any time to quit.)"
    print

    have_account = ''
    while have_account.lower() not in ['y','n']:
        have_account = raw_input("First off, do you already have an account on GitHub? (y/n): ")

    print
    if have_account.lower() == 'n':
        print "No problem, let's send you over to the GitHub user registration website."
        print "Please sign up for a new account and then come back here when you're done."
        print
        raw_input("Press [Enter] to open up the browser...")
        openInBrowser("https://github.com/signup/free")

        print
        print "OK, awesome.  Welcome back."
    else:
        print "Fantastic.  That will save us some time."

    print
    print "Now you're going to need to give me the login information for your GitHub account."
    print "I promise I won't do anything rude.  Remember, I'm just a harmless cat."
    print

    authenticated = False
    while not authenticated:
        github_username=""
        github_password=""

        while github_username == "":
            github_username = raw_input("Please enter your GitHub username: ")

        while github_password == "":
            print "Please enter your GitHub password"
            github_password = getpass.getpass("(note: the characters will not show up as you type): ")

        authenticated = True

        # Set up authentication to the GitHub website
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm='GitHub',
                      uri='https://api.github.com',
                      user=github_username,
                      passwd=github_password)
        opener = urllib2.build_opener(auth_handler)
        urllib2.install_opener(opener)

        try:
            user_data = githubAPICall("/user")
            email_data = githubAPICall("/user/emails")
        except urllib2.HTTPError as e:
            if e.code == 403:
                print
                print "Invalid login!  Let's try this again."
                print
                authenticated = False
            else:
                print "HTTP Error Code %d. :(  Aborting." % e.code
                sys.exit(1)

    github_fullname = ""
    if 'name' in user_data:
        github_fullname = user_data['name']

    if github_fullname.strip() == "":
        print
        print "It looks like you didn't give GitHub your full name."
        print "As a paranoid cat myself, I respect your decision, but would urge you to"
        print "consider changing your mind.  You should be proud of your work on LTLMoP!"
        print
        print "Please enter your full name (i.e. Firstname Lastname), or"
        github_fullname = raw_input("just press [Enter] to use your username (%s): " % github_username).strip()
        if github_fullname == "":
            github_fullname = github_username

        # Update the GitHub profile
        githubAPICall("/user", {'name': github_fullname}, method="PATCH")

    github_email = email_data[0]

    patrickSays("Nice to meet you, %s! ... My name's Patrick, by the way." % github_fullname.split(" ")[0])
    print

    pubkey_path = os.path.expanduser("~/.ssh/id_rsa.pub")
    if os.path.exists(pubkey_path):
        print "Looks like you already have an SSH key.  We're just going to use that."
        print "(If this isn't what you were expecting, consider deleting ~/.ssh/id_rsa.pub and coming back.)"
        print
        raw_input("Press [Enter] to continue...")
    else:
        print "Next, we need to generate an SSH key to authenticate this computer to GitHub."
        print "Come up with a password that you can remember; you'll need to use it"
        print "when committing code to GitHub."
        print

        # Make the ~/.ssh directory if necessary
        if not os.path.exists(os.path.dirname(pubkey_path)):
            os.mkdir(os.path.dirname(pubkey_path))

        cmd = subprocess.Popen(["ssh-keygen", "-t", "rsa", "-C", github_email, "-f", os.path.splitext(pubkey_path)[0]], shell=True)

        # Wait for subprocess to finish
        while cmd.returncode is None:
            cmd.poll()
            time.sleep(0.1)

    print
    # On windows, we want to use ssh-agent to keep the user from having to
    # type in their ssh password multiple times
    if sys.platform in ['win32', 'cygwin']:
        print "Now just authenticate once for the rest of this session."
        print "Please type in your SSH password."
        cmd = subprocess.Popen(["bash", "-c", "eval `ssh-agent` ssh-add"], shell=True)

        # Wait for subprocess to finish
        while cmd.returncode is None:
            cmd.poll()
            time.sleep(0.1)
        #os.chdir(os.path.expanduser("~/LTLMoP"))
        #cmd = subprocess.Popen(["git","push"],shell=True)
        # Wait for subprocess to finish
        #while cmd.returncode is None:
        #    cmd.poll()
        #    time.sleep(0.1)

    print
    print "Great, thanks.  The rest I can do by myself, so sit back and relax."
    time.sleep(1)

    print
    print "Adding this SSH key to GitHub..."
    print 

    hostname = socket.gethostname().split(".")[0]

    keyfile = open(pubkey_path, 'r')
    pubkey = keyfile.read().strip()
    keyfile.close()

    try:
        githubAPICall("/user/keys", {"title": "%s (%s)" % (github_email, hostname), "key": pubkey})
    except urllib2.HTTPError as e:
        if e.code == 422:
            print "It looks like you probably already have this key enabled.  Skipping this step."
        else:
            print "HTTP Error Code %d. :( Aborting." % e.code
            sys.exit(1)

    print

    repo_data = githubAPICall("/user/repos")
    if any([(r['name'] == "LTLMoP") for r in repo_data]):
        print "Looks like you already have a fork of LTLMoP on GitHub.  Good on you!"
        fresh_fork = False
    else:
        print "Creating a fork of LTLMoP on GitHub for you.  This may take a few minutes..."
        response = githubAPICall("/repos/LTLMoP/LTLMoP/forks", method="POST")
        print "Creation started at URL: " + response['html_url']
        patrickSays("Please wait!")
        print
        sys.stdout.write("Waiting for fork to complete...")
        repo_data = None
        while repo_data is None or not any([(r['name'] == "LTLMoP") for r in repo_data]):
            repo_data = githubAPICall("/user/repos")
            time.sleep(2)
            sys.stdout.write(".")

        fresh_fork = True

        print "\nOkay, looks good!"

    print
    print "Making sure your commits are made under your name..."
    os.system("git config --global --replace-all user.name \"%s\"" % github_fullname)
    os.system("git config --global --replace-all user.email \"%s\"" % github_email)

    if os.path.exists(os.path.expanduser("~/LTLMoP")):
        print "It looks like you already have a LTLMoP folder in your home directory."
        print "If you actually want to clone a new copy, please delete or rename it first and come back."
    else:
        print
        print "Cloning a copy of LTLMoP into your home directory..."
        print "(Tip: If it asks you if you want to continue connecting, type 'yes' and press [Enter])"
        os.system("git clone git@github.com:%s/LTLMoP.git %s" % (github_username, os.path.expanduser("~/LTLMoP")))

    print

    os.chdir(os.path.expanduser("~/LTLMoP"))

    if fresh_fork:
        branch_data = githubAPICall("/repos/%s/LTLMoP/branches" % (github_username))
        print "Deleting extraneous branches to make your life simpler..."

        # Delete all remote branches
        for b in branch_data:
            if b['name'] == "development": continue
            os.system("git push origin :%s" % b['name'])

    print "Adding official repository as `upstream` remote..."
    os.system("git remote add upstream https://github.com/LTLMoP/LTLMoP.git")
    os.system("git fetch upstream development")

    patrickSays("Hooray!  All done!  See you around.")

    print
    print "Your copy of LTLMoP is checked out into %s." % os.path.expanduser("~/LTLMoP")

    print "If you want more guidance, please look at the companion tutorial."

    # TODO: kill ssh-agent?
