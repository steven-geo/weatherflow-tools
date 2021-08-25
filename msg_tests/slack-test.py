import slackmsg

# Replace this with a valid hook/token URL
slack_hook_url = "https://hooks.slack.com/services/XXXXXXXXX/YYYYYYYYY/ZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"

slack = slackmsg.Connect(slack_hook_url, '#general', 'slackmsg module test')

response = slack.send('title', 'messagetext', 'ok')
if response:
    print("Error Sending Message: " + str(response))
